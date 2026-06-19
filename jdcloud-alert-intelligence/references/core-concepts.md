# 京东云告警智能助手 — 核心概念

> 本文件是 `jdcloud-alert-intelligence` 的概念词典。所有术语、模型、计算公式
> 在本 skill 内部统一引用，外部 skill 通过 [../SKILL.md](../SKILL.md) 入口引用本文件。

---

## 1. 告警模型

### 1.1 告警生命周期（三态机）

京东云云监控的告警事件在 `describe-alarm-history` 返回中以三态流转：

```
            满足条件 / 跨过阈值
   ┌──────────────────────────────────┐
   ▼                                  │
[OK]  ──────────►  [ALARM]  ──────────┘
   ▲                │
   │                │ 数据采集中断 / 资源变更
   │                ▼
   └─────  [INSUFFICIENT_DATA]
```

| 状态 (status) | 含义 | 何时出现 |
|---|---|---|
| `OK` | 指标在阈值内 | 正常态 / 恢复态 |
| `ALARM` | 指标持续超阈值达到 `evaluation-periods` | 真实触发态 |
| `INSUFFICIENT_DATA` | 数据采集中断或资源变更导致无法判定 | 资源关机/重启/网络断/无权限 |

**重要**：v0.1 聚合时只统计 `status == "ALARM"` 的事件；`INSUFFICIENT_DATA` 不计入触发次数，
但单独纳入"数据连续性"统计（连续 INSUFFICIENT_DATA > 3 次建议关注采集异常）。

### 1.2 告警事件核心字段

> 字段命名以 jdc CLI 的 `describe-alarm-history` 响应 JSON 为准（详见 `cli-usage.md`）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `alarmId` | string | 告警规则 ID，对应一个持续生效的告警规则 |
| `alarmName` | string | 告警规则名称（人工可读） |
| `serviceCode` | string | 京东云产品服务代码（`vm` / `rds` / `lb` / `redis` / `eip` / `oss` / ...） |
| `resourceId` | string | 资源 ID（实例 ID / LB ID / Redis ID 等） |
| `metricName` | string | 监控项名称（如 `vm.cpu.util`、`lb.httpcode.5xx`） |
| `status` | string | 事件状态（`ALARM` / `OK` / `INSUFFICIENT_DATA`） |
| `triggerTime` | string (ISO 8601) | 事件触发时间 |
| `value` | number | 触发时刻的指标值（部分规则带） |
| `threshold` | number | 触发阈值（部分规则带） |
| `regionId` | string | 区域 ID，如 `cn-north-1` |

### 1.3 服务代码（serviceCode）参考

> 仅列出 v0.1 委派映射覆盖到的常用服务。其他服务代码同样可在聚合中使用，但本 skill
> 的"下一跳建议"会标注"暂无对应产品 skill"。

| serviceCode | 产品 | 对应 `jdcloud-*-ops` |
|---|---|---|
| `vm` | 云主机 | `jdcloud-vm-ops` |
| `rds` | 云数据库 RDS | `jdcloud-rds-ops` |
| `lb` | 负载均衡 | `jdcloud-clb-ops` |
| `redis` | 分布式缓存 Redis | `jdcloud-redis-ops` |
| `eip` | 弹性公网 IP | `jdcloud-vpc-ops`（如无则建议升级规格） |
| `oss` | 对象存储 | `jdcloud-oss-ops`（如无则建议联系运维） |
| `kms` | 密钥管理服务 | `jdcloud-kms-ops` |
| `iam` | 访问控制 | `jdcloud-iam-ops` |

### 1.4 核心约定 (Authority Source)

> **本节是 v0.1 的唯一权威源**。如与其他 references 文件冲突，以本节为准。

#### 业务影响等级 (业务 tag 约定)

资源 tag 中 `business=*` 字段的 4 个合法值:

| 取值 | 含义 | 默认 |
|---|:--:|:--:|
| `core` | 核心业务（订单/支付/登录/交易链路）| 否 |
| `important` | 重要业务 | 否 |
| `general` | 一般业务 | **是** |
| `peripheral` | 边缘业务 | 否 |

**缺省值：未打 `business` tag 的资源按 `general` 处理。**

#### 频次维度 (次/小时)

**计算公式**：`频次 = 触发次数 / 时间窗小时数`

| 档位 | 阈值 |
|:--:|:--|
| `low` | < 3 次/小时 |
| `mid` | 3-10 次/小时 |
| `high` | > 10 次/小时 |

时间窗默认 24h；用户可指定 1h / 6h / 24h / 7d。

#### 抑制降档 (两段式)

| 命中类型 | 降档规则 |
|---|---|
| 维护窗 | 降一档（P0→P1，P1→P2，P2→P3，P3 不再降）|
| 已知周期性 | 降一档（同上）|
| 已知误报清单（5 类）| 一律降为 P3（跨级豁免）|

**约束**：
- P3 不再降档
- 维护窗/周期性不跨级降
- 已知误报清单跨级豁免（任意级别都降为 P3）
- 多个命中时按"最重抑制"原则：已知误报 > 已知周期性 > 维护窗

#### 5 类已知误报清单

1. **备份任务** → P3
2. **批处理** → P3
3. **滚动重启** → P3
4. **CD 流量回切** → P3
5. **镜像拉取** → P3

> **注意**：5 类已知误报在 v0.1 全部降为 P3，与 §1.4 抑制降档表格一致。
> 历史版本中"滚动重启/CD 流量回切降 P2"的规则已被本约定取代。

## 2. 聚合键与告警簇

### 2.1 聚合键定义

**聚合键（Aggregation Key）**：三元组 `(service_code, resource_id, metric_name)`

- **同一三元组** 的多次触发视为"同一现象的重复"
- **不同三元组** 即使 `alarmName` 相同，也视为不同现象（因为资源/指标变了）
- 三个字段中任一为 `null` / `""` → **不参与聚合**，单条直接进入分级

**为什么不用 `alarmId`**：同一个告警规则的两次连续触发（rule 没改）应该合并；
但如果规则被修改（如阈值从 80% 改到 90%）产生的新告警事件，用 `(service, resource, metric)`
聚合可保留"现象视角"，用 `alarmId` 反而会拆散。

**为什么不只用 `resourceId`**：同一资源可能挂多个告警规则（CPU + 内存 + 磁盘），现象不同，
应分别聚合便于分别处置。

### 2.2 告警簇（Cluster）

**告警簇 (Cluster)**：同一聚合键下时间窗内的全部 `ALARM` 事件聚合而成的逻辑单元。

每个 Cluster 包含以下属性：

| 属性 | 类型 | 含义 |
|---|---|---|
| `cluster_id` | string | 本次分析的簇唯一标识（`{service}-{resource}-{metric}` 的小写拼接） |
| `service_code` | string | 服务代码 |
| `resource_id` | string | 资源 ID |
| `metric_name` | string | 监控项名称 |
| `trigger_count` | int | 时间窗内 `ALARM` 事件次数 |
| `first_trigger` | string (ISO 8601) | 首次触发时间 |
| `last_trigger` | string (ISO 8601) | 末次触发时间 |
| `duration_minutes` | number | `last_trigger - first_trigger`（分钟） |
| `peak_value` | number | 关联 `describe-metric-data` 后取 max；未取时为 `null` |
| `affected_resources` | array[string] | 受影响资源 ID 列表（单资源 = `[resource_id]`） |
| `related_alarm_ids` | array[string] | 关联的告警规则 ID 列表（去重） |
| `status` | string | 末次事件状态（`ALARM` / `OK` / `INSUFFICIENT_DATA`） |

### 2.3 簇 vs 工单（重要区别）

| 概念 | 数量级 | 处置单位 |
|---|---|---|
| 告警事件 (Event) | 一次触发 | 不可单独处置 |
| 告警簇 (Cluster) | 一组现象 | 人工介入的最小单位 |
| 工单 (Ticket) | 一次排查任务 | 可包含多个 Cluster |

**v0.1 规则**：本 skill 只产出 Cluster 分析，**不**自动开工单；工单由 on-call 工程师
基于 Cluster 列表自行决定是否开。

---

## 3. 术语表

### 3.1 抑制 / 过滤 / 降级（三者必须区分）

| 术语 | 含义 | 是否进入报告 | 典型动作 |
|---|---|---|---|
| **抑制 (Suppress)** | 命中已知规则（维护窗/周期性/已知误报），降低或消除通知 | **不进**报告 | 调整规则、加入维护清单 |
| **过滤 (Filter)** | 用户指定条件（severity_filter / service_filter）排除部分簇 | **不进**报告 | 仅筛选展示 |
| **降级 (Demote)** | 命中抑制规则但仍展示，级别下调一档（P1→P2 / P2→P3） | **进**报告但级别降低 | 标注"已降级"原因 |

**反例**（常见误用）：
- ❌ "把 P0 抑制掉" — 应是 "把 P0 **降级**为 P3"
- ❌ "这个告警被过滤了所以没分析" — 应是 "这个告警**抑制**了，分析时已考虑"

> **术语约定（本 skill 专有）**：
> - 本 skill 中"降级 (Demote)" **专指**抑制层的级别下调。
> - jdc CLI 失败后的回退动作使用 **"fallback"** 表示（如"jdc 失败 → fallback 到原始数据"），**不**使用"降级"一词。
> - 翻译习惯：英文优先用 suppress / filter / demote / fallback 四个词表达；中文可保留"降级"但需明确上下文。

### 3.2 簇 / 工单 / 指纹 / 规则 ID

| 术语 | 含义 | 例子 |
|---|---|---|
| 簇 (Cluster) | 见 §2.2 | `vm-i-abc123-vm.cpu.util` |
| 工单 (Ticket) | 一次排查任务（不在本 skill 范围） | `JD-INC-20260603-0001` |
| 指纹 (Fingerprint) | 簇的特征哈希，用于跨分析周期追踪（v0.1 留位） | `sha1(service\|resource\|metric).hexdigest()[:12]` |
| 规则 ID (alarmId) | 一条 jdcloud 告警规则 | `alarm-7f3a2b` |
| 事件 ID | 单次告警事件（`describe-alarm-history` 数组每项的 ID） | `evt-20260603001234` |

**v0.1 范围**：仅产生 Cluster；指纹 v0.2 引入用于趋势分析。

---

## 4. 值班疲劳指标

> 三个指标均基于"已聚合后的 Cluster 列表"计算，**不**基于原始事件数。
> 计算时段 = 用户指定的时间窗（默认 24h）。

### 4.1 打扰率（Disturbance Rate）

**定义**：时间窗内实际告警（去重后 Cluster 数）与"理想静默状态"之差。

```
disturbance_rate = (cluster_count - suppressed_count) / cluster_count
```

| 指标值 | 评级 | 含义 |
|---|---|---|
| ≥ 0.8 | 🟢 静默 | on-call 可安心 |
| 0.5 - 0.8 | 🟡 正常 | 一般在岗工作量 |
| 0.3 - 0.5 | 🟠 偏高 | 建议优化告警规则 |
| < 0.3 | 🔴 过载 | 告警风暴，需立即治理 |

**注意**：打扰率 = 1 - 抑制率（仅当抑制生效时）。它衡量"多少告警没被抑制掉"。

### 4.2 重复率（Repetition Rate）

**定义**：触发次数 ≥ 3 的 Cluster 占总 Cluster 的比例。

```
repetition_rate = cluster_with_trigger_count_ge_3 / total_cluster_count
```

| 指标值 | 评级 | 含义 |
|---|---|---|
| < 0.2 | 🟢 低 | 告警"散点"特征 |
| 0.2 - 0.5 | 🟡 中 | 部分现象重复 |
| 0.5 - 0.8 | 🟠 高 | 多处反复异常 |
| ≥ 0.8 | 🔴 极高 | 告警规则需重新审视（阈值？evaluation-periods？） |

**根因建议**：重复率 > 0.5 → 输出"建议改告警规则"委派给 `jdcloud-cloudmonitor-ops`。

### 4.3 夜间打扰率（Night Disturbance Rate）

**定义**：22:00 - 次日 08:00（本地时区，**默认 UTC+8**）触发的 Cluster 占总比例。

```
night_clusters = cluster_count where first_trigger.hour in [22, 23, 0..7]
night_disturbance_rate = night_clusters / total_cluster_count
```

| 指标值 | 评级 | 含义 |
|---|---|---|
| < 0.1 | 🟢 低 | 夜间基本静默 |
| 0.1 - 0.3 | 🟡 中 | 偶发夜间告警 |
| 0.3 - 0.5 | 🟠 偏高 | 需排查是否有"伪夜间"任务（备份/批处理漏配） |
| ≥ 0.5 | 🔴 高 | 值班疲劳风险，建议立即批量处理维护窗 |

**v0.1 时区硬约束**：仅识别 UTC+8。其他时区 v0.2 再加（按 `JDC_REGION` 推断）。

---

## 5. 数据保留期与时间窗约束

### 5.1 京东云云监控保留期（来自 cloudmonitor-ops/monitoring.md）

| 数据类型 | 保留期 | 本 skill 推荐窗口 |
|---|---|---|
| 原始数据 | 15 天 | ≤ 15d |
| 1 小时聚合 | 30 天 | 15d - 30d |
| 1 天聚合 | 180 天 | 30d+（仅做趋势） |

### 5.2 时间窗检查规则

- 用户指定窗口 **起始时间不能早于 `now - 180d`**（1d 聚合最远边界）
- 用户指定窗口 **结束时间不能晚于 `now`**
- 推荐默认窗口：**最近 24h**（on-call 值班交接场景）
- 周报场景：固定 **7d**
- 月报场景：固定 **30d**

### 5.3 时间窗超限处理

| 情况 | 行为 |
|---|---|
| 起始时间 > 15d 前 | 提示用户："原始告警数据可能不全，建议使用 1h 聚合接口"（v0.2 实现） |
| 起始时间 > 180d 前 | **拒绝执行**，提示用户"超出最长可分析窗口（180d）" |
| 结束时间 > now | **拒绝执行**，提示"结束时间不能在未来" |

---

## 6. 安全模型

### 6.1 凭证处理（强约束）

| 规则 | 实现 |
|---|---|
| `JDC_SECRET_KEY` 绝不打印、绝不记录、绝不进报告 | 仅 `test -n "$JDC_SECRET_KEY"` 检查存在性 |
| `JDC_ACCESS_KEY` 可在脱敏状态下展示 | 展示形如 `AKC123****MASKED` |
| 报告文件不外发 | 默认输出本地 `alert_intelligence_report_*.md` |
| 日志/调试输出脱敏 | 用 `JDC_SECRET_KEY=<masked>` 替代实际值 |

### 6.2 最小权限

本 skill 只读云监控告警数据。**最低权限要求**：

```
monitor:DescribeAlarmHistory
monitor:DescribeAlarms
monitor:DescribeAlarm
monitor:DescribeMetrics
monitor:DescribeMetricData
```

> 其他权限（如 `CreateAlarm` / `DeleteAlarms`）**不应**授予本 skill 使用的 IAM 用户/角色。
> 详细 IAM 策略配置委派 [`jdcloud-iam-ops`](../../jdcloud-iam-ops/SKILL.md)。

### 6.3 报告输出安全

- 报告文件名：`alert_intelligence_report_<region>_<start>_<end>.md`
  例：`alert_intelligence_report_cn-north-1_20260602_20260603.md`
- 默认输出到当前工作目录
- **不**上传到 OSS / **不**发邮件 / **不**调 webhook
- 如需外发，必须用户显式确认

### 6.4 审计可追溯

本 skill 每次执行应在报告中记录：

- 执行时间（Agent 本地时间）
- 时间窗范围
- 拉取的原始事件数
- 聚合后 Cluster 数
- 各分级 Cluster 数
- 抑制/过滤数

**不**记录：凭证值、用户 IP、jdc 内部命令（这些在 jdcloud-cloudmonitor-ops 范围内已审计）。

---

## 7. 引用本文件

外部 skill 在引用本文件的术语时，应**保留术语原文**（如 "Cluster"、"Alarm Fingerprint"），
不要做翻译变体，避免在跨 skill 协作时产生歧义。
