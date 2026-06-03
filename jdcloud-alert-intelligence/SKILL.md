---
name: jdcloud-alert-intelligence
description: >-
  京东云告警智能助手。Use when 京东云账户/项目/资源 已产生告警后,需要
  分级、聚合、抑制、降噪、值班疲劳统计 或 生成可读性高的告警分析报告。
  Trigger keywords: 告警降噪, 告警分析, 告警分级, 告警聚合, 告警抑制,
  on-call 疲劳, alert fatigue, alert aggregation, alert grouping,
  京东云告警, 告警历史分析, 告警模板。
  仅适用于已有告警的二次处理(只读);不创建告警规则(用 jdcloud-cloudmonitor-ops),
  不修产品配置(用各 jdcloud-*-ops)。
license: MIT
compatibility: >-
  jdc CLI 1.2.12+; 京东云账户已开通云监控;
  已配置 JDC_ACCESS_KEY / JDC_SECRET_KEY / JDC_REGION。
metadata:
  author: jdcloud
  version: "0.2.0"
  last_updated: "2026-06-04"
  runtime: Harness AI Agent
  api_profile: "monitor v1 - https://docs.jdcloud.com/cn/monitoring/api/overview"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  parent_skill: jdcloud-cloudmonitor-ops
  ecosystem_skills:
    - jdcloud-cloudmonitor-ops
    - jdcloud-vm-ops
    - jdcloud-clb-ops
    - jdcloud-redis-ops
    - jdcloud-rds-ops
---

> 本 Skill 遵循 [Agent Skill OpenSpec](https://agentskills.io/specification)。
> 京东云 Skills Farm 元规范：详情见 [`../jdcloud-skill-generator/SKILL.md`](../jdcloud-skill-generator/SKILL.md)。

# 京东云告警智能助手 (jdcloud-alert-intelligence)

## Overview

**京东云告警智能助手** 是云监控的**告警后处理层**：从 `jdc monitor describe-alarm-history`
拉取原始告警事件，做**聚合 → 分级 → 抑制 → 报告**四步处理，降低 on-call 工程师的告警疲劳。

**本 Skill 范围严格限定：**

- ✅ 拉取告警历史、统计、聚合、分级、抑制
- ❌ **不**创建 / 修改 / 删除告警规则 → 委派 [`jdcloud-cloudmonitor-ops`](../jdcloud-cloudmonitor-ops/SKILL.md)
- ❌ **不**修复底层资源问题 → 委派各 `jdcloud-*-ops`
- ❌ **不**配置告警联系人/通知渠道 → 委派 `jdcloud-cloudmonitor-ops`

### CLI 适用策略

- `cli_applicability: jdc-first-with-fallback`：本 Skill 全部为只读分析，无需 SDK/API fallback 路径。
- 命令一律前置 `--output json`；禁止使用不存在的 `--no-interactive`。
- 失败重试 3 次（指数退避 0s/2s/4s）；3 次失败后**返回原始错误**，不静默吞错。
- 详见 [references/cli-usage.md](./references/cli-usage.md)。

## Changelog

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.2.0 | 2026-06-04 | **GCL 推广（optional）**：新增 `## Quality Gate (GCL)` 章节接入仓库级 GCL。新增 `references/rubric.md`（5 维 rubric，静默故障保护：报告不得建议删/禁/改告警规则、4-tuple 引用、P0/P1 需下一跳建议）和 `references/prompt-templates.md`（G/C/O prompt 模板）。`max_iterations=5`。`safety_confirm_required=false`（read-only by mandate）。 |
| 0.1.0 | 2026-06-03 | 初版：聚合 / 分级 / 抑制 / 报告四件套；规则引擎实现，ML 留 v0.3 |

## 触发范围

### 应使用本 Skill

- "今天告警太多，帮我看看哪些是同一类"
- "上周 on-call 被打扰了多少次？"
- "这个告警严重吗？P0 还是 P3？"
- "告警风暴期哪些是真正的故障、哪些是误报？"
- "生成一份本周告警周报"

### 不应使用本 Skill

| 用户问题 | 应委派给 |
|---|---|
| 创建/修改告警规则、配置阈值 | `jdcloud-cloudmonitor-ops` |
| 告警说 VM CPU 高，帮我扩容/重启 | `jdcloud-vm-ops` |
| 告警说 LB 5xx 增多，帮我看后端 | `jdcloud-clb-ops` |
| 告警说 Redis 慢，帮我看大 Key | `jdcloud-redis-ops` |
| 实时监控大盘/面板 | `jdcloud-cloudmonitor-ops` (monitoring.md) |
| 阿里云/腾讯云/AWS 告警 | 对应云的 skill，本 skill 仅京东云 |

### 委派规则

- 本 Skill **只读**，**永不**自动调用其他 `jdcloud-*-ops` 执行变更动作
- 分析完成后，输出**下一跳建议**，由用户/上层 Agent 决定是否委派
- 委派建议格式：`→ 建议使用 \`jdcloud-vm-ops\` 升级实例规格`

## 变量约定

| 占位符 | 含义 | Agent 行为 |
|--------|------|-----------|
| `{{env.JDC_ACCESS_KEY}}` | 凭证 | 绝不向用户索取；未设置则失败 |
| `{{env.JDC_SECRET_KEY}}` | 凭证 | 同上；**绝不打印或记录** |
| `{{env.JDC_REGION}}` | 默认区域 | 默认 `cn-north-1` |
| `{{user.region}}` | 区域 | 询问一次，缓存复用 |
| `{{user.time_window}}` | 时间窗 | ISO 8601 区间，默认"最近 24h" |
| `{{user.severity_filter}}` | 分级过滤 | 可选 P0/P1/P2/P3 |
| `{{user.service_filter}}` | 服务过滤 | 可选服务代码 (vm/rds/lb/redis/...) |
| `{{output.alarm_id}}` | 告警 ID | 从 `$.result.alarmHistoryList[*].alarmId` 解析 |

## 工作流（5 步）

```
0. 前置检查
   ├─ 凭证存在性（仅检查，不打印）
   ├─ 时间窗确认（默认最近 24h，最多 15d 原始数据保留期）
   └─ 明确"只读"边界 → 提示用户本 skill 不变更任何资源
1. 拉取 → jdc monitor describe-alarm-history 拉时间窗内全部告警事件
2. 聚合 → 按 (service_code, resource_id, metric_name) 聚合为告警簇
3. 分级 → 按 P0-P3 矩阵给每个簇打级
4. 抑制 → 维护窗/周期性/已知误报 三类抑制
5. 报告 → 按 [assets/report-template.md](./assets/report-template.md) 输出
```

### Step 0 前置检查

**必做：**

```bash
# 仅检查凭证存在性，绝不打印值
test -n "$JDC_ACCESS_KEY" || { echo "FAIL: JDC_ACCESS_KEY 未设置"; exit 1; }
test -n "$JDC_SECRET_KEY" || { echo "FAIL: JDC_SECRET_KEY 未设置"; exit 1; }
test -n "$JDC_REGION" && export JDC_REGION || export JDC_REGION=cn-north-1
```

> **凭证加载链路**：
> - 上面 `test -n $JDC_*` 仅检查 Agent 进程环境变量是否设置（Agent 自己的检查逻辑）。
> - 实际 jdc CLI 通过 `~/.jdc/config` INI 文件读取凭证（详见 [references/cli-usage.md §1 凭证准备](./references/cli-usage.md)）。
> - Agent 启动前需保证：**(a)** 环境变量已设置 **(b)** `~/.jdc/config` 已配置 **(c)** 两边凭证值一致。

**时间窗约束：**

| 数据类型 | 保留期 | 本 skill 推荐窗口 |
|---|---|---|
| 原始数据 | 15d | ≤ 15d |
| 1h 聚合 | 30d | 15d - 30d |
| 1d 聚合 | 180d | 30d+（仅做趋势） |

### Step 1 拉取

```bash
jdc --output json monitor describe-alarm-history \
  --region-id "${JDC_REGION:-cn-north-1}" \
  --start-time "2026-06-02T00:00:00+08:00" \
  --end-time   "2026-06-03T00:00:00+08:00" \
  --page-size 100
```

完整命令、参数、响应路径、分页处理见 [references/cli-usage.md](./references/cli-usage.md)。

### Step 2 聚合

**聚合键：`(service_code, resource_id, metric_name)`** —— 同一三元组的多次触发视为"同一现象的重复"。

聚合后生成 **告警簇 (Cluster)**，每个簇包含：

- 触发次数、首次/末次触发时间、持续时长
- 受影响资源列表（通常 = 1，多资源时展开）
- 峰值指标值（如有 metric data 关联）
- 关联告警规则 ID 列表

完整策略与伪代码见 [references/playbook-aggregate.md](./references/playbook-aggregate.md)。

### Step 3 分级

**4 级矩阵 P0/P1/P2/P3**，按"影响面 × 持续时间 × 频次"三维判定。完整矩阵 20 个判定单元见
[references/severity-matrix.md](./references/severity-matrix.md)。

**核心分级速查（详细见 references）：**

| 级别 | 典型场景 |
|:--|:--|
| P0 | 核心业务中断 / 多资源同时异常 / 持续 > 30min |
| P1 | 单资源持续异常 5-30min |
| P2 | 单资源偶发 / 持续 < 5min |
| P3 | 已知周期性 / 维护窗内 / 已自动恢复 |

### Step 4 抑制

**三类抑制源（命中则降级一档或过滤）：**

1. **维护窗口**：资源 tag 含 `maintenance_window=*` 或用户在本次分析中显式声明的维护期
2. **已知周期性**：命中历史 7d 同时段（±30min）≥ 3 次的告警簇 → 降为 P3
3. **已知误报清单**：备份任务、批处理、滚动重启、CD 流量回切、镜像拉取 5 类常见 case

完整规则与脚本见 [references/suppression-rules.md](./references/suppression-rules.md)。

**v0.1 不做：** 同根因关联簇（依赖 v0.2 rca-engine）、动态阈值建议（v0.3）、ML 异常检测（v0.3）。

### Step 5 报告

报告固定 5 段：

1. **执行摘要**：告警总量 / 聚合后簇数 / P0-P3 分布 / 抑制数
2. **Top 簇列表**：按触发频次降序，Top 10
3. **P0/P1 详单**：必须人工介入的告警簇
4. **降噪统计**：重复率、夜间打扰率（22:00-08:00）、已被抑制数
5. **下一跳建议**：哪些应交给 `jdcloud-*-ops`、哪些应改告警规则

骨架见 [assets/report-template.md](./assets/report-template.md)。

## 输出解析规则

| 操作 | JSON 路径 | 类型 |
|------|-----------|------|
| 告警历史查询 | `$.result.alarmHistoryList[*]` | array |
| 告警规则列表 | `$.result.alarms[*].alarmId` | array |
| 告警规则详情 | `$.result.alarm.status` | string (`ALARM`/`OK`/`INSUFFICIENT_DATA`) |
| 监控项查询 | `$.result.metrics[*].metric` | array |
| 监控数据查询 | `$.result.metricDatas[*].dataPoints` | array |

更多路径与异常 case 见 [references/cli-usage.md § 关键 JSON 路径](./references/cli-usage.md)。

## 安全与合规

- **不**输出、不记录 `JDC_SECRET_KEY`（任何路径、日志、报告均不出现）
- 凭证检查仅 `test -n`，不打印值；如需状态用 `<masked>` 占位
- 全部操作**只读**：不改任何云资源、不改告警规则、不改配置
- 报告默认本地输出 `alert_intelligence_report_<region>_<时间窗>.md`，不外发
- 详细安全规则见 [references/core-concepts.md § 安全模型](./references/core-concepts.md)

## 核心原则

- **不编造**：缺失数据回答"暂无相关信息"，不推测
- **不执行破坏性动作**：本 Skill 全程只读
- **不替用户做决策**：只输出分级+建议，动作必须用户确认
- **不依赖 ML**：v0.1 用规则引擎，可解释、可审计
- **不强求全量数据**：jdc 失败 → 返回已有数据 + 错误信息，不静默吞错
- **可 fallback**：jdc 失败 3 次后不静默，回退到"原始数据 + 错误说明"

## 自检清单（输出报告前必过）

- [ ] 时间窗未超过 15d 原始数据保留期
- [ ] 凭证未打印
- [ ] 聚合键三元组完整（service/resource/metric 均非空）
- [ ] 每个 P0/P1 簇都有"下一跳建议"指向具体 jdcloud-*-ops
- [ ] 报告未捏造任何数字（所有数字均可追溯到 jdc 响应）

## 参考文档索引

| 路径 | 用途 |
|------|------|
| [references/core-concepts.md](./references/core-concepts.md) | 告警模型、聚合键、抑制术语、安全模型 |
| [references/cli-usage.md](./references/cli-usage.md) | jdc monitor 告警命令详解 + JSON 路径 |
| [references/severity-matrix.md](./references/severity-matrix.md) | P0-P3 分级矩阵（20 判定单元） |
| [references/suppression-rules.md](./references/suppression-rules.md) | 抑制规则清单 + 已知误报 5 类 |
| [references/playbook-aggregate.md](./references/playbook-aggregate.md) | 聚合策略与伪代码 |
| [references/playbook-classify.md](./references/playbook-classify.md) | 分级规则详解（含边界 case） |
| [references/playbook-suppress.md](./references/playbook-suppress.md) | 抑制规则脚本与示例 |
| [references/examples.md](./references/examples.md) | 端到端示例 5+ |

> ✅ v0.1.0 起 examples.md 已就绪，含 5 个端到端场景。

## 核心约束

- 不创建/修改/删除告警规则（委派 `jdcloud-cloudmonitor-ops`）
- 不修复产品配置（委派各 `jdcloud-*-ops`）
- 不替代 on-call 决策（只输出分级+建议）
- 不消费告警回调 Webhook（v0.2 再加）
- 不做跨云聚合（仅京东云内部）
- 不依赖 ML / 异常检测算法（v0.3 再加）

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this read-only skill (per
> `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for `jdcloud-alert-intelligence` (optional, read-only) |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **false** | read-only by mandate |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify workflow step
   │
   ▼
[1] Generator (G)            ──► jdc monitor (primary) → SDK (after 3 fails)
   │
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │
   ▼
[3] Orchestrator decider
   ├─ Safety=0 / blocking   → ABORT
   ├─ all pass              → RETURN
   ├─ iter<5 & not all pass → RETRY (inject suggestions)
   └─ iter=5 & not all pass → RETURN_BEST
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)

### Integration with existing flows

The GCL **wraps** the 5-step **工作流** defined above. The Generator (G) IS
the existing jdc-or-SDK executor that fetches alert data. The Critic (C)
audits the produced report's citations and completeness. The Orchestrator
(O) owns the loop and persists the GCL trace.

### Workflow-step-specific behavior

- **Step 1. 加载时间窗告警** — Time window MUST be explicit; default 24h;
  max 15d. Time window > 15d → ABORT.
- **Step 2. 聚合** — Aggregation key `(service, resource, metric)` MUST be
  complete for every cluster. Dropped clusters MUST cite a suppression
  rule.
- **Step 3. 分级** — Each cluster gets P0-P3 per `severity-matrix.md` with
  the 4-tuple citation `(metric_value, threshold, time_window, jdc_query)`.
- **Step 4. 抑制** — Every suppression MUST cite the matching rule in
  `suppression-rules.md`.
- **Step 5. 报告输出** — Every P0/P1 cluster MUST have a 下一跳建议 pointing
  to a specific `jdcloud-*-ops` operation. The report MUST NOT recommend
  `delete` / `disable` / `modify` on an alert rule (this skill is
  read-only by mandate).
