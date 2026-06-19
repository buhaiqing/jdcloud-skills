# 告警智能助手 — 监控指标与告警模式参考

> 本文件列出 `jdcloud-alert-intelligence` v0.1 在聚合/分级/抑制阶段用到的核心监控指标，
> 以及常见的告警模式（pattern）。完整监控指标清单见
> [`jdcloud-cloudmonitor-ops` monitoring.md](../../jdcloud-cloudmonitor-ops/references/monitoring.md)。
>
> 本 Skill **不**对监控指标做"全量解释"，仅聚焦"分析告警时需要看到的指标子集"。

## 1. 本 Skill 涉及的指标范围

| 服务代码 | 关键指标前缀 | 本 Skill 用到的子集 |
|---|---|---|
| `vm` | `vm.*` | `vm.cpu.util`, `vm.memory.util`, `vm.disk.util`, `vm.network.in/out`, `vm.tcp.connections` |
| `rds` | `rds.*` | `rds.cpu.util`, `rds.connection.util`, `rds.qps`, `rds.slow.queries`, `rds.replication.lag` |
| `lb` | `lb.*` | `lb.httpcode.4xx`, `lb.httpcode.5xx`, `lb.newconnection`, `lb.unhealthy_host_count`, `lb.latency` |
| `redis` | `redis.*` | `redis.memory.usage`, `redis.connection.count`, `redis.qps`, `redis.hit_ratio` |
| `eip` | `eip.*` | `eip.traffic.in/out`, `eip.bandwidth.util` |
| `oss` | `oss.*` | `oss.traffic.in/out`, `oss.qps`, `oss.requests.4xx/5xx` |

> **完整指标**：上游 `jdcloud-cloudmonitor-ops/monitoring.md` 列出 40+ 种云产品的全量监控指标。
> 本 Skill 仅在上表中做"聚合/分级"分析，不直接查询指标元数据（除非 Step 2 peak_value 关联查询）。

## 2. 聚合键三元组覆盖

本 Skill 用 `(service_code, resource_id, metric_name)` 三元组聚合为 Cluster。

**举例（来自 [examples.md](./examples.md)）：**

| 三元组 | 现象 | 处置 skill |
|---|---|---|
| `(lb, lb-prod-entry-01, lb.httpcode.5xx)` | LB 入口 5xx 增多 | `jdcloud-clb-ops` |
| `(vm, i-prod-app-01, vm.cpu.util)` | 单 VM CPU 高 | `jdcloud-vm-ops` |
| `(rds, rds-mysql-order, rds.cpu.util)` | 订单库 CPU 高 | `jdcloud-rds-ops` |
| `(redis, redis-cache-01, redis.connection.count)` | Redis 连接打满 | `jdcloud-redis-ops` |
| `(eip, eip-prod-01, eip.bandwidth.util)` | EIP 带宽跑满 | `jdcloud-vpc-ops`（升级规格）|

## 3. 常见告警模式（v0.1 分析场景）

### 3.1 持续型告警（S1 + D3-D4）

- **特征**：单资源指标持续超阈值 > 30min
- **典型场景**：
  - `vm.cpu.util > 90%` 持续 1h
  - `rds.cpu.util > 85%` 持续 2h
- **本 Skill 分级倾向**：核心业务 → P0；重要业务 → P1；一般业务 → P1/P2；边缘业务 → P3

### 3.2 抖动型告警（S1 + D1 + high 频次）

- **特征**：单资源频繁短时触发（> 10 次/小时）
- **典型场景**：
  - `vm.cpu.util` 每 5min 触发 1 次，持续 1h → 12 次
  - `lb.httpcode.5xx` 周期性尖刺，每次 < 1min
- **本 Skill 分级倾向**：核心业务 → P1（升档规则）；其他 → P2
- **下一跳**：高频抖动多半是阈值设计不合理 → `jdcloud-cloudmonitor-ops` 调整
  `evaluation-periods` 或阈值

### 3.3 多资源同时触发（S3-S4）

- **特征**：同一 service_code 下 ≥ 3 资源同时告警
- **典型场景**：
  - 同 LB 后端 3 台 ECS 同时 CPU 100%
  - 同 RDS 主从同时告警
- **本 Skill 分级倾向**：默认 P0（除非业务=peripheral 降到 P1）
- **下一跳**：可能是后端共性故障（上游流量/共享资源/网络分区）

### 3.4 跨服务故障（v0.1 仅展示共时性）

- **特征**：≥ 2 个不同 service_code 同时段告警
- **典型场景**：
  - 14:18 LB 5xx + 14:20 VM CPU + 14:21 Redis 连接
- **本 Skill 分级**：v0.1 不做根因关联，仅做共时性时间对齐展示
- **下一跳**：v0.2 rca-engine 自动关联；v0.1 由人工按时间顺序推断

### 3.5 已知周期性（S1 + D1 + 历史 7d 同时段 ≥ 3 次）

- **特征**：告警在固定时段反复出现（如每天凌晨 3 点）
- **典型场景**：
  - 备份任务（`vm.disk.io.write` 凌晨 2-4 点）
  - 批处理（`rds.cpu.util` 整点/半点）
- **本 Skill 抑制**：R1 两段式 — **降一档**（P0→P1→P2→P3）
- **下一跳**：建议调整告警规则 evaluation-periods，或将资源加入维护窗 tag

### 3.6 已知误报（命中 5 类清单）

| 类别 | 典型指标 | 时间模式 | 处置 |
|---|---|---|---|
| 备份任务 | `vm.disk.io.write`, `vm.network.out` | 凌晨 2-4 点 | 跨级降 P3 |
| 批处理 | `rds.cpu.util`, `rds.connections.active` | 整点/半点 ±10min | 跨级降 P3 |
| 滚动重启 | `vm.cpu.util` 多资源 | 5min 内 | 跨级降 P3 |
| CD 流量回切 | `lb.newconnection`, `lb.traffic.in` | 发布后 5-15min | 跨级降 P3 |
| 镜像拉取 | `vm.network.out`, `eip.traffic.out` | 任意 < 5min | 跨级降 P3 |

> **R1 联动**：已知误报清单命中 → **跨级豁免降 P3**（任意级别都降 P3），
> 与维护窗/周期性的"降一档"区分。详见 [core-concepts.md §1.4](./core-concepts.md)。

## 4. 监控指标查询用法

### Step 2 取 peak_value

```bash
jdc --output json monitor describe-metric-data \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metric vm.cpu.util \
  --start-time "2026-06-02T00:00:00+08:00" \
  --end-time   "2026-06-03T00:00:00+08:00" \
  --aggr-type max \
  --period 300
```

**JSON 路径**：`$.result.metricDatas[*].dataPoints[*].value`

**取 peak**：

```python
peak = max((dp["value"] for dp in metric_data["result"]["metricDatas"][0]["dataPoints"]), default=None)
```

### Step 3 取规则元信息

```bash
jdc --output json monitor describe-alarms \
  --region-id cn-north-1 \
  --service-code vm \
  --page-size 100
```

**JSON 路径**：`$.result.alarms[*]`，含 `alarmId`、`threshold`、`evaluationPeriods`、`comparisonOperator`。

## 5. 监控数据保留期

| 数据类型 | 保留期 | 本 Skill 推荐窗口 |
|---|---|---|
| 原始告警历史 | 15d | ≤ 15d |
| 1h 聚合 | 30d | 15d - 30d |
| 1d 聚合 | 180d | 30d+（仅做趋势） |

> **关键约束**：周期性检测（Step 4）需要 7d 同时段历史，原始告警数据保留 15d 足够；
> 更大窗口（如 30d 趋势）需用 1h 聚合接口，超出 v0.1 范围。

## 6. 与 cloudmonitor-ops 的边界

| 能力 | 本 Skill | cloudmonitor-ops |
|---|:---:|:---:|
| 告警规则 CRUD | ❌（委派）| ✅ |
| 告警历史拉取 | ✅（主调用）| ✅ |
| 告警规则详情查询 | ✅ | ✅ |
| 实时面板/监控大盘 | ❌（委派）| ✅ |
| 告警联系人配置 | ❌（委派）| ✅ |
| 告警智能分析（聚合/分级/抑制/报告）| ✅（核心）| ❌ |

> 本 Skill 是 `jdcloud-cloudmonitor-ops` 的"告警后处理层"，不替代其查询与变更能力。