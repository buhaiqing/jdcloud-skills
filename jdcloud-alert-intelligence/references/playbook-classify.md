# 告警分级 Playbook (playbook-classify)

> 本文件定义 `jdcloud-alert-intelligence` v0.1 的**分级 (Classify)** 步骤。
> 输入是 [playbook-aggregate.md](./playbook-aggregate.md) 输出的**告警簇 (Cluster)**，
> 输出是 **P0 / P1 / P2 / P3** 4 级标签。
> 完整矩阵见 [severity-matrix.md](./severity-matrix.md)；本文件重点是**判定流程 + 边界 case**。

## 与 SKILL.md 的契约

| 项 | 值 | 来源 |
|---|---|---|
| 输入 | `Cluster` 对象 (见 playbook-aggregate.md) | Step 2 输出 |
| 输出 | 字符串 `"P0" / "P1" / "P2" / "P3"` | — |
| 判定维度 | 影响面 × 持续时间 × 频次 | SKILL.md § Step 3 |
| 业务影响等级 | core / important / general / peripheral | severity-matrix.md |
| v0.1 限制 | 规则引擎，**不**用 ML | SKILL.md § 核心约束 |

---

## 1. 分级流程（5 步）

```
cluster = 聚合后的告警簇
  │
  ├─ Step 1. 提取三维原始值
  │     - impact_scope:    影响资源数 + 服务代码 + 业务标签
  │     - duration_min:    持续时长（分钟）
  │     - frequency:       单位时间触发次数（次/小时）
  │
  ├─ Step 2. 查业务影响等级
  │     - 由 service_code + 资源 tag.business 决定
  │     - 见下方"§2 影响面评估细则"
  │
  ├─ Step 3. 持续时长分档
  │     - < 5min     → short
  │     - 5-30min    → mid
  │     - > 30min    → long
  │
  ├─ Step 4. 频次分档
  │     - < 3 次/小时  → low
  │     - 3-10 次/小时 → mid
  │     - > 10 次/小时 → high
  │
  └─ Step 5. 查 severity-matrix.md 命中单元 → 输出 P0/P1/P2/P3
```

**重要原则：先分级 → 后抑制**。抑制步骤（playbook-suppress.md）会**降档 (demote)**已分好的标签。

---

## 2. 影响面评估细则

影响面 = **资源数** + **服务代码** + **业务标签** 三个因子。

### 2.1 资源数量阈值

| 资源数 (`len(cluster.resource_ids)`) | 标记 |
|---|---|
| = 1 | `single` |
| 2 - 3 | `few` |
| ≥ 4 | `multi`（注意：聚合键含 `resource_id`，多资源通常意味着不同簇；出现"多资源单簇"通常是同一 LB 后端的多 VM） |

> **注**：聚合键含 `resource_id`，理论上"多资源单簇"较少见。若出现，需在报告中标注"该簇跨 N 个资源"以引起注意。

### 2.2 服务代码白名单（哪些算"核心业务"）

| service_code | 业务影响默认 | 备注 |
|---|---|---|
| `lb`（负载均衡） | **core** | 入口层故障=全局影响 |
| `rds`（云数据库） | **core** | 数据层故障=全局影响 |
| `redis`（缓存） | **important** | 性能下降常见，但通常不直接中断 |
| `vm`（云主机） | 取决于 tag | 单 VM = general；集群节点 = important/core |
| `eip`（公网 IP） | **important** | 影响外部访问 |
| `oss`（对象存储） | **general** | 通常不中断 |
| `cdn` | **important** | 边缘可用性 |
| 其他 (`monitor`/`nat`/`vpc` 等) | **general** | 控制面告警需人工评估 |

> **白名单外的服务**：默认为 `general`。若用户标记过 `business=core`，以 tag 为准。

### 2.3 业务标签识别

资源 tag 中读取 `business` 字段（需资源元数据支持，v0.1 通过 `describe-instance` 或 `describe-resource` 拉取）：

| tag 值 | 业务等级 |
|---|---|
| `business=core` | core（覆盖默认值） |
| `business=important` | important |
| `business=general` | general |
| `business=peripheral` | peripheral |
| 无 tag | 走 service_code 默认值 |

> **v0.1 简化**：若 tag 拉取失败，按 service_code 默认值走，并在报告"数据局限"章节标注"业务标签未识别"。

### 2.4 影响面最终值

| 判定条件 | `impact_scope` |
|---|---|
| 资源数 = `multi` **或** 业务等级 = `core` | `wide` |
| 资源数 = `few` **或** 业务等级 = `important` | `moderate` |
| 资源数 = `single` 且 业务等级 = `general` | `narrow` |
| 资源数 = `single` 且 业务等级 = `peripheral` | `minimal` |

---

## 3. 持续时间评估细则

### 3.1 三档定义

| 档位 | 区间 | 标识 |
|---|---|---|
| 短 | `duration_min < 5` | `short` |
| 中 | `5 <= duration_min <= 30` | `mid` |
| 长 | `duration_min > 30` | `long` |

### 3.2 "持续时长"如何计算

```
duration_min = cluster.last_trigger_time - cluster.first_trigger_time  (单位：分钟)
```

**前提假设**：聚合键相同 → 同一现象。**首次触发** 与 **末次触发** 之差视为"持续时长"。

> **重要**：此处"末次"指**当前分析时间窗内的最末一次触发**。
> 若告警在分析结束前已恢复（`status=OK`），用**恢复时间戳**替代。

### 3.3 告警抖动 (ALARM → OK → ALARM) 如何计入

**问题**：CPU 阈值告警在 1 小时内抖动 10 次（每次 30s ALARM，间隔 5min OK），应算 P1 还是 P0？

**v0.1 决策**：

```
duration_min = last_trigger_time - first_trigger_time  (不扣除 OK 间隔)
```

即"抖动簇"按**外层包络**计算，不按"实际 ALARM 累计时长"。

**理由**：

- 用户感知的是"被反复打扰"，而不是"ALARM 状态秒数"
- v0.1 数据只有触发历史（`describe-alarm-history`），未暴露完整状态机时间线
- v0.2 若引入实时 API，可改为"ALARM 累计时长"算法

**边界 case**：抖动 > 100 次/小时仍按外层包络算 → 走"频次 = high"路径升级 P0（见 §4）。

### 3.4 持续时长缺失时

若聚合结果 `duration_min` 缺失或为 0（仅 1 次触发，瞬时恢复），按 `short` 档处理。

---

## 4. 频次评估细则

### 4.1 单位时间触发次数

```
frequency = cluster.trigger_count / (duration_min / 60 + ε)   (次/小时, ε=0.01 防除零)
```

### 4.2 三档定义

| 频次（次/小时） | 标识 |
|---|---|
| `< 3` | `low` |
| `3 - 10` | `mid` |
| `> 10` | `high` |

### 4.3 与历史基线对比（v0.1 暂用绝对值）

- **v0.1**：仅用绝对阈值（`> 10 次/小时 = high`），不考虑历史基线
- **v0.3**：引入 7d/30d 同时段基线，频次偏离 > 2σ 才升级 high
- **v0.1 临时缓解**：若用户显式声明"该资源本就高频触发"，可在 input 中加 `baseline_known=true` 修饰，所有频次档降一级

### 4.4 频次缺失

若 `trigger_count` 缺失 → 频次 = `low`（保守判定，避免误升 P0）。

---

## 5. 三维 → 四级 判定伪代码

```python
from enum import Enum
from typing import Literal


class ImpactScope(Enum):
    WIDE = "wide"          # 多资源 / 核心业务
    MODERATE = "moderate"  # 少量资源 / 重要业务
    NARROW = "narrow"      # 单资源 / 一般业务
    MINIMAL = "minimal"    # 单资源 / 边缘业务


class DurationTier(Enum):
    SHORT = "short"   # < 5min
    MID = "mid"       # 5-30min
    LONG = "long"     # > 30min


class FrequencyTier(Enum):
    LOW = "low"       # < 3/h
    MID = "mid"       # 3-10/h
    HIGH = "high"     # > 10/h


def classify_cluster(cluster: dict) -> Literal["P0", "P1", "P2", "P3"]:
    """
    将聚合簇分级为 P0/P1/P2/P3。

    输入 cluster 字段（来自 playbook-aggregate.md）:
      - resource_ids:     list[str]   受影响资源
      - service_code:     str         服务代码
      - business_tag:     str|None    'core'/'important'/'general'/'peripheral'/None
      - duration_min:     float       持续时长（分钟）
      - trigger_count:    int         触发次数

    输出:
      - "P0" / "P1" / "P2" / "P3"

    权威源: core-concepts.md §1.4
      - R2 (次/小时频次): low<3/h, mid 3-10/h, high>10/h
      - R3 (业务 tag): business=core|important|general|peripheral; 缺省 general
    """
    # Step 1: 影响面
    impact = _evaluate_impact_scope(
        len(cluster["resource_ids"]),
        cluster["service_code"],
        cluster.get("business_tag"),
    )

    # Step 2: 持续时长
    duration = _evaluate_duration(cluster.get("duration_min", 0))

    # Step 3: 频次
    frequency = _evaluate_frequency(
        cluster.get("trigger_count", 0),
        cluster.get("duration_min", 0),
    )

    # Step 4: 查矩阵（详见 severity-matrix.md 的 20 判定单元）
    return _lookup_severity(impact, duration, frequency)


# 业务影响等级默认值表
_SERVICE_DEFAULT_IMPORTANCE = {
    "lb": "core",
    "rds": "core",
    "redis": "important",
    "eip": "important",
    "cdn": "important",
    "vm": "general",
    "oss": "general",
}


def _evaluate_impact_scope(
    resource_count: int, service_code: str, business_tag: str | None
) -> ImpactScope:
    """资源数 + 服务代码 + 业务标签 → 影响面"""
    importance = business_tag or _SERVICE_DEFAULT_IMPORTANCE.get(service_code, "general")

    if resource_count >= 4 or importance == "core":
        return ImpactScope.WIDE
    if resource_count >= 2 or importance == "important":
        return ImpactScope.MODERATE
    if importance == "general":
        return ImpactScope.NARROW
    return ImpactScope.MINIMAL


def _evaluate_duration(duration_min: float) -> DurationTier:
    """持续时长 → 短/中/长"""
    if duration_min < 5:
        return DurationTier.SHORT
    if duration_min <= 30:
        return DurationTier.MID
    return DurationTier.LONG


def _evaluate_frequency(trigger_count: int, duration_min: float) -> FrequencyTier:
    """触发次数 + 持续时长 → 频次档"""
    hours = (duration_min / 60) + 0.01
    freq_per_hour = trigger_count / hours
    if freq_per_hour < 3:
        return FrequencyTier.LOW
    if freq_per_hour <= 10:
        return FrequencyTier.MID
    return FrequencyTier.HIGH


def _lookup_severity(
    impact: ImpactScope, duration: DurationTier, frequency: FrequencyTier
) -> Literal["P0", "P1", "P2", "P3"]:
    """
    3 维 → 4 级判定矩阵（与 severity-matrix.md 完全一致）。

    矩阵 20 单元（4 影响面 × 3 持续 × 3 频次）：
    """
    # 影响面 = WIDE (多资源 / 核心业务)
    if impact == ImpactScope.WIDE:
        if duration == DurationTier.LONG or frequency == FrequencyTier.HIGH:
            return "P0"
        if duration == DurationTier.MID:
            return "P0"  # 核心业务中持续时间=5-30min 也是 P0
        return "P1"  # wide + short + low

    # 影响面 = MODERATE
    if impact == ImpactScope.MODERATE:
        if duration == DurationTier.LONG:
            return "P0"
        if duration == DurationTier.MID and frequency == FrequencyTier.HIGH:
            return "P0"
        if duration == DurationTier.MID:
            return "P1"
        if frequency == FrequencyTier.HIGH:
            return "P1"
        return "P2"  # moderate + short + low/mid

    # 影响面 = NARROW
    if impact == ImpactScope.NARROW:
        if duration == DurationTier.LONG and frequency == FrequencyTier.HIGH:
            return "P1"
        if duration == DurationTier.LONG:
            return "P2"
        if frequency == FrequencyTier.HIGH:
            return "P2"
        return "P3"

    # 影响面 = MINIMAL
    return "P3"  # 边缘业务所有情况统一 P3
```

---

## 6. 边界 Case 决策表

| # | 场景 | 决策 | 理由 |
|--:|---|---|---|
| 1 | 持续 4min（临界 P2 vs P1） | **P2** | < 5min 走 short 档；保守升级风险高 |
| 2 | 持续 30min（临界 P1 vs P0） | **P1**（mid 上限） | ≤ 30min 走 mid 档；再长才 P0 |
| 3 | 持续 31min（刚跨过 P0 阈值） | **P0** | > 30min 走 long 档 |
| 4 | 单次触发瞬时恢复（duration=0） | 按 short + low → 影响面决定 | 抖动的"小毛刺"，靠频次和影响面升档 |
| 5 | 频次刚好 10 次/小时（mid 上限） | **mid 档** | ≤ 10 走 mid；不升 high |
| 6 | 多资源（4+）但单资源各自只触发 1 次 | **wide + short + low → P1** | 多资源即便短时也是 P1，宁可升级不可漏报 |
| 7 | 核心业务（rds）+ 持续 1min + 频次 1 | **wide + short + low → P1** | 核心业务即便短时也是 P1（不可接受 1min 中断） |
| 8 | 边缘业务 + 持续 2h + 频次 50/h | **P3** | 业务等级压制影响面，所有 minimal 情形统一 P3 |
| 9 | tag 拉取失败，默认值与"已知业务"矛盾 | **以 service_code 默认值 + 报告标注"业务标签未识别"** | 数据缺失保守处理优于猜测 |
| 10 | 跨多 region 的同名资源（聚合时合并了不同 region） | **拆分簇（按 region 分别聚合）** | 聚合键应在 Step 1 之前就含 region |

---

## 7. 与 suppression-rules.md 的协同顺序

**原则：先分级 → 后抑制。**

**为什么不是"先抑制后分级"**：

- 分级需要完整的三维数据（频次、持续、影响面）
- 抑制判定依赖"已分好的级别"（如 P0 不允许被维护窗直接过滤，必须降档为 P1 并标注）
- 反过来：若先抑制，P3 周期性告警无法进入"分级"流水线，会被误过滤

**抑制阶段的降档方向**（详见 [playbook-suppress.md](./playbook-suppress.md)）：

| 原级别 | 命中维护窗 | 命中周期性 | 命中已知误报 |
|---|---|---|---|
| P0 | 降 P1（降一档） | 降 P1（降一档） | 降 P3（跨级豁免 + 报告标注）|
| P1 | 降 P2（降一档） | 降 P2（降一档） | 降 P3（跨级豁免 + 报告标注）|
| P2 | 降 P3（降一档） | 降 P3（降一档） | 降 P3（跨级豁免 + 报告标注）|
| P3 | 不变（P3 不再降）| 不变（P3 不再降）| 不变（P3 不再降）|

> **关键约束**：本表无"过滤"行——v0.1 R1 两段式下，**任何级别的命中都进入报告**，仅级别下调 + 标注原因。

**关键约束**：

- **P0 不会跳到 P3**（维护窗/周期性最多降为 P1 + 标注；已知误报豁免可跨级降 P3）
- **所有降级**必须在报告中**显式记录**（避免被静默吞掉）
- **权威源**：[`./core-concepts.md §1.4`](./core-concepts.md) "抑制降档 (两段式)"

---

## 8. 单元测试样例（仅供规则一致性校验）

```python
def test_classify():
    # Case: 核心业务 RDS CPU 高，持续 35min
    assert classify_cluster({
        "resource_ids": ["rds-001"],
        "service_code": "rds",
        "business_tag": None,
        "duration_min": 35,
        "trigger_count": 8,
    }) == "P0"  # wide + long + low

    # Case: 单 VM CPU 抖动 1min
    assert classify_cluster({
        "resource_ids": ["i-xxx"],
        "service_code": "vm",
        "business_tag": None,
        "duration_min": 1,
        "trigger_count": 2,
    }) == "P3"  # narrow + short + low

    # Case: LB 5xx 持续 15min
    assert classify_cluster({
        "resource_ids": ["lb-001"],
        "service_code": "lb",
        "business_tag": None,
        "duration_min": 15,
        "trigger_count": 4,
    }) == "P0"  # wide(core) + mid + low

    # Case: OSS 流量持续 1h
    assert classify_cluster({
        "resource_ids": ["oss-bucket-1"],
        "service_code": "oss",
        "business_tag": None,
        "duration_min": 60,
        "trigger_count": 6,
    }) == "P2"  # narrow + long + low
```

---

## 9. 已知不足（v0.1）

- **不支持同根因关联簇**（依赖 v0.2 rca-engine）—— 当前只看"同 metric 同 resource"维度
- **频次判定未引入基线** —— v0.1 用绝对阈值 v0.3 改 ML/统计基线
- **告警抖动按外层包络计算** —— 实际 ALARM 累计时长更准，但数据依赖 v0.2 实时 API
- **业务标签缺失会回退到服务代码默认值** —— 不够精准但可解释
- **不支持自定义业务影响等级** —— 用户若需自定义需走 v0.4 配置化
