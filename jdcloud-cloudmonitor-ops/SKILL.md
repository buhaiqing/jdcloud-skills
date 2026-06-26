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
  version: "1.8.0"
  last_updated: "2026-06-26"
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

# JD Cloud CloudMonitor Ops Skill

## Overview

JD Cloud CloudMonitor is a monitoring and alerting service for cloud resources under your account, supporting monitoring of over 40 cloud products. This skill is an **Ops Runbook**: explicit trigger scope, credential rules, pre-flight checks, **jdc-first execution (SDK/API fallback)**, response validation, and failure recovery.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** The official `jdc` supports the CloudMonitor product. The Agent **must** prioritize `jdc` as the primary execution path. If `jdc` installation or command execution fails, the Agent **must** retry up to **3 times** (exponential backoff: 0s → 2s → 4s). Only after **3 consecutive failures** should it fall back to **SDK/API**. Both paths must be logged.
- **Path preference**: Follow the **jdc-first with SDK fallback** strategy. `jdc` is preferred for CLI operations; SDK is used for batch operations/integration tests (fallback path when jdc is unavailable).

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.8.0 | 2026-06-26 | **Full English translation**: All SKILL.md and reference files translated from Chinese to English. Consolidated cli-commands.md into cli-usage.md, best-practices.md into monitoring.md, removed orphan eval_queries.md. Chinese trigger keywords preserved in frontmatter description for agent matching. |
| 1.6.0 | 2026-06-18 | Initial GCL v2 content: Added Phase 6 H layer and Phase 7 Reflexion sections to Quality Gate. |
| 1.5.0 | 2026-06-10 | **Bidirectional routing & GCL chapter restructure**: ① Added `parent_skill: null` + `ecosystem_skills` (includes `jdcloud-alert-intelligence`) to frontmatter; ② Added two delegation rules pointing to `jdcloud-alert-intelligence` in the "Scenarios where this skill should NOT be used" table (alert post-processing / alarm history trend analysis); ③ The `## Quality Gate (GCL)` section was previously broken by `## Smart Fallback Strategy` (appeared as "continued"), now fully integrated loop diagram / Artifacts / Integration / Operation-specific behavior into the GCL chapter, removing the continuation; ④ Added `rubric.md` and `prompt-templates.md` links to Reference directory (achieving 8/8 ref validation). |
| 1.4.0 | 2026-06-04 | **GCL rollout (recommended)**: Added `## Quality Gate (GCL)` section, connecting this skill to the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, CloudMonitor-specific silent failure protection: `confirm=DELETE` / `confirm=DISABLE` gate for delete/disable alarm rules, `confirm=DELETE_AFTER_FIRING` for rules fired in the last 7 days, prod tag double-confirm, notification channel cannot be empty) and `references/prompt-templates.md` (G/C/O prompt templates). `max_iterations=3` (per `AGENTS.md` §8 recommended). `safety_confirm_required=true` for `delete-alarm-rule`, `disable-alarm-rule`. |
| 1.3.0 | 2026-05-06 | **Critical CLI behavioral fixes**: Fixed `--output json` placement (must be before subcommand), removed non-existent `--no-interactive` flag, corrected credential documentation (CLI only reads from `~/.jdc/config` INI, does not support environment variables), added sandbox config workspace |
| 1.2.0 | 2026-05-06 | **jdc-first fallback strategy**: Execution flow changed to `jdc` CLI first (primary path) + SDK/API fallback (after 3 retries); prerequisites updated to `uv`-guided Phase 1 (jdc) / Phase 2 (SDK fallback); path preference flipped; pre-flight check order adjusted |
| 1.1.0 | 2026-05-03 | Added SDK/API dual-path execution flow, improved frontmatter, added api-sdk-usage.md |
| 1.0.0 | 2026-04-28 | Initial version, includes CloudMonitor core functionality, alarm configuration, and operations best practices |

## Trigger Scope (Agent-readable)

### Scenarios where this skill SHOULD be used
- User mentions keywords such as "CloudMonitor", "云监控", "monitoring", "告警"
- Task involves monitoring data queries, alarm rule CRUD, alarm history viewing, custom monitoring reporting
- Task keywords: describe-metric-data, create-alarm, alarm, metric, dashboard, put-metric-data
- User requests cloud resource monitoring metric querying, alarm configuration, or alarm history analysis

### Scenarios where this skill SHOULD NOT be used
- Task is purely VM creation/deletion/start-stop → Delegate to `jdcloud-vm-ops`
- Task is purely RDS database management → Delegate to `jdcloud-rds-ops`
- Task is purely Load Balancer (LB) configuration → Delegate to `jdcloud-lb-ops`
- Task involves billing/account management → Delegate to `jdcloud-billing-ops`
- Task is purely **alert post-processing** (aggregation / classification / suppression / reporting / alert fatigue statistics / weekly report generation) → Delegate to `jdcloud-alert-intelligence` (read-only analysis skill; this skill does not handle alert noise reduction or on-call fatigue analysis)
- Task requires analyzing **alarm history trends**, **alarm cluster pattern mining**, **P0/P1 auto-classification suggestions** → Delegate to `jdcloud-alert-intelligence` (aggregated reports based on `monitor describe-alarm-history`)

### Delegation Rules
- If the user needs to first confirm monitoring data for a resource (e.g., VM), use this skill to query first, then recommend the appropriate resource management skill based on the results
- If the request involves monitoring across multiple independent cloud products, use this skill to query each product independently

## Variable Convention (Agent-readable)

This skill uses structured placeholders to prevent prompt injection and parsing ambiguity:

| Placeholder | Meaning | Agent Behavior |
|-------------|---------|----------------|
| `{{env.JDC_ACCESS_KEY}}` | Agent runtime environment variable | Never request from the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | Agent runtime environment variable | Never request from the user; fail if unset |
| `{{env.JDC_REGION}}` | Agent runtime environment variable | Default `cn-north-1`, can be overridden by user |
| `{{user.region}}` | Must collect from user | Ask once, cache and reuse |
| `{{user.resource_id}}` | Must collect from user | Ask once, cache and reuse |
| `{{user.alarm_id}}` | Must collect from user | Ask once, cache and reuse |
| `{{output.alarm_id}}` | Captured from CLI JSON output | Parse from `$.result.alarmId` |

> Rule: `{{env.*}}` placeholders must NOT be exposed or requested from the user. `{{user.*}}` placeholders must be collected through interaction.
> **Security Warning:** **Never** log, print, or expose the `JDC_SECRET_KEY` (or any secret) in console output, debug information, or logs. When verifying, only check existence (e.g., `if os.environ.get('JDC_SECRET_KEY')`), do not print the actual value. If credential status needs to be logged, use masked placeholders such as `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This rule applies to all execution paths (SDK, CLI, and debug scripts).

## Output Parsing Rules (Agent-readable)

### CLI Mandatory Conventions
- All CLI commands must place `--output json` **before** the subcommand: `jdc --output json monitor <command> ...`
- All CLI commands **must NOT** use `--no-interactive` (this flag does not exist)
- Timestamps use ISO 8601 format with timezone: `2026-04-28T10:00:00+08:00`
- Boolean values: `true` / `false` (lowercase)

### SDK Response Conventions
- SDK return object properties follow OpenAPI definitions
- Errors are thrown via `ClientException` / `ServerException`
- Timestamp format is the same as CLI

### Key JSON Paths
| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create alarm | `$.result.alarmId` / `response.result.alarmId` | string | Alarm rule ID |
| Query alarm list | `$.result.alarms[*].alarmId` | array | All alarm IDs |
| Query alarm details | `$.result.alarm.status` | string | ALARM / OK / INSUFFICIENT_DATA |
| Query metric data | `$.result.metricDatas[*].value` | array | Metric values |
| Query service list | `$.result.services[*].serviceCode` | array | Service code list |

### Operation Timeout Conventions
| Operation | Max Wait | Polling Interval |
|-----------|----------|------------------|
| Create alarm rule | 10s (synchronous operation) | - |
| Query metric data | 30s (API rate limit retry) | 2s |
| Delete alarm rule | 10s (synchronous operation) | - |

## Core Functions

- **Metric data query**: Query real-time and historical monitoring metric data for cloud resources
- **Alarm rule management**: Create, modify, enable/disable, delete alarm rules
- **Alarm history viewing**: Query alarm trigger history and notification records
- **Custom monitoring**: Report and query custom business metrics
- **Dashboard management**: Monitoring dashboard and chart management

## Execution Flow

Each operation follows: **Pre-flight check → Execute (jdc primary path / SDK fallback) → Post-execution validation → Failure recovery**. The Agent must not skip any phase.

**jdc-first strategy:** The Agent **must** prioritize trying `jdc` CLI (primary path). If `jdc` fails after (exponential backoff **3 retries**: 0s → 2s → 4s), fall back to SDK/API.

> Detailed execution flow (create alarm rule / query metric data / delete alarm rule) see [references/operations.md](references/operations.md).
> Smart fallback strategy (error classification / CLI Bug workarounds / SDK reference pitfalls / silent failures) see [references/fallback-strategy.md](references/fallback-strategy.md).
> Prerequisites and environment configuration see [references/prerequisites.md](references/prerequisites.md).
> CLI command reference see [references/cli-usage.md](references/cli-usage.md).

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
`## Execution Flow` above. The Generator (G) IS the existing
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

## Reference Directory

| Path | Purpose |
|------|---------|
| [references/core-concepts.md](references/core-concepts.md) | CloudMonitor core concepts and terminology |
| [references/api-sdk-usage.md](references/api-sdk-usage.md) | SDK operation mapping, request/response fields, error handling |
| [references/cli-usage.md](references/cli-usage.md) | CLI command reference + detailed CLI command descriptions |
| [references/troubleshooting.md](references/troubleshooting.md) | Common issues and solutions |
| [references/monitoring.md](references/monitoring.md) | Monitoring metrics, alarm configuration + operations best practices |
| [references/integration.md](references/integration.md) | SDK, OpenAPI, Prometheus, Grafana, Webhook integration |
| [references/integration-java.md](references/integration-java.md) | Java SDK integration |
| [references/integration-iac.md](references/integration-iac.md) | Terraform & CI/CD integration |
| [references/rubric.md](references/rubric.md) | GCL Critic scoring rules (5-dimension rubric + silent failure protection) |
| [references/prompt-templates.md](references/prompt-templates.md) | Generator / Critic / Orchestrator prompt skeletons |
| [references/operations.md](references/operations.md) | Core operation execution flow (create alarm / query monitoring / delete alarm) |
| [references/fallback-strategy.md](references/fallback-strategy.md) | Smart fallback strategy (error classification / CLI Bug workarounds / SDK pitfalls) |
| [references/prerequisites.md](references/prerequisites.md) | Prerequisites and environment configuration (uv / jdc / SDK installation) |
| [references/monitor-pitfalls.md](references/monitor-pitfalls.md) | Monitoring pitfalls (7 known pitfalls + fix patterns) |