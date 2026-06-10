# 抑制执行手册 (Playbook · Suppression)

> 配套 [SKILL.md §Step 4 抑制](../SKILL.md)；本文件为**执行层**——给出三类抑制源的判定算法、
> 已知误报清单的展开、以及 `suppress_cluster()` 的可运行伪代码。
>
> 本手册**只读**：不修改任何告警规则或资源配置；只对已分级的告警簇做降档或过滤。

## 1. 抑制总流程

```
输入: 已分级的告警簇列表 clusters: List[Cluster]
                (每个 Cluster 含 service_code, resource_id, metric_name,
                 severity ∈ {P0, P1, P2, P3}, first_seen, last_seen, count, ...)

for cluster in clusters:
    ├─ 1) 维护窗匹配        → 命中 → suppressed_by='maintenance', severity = _demote_one()
    ├─ 2) 周期性检测        → 命中 → suppressed_by='periodic',    severity = _demote_one()
    └─ 3) 已知误报匹配      → 命中 → suppressed_by='known_fp',    severity = P3 (跨级豁免)

输出: List[Cluster], 每个 Cluster 追加
       - suppressed: bool
       - suppressed_by: Optional[str]   # 'maintenance' | 'periodic' | 'known_fp'
       - original_severity: 'P0'|'P1'|'P2'|'P3'
       - final_severity:    'P0'|'P1'|'P2'|'P3'
       - suppression_reason: Optional[str]   # 命中条件的人类可读描述
```

**降档规则（两段式，权威源：core-concepts.md §1.4）：**

| 命中 | 降档 | 示例 |
|---|:--:|---|
| 维护窗 | -1 档 | P0→P1, P1→P2, P2→P3 |
| 已知周期性 | -1 档 | P0→P1, P1→P2, P2→P3 |
| 已知误报清单 | → P3 | P0/P1/P2 → P3（跨级豁免）|

**约束**：
- P3 不再降
- 维护窗/周期性**不跨级**（只能逐级降一档）
- 已知误报清单跨级豁免
- 多个命中时按"最重抑制"原则：已知误报 > 已知周期性 > 维护窗

> 设计原则：抑制不是"删告警"，而是"降档 (demote) + 标记原因"，以便 on-call 复盘时仍能看到原始告警。

## 2. 维护窗识别实现

### 2.1 数据来源

| 来源 | 字段 | 格式 |
|---|---|---|
| 资源 tag | `tags.maintenance_window` | `START/END` ISO8601 区间串 |
| 资源 tag | `tags.maintenance_recurring` | Cron-like `0 2 * * *` 表示每天 02:00 起 |
| 用户显式声明 | 本次分析调用的 `--maintenance-window` 参数 | `START,END` |

> tag 拉取需要先调各产品 `describe-*` 接口；本 skill v0.1 假设 tag 已由上游封装在
> `cluster.resource_tags: Dict[str, str]` 中（聚合阶段已合并）。若 tag 缺失，按"无维护窗"处理。

### 2.2 匹配算法

**输入区间维护窗 `window = (start_ts, end_ts)`，告警触发时间 `t`（epoch ms）**：

```
is_in_window(t, window) =
    let (s, e) = window
    in s <= t < e
```

**一次性窗口与循环窗口统一处理**：

- 一次性：`window = (start, end)` 直接判定
- 循环（如每天 02:00-04:00）：展开为"今日 + 昨日"两个一次性窗口后判定
  - 例：cluster 触发时间 2026-06-03 02:30 → 检查 2026-06-03T02:00:00+08:00 / 2026-06-03T04:00:00+08:00

### 2.3 伪代码

```python
from datetime import datetime, timezone
from typing import Optional, Tuple, List

Window = Tuple[datetime, datetime]  # (start, end) tz-aware

def parse_resource_tag(tag_value: str) -> Optional[Window]:
    """'2026-06-03T02:00:00+08:00/2026-06-03T04:00:00+08:00' -> Window"""
    try:
        s, e = tag_value.split("/")
        return (
            datetime.fromisoformat(s),
            datetime.fromisoformat(e),
        )
    except Exception:
        return None

def parse_cron_window(cron_expr: str, on_date: datetime) -> Optional[Window]:
    """v0.1 仅支持 'M H * * *' 形式。返回 on_date 当天的一次性窗口。"""
    # 简化实现：解析 'M H'，构造当天 H:M 到 H:M+2h 的窗口
    # 完整 cron 解析留给 v0.2
    parts = cron_expr.split()
    if len(parts) != 5 or parts[2:] != ["*", "*", "*"]:
        return None
    minute, hour = int(parts[0]), int(parts[1])
    start = on_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    end   = start.replace(hour=(hour + 2) % 24)  # 默认 2h 窗口
    return (start, end)

def in_any_window(t: datetime, windows: List[Window]) -> bool:
    return any(s <= t < e for s, e in windows)

def match_maintenance(cluster, user_declared: List[Window]) -> Optional[str]:
    """返回命中原因描述；未命中返回 None。"""
    t = cluster.first_seen  # 用首次触发时间判定

    # 来源 1: 资源 tag（一次性）
    tag_once = cluster.resource_tags.get("maintenance_window")
    if tag_once:
        w = parse_resource_tag(tag_once)
        if w and in_any_window(t, [w]):
            return f"资源 tag 维护窗 {tag_once}"

    # 来源 2: 资源 tag（循环）
    tag_cron = cluster.resource_tags.get("maintenance_recurring")
    if tag_cron:
        w = parse_cron_window(tag_cron, t)
        if w and in_any_window(t, [w]):
            return f"资源 tag 循环维护窗 {tag_cron} (展开 {w[0].isoformat()}/{w[1].isoformat()})"

    # 来源 3: 用户本次显式声明
    if user_declared and in_any_window(t, user_declared):
        return f"用户本次显式声明维护窗 (共 {len(user_declared)} 个)"

    return None
```

## 3. 周期性检测实现

### 3.1 数据来源

周期性检测**需要历史数据**——必须额外拉取"目标告警簇"对应规则在过去 **7 天同时段**的触发记录。

```bash
# 1. 先获取当前簇的告警规则 ID（cluster.alarm_rule_ids）
# 2. 拉历史 7d 同规则告警
#    v0.1 限制: jdc CLI 单次只能传 1 个 alarm-id (单数 string); 多规则需循环调用
jdc --output json monitor describe-alarm-history \
  --region-id "${JDC_REGION:-cn-north-1}" \
  --alarm-id "alarm-xxx" \
  --start-time "<now-7d>" \
  --end-time   "<now>" \
  --page-size 200
```

> 注意：原始告警数据保留 15d，7d 在保留期内。更大窗口（如 30d）需用 1h 聚合接口，超出 v0.1 范围。

### 3.2 时间窗匹配算法

**目标**：判断"今天这次告警"是不是"周期性发生"。

```
判定步骤:
  1. 取 cluster.first_seen 在 24h 制下的 (hour, minute) → target_hm
  2. 在历史 7d 数据中，筛选 (hour, minute) 落在 [target_hm - 30min, target_hm + 30min] 的所有触发
  3. 统计不同日期数量 distinct_days
  4. distinct_days >= 3 → 判定为周期性
```

**为什么 ±30min？** 业务周期（备份、批处理）通常精度 ±15min；放宽到 30min 防止漏判；过宽（如 ±2h）则
易把"同资源不同周期"误判为同一周期。

**为什么 ≥ 3 天？** 7d 中出现 3 天（≥ 43% 频率）即可视为"显著周期"。若需 ≥ 5 天，可在配置项中调整。

### 3.3 伪代码

```python
from datetime import timedelta
from collections import defaultdict

PERIODIC_WINDOW_MIN = 30   # ±30min
PERIODIC_DAY_THRESHOLD = 3 # 7d 中 ≥ 3 天

def fetch_history_alarms(alarm_rule_ids, region, end_ts) -> List[dict]:
    """调用 jdc monitor describe-alarm-history 拉 7d 历史。"""
    start_ts = end_ts - timedelta(days=7)
    # 实际通过 jdc CLI / SDK 调用，结果为 List[dict]
    # 每条 dict 含 alarmId, resourceId, metricName, triggerTime
    # v0.1 由调用方实现，签名预留
    raise NotImplementedError  # 由上层注入

def match_periodic(cluster, history_alarms: List[dict]) -> Optional[str]:
    target = cluster.first_seen
    target_lo = target - timedelta(minutes=PERIODIC_WINDOW_MIN)
    target_hi = target + timedelta(minutes=PERIODIC_WINDOW_MIN)

    matched_days = set()
    for h in history_alarms:
        if h["alarmId"] not in cluster.alarm_rule_ids:
            continue
        if h["resourceId"] != cluster.resource_id:
            continue
        if h["metricName"] != cluster.metric_name:
            continue
        ht = h["triggerTime"]
        if target_lo <= ht <= target_hi:
            matched_days.add(ht.date())

    if len(matched_days) >= PERIODIC_DAY_THRESHOLD:
        return (
            f"近 7d 同时段(±{PERIODIC_WINDOW_MIN}min)出现 {len(matched_days)} 天"
            f"(阈值 {PERIODIC_DAY_THRESHOLD})"
        )
    return None
```

**注意：** 周期性检测是**有副作用的**——它需要额外拉一次历史数据。如果历史数据接口调用失败，
按"无法判定"处理，**不**降档（避免误抑制真正的故障）。

## 4. 已知误报匹配实现

### 4.1 5 类已知误报清单

| 编号 | 类别 | 特征 metric | 时间模式 | 典型表现 |
|:--|:--|:--|:--|:--|
| FP1 | 备份任务 | `vm.disk.io.write` 或 `vm.network.out` 突增 | 凌晨 02:00 - 04:00 | 单次持续 5-30min，VM 自身 CPU 不高 |
| FP2 | 批处理 | `rds.cpu.util` 或 `rds.connections.active` 突增 | 整点/半点 ±10min | 持续 < 10min 后自动回落 |
| FP3 | 滚动重启 | 多 VM 同时 `vm.cpu.util` 高 | 短窗口（5min）内多资源 | 通常紧跟一次 "status=OK→running" 切换 |
| FP4 | CD 流量回切 | `lb.newconnection` 或 `lb.traffic.in` 突增 | 发布完成后 5-15min | 5min 内自动恢复，伴随 `lb.httpcode.5xx` 不变 |
| FP5 | 镜像/包拉取 | `vm.network.out` 短时高峰 | 任意时间，但单次 < 5min | 伴随 CDN/对象存储同区域流量同向 |

### 4.2 匹配策略

每类误报都是一个 `(metric_pattern, time_window, duration_pattern, supplementary)` 的复合判定：

- `metric_pattern`: 命中的指标名/前缀
- `time_window`: 触发时间是否在常见业务时段（如 02:00-04:00）
- `duration_pattern`: 持续时长是否符合该类误报的典型时长
- `supplementary`: 辅助证据（可选，如"同时间 rds.cpu 不高"）

**匹配优先级**：维护窗 > 周期性 > 已知误报；已知误报内部按表 4.1 顺序匹配，命中即返回。

### 4.3 伪代码

```python
from datetime import time as dtime
from typing import Optional, List, Dict

# ---------- 已知误报规则表 ----------
KNOWN_FALSE_POSITIVES: List[Dict] = [
    {
        "id": "FP1",
        "name": "备份任务",
        "metric_prefix": ["vm.disk.io.", "vm.network.out"],
        "time_window": (dtime(2, 0), dtime(4, 0)),
        "max_duration_sec": 30 * 60,
        "min_duration_sec": 5 * 60,
        "description": "凌晨 2-4 点磁盘/网络写突增，符合备份任务特征",
    },
    {
        "id": "FP2",
        "name": "批处理",
        "metric_prefix": ["rds.cpu.util", "rds.connections.active"],
        # 整点/半点: 触发时间 minute ∈ {0, 30} ± 10
        "minute_set": {0, 30},
        "minute_tolerance": 10,
        "max_duration_sec": 10 * 60,
        "min_duration_sec": 0,
        "description": "整点/半点 rds 指标突增，< 10min 自动恢复",
    },
    {
        "id": "FP3",
        "name": "滚动重启",
        "metric_prefix": ["vm.cpu.util"],
        "min_resource_count": 3,         # ≥ 3 个 VM 同时
        "max_duration_sec": 5 * 60,
        "supplementary_check": "post_ok_transition",  # 需在 v0.2 关联 status 历史
        "description": "多 VM 同时 CPU 突增 5min 内，常因滚动重启",
    },
    {
        "id": "FP4",
        "name": "CD 流量回切",
        "metric_prefix": ["lb.newconnection", "lb.traffic.in"],
        "min_duration_sec": 0,
        "max_duration_sec": 5 * 60,
        "supplementary_check": "no_5xx_increase",
        "description": "LB 新建连接突增 5min 内回落，无 5xx 伴随",
    },
    {
        "id": "FP5",
        "name": "镜像/包拉取",
        "metric_prefix": ["vm.network.out"],
        "min_duration_sec": 0,
        "max_duration_sec": 5 * 60,
        "supplementary_check": "cdn_correlated",
        "description": "VM 出流量短时高峰，与 CDN/对象存储同区域流量同向",
    },
]

# ---------- 匹配实现 ----------
def _in_time_window(t, win_start: dtime, win_end: dtime) -> bool:
    return win_start <= t.time() < win_end

def _minute_match(t, minute_set, tolerance) -> bool:
    m = t.minute
    return any(abs(m - target) <= tolerance or abs(m - target - 60) <= tolerance
               for target in minute_set)

def match_known_fp(cluster, supplementary_data: Optional[dict] = None) -> Optional[str]:
    duration = (cluster.last_seen - cluster.first_seen).total_seconds()
    first_t = cluster.first_seen

    for rule in KNOWN_FALSE_POSITIVES:
        # 1. metric 匹配
        if not any(cluster.metric_name.startswith(p) for p in rule["metric_prefix"]):
            continue

        # 2. 时长匹配
        if duration > rule.get("max_duration_sec", float("inf")):
            continue
        if duration < rule.get("min_duration_sec", 0):
            continue

        # 3. 时间窗匹配
        if "time_window" in rule:
            if not _in_time_window(first_t, *rule["time_window"]):
                continue
        if "minute_set" in rule:
            if not _minute_match(first_t, rule["minute_set"], rule["minute_tolerance"]):
                continue

        # 4. 资源数匹配（如滚动重启）
        if "min_resource_count" in rule:
            if cluster.affected_resource_count < rule["min_resource_count"]:
                continue

        # 5. 辅助证据（v0.1 仅占位；v0.2 接 rca-engine）
        supp = rule.get("supplementary_check")
        if supp and not _check_supplementary(cluster, supp, supplementary_data):
            continue

        return f"命中已知误报 [{rule['id']}] {rule['name']}: {rule['description']}"

    return None

def _check_supplementary(cluster, check_name: str, data: Optional[dict]) -> bool:
    """v0.1: 占位实现，所有 supplementary_check 一律返回 True (不阻断匹配)。
    v0.2: 接入 jdcloud-rca-engine 后实现。
    """
    return True
```

### 4.4 误报规则扩展

如需新增误报类型，向 `KNOWN_FALSE_POSITIVES` 追加一项即可。**不要修改现有规则**——保持可审计。

新增规则前应回答：
- 该误报的"指纹"是什么（metric + 时间 + 时长三元组）？
- 历史 30d 中此误报至少出现几次？（< 5 次不收录）
- 是否会产生"漏判真故障"的风险？（高风险场景不收录）

## 5. 抑制决策主流程

```python
from typing import List, Optional, Dict

def suppress_cluster(
    cluster,
    user_declared_windows: List[Window],
    history_alarms: Optional[List[dict]] = None,
    supplementary_data: Optional[dict] = None,
) -> Cluster:
    """对单个告警簇执行三类抑制判定。返回新 Cluster，不修改入参。

    权威源: core-concepts.md §1.4 R1 (两段式抑制降档)
    - 维护窗 / 周期性：降一档
    - 已知误报清单：跨级降为 P3
    """

    # 记录原始级别
    cluster.original_severity = cluster.severity
    cluster.suppressed = False
    cluster.suppressed_by = None
    cluster.suppression_reason = None

    # ---------- 1. 维护窗 (降一档) ----------
    reason = match_maintenance(cluster, user_declared_windows)
    if reason:
        cluster.suppressed = True
        cluster.suppressed_by = "maintenance"
        cluster.suppression_reason = reason
        cluster.severity = _demote_one(cluster.severity)  # P0->P1, P1->P2, P2->P3, P3->P3
        return cluster

    # ---------- 2. 周期性 (降一档) ----------
    if history_alarms is not None:
        reason = match_periodic(cluster, history_alarms)
        if reason:
            cluster.suppressed = True
            cluster.suppressed_by = "periodic"
            cluster.suppression_reason = reason
            cluster.severity = _demote_one(cluster.severity)
            return cluster
    # 注: history_alarms 为 None 时跳过此项（不阻断）

    # ---------- 3. 已知误报 (跨级降为 P3) ----------
    reason = match_known_fp(cluster, supplementary_data)
    if reason:
        cluster.suppressed = True
        cluster.suppressed_by = "known_fp"
        cluster.suppression_reason = reason
        cluster.severity = "P3"  # 跨级豁免
        return cluster

    # ---------- 未命中任何抑制 ----------
    cluster.final_severity = cluster.severity
    return cluster


_DEMOTE_ORDER = ["P0", "P1", "P2", "P3"]

def _demote_one(severity: str) -> str:
    """降一档：P0->P1, P1->P2, P2->P3, P3->P3。权威源: core-concepts.md §1.4"""
    try:
        idx = _DEMOTE_ORDER.index(severity)
    except ValueError:
        return "P3"
    # P3 (idx=3) 保持 P3; 其他降一档
    return _DEMOTE_ORDER[min(idx + 1, 3)]


def suppress_all(
    clusters: List[Cluster],
    user_declared_windows: List[Window],
    history_alarms: Optional[List[dict]] = None,
    supplementary_data: Optional[dict] = None,
) -> Dict:
    """批量抑制，并返回统计指标。"""
    suppressed_count = 0
    downgrade_count = 0
    original_p0_to_p3 = 0

    for c in clusters:
        before = c.severity
        suppress_cluster(c, user_declared_windows, history_alarms, supplementary_data)
        c.final_severity = c.severity
        if c.suppressed:
            suppressed_count += 1
            if before != c.severity:
                downgrade_count += 1
                if before == "P0" and c.severity == "P3":
                    original_p0_to_p3 += 1

    return {
        "suppressed_count": suppressed_count,
        "downgrade_count": downgrade_count,
        "original_p0_to_p3_count": original_p0_to_p3,
        "by_source": _count_by_source(clusters, "suppressed_by"),
    }

def _count_by_source(clusters, field):
    from collections import Counter
    c = Counter()
    for cl in clusters:
        if cl.suppressed:
            c[cl.suppressed_by] += 1
    return dict(c)
```

## 6. 抑制效果报告字段

报告（`assets/report-template.md`）"降噪统计"段使用以下字段：

| 字段 | 含义 | 公式 |
|---|---|---|
| `total_clusters` | 聚合后总簇数 | 入参 clusters 长度 |
| `suppressed_count` | 命中任一抑制的簇数 | `count(c.suppressed for c in clusters)` |
| `suppression_rate` | 抑制率 | `suppressed_count / total_clusters` |
| `by_source.maintenance` | 维护窗命中数 | `_count_by_source(...)['maintenance']` |
| `by_source.periodic` | 周期性命中数 | 同上 |
| `by_source.known_fp` | 已知误报命中数 | 同上 |
| `downgrade_count` | 发生降档的簇数 | `before_severity != final_severity` |
| `original_p0_to_p3_count` | 原 P0 被压成 P3 的数 | 高风险指标，应受监控 |
| `suppression_failures` | 抑制环节出错数 | jdc 拉历史失败、tag 解析异常等 |

> **审计要求**：`original_p0_to_p3_count` 在 v0.1 降一档模式下**仅在已知误报清单命中时发生**（误报跨级豁免到 P3）。
> 维护窗/周期性命中下 P0 仅降到 P1，**不会**进入 original_p0_to_p3_count 统计。
> 若该值 > 0，必须在报告中高亮显示"以下 P0 告警被误报规则压成 P3，请人工复核"。

## 7. 不做的事（v0.1 范围外）

- ❌ ML 异常检测（v0.3）
- ❌ 动态阈值建议（v0.3）
- ❌ 跨账户/跨云聚合
- ❌ 自动开 jdcloud 工单（v0.4）
- ❌ 告警回调 Webhook 消费（v0.2）
- ❌ 相似工单检索（v0.2 依赖 jdcloud-rca-engine）
- ❌ 抑制规则的"自学习"——v0.1 规则为静态，由人工维护

## 8. 异常处理

| 异常 | 行为 |
|---|---|
| `cluster.resource_tags` 为 None 或缺失 | 按"无维护窗"处理，不阻断 |
| `history_alarms` 拉取失败（jdc 重试 3 次后仍失败） | 跳过周期性检测，**不降档**；在报告 `suppression_failures` 字段记录 |
| 资源 tag 格式非法 | 解析失败按"无维护窗"处理；不抛出 |
| 同一簇同时命中维护窗 + 周期性 + 已知误报 | 按优先级（维护窗 > 周期性 > 已知误报）取第一个，**不重复降档** |
| 抑制导致 final_severity=P3 但 cluster.count 仍很大 | 仍标记为 P3；报告的"Top 簇"按 count 排序，不受 final_severity 影响 |

## 9. 与上下游的契约

**上游（playbook-classify）** 须保证每个 cluster 至少含：

```
Cluster(
    service_code: str        # 来自 jdc 告警
    resource_id: str
    metric_name: str
    severity: 'P0'|'P1'|'P2'|'P3'  # 已分级
    first_seen: datetime     # tz-aware
    last_seen:  datetime
    count: int
    affected_resource_count: int  # 默认 1，跨资源簇时 > 1
    resource_tags: Dict[str, str] # 可选，缺失则按空处理
    alarm_rule_ids: List[str]     # 用于周期性检测
)
```

**下游（report 渲染）** 读取本手册 §6 的 9 个字段渲染"降噪统计"段。
