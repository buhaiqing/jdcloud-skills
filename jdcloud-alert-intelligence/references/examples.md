# 京东云告警智能助手 — 端到端示例 (examples)

> **5 个端到端场景**：①24h 压测 ②周报生成 ③告警风暴 ④周期性诊断 ⑤跨服务故障
>
> **规则口径**（v0.1.0 目标态）：聚合键 `(service_code, resource_id, metric_name)` ·
> 业务 tag `business=core|important|general|peripheral` · 频次按次/小时 ·
> 抑制两段式：维护窗/周期性 **降一档**，已知误报 5 类 **统一降 P3**。R1/R2/R3 修复目标
> 尚未在所有 references 同步生效，本文件按目标态编写。
>
> **章节结构**（每示例 6 段）：①用户问题 ②入参 ③Step 1 拉取 ④Step 2-4 处理 ⑤Step 5 报告 ⑥下一跳

---

## 示例 1: 24h 紧急压测（告警风暴）

### 1) 用户问题

> "昨晚 22:00-02:00 告警风暴，帮我看看哪些是真正的故障。"

### 2) 入参

`region=cn-north-1` · `time_window=2026-06-02T00:00:00+08:00 / 2026-06-03T00:00:00+08:00 (24h)` · `severity_filter/service_filter=无` · `maintenance_windows=无`

### 3) Step 1 拉取

```bash
jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 \
  --start-time "2026-06-02T00:00:00+08:00" --end-time "2026-06-03T00:00:00+08:00" --page-size 100
```

**预期返回（节选，2 条同簇 `lb/lb-prod-entry-01/lb.httpcode.5xx`）：**

```json
{"result":{"alarmHistoryList":[
  {"alarmId":"alarm-7f3a2b","serviceCode":"lb","resourceId":"lb-prod-entry-01",
   "metricName":"lb.httpcode.5xx","status":"ALARM","triggerTime":"2026-06-02T22:14:00+08:00","value":187.3,"threshold":10},
  {"alarmId":"alarm-7f3a2b","serviceCode":"lb","resourceId":"lb-prod-entry-01",
   "metricName":"lb.httpcode.5xx","status":"ALARM","triggerTime":"2026-06-02T22:21:00+08:00","value":234.5}
]}}
```

完整命令与异常 case 见 [cli-usage.md](./cli-usage.md)。

### 4) Step 2-4 处理

**聚合（312 条事件 → 6 个簇）：**

| 簇 ID | 三元组 | 触发次数 | 首次 | 末次 | 持续 | 频次(次/h) |
|---|---|---:|---|---|---:|---:|
| `C-001` | (lb, lb-prod-entry-01, lb.httpcode.5xx) | 87 | 22:14 | 23:58 | 104min | 3.6 |
| `C-002` | (vm, i-prod-app-01, vm.cpu.util) | 65 | 22:15 | 22:48 | 33min | 2.7 |
| `C-003` | (vm, i-prod-app-02, vm.cpu.util) | 64 | 22:15 | 22:48 | 33min | 2.7 |
| `C-004` | (vm, i-prod-app-03, vm.cpu.util) | 62 | 22:15 | 22:48 | 33min | 2.6 |
| `C-005` | (redis, redis-cache-01, redis.connection.count) | 28 | 22:18 | 22:35 | 17min | 1.2 |
| `C-006` | (rds, rds-mysql-order, rds.cpu.util) | 6 | 22:20 | 22:25 | 5min | 0.3 |

**业务影响等级识别：**

| 簇 | service_code | tag | 业务等级 |
|---|---|---|:--:|
| C-001 | `lb` | `business=core` | **core** |
| C-002-004 | `vm` | `business=core` (集群节点) | **core** |
| C-005 | `redis` | `business=important` (缓存) | **important** |
| C-006 | `rds` | `business=core` (订单库) | **core** |

**分级（依据 severity-matrix.md §1.3）：**

| 簇 | S | D | F | 业务 | 命中规则 | 级别 |
|---|---|---|---|---|---|:--:|
| C-001 | S1 | D3 | F3 | core | S1/D3 + 核心 → P0 § 4 P1-1 | **P0** |
| C-002-004 | S3 | D2 | F3 | core | S3 优先 → P0-2 | **P0** |
| C-005 | S1 | D2 | F2 | important | S1/D2/important → P1 | **P1** |
| C-006 | S1 | D1 | F1 | core | S1/D1/F1 + 核心 → P2 | **P2** |

> 聚合键三元组在 `lb.httpcode.5xx` 命中的 87 次事件中全部并入 `C-001`，
> 体现"同一现象合并"的降噪效果。

**抑制（R1 目标态：维护窗/周期性降一档，已知误报降 P3）：**

- 所有簇均无 tag `maintenance_window=*`，未命中维护窗
- 全部簇在历史 7d 同时段（22:00-23:00）触发 < 3 次，未命中周期性
- 全部簇未命中 5 类已知误报（备份/批处理/滚动重启/CD 回切/镜像拉取）
- **结论**：本例无抑制作用，分级结果 = 抑制后结果

### 5) Step 5 报告

按 [`assets/report-template.md`](../assets/report-template.md) 填充，文件命名：
`alert_intelligence_report_cn-north-1_20260602_20260603.md`

**§1 执行摘要（片段）：**

```
P0 簇: 2（C-001, C-002-C004 视为 S3 簇群）
P1 簇: 1（C-005）
P2 簇: 1（C-006）
重复率: 312 事件 → 6 簇，去重率 98%
打扰率: 高（22:00 起持续 2h）
```

**§3 P0/P1 详单（节选 C-001）：**

```
🔴 簇 C-001 — lb/lb-prod-entry-01/lb.httpcode.5xx （P0）
  业务影响: core (order entry)
  触发次数: 87  |  持续: 104min  |  频次: 3.6/h
  峰值: 234.5 次/5min
  下一跳:
    → jdcloud-clb-ops 检查 lb-prod-entry-01 后端健康度
    → 同时段 C-002-C004 为同一现象（S3 跨资源），建议联合处置
  响应时限: ≤ 5 分钟
```

### 6) 下一跳

- **C-001** → `jdcloud-clb-ops`（检查 LB 后端健康度）+ `jdcloud-vm-ops`（处置 C-002/003/004）
- **C-005** → `jdcloud-redis-ops`（查连接打满根因，慢查询/大 Key）
- **C-006** → `jdcloud-rds-ops`（订单库主库 5min 抖动需关注，但不紧急）
- **整体** → `jdcloud-cloudmonitor-ops`（评估告警规则阈值：`lb.httpcode.5xx > 10` 是否过低导致风暴）

---

## 示例 2: 每周告警周报

### 1) 用户问题

> "生成本周（Mon-Sun）告警周报。"

### 2) 入参

`region=cn-north-1` · `time_window=2026-05-27T00:00:00+08:00 / 2026-06-03T00:00:00+08:00 (7d)` · `severity_filter/service_filter=无`

### 3) Step 1 拉取

同示例 1 命令结构，时间窗 7d。**7d 数据**超出 `--page-size 100` 容量需分页，见
[cli-usage.md § 分页](./cli-usage.md#分页)。

### 4) Step 2-4 处理

**聚合（1247 条事件 → 89 个簇）：**

| 业务影响等级 | 簇数 | 说明 |
|---|---:|---|
| core | 18 | 订单/支付/登录链路 |
| important | 31 | 报表/对账/缓存 |
| general | 35 | 内部工具/普通业务 |
| peripheral | 5 | 文档站/备份节点 |

**分级结果（89 簇）：**

| 级别 | 簇数 | 占比 |
|---|---:|---:|
| P0 | 2 | 2.2% |
| P1 | 7 | 7.9% |
| P2 | 14 | 15.7% |
| P3 | 66 | 74.2%（含 43 个被抑制） |

**抑制生效明细：**

| 抑制源 | 命中簇数 | 降档后级别 |
|---|---:|---|
| 维护窗 | 5 | 全降一档（多为 P0/P1 → P1/P2） |
| 已知周期性 | 23 | 全降一档 |
| 已知误报 5 类 | 15 | 一律降 P3（其中备份 8、批处理 4、镜像拉取 2、滚动重启 1） |
| **合计抑制** | **43** | 占总簇 48.3% |

**降噪指标（依据 core-concepts.md §4）：**

| 指标 | 值 | 评级 |
|---|---:|:--:|
| 重复率 | 1247 事件 / 89 簇 = 14.0 → 89 簇中 31 簇触发 ≥3 次 → 重复率 34.8% | 🟡 中 |
| 夜间打扰率 | 89 簇中 12 簇首次触发 22:00-08:00 → 13.5% | 🟡 中 |
| 打扰率 | (89-43) / 89 = 51.7% | 🟡 正常 |

### 5) Step 5 报告

**§1 TL;DR（示例填充）：**

> 本周期共 1247 条告警事件，聚合为 89 个簇；其中 2 个 P0 需立即介入（详见 §3），主要根因集中在 `lb-prod-entry-01` 与 `rds-mysql-order`；降噪后实际需人工处理事件从 1247 降至 23。

**§4 降噪统计（节选）：**

```
原始事件:    1247
聚合后簇:    89
被抑制簇:    43 (48.3%)
  ├─ 维护窗:        5
  ├─ 已知周期性:   23
  └─ 已知误报:     15

重复率:       34.8% 🟡
夜间打扰率:   13.5% 🟡
打扰率:       51.7% 🟡
```

### 6) 下一跳

- **P0 簇**（2 个）→ 委派 `jdcloud-clb-ops` / `jdcloud-rds-ops` 紧急处置
- **P1 簇**（7 个）→ 各资源对应 `jdcloud-*-ops`
- **重复率 34.8% 偏中** → 委派 `jdcloud-cloudmonitor-ops` 评估告警规则：
  - 重点关注 F4 高频抖动簇（>20 次/7d），多半是阈值设计不合理
- **夜间打扰 13.5%** → 建议批量维护窗配置，委派 `jdcloud-iam-ops` 检查 tag 体系

---

## 示例 3: 告警风暴日

### 1) 用户问题

> "今天告警太多了，帮我找出哪些是同一类。"

### 2) 入参

`region=cn-north-1` · `time_window=2026-06-03T08:00:00+08:00 / 2026-06-03T16:00:00+08:00 (8h)` · `severity_filter/service_filter=无`

### 3) Step 1 拉取

同示例 1 命令结构，时间窗 8h。

### 4) Step 2-4 处理

**聚合（580 条事件 → 11 个簇）：** 重复率 78%，聚合键三元组去重效果显著。

| 簇 ID | 三元组 | 触发次数 | 占比 |
|---|---|---:|---:|
| `C-101` | (vm, i-prod-app-01, vm.cpu.util) | 120 | 20.7% |
| `C-102` | (vm, i-prod-app-02, vm.cpu.util) | 115 | 19.8% |
| `C-103` | (lb, lb-prod-entry-01, lb.httpcode.5xx) | 98 | 16.9% |
| `C-104` | (vm, i-prod-app-01, vm.memory.util) | 76 | 13.1% |
| `C-105` | (redis, redis-cache-01, redis.memory.usage) | 52 | 9.0% |
| `C-106` | (rds, rds-mysql-order, rds.connection.util) | 38 | 6.6% |
| `C-107` | (vm, i-prod-app-03, vm.cpu.util) | 33 | 5.7% |
| `C-108` | (vm, i-prod-app-01, vm.disk.util) | 18 | 3.1% |
| `C-109` | (lb, lb-prod-entry-01, lb.latency) | 15 | 2.6% |
| `C-110` | (eip, eip-prod-01, eip.bandwidth.util) | 9 | 1.6% |
| `C-111` | (oss, oss-logs-bucket, oss.traffic.out) | 6 | 1.0% |
| **合计** | | **580** | **100%** |

**重点簇 C-101 分析：**

- 聚合键 (vm, i-prod-app-01, vm.cpu.util) 在 8h 内出现 120 次
- 频次 = 120 / 8h = **15 次/h** → F4（high）
- 业务 tag `business=core` → 业务等级 core
- S1（单资源）+ D3（首末触发跨度 6h）
- 命中矩阵：S1/D3 + core → **P1**（见 severity-matrix §1.3）
- F4 升档规则：仅当业务=core 时 S1/D1/F4 升档，本例 D3 不触发升档，保留 P1

### 5) Step 5 报告

**§2 Top 簇列表（节选前 5）：**

| # | 簇 ID | 服务 | 资源 | 指标 | 触发 | 持续 | 级别 |
|:--:|-------|------|------|------|---:|---:|:--:|
| 1 | C-101 | vm | i-prod-app-01 | vm.cpu.util | 120 | 6h | 🟡 P1 |
| 2 | C-102 | vm | i-prod-app-02 | vm.cpu.util | 115 | 6h | 🟡 P1 |
| 3 | C-103 | lb | lb-prod-entry-01 | lb.httpcode.5xx | 98 | 5h | 🔴 P0 |
| 4 | C-104 | vm | i-prod-app-01 | vm.memory.util | 76 | 6h | 🟡 P1 |
| 5 | C-105 | redis | redis-cache-01 | redis.memory.usage | 52 | 4h | 🟢 P2 |

**§1 关键洞察：**

```
聚合降噪: 580 → 11 簇（去重率 98%）
单一现象最大贡献: C-101 占 20.7%（120/580）
P0 识别: 1 个（C-103，LB 5xx + 同源 5 个 vm 簇同步）
```

### 6) 下一跳

- **C-101/C-102/C-104/C-107/C-108**（同集群 vm 簇）→ `jdcloud-vm-ops` 联合处置
- **C-103** → `jdcloud-clb-ops`（P0，立即）
- **C-105** → `jdcloud-redis-ops`
- **C-106** → `jdcloud-rds-ops`
- **核心建议** → `jdcloud-cloudmonitor-ops`：当前 8h 内单 VM 触发 120 次告警
  （evaluation-periods 1 + 阈值过低），建议调整 evaluation-periods=3 或调整阈值

---

## 示例 4: 单资源反复触发（周期性检测）

### 1) 用户问题

> "i-bak-node-01 这台机器每天凌晨 3 点都告警，是真的吗？"

### 2) 入参

`region=cn-north-1` · `time_window=2026-06-03T00:00:00+08:00 / 2026-06-03T06:00:00+08:00 (6h)` · `service_filter=vm` · 用户口头补充关注 `i-bak-node-01`

### 3) Step 1 拉取

```bash
jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 --service-code vm --resource-id i-bak-node-01 \
  --start-time "2026-06-03T00:00:00+08:00" --end-time "2026-06-03T06:00:00+08:00" --page-size 100
```

**预期返回（1 条）：**

```json
{"result":{"alarmHistoryList":[
  {"alarmId":"alarm-bak-001","serviceCode":"vm","resourceId":"i-bak-node-01",
   "metricName":"vm.cpu.util","status":"ALARM","triggerTime":"2026-06-03T03:02:17+08:00","value":96.8}
]}}
```

### 4) Step 2-4 处理

**聚合（窗口内 1 簇）：**

| 簇 ID | 三元组 | 触发次数 | 首次 | 末次 | 持续 |
|---|---|---:|---|---|---:|
| `C-201` | (vm, i-bak-node-01, vm.cpu.util) | 1 | 03:02 | 03:18 | 16min |

**业务识别：**

- 资源 tag：`name=backup-node-01`（含关键字 `backup`）→ 命中已知误报清单 §4.1
- 业务 tag `business=peripheral`（边缘备份节点）→ 业务等级 peripheral

**周期性检测（同时段 ±30min，7d 内）：**

| 历史日期 | 触发次数 | 时间 |
|---|---:|---|
| 2026-05-28 | 1 | 03:05 |
| 2026-05-29 | 1 | 03:01 |
| 2026-05-30 | 1 | 03:08 |
| 2026-05-31 | 1 | 03:03 |
| 2026-06-01 | 1 | 03:06 |
| 2026-06-02 | 1 | 03:04 |
| **合计** | **6 次** | 命中同时段 ≥ 3 次 |

→ **命中已知周期性**（置信度 = 0.86，6/7 天同槽触发，见 suppression-rules.md §3.3）

**分级初始 → 抑制降档（R1 目标态）：**

| 阶段 | 级别 | 依据 |
|---|:--:|---|
| 初始分级 | P2 | S1 + D1（16min < 5min 边界，按 D1）+ peripheral → 矩阵外缘 P2 |
| 命中已知周期性 | **降一档 → P3** | R1 周期性规则 |
| 命中已知误报（备份） | **降 P3**（已为 P3，保留） | R1 已知误报规则 |

> **R1 目标态注释**：本例同时命中"周期性"与"已知误报"两条抑制规则。
> 按 v0.1.0 R1 规则："维护窗/周期性 → 降一档；已知误报 → 一律 P3"。
> 由于降档不可跨级，本例执行顺序：P2 → (周期性降一档) P3 → (已知误报，保留) P3。
> 若按当前 severity-matrix.md §8.1 旧规则（"逐级降"），本例将 P2 → P3，结果一致。
> **本示例按 v0.1.0 目标态 R1 编写**。

### 5) Step 5 报告

**§3 P3 详单（按 R1 仍展示但降级标注）：**

```
ℹ️  簇 C-201 — vm/i-bak-node-01/vm.cpu.util （P3，降级前 P2）
  抑制原因:
    1. 已知周期性（置信度 0.86, 历史 7d 同槽触发 6/7 次）
    2. 已知误报 §4.1 备份任务（资源名含 "backup"）
  业务影响: peripheral
  触发次数: 1  |  持续: 16min
  下一跳:
    → jdcloud-cloudmonitor-ops 调整告警规则: 备份任务评估期拉长（evaluation-periods=3）
       或针对 backup_window 内的事件加入抑制规则
    → 或: 将此资源加入 jdcloud-iam-ops 维护窗 tag 体系
  响应时限: 仅日报聚合
```

### 6) 下一跳

- **告警规则优化** → `jdcloud-cloudmonitor-ops`（evaluation-periods / threshold）
- **批量维护窗配置** → `jdcloud-iam-ops`（资源 tag 治理）
- **不建议动作**：
  - ❌ 直接忽略（值班人员仍会收到通知）
  - ❌ 删除告警规则（备份异常也可能反映真实故障）
  - ❌ 升级实例规格（治标不治本）

---

## 示例 5: 跨服务故障（AIOps 协同）

### 1) 用户问题

> "网站访问慢，但不知道哪里出问题。"

### 2) 入参

`region=cn-north-1` · `time_window=2026-06-03T14:00:00+08:00 / 2026-06-03T15:00:00+08:00 (1h)` · `severity_filter/service_filter=无`

### 3) Step 1 拉取

同示例 1 命令结构，时间窗 1h。

### 4) Step 2-4 处理

**聚合（3 个不同 service_code 的簇，**注意：v0.1 不做跨簇关联**，仅展示共时性）**

| 簇 ID | 三元组 | 触发 | 首次 | 末次 | 持续 | 业务 | 级别 |
|---|---|---:|---|---|---:|---|:--:|
| `C-301` | (lb, lb-prod-entry-01, lb.httpcode.5xx) | 4 | 14:18 | 14:42 | 24min | core | **P1** |
| `C-302` | (vm, i-prod-app-01, vm.cpu.util) | 5 | 14:20 | 14:50 | 30min | core | **P0** |
| `C-303` | (redis, redis-cache-01, redis.connection.count) | 3 | 14:21 | 14:35 | 14min | important | **P2** |

**时间对齐（共时性分析）：**

```
14:18 ━━ C-301 (LB 5xx 首次)
14:20 ━━ C-302 (VM CPU 首次)
14:21 ━━━ C-303 (Redis 连接打满 首次)
   ↓ 3 分钟内 3 个服务同时告警 (vm + lb + redis)
   ↓ 高度疑似同根因
```

**v0.1 限制说明（关键）：**

```
⚠️  v0.1 本 skill 不做跨簇根因关联。
   以下"疑似同根因"判断由 Agent 基于时间对齐+业务常识推断，
   不是 v0.1 的算法输出，不应作为自动化动作依据。
```

**疑似根因推断（人工/Agent 推断）：**

- 14:21 Redis 连接打满 → 14:20 应用 VM 因无法连接 Redis 触发 CPU 上涨
  → 14:18 LB 后端 5xx 开始上升
- 推断根因顺序：Redis 连接瓶颈 → 应用 VM 资源耗尽 → LB 后端 5xx

### 5) Step 5 报告

**§3 P0/P1 详单（按 v0.1 独立分级输出）：**

```
🔴 簇 C-302 — vm/i-prod-app-01/vm.cpu.util （P0）
  业务影响: core
  触发次数: 5  |  持续: 30min  |  频次: 5/h
  下一跳:
    → jdcloud-vm-ops 检查 i-prod-app-01 进程与资源使用
    → ⚠️ 与 C-301/C-303 共时性高，建议跨 skill 联合处置（v0.2 rca-engine）

⚠️  簇 C-301 — lb/lb-prod-entry-01/lb.httpcode.5xx （P1）
  业务影响: core
  触发次数: 4  |  持续: 24min  |  频次: 4/h
  下一跳:
    → jdcloud-clb-ops 检查 lb-prod-entry-01 后端健康度
    → ⚠️ 14:18 首次触发，疑似由 C-302 引发

📋 簇 C-303 — redis/redis-cache-01/redis.connection.count （P2）
  业务影响: important
  触发次数: 3  |  持续: 14min  |  频次: 3/h
  下一跳:
    → jdcloud-redis-ops 检查连接打满根因
    → ⚠️ 14:21 首次触发，疑似根因起点
```

**§5 下一跳建议（聚合）：**

```
本时段共 3 个不同 service_code 簇同时告警（vm + lb + redis），
时间差 < 3 分钟，高度疑似同根因。
v0.1 限制：本 skill 仅展示共时性，不做根因关联。
建议处置顺序（按推断根因起点）：
  1. jdcloud-redis-ops （C-303，可能根因）
  2. jdcloud-vm-ops   （C-302，下游）
  3. jdcloud-clb-ops  （C-301，最下游表现）
v0.2 rca-engine 将自动化此关联过程。
```

### 6) 下一跳

- **本 skill 范围（v0.1）**：输出共时性分析，**不**自动委派、不**自动**开工单
- **手动协作（v0.1 临时方案）**：
  1. 人工按 §5 处置顺序依次调用各 `jdcloud-*-ops`
  2. 在工单中附本报告 §3 + §5 内容
- **v0.2 路径**：`jdcloud-rca-engine`（计划）将自动检测跨服务共时簇、给出根因假设排序
  - **不承诺 v0.2 时间表**，仅作"演进方向"说明
- **跨 skill 协作原则**：
  - 本 skill 永不变更云资源
  - 委派动作由用户/上层 Agent 决定
  - 详见 SKILL.md "委派规则" 章节

---

## 附录: 5 个示例对照 + 引用映射

**对照表：**

| 维度 | ①压测 | ②周报 | ③风暴 | ④周期 | ⑤跨服务 |
|---|---|---|---|---|---|
| 时间窗 | 24h | 7d | 8h | 6h | 1h |
| 原始→簇 | 312→6 | 1247→89 | 580→11 | 1→1 | 12→3 |
| 去重率 | 98% | 93% | 98% | — | 75% |
| P0 | 1+3(S3) | 2 | 1 | 0 | 1 |
| 抑制命中 | 0 | 43(48%) | 少 | 2 | 0 |
| 主要委派 | clb+vm+rds | cloudmonitor | vm+clb | cloudmonitor | redis+vm+clb |

**引用映射：** Step 1 拉取 → [cli-usage.md](./cli-usage.md)；Step 2 聚合 → [playbook-aggregate.md](./playbook-aggregate.md)；
Step 3 分级 → [severity-matrix.md](./severity-matrix.md) + [playbook-classify.md](./playbook-classify.md)；
Step 4 抑制 → [suppression-rules.md](./suppression-rules.md) + [playbook-suppress.md](./playbook-suppress.md)；
业务识别 → [core-concepts.md §1.3](./core-concepts.md)；降噪统计 → [core-concepts.md §4](./core-concepts.md)；
报告填充 → [assets/report-template.md](../assets/report-template.md)。

**使用建议：** 首次集成用 ③ 照搬可跑；on-call 培训用 ①+④；周报自动化参考 ② 的 7d 窗口；
故障复盘用 ⑤ 的共时性分析；阈值调优用 ④ 委派 `jdcloud-cloudmonitor-ops` 的描述。
