# 聚合 Playbook — 告警簇（Cluster）生成

> 本文件是 SKILL.md Step 2 的细节展开。聚合键、簇字段定义均以 SKILL.md 为唯一真相源。

## 1. 聚合目标

把时间窗内 `N` 条原始告警事件，归并为 `M` 条**告警簇（Cluster）**，且 `M ≪ N`。
聚合后用于 Step 3 分级、Step 4 抑制、Step 5 报告。

**输入**：`jdc monitor describe-alarm-history` 返回的 `$.result.alarmHistoryList[*]`。
**输出**：Cluster 对象列表（`List[Cluster]`），每个 Cluster 对应一种"告警现象"。

## 2. 聚合键定义

### 2.1 主聚合键

```
group_key = (service_code, resource_id, metric_name)
```

三者完全相等的两条告警事件视为"同一现象的重复触发"，归入同一簇。

### 2.2 边界 case 与处理

| 边界 case | 处理策略 | 理由 |
|---|---|---|
| `resource_id` 为空字符串 | 用 `service_code + metric_name` 二元组聚合，并标记 `cluster.is_multi_resource = True` | 资源未指定时通常是"同服务同指标簇"问题 |
| `service_code` 为空 | 整条事件记入 `unknown_clusters` 桶，不参与分级 | 数据缺失，不能编造 |
| `metric_name` 为空 | 整条事件记入 `unknown_clusters` 桶 | 同上 |
| 同 `resource_id` 不同 `metric_name` | **不合并**，生成多个簇，报告里"相关簇"章节关联展示 | 不同指标往往不同根因 |
| 同 `metric_name` 不同 `resource_id` | **不合并**，各自独立成簇 | 资源隔离是云架构基本单位 |
| `status = INSUFFICIENT_DATA` | 单独桶 `insufficient_data_events`，不计入主簇 | 状态语义不同，可能是资源刚启动/数据采集中断 |

### 2.3 簇指纹（fingerprint）

为方便后续检索与去重，给每个 Cluster 计算一个稳定指纹：

```python
import hashlib

def fingerprint(service_code: str, resource_id: str, metric_name: str) -> str:
    raw = f"{service_code}|{resource_id}|{metric_name}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
```

**指纹用途**：跨时间窗追溯、报告里去重显示、写工单时引用。

## 3. 簇字段填充规则

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Cluster:
    fingerprint: str                          # 簇指纹（见 2.3）
    service_code: str                         # 服务代码
    resource_id: str                          # 资源 ID
    metric_name: str                          # 指标名

    # 触发统计
    trigger_count: int = 0                    # 触发次数 = 主簇内 event 数
    first_trigger_at: Optional[datetime] = None   # 首次触发时间（最早）
    last_trigger_at: Optional[datetime] = None    # 末次触发时间（最近）
    last_recover_at: Optional[datetime] = None    # 最近一次恢复时间（如有 OK 事件）

    # 影响面
    affected_resources: List[str] = field(default_factory=list)  # 通常 = [resource_id]
    is_multi_resource: bool = False            # 标记是否跨资源

    # 指标极值
    peak_value: Optional[float] = None         # 触发时的指标峰值
    peak_at: Optional[datetime] = None         # 峰值发生时刻

    # 关联信息
    alarm_rule_ids: List[str] = field(default_factory=list)    # 关联告警规则 ID 列表（去重）
    alarm_event_ids: List[str] = field(default_factory=list)   # 原始告警事件 ID 列表

    # 状态语义
    has_flapping: bool = False                 # 是否抖动（ALARM↔OK 反复 ≥ 3 次）
    flapping_count: int = 0                    # 抖动切换次数

    # 时间窗内最终状态
    current_status: str = "UNKNOWN"            # 时间窗内最后状态: ALARM / OK / UNKNOWN
```

### 3.1 字段填充算法

| 字段 | 计算方法 |
|---|---|
| `trigger_count` | `len(alarm_event_ids)` |
| `first_trigger_at` | `min(triggerTime of all events)` |
| `last_trigger_at` | `max(triggerTime of all events)` |
| `last_recover_at` | `max(recoverTime of all events where status == 'OK')` |
| `duration_seconds` | `(last_trigger_at - first_trigger_at).total_seconds()` |
| `peak_value` | `max(value of all events)` |
| `peak_at` | 触发 `peak_value` 的那次 `triggerTime` |
| `affected_resources` | `list(set([resource_id]))` |
| `alarm_rule_ids` | `list(set([event.alarmId for event in events]))` |
| `has_flapping` | `flapping_count >= 3` |
| `current_status` | 时间窗内最后一条事件的 `status` |

> **注意**：`duration_seconds` 不包含恢复后的"静默期"，仅代表"首次到最后一次触发"的实际跨度。Step 3 分级时若需"业务影响时长"，应再叠加上 `last_recover_at - last_trigger_at`（未恢复则用 `now - last_trigger_at`）。

## 4. 聚合伪代码（Python）

```python
import json
import subprocess
from collections import defaultdict
from datetime import datetime

def fetch_alarm_events(region: str, start_iso: str, end_iso: str) -> list:
    """Step 1: 拉取原始告警事件（含分页处理）"""
    events = []
    page = 1
    while True:
        cmd = [
            "jdc", "--output", "json", "monitor", "describe-alarm-history",
            "--region-id", region,
            "--start-time", start_iso,
            "--end-time", end_iso,
            "--page-number", str(page),
            "--page-size", "100",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        batch = data.get("result", {}).get("alarmHistoryList", [])
        if not batch:
            break
        events.extend(batch)
        if len(batch) < 100:  # 末页
            break
        page += 1
    return events


def aggregate_to_clusters(events: list) -> tuple:
    """Step 2: 聚合为 Cluster 列表 + 异常桶"""
    buckets = defaultdict(list)
    insufficient = []
    unknown = []

    for ev in events:
        sc = ev.get("serviceCode", "")
        rid = ev.get("resourceId", "")
        mn = ev.get("metricName", "")

        # 异常状态分离
        if ev.get("status") == "INSUFFICIENT_DATA":
            insufficient.append(ev)
            continue
        if not sc or not mn:  # resource_id 可空
            unknown.append(ev)
            continue

        # 主聚合键
        key = (sc, rid, mn) if rid else (sc, "<empty>", mn)
        buckets[key].append(ev)

    # 构建 Cluster
    clusters = []
    for (sc, rid, mn), evs in buckets.items():
        c = Cluster(
            fingerprint=fingerprint(sc, rid, mn),
            service_code=sc,
            resource_id=rid,
            metric_name=mn,
        )
        _fill_cluster(c, evs)
        clusters.append(c)

    return clusters, insufficient, unknown


def _fill_cluster(c: Cluster, events: list) -> None:
    """填充 Cluster 字段（实现见 §3.1）"""
    c.alarm_event_ids = [e["alarmId"] for e in events]
    c.alarm_rule_ids = list({e.get("alarmRuleId", e["alarmId"]) for e in events})
    c.trigger_count = len(events)

    times = [_parse_dt(e["triggerTime"]) for e in events]
    c.first_trigger_at = min(times)
    c.last_trigger_at = max(times)

    rec_times = [_parse_dt(e["recoverTime"]) for e in events
                 if e.get("status") == "OK" and e.get("recoverTime")]
    if rec_times:
        c.last_recover_at = max(rec_times)

    # 峰值
    values = [(e.get("value"), _parse_dt(e["triggerTime"]))
              for e in events if e.get("value") is not None]
    if values:
        peak_v, peak_t = max(values, key=lambda x: x[0])
        c.peak_value = peak_v
        c.peak_at = peak_t

    # 抖动检测：按时间排序后统计 ALARM↔OK 切换
    sorted_evs = sorted(events, key=lambda e: _parse_dt(e["triggerTime"]))
    flips = 0
    prev = None
    for e in sorted_evs:
        st = e.get("status")
        if prev and st != prev and st in ("ALARM", "OK"):
            flips += 1
        prev = st
    c.flapping_count = flips
    c.has_flapping = flips >= 3

    c.affected_resources = list({c.resource_id})
    c.is_multi_resource = c.resource_id == "<empty>"
    c.current_status = sorted_evs[-1].get("status", "UNKNOWN") if sorted_evs else "UNKNOWN"


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
```

## 5. 边界 case 详解

### 5.1 告警抖动（Flapping）

**定义**：在时间窗内，同一聚合键的状态在 `ALARM` ↔ `OK` 之间反复切换 ≥ 3 次。

**处理**：

1. 仍归入一个 Cluster（不拆分），因为根因未变。
2. 设 `has_flapping = True`，`flapping_count` 记切换次数。
3. 在报告中**显式标记"抖动"**，建议用户检查告警阈值是否在临界值附近（这是配置问题，委派 `jdcloud-cloudmonitor-ops`）。

**示例**：阈值 80%，指标在 79.5% ~ 80.5% 抖动 → 每 5 分钟触发一次。

### 5.2 同资源不同指标

**不合并**，各自成簇。**但在报告中**用"相关簇"小节关联展示。

**理由**：CPU 高 + 内存高 + 磁盘满 三个独立簇可能是**同一根因**（如资源被攻击），但也可能是**三个独立问题**（如应用慢 + 内存泄漏 + 日志未清理）。让用户判断，不替用户做决定。

### 5.3 跨资源同指标

**不合并**。这是云监控的"反模式"——`resource_id` 缺失时应补全，或在告警规则里用模板变量指定资源维度。

**处理**：标记 `is_multi_resource = True`，在报告中作为"宽泛告警"提示，建议用户优化告警规则。

### 5.4 INSUFFICIENT_DATA

**单独桶**，不计入主簇统计。报告中作为"数据缺失"独立章节提示用户。

**典型原因**：

- 资源刚创建 < 5min
- 资源已关机/删除
- 监控采集端到端链路异常（云监控自身问题）

### 5.5 OK 事件是否参与聚合

**参与**，但仅用于：

- 计算 `last_recover_at`（最近恢复时间）
- 抖动检测（`flapping_count`）
- `current_status` 取时间窗内最后一条

**不参与**：`trigger_count`（OK 不算触发）、`peak_value`（OK 时 value 通常是正常值，会拉低峰值）。

## 6. 聚合结果样例

时间窗 `2026-06-02 00:00 ~ 2026-06-03 00:00` 内，原始 312 条告警事件聚合后：

| fingerprint | service | resource_id | metric | 触发次数 | 持续时长 | 峰值 | 状态 | 抖动 |
|:--|:--|:--|:--|--:|--:|--:|:--|:--:|
| a3f2c1b8d4e5 | vm | i-abc123 | vm.cpu.util | 47 | 23h12m | 96.3% | ALARM | 否 |
| 7e9b2c5f1a83 | vm | i-abc123 | vm.memory.util | 12 | 8h45m | 88.1% | OK | 是 |
| b1c3d4e5f6a7 | rds | rds-xyz789 | rds.cpu.util | 8 | 2h30m | 91.0% | ALARM | 否 |
| 2d8e4f1a3c5b | lb | lb-mno456 | lb.httpcode.5xx | 124 | 23h58m | 47/s | ALARM | 是 |
| 9c1b3a5d7e2f | redis | redis-qwe321 | redis.memory.util | 3 | 45m | 75.0% | OK | 否 |
| 5e7a9b1c3d2f | vm | `<empty>` | vm.disk.util | 15 | 12h | 92.0% | ALARM | 否 |

**说明**：

- 312 条原始事件 → 6 条主簇 + 2 条 insufficient_data + 1 条 unknown
- 4 个簇标 P0/P1 候选，2 个簇明显是误报（已恢复 + 持续短）
- LB 簇是典型的"反复触发"——配合 cloudmonitor-ops 检查阈值

## 7. 性能与限制

| 指标 | 限制 | 说明 |
|---|---|---|
| 单次拉取最大事件数 | 10,000 | `describe-alarm-history` 单窗口建议 ≤ 10k |
| 超过 10k 怎么办 | 分窗口聚合 | 拆为多个 24h 窗口分别聚合，再合并 Cluster（用 fingerprint 去重） |
| 内存占用 | O(N) | 1 万事件 ≈ 5MB JSON 解析后 ≈ 15MB 对象 |
| 时间复杂度 | O(N) | 单次遍历 + dict 累加 |
| 推荐硬上限 | 50,000 | 超过建议缩窗到 7d，或先做时间窗过滤再聚合 |

**分窗口聚合示例**：

```python
# 7d 数据分 7 个 1d 窗口
clusters_by_day = []
for day_offset in range(7):
    start, end = _day_range(day_offset)
    events = fetch_alarm_events(region, start, end)
    day_clusters, _, _ = aggregate_to_clusters(events)
    clusters_by_day.append(day_clusters)

# 合并：同 fingerprint 视为同一簇，累加 trigger_count
merged = {}
for day_clusters in clusters_by_day:
    for c in day_clusters:
        if c.fingerprint not in merged:
            merged[c.fingerprint] = c
        else:
            _merge_clusters(merged[c.fingerprint], c)
```

`_merge_clusters` 实现：累加 `trigger_count`，取 `min(first_trigger_at)` / `max(last_trigger_at)` / `max(peak_value)`，合并 `alarm_event_ids` / `alarm_rule_ids`。

## 8. 与 Step 3/4 的交接

聚合完成后，向 Step 3（分级）传入：

- `clusters: List[Cluster]`（主簇）
- `insufficient_data_events: list`（数据缺失桶，单独提示）
- `unknown_events: list`（数据异常桶，单独提示）

向 Step 5（报告）额外传入：

- `cluster.is_multi_resource`（宽泛告警标记）
- `cluster.has_flapping`（抖动标记）
- `cluster.flapping_count`（抖动次数）

详细分级规则见 [references/severity-matrix.md](./severity-matrix.md) 和 [references/playbook-classify.md](./playbook-classify.md)。
