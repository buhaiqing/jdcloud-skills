---
name: jdcloud-cloudmonitor-ops
description: >-
  Use when you need to query monitoring metrics, set up alarm thresholds,
  check resource health, view alarm history, or configure custom monitoring
  on JD Cloud CloudMonitor. This DevOps runbook handles metric queries,
  threshold alerts, health checks, and incident response. Applicable when
  user mentions CloudMonitor, 云监控, monitoring, 告警, 指标查询, 资源告警,
  监控面板, health check, 阈值告警, or metric-related tasks. Use even when
  user describes cloud resource status issues without explicitly mentioning
  "monitoring" or "alarm."
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network access
  to JD Cloud endpoints, and official JD Cloud CLI (jdc) for this product.
metadata:
  author: buhaiqing
  version: "1.7.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "monitor v1 - https://docs.jdcloud.com/cn/monitoring/api/overview"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Official jdc supports monitor product. Verified via `jdc monitor --help`
    and official CLI documentation at https://github.com/jdcloud-api/jdcloud-cli
  parent_skill: null
  ecosystem_skills:
    - jdcloud-alert-intelligence
    - jdcloud-vm-ops
    - jdcloud-clb-ops
    - jdcloud-redis-ops
    - jdcloud-rds-ops
    - jdcloud-kms-ops
    - jdcloud-iam-ops
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# 京东云云监控(CloudMonitor)运维 Skill

## Overview

京东云云监控(CloudMonitor)是对用户名下云资源进行监控和报警的服务，支持40余种云产品的监控。本 Skill 是 **运维 Runbook**：明确的触发范围、凭证规则、前置检查、**jdc-first 执行（SDK/API 降级）**、响应验证和失败恢复。

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** 官方 `jdc` 支持云监控产品。Agent **必须**优先使用 `jdc` 作为主执行路径。若 `jdc` 安装或命令执行失败，Agent **必须**最多重试 **3 次**（指数退避：0s → 2s → 4s）。仅当 **3 次连续失败** 后，才降级到 **SDK/API**。两条路径均需记录。
- **路径偏好**: 遵循 **jdc-first with SDK fallback** 策略。`jdc` 优先用于 CLI 操作；SDK 用于批量操作/集成测试（jdc 不可用时的降级路径）。

## Changelog

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.7.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, recommended) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for CLI parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.6.0 | 2026-06-18 | Initial GCL v2 content: Added Phase 6 H layer and Phase 7 Reflexion sections to Quality Gate. |
| 1.5.0 | 2026-06-10 | **双向路由与 GCL 章节重构**：① frontmatter 增加 `parent_skill: null` + `ecosystem_skills`（包含 `jdcloud-alert-intelligence`）;② "不应使用本 Skill 的场景"表新增两条指向 `jdcloud-alert-intelligence` 的委派规则（告警后处理 / 告警历史趋势分析）；③ `## Quality Gate (GCL)` 章节原本被 `## Smart Fallback Strategy` 拆断（出现"continued"续接），本次将 loop diagram / Artifacts / Integration / Operation-specific behavior 完整整合进 GCL 章节，删除续接；④ Reference 目录补充 `rubric.md` 与 `prompt-templates.md` 链接（达成 8/8 ref 校验）。 |
| 1.4.0 | 2026-06-04 | **GCL 推广（recommended）**：新增 `## Quality Gate (GCL)` 章节，将本 skill 接入仓库级 Generator-Critic-Loop。新增 `references/rubric.md`（5 维 rubric，云监控特有的静默故障保护：删/禁告警规则的 `confirm=DELETE` / `confirm=DISABLE` 门、规则 7 天内曾触发需 `confirm=DELETE_AFTER_FIRING`、prod 标签双重确认、告警通道不能为空）和 `references/prompt-templates.md`（G/C/O prompt 模板）。`max_iterations=3`（按 `AGENTS.md` §8 recommended）。`safety_confirm_required=true` for `delete-alarm-rule`, `disable-alarm-rule`。 |
| 1.3.0 | 2026-05-06 | **Critical CLI behavioral fixes**: 修复 `--output json` 定位（必须放在子命令之前）、删除不存在的 `--no-interactive` 标志、修正凭证文档说明（CLI 仅从 `~/.jdc/config` INI 读取，不支持环境变量）、增加了沙箱配置工作区 |
| 1.2.0 | 2026-05-06 | **jdc-first 降级策略**：执行流程改为 `jdc` CLI 优先（主路径）+ SDK/API 降级（3次重试后）；前提条件更新为 `uv` 引导的 Phase 1 (jdc) / Phase 2 (SDK 降级)；路径偏好翻转；前置检查顺序调整 |
| 1.1.0 | 2026-05-03 | 添加 SDK/API 双路径执行流程、完善 frontmatter、新增 api-sdk-usage.md |
| 1.0.0 | 2026-04-28 | 初始版本，包含云监控核心功能、告警配置和运维最佳实践 |

## 触发范围（Agent 可读）

### 应使用本 Skill 的场景
- 用户提及"云监控"、"CloudMonitor"、"监控"、"告警"等关键词
- 任务涉及监控数据查询、告警规则 CRUD、告警历史查看、自定义监控上报
- 任务关键词：describe-metric-data、create-alarm、alarm、metric、dashboard、put-metric-data
- 用户要求对云资源监控指标进行查询、配置告警、或分析告警历史

### 不应使用本 Skill 的场景
- 任务纯粹是云主机(VM)的创建/删除/启停 → 委派给 `jdcloud-vm-ops`
- 任务纯粹是云数据库(RDS)的管理 → 委派给 `jdcloud-rds-ops`
- 任务纯粹是负载均衡(LB)的配置 → 委派给 `jdcloud-lb-ops`
- 任务涉及账单/账户管理 → 委派给 `jdcloud-billing-ops`
- 任务纯粹是**告警后处理**（聚合 / 分级 / 抑制 / 报告 / 告警疲劳统计 / 周报生成） → 委派给 `jdcloud-alert-intelligence`（只读分析 skill；本 skill 不做告警降噪或值班疲劳分析）
- 任务需要分析**告警历史趋势**、**告警簇模式挖掘**、**P0/P1 自动分级建议** → 委派给 `jdcloud-alert-intelligence`（基于 `monitor describe-alarm-history` 的聚合报告）

### 委派规则
- 若用户需要先确认某资源（如 VM）的监控数据，先用本 Skill 查询，再根据结果建议使用对应的资源管理 Skill
- 若请求涉及多个独立云产品的监控，分别用本 Skill 对每个产品独立查询

## 变量约定（Agent 可读）

本 Skill 使用结构化占位符，防止 prompt 注入和解析歧义：

| 占位符 | 含义 | Agent 行为 |
|--------|------|-----------|
| `{{env.JDC_ACCESS_KEY}}` | Agent 运行时环境变量 | 绝不向用户索取；未设置则失败 |
| `{{env.JDC_SECRET_KEY}}` | Agent 运行时环境变量 | 绝不向用户索取；未设置则失败 |
| `{{env.JDC_REGION}}` | Agent 运行时环境变量 | 默认 `cn-north-1`，可被用户覆盖 |
| `{{user.region}}` | 须向用户收集 | 询问一次，缓存复用 |
| `{{user.resource_id}}` | 须向用户收集 | 询问一次，缓存复用 |
| `{{user.alarm_id}}` | 须向用户收集 | 询问一次，缓存复用 |
| `{{output.alarm_id}}` | 从 CLI JSON 输出捕获 | 从 `$.result.alarmId` 解析 |

> 规则：`{{env.*}}` 占位符不得向用户暴露或索取。`{{user.*}}` 占位符须通过交互收集。
> **安全警告：** **绝不**在控制台输出、调试信息或日志中记录、打印或暴露 `JDC_SECRET_KEY`（或任何密钥）。验证时仅检查存在性（如 `if os.environ.get('JDC_SECRET_KEY')`），不打印实际值。如需记录凭证状态，使用脱敏占位符如 `JDC_SECRET_KEY=<masked>` 或 `JDC_SECRET_KEY=***`。此规则适用于所有执行路径（SDK、CLI 及调试脚本）。

## 输出解析规则（Agent 可读）

### CLI 强制约定
- 所有 CLI 命令必须将 `--output json` **前置**（放在子命令之前）：`jdc --output json monitor <command> ...`
- 所有 CLI 命令**不得**使用 `--no-interactive`（此标志不存在）
- 时间戳采用 ISO 8601 格式带时区：`2026-04-28T10:00:00+08:00`
- 布尔值：`true` / `false`（小写）

### SDK 响应约定
- SDK 返回对象属性遵循 OpenAPI 定义
- 错误通过 `ClientException` / `ServerException` 抛出
- 时间戳格式同 CLI

### 关键 JSON 路径
| 操作 | JSON 路径 | 类型 | 说明 |
|------|-----------|------|------|
| 创建告警 | `$.result.alarmId` / `response.result.alarmId` | string | 告警规则 ID |
| 查询告警列表 | `$.result.alarms[*].alarmId` | array | 所有告警 ID |
| 查询告警详情 | `$.result.alarm.status` | string | ALARM / OK / INSUFFICIENT_DATA |
| 查询监控数据 | `$.result.metricDatas[*].value` | array | 监控数值 |
| 查询服务列表 | `$.result.services[*].serviceCode` | array | 服务代码列表 |

### 操作超时约定
| 操作 | 最长等待 | 轮询间隔 |
|------|---------|---------|
| 创建告警规则 | 10s（同步操作） | - |
| 查询监控数据 | 30s（API 限流重试） | 2s |
| 删除告警规则 | 10s（同步操作） | - |

## 核心功能

- **监控数据查询**: 查询云资源的实时和历史监控指标数据
- **告警规则管理**: 创建、修改、启用/禁用、删除告警规则
- **告警历史查看**: 查询告警触发历史和通知记录
- **自定义监控**: 上报和查询自定义业务指标
- **Dashboard管理**: 监控面板和图表管理

## 执行流程

每个操作遵循：**前置检查 → 执行（jdc 主路径 / SDK 降级） → 后置验证 → 失败恢复**。Agent 不得跳过任何阶段。

**jdc-first 策略：** Agent **必须**优先尝试 `jdc` CLI（主路径）。若 `jdc` 失败后（指数退避 **3 次重试**：0s → 2s → 4s），降级到 SDK/API。

> 详细执行流程（创建告警规则 / 查询监控数据 / 删除告警规则）见 [references/operations.md](references/operations.md)。
> 智能降级策略（错误分类 / CLI Bug 绕过 / SDK 引用陷阱 / 静默失败）见 [references/fallback-strategy.md](references/fallback-strategy.md)。
> 前提条件与环境配置见 [references/prerequisites.md](references/prerequisites.md)。
> CLI 命令速查见 [references/cli-commands.md](references/cli-commands.md)。

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **recommended** for all operations exposed by this
> skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-cloudmonitor-ops` (recommended); `delete-alarm-rule` / `disable-alarm-rule` are impactful but recoverable by re-creation |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-alarm-rule`, `disable-alarm-rule` | matches repository safety gate policy |
| `hallucination_check` | **recommended** | Phase 6 H layer; validates CLI parameters before execution |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► jdc (primary) → SDK (after 3 fails)
   │                              generate command (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (recommended for              - CLI parameter existence
   │    cloudmonitor-ops)             - JSON structure compliance
   │
   ├── PASS → [1a] Execute (run the jdc/SDK call)
   ├── FAIL → [1b] Regenerate (H retriggers G with hallucination report; max 1 retry)
   │         still FAIL → HALT with "HALLUCINATION_ABORT"
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │                              score every rubric dimension (5+3)
   │                              assess test accuracy + regression gate
   ▼
[3] Orchestrator decider
   ├─ HALLUCINATION_ABORT     → ABORT (no partial)
   ├─ Safety=0 / blocking     → ABORT
   ├─ all pass                → RETURN
   ├─ iter<3 & not all pass   → RETRY (inject suggestions)
   └─ iter=3 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Recommended

> **Purpose**: Catch LLM-generated CLI/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud CloudMonitor API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for cloudmonitor-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in `jdc monitor <operation>` | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads (e.g., alarm rule spec, metric queries) | Validate field nesting matches OpenAPI schema |

**Key Parameters to Validate:**

| Operation | Critical Parameters |
|---|---|
| `create-alarm-rule` | `--alarm-rule-name`, `--product`, `--metric`, `--resource-id`, `--threshold`, `--comparison`, `--notification-channel` |
| `delete-alarm-rule` | `--alarm-id` |
| `disable-alarm-rule` | `--alarm-id` |
| `describe-metric-data` | `--metric`, `--resource-id`, `--start-time`, `--end-time` |
| `describe-alarm-history` | `--alarm-id`, `--start-time`, `--end-time` |

**Termination:**

| Condition | Exit Code | Action |
|---|---|---|
| **H_PASS** | — | Continue to [1a] Execute |
| **H_FAIL → Regenerate** | — | Inject hallucination report into G; max 1 regeneration attempt |
| **HALLUCINATION_ABORT** | 5 | HALT — structural hallucinations persist after regeneration |

**Trace Integration:**

The H result is embedded in the GCL trace JSON under `iterations[].hallucination_detector`:

```json
{
  "iter": 1,
  "hallucination_detector": {
    "status": "PASS|FAIL",
    "checks": {
      "cli_parameters": { "status": "PASS|FAIL", "unrecognized_params": [] },
      "json_structure": { "status": "PASS|FAIL", "issues": [] }
    },
    "report": "..."
  },
  "regenerated": false,
  "generator": { ... },
  "critic": { ... }
}
```

### Reflexion Integration (Lightweight Reflexion)

> **Purpose**: Enable cross-session learning from failure patterns, complementing the within-session
> GCL loop with persistent failure memory.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCL Execution (per-session)                   │
│   [0] Pre-flight → [1] Generate → [1.5] H → [2] C → [3] Decide │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    failure_pattern (in trace)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Reflexion Memory (cross-session)                    │
│   docs/failure-patterns.md (structured text, ≤200 lines)        │
│   §1 CLI Parameter Errors | §2 Skill Generation | §3 Cross-Skill│
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    Pre-flight retrieval (optional)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prevention (next session)                           │
│   Inject known patterns into Generator context                  │
│   Agent avoids repeating known mistakes                          │
└─────────────────────────────────────────────────────────────────┘
```

**Pre-flight Retrieval (Optional):**

During GCL Pre-flight (step [0]), the Orchestrator MAY:

```bash
# 1. Load docs/failure-patterns.md (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name (jdcloud-cloudmonitor-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidNotificationChannel: notificationChannel must be a valid ID, not empty/null
- DELETE_AFTER_FIRING: Alarm rules fired in last 7 days need confirm=DELETE_AFTER_FIRING
- SilentDisable: Disabling alarm rules means silent failure; require explicit confirmation"
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): `docs/failure-patterns.md` (repository-wide)

### Integration with existing flows

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## 执行流程` above. The Generator (G) IS the existing
jdc-or-SDK executor. The Critic (C) is a new, read-only role with no
`jdc` / SDK access. The Orchestrator (O) owns the loop and persists the
GCL trace.

### Operation-specific behavior

- **`create alarm rule`** — Product + metric + resourceId + threshold +
  comparison + notification channel all must be explicit. `notificationChannel`
  MUST be a valid id (not empty / "0" / "null"). Check for duplicate
  `(product, metric, resourceId)` first.
- **`query metric data`** / **`query latest metric data`** — Read-only;
  Safety = 1.0 by default. Traceability and Correctness scored normally.
- **`modify alarm rule`** — Lowering threshold by > 50% can cause alarm
  spam; require explicit opt-in.
- **`disable alarm rule`** — **Means silent failure**. `confirm=DISABLE`
  required. For prod-tagged resources, additional `confirm=DISABLE_PROD`.
- **`delete alarm rule`** — **Means permanent loss of monitoring**.
  `confirm=DELETE` required. If the rule has fired in the last 7 days,
  additional `confirm=DELETE_AFTER_FIRING`. For prod-tagged resources,
  additional `confirm=DELETE_PROD`. Must include pre-delete snapshot of
  rule definition + recent alert history.

## Reference 目录

| 路径 | 用途 |
|------|------|
| [references/core-concepts.md](references/core-concepts.md) | 云监控核心概念和术语 |
| [references/api-sdk-usage.md](references/api-sdk-usage.md) | SDK 操作映射、请求/响应字段、错误处理 |
| [references/cli-usage.md](references/cli-usage.md) | 详细的 CLI 命令说明、CLI vs API 覆盖对比 |
| [references/troubleshooting.md](references/troubleshooting.md) | 常见问题及解决方案 |
| [references/monitoring.md](references/monitoring.md) | 监控指标和告警配置 |
| [references/integration.md](references/integration.md) | SDK、OpenAPI、Prometheus、Grafana、Webhook 集成 |
| [references/integration-java.md](references/integration-java.md) | Java SDK 集成 |
| [references/integration-iac.md](references/integration-iac.md) | Terraform & CI/CD 集成 |
| [references/rubric.md](references/rubric.md) | GCL Critic 评分规则（5 维 rubric + 静默故障保护） |
| [references/prompt-templates.md](references/prompt-templates.md) | Generator / Critic / Orchestrator prompt 骨架 |
| [references/operations.md](references/operations.md) | 核心操作执行流程（创建告警 / 查询监控 / 删除告警） |
| [references/fallback-strategy.md](references/fallback-strategy.md) | 智能降级策略（错误分类 / CLI Bug 绕过 / SDK 陷阱） |
| [references/prerequisites.md](references/prerequisites.md) | 前提条件与环境配置（uv / jdc / SDK 安装） |
| [references/cli-commands.md](references/cli-commands.md) | CLI 命令速查（常用 jdc monitor 命令） |
| [references/best-practices.md](references/best-practices.md) | 运维最佳实践、监控指标、API 限制 |
| [references/monitor-pitfalls.md](references/monitor-pitfalls.md) | 监控陷阱库（7 个已知陷阱 + 修复模式） |