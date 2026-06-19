---
name: jdcloud-audit-ops
description: >-
  Use when querying/inspecting JD Cloud Audit Log events and trails —
  query operation events, describe event details, list operation trails,
  analyze user activity history, and review event tracking data. Works with "审计日志", "操作审计", "云审计",
  "Audit Log", or "操作记录" without saying "audit". Not for CloudTrail
  configurations from other clouds, VPC flow logs, or general monitoring.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) — see
  Current Status for current CLI/SDK limitations.
metadata:
  author: buhaiqing
  version: "1.4.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "JD Cloud Audit Log API v1 - https://docs.jdcloud.com/cn/audit-log"
  cli_applicability: sdk-or-api-only
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    NOT VERIFIED in current locked toolchain (jdcloud_cli==1.2.12).
    `jdc audit` returned "invalid choice: 'audit'" in testing.
    All CLI examples are expected syntax only.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Audit Log Operations Skill

> **⚠️ Current Status**: This skill is a **documentation stub** for the JD Cloud Audit Log / 操作审计 product.
>   - The `jdc audit` CLI command has NOT been verified in the current locked toolchain (`jdcloud_cli==1.2.12`).
>   - The `jdcloud_sdk.services.audit` Python SDK module has NOT been found in the current lock.
>   - All CLI/SDK examples below are **expected API syntax only**; actual execution requires:
>     1. Confirming that a newer CLI version supports `jdc audit ...`
>     2. Or using the raw REST API at `https://audit.jdcloud-api.com/v1/...`
>     3. Or confirming the correct SDK service module name with JD Cloud documentation.
>   - See [QUICK_REFERENCE.md](references/QUICK_REFERENCE.md) for quick look-up.

## Overview

JD Cloud Audit Log (操作审计/云审计) provides comprehensive tracking and recording of user operations and API calls on JD Cloud resources. It enables security auditing, compliance monitoring, operational troubleshooting, and accountability by capturing who did what, when, and from where. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **SDK/API 优先（当前 CLI 未验证）**, response validation, and failure recovery.

**Quick Reference**: [QUICK_REFERENCE.md](references/QUICK_REFERENCE.md) - For commonly used commands and quick lookup.

### CLI applicability (repository policy)

- **`cli_applicability: sdk-or-api-only`:** 当前仓库锁定的 `jdcloud_cli==1.2.12` 未暴露 `jdc audit` 顶层命令。Agent MUST treat CLI snippets as **期望语法示例** only, and MUST verify CLI support before execution. Use SDK/API semantics first; because the locked SDK also lacks `jdcloud_sdk.services.audit`, raw OpenAPI REST is the current safest execution path until JD Cloud confirms the SDK module.

### Path Preference (SDK/API 优先，当前 CLI 未验证)

The Agent MUST follow this execution priority:

1. **Raw OpenAPI REST (current executable path)** — Use `https://audit.jdcloud-api.com/v1/...` with JD Cloud request signing after confirming endpoint/path with official docs.
2. **Official SDK (only after service module is confirmed)** — Do not import `jdcloud_sdk.services.audit` until the real SDK service name is verified.
3. **`jdc` CLI (expected syntax only)** — Execute only after confirming a newer CLI exposes `jdc audit ...`.

When a path is not verified, present it as documentation-only and do not claim successful execution.

### Critical jdc CLI Behavioral Notes (from empirical testing)

> **⚠️ 注意**: 以下 CLI 失败模式基于当前锁定版本 `jdcloud_cli==1.2.12`。该版本不支持 `jdc audit` 顶层命令。所有 CLI 示例仅供参考，实际执行前请确认 CLI 版本支持。

**Failure 0: `jdc audit` 命令不存在（当前锁定版本）**
当前锁定的 `jdcloud_cli==1.2.12` 未暴露 `audit` 顶层命令。执行 `jdc audit --help` 会返回 `invalid choice: 'audit'`。需等待官方 CLI 更新后方可使用。

**Failure 1: `--output json` must be TOP-LEVEL, not subcommand-level**
The `--output json` argument is defined in the base controller, not in individual subcommands. It MUST be placed **before** the subcommand.

**Failure 2: jdc CLI does NOT support `--no-interactive`**
The `--no-interactive` flag does not exist in the jdc CLI. Using it will cause an `unrecognized arguments` error. Omit this flag entirely.

**Failure 3: jdc CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables**
The CLI reads credentials exclusively from `~/.jdc/config` (INI format). Setting environment variables alone is insufficient.

**Failure 4: `PermissionError` on `~/.jdc/` directory creation**
In sandboxed environments where home is not writable, set `HOME` to a writable path and pre-create config files before running `jdc`. See [CLI Usage](references/cli-usage.md) for details.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud Audit" OR "审计日志" OR "操作审计" OR "云审计" OR "Audit Log" OR "操作记录"
- Task involves querying operation events: describe events, list events, filter by time range
- Task involves analyzing user activity: who accessed what resource, when, from which IP
- Task keywords: describeEvents, describeEventDetail, describeTrails, searchEvents, 查询事件, 操作记录
- User asks to track resource changes, API calls, or user actions on JD Cloud
- Task involves compliance auditing or security investigation
- Task involves trail listing and inspection

### SHOULD NOT Use This Skill When

- Task is about CloudTrail from AWS or other clouds → state this is JD Cloud only
- Task is about VPC flow logs → delegate to appropriate VPC skill
- Task is about Cloud Monitor metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task involves alert aggregation, deduplication, weekly reports → delegate to: `jdcloud-alert-intelligence`
- Task is full-link cruise, topology, capacity planning, comprehensive root cause → delegate to: `jdcloud-aiops-cruise`
- Task is purely billing / account management → delegate to appropriate skill
- Task is IAM permission analysis only → delegate to: `jdcloud-iam-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If audit analysis reveals resource issues (e.g., unauthorized VM changes), delegate resource remediation to appropriate skill (e.g., `jdcloud-vm-ops`)
- Alert aggregation / deduplication / rollup → delegate to: `jdcloud-alert-intelligence`
- Monitoring metric queries / alarm rule CRUD / custom metric → delegate to: `jdcloud-cloudmonitor-ops`
- Full-link cruise inspection / topology / capacity / comprehensive root cause → delegate to: `jdcloud-aiops-cruise`
- Audit logs / who changed what / change evidence → `jdcloud-audit-ops` (self)
- Resource remediation after audit finding → delegate to corresponding `jdcloud-*-ops` (e.g., `jdcloud-vm-ops`, `jdcloud-disk-ops`)
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.start_time}}` | Query start time (ISO 8601) | Ask once; reuse |
| `{{user.end_time}}` | Query end time (ISO 8601) | Ask once; reuse |
| `{{user.resource_type}}` | Resource type filter | Ask once; reuse (e.g., `vm`, `vpc`) |
| `{{user.event_name}}` | Event/operation name filter | Ask once; reuse |
| `{{user.username}}` | Username filter | Ask once; reuse |
| `{{user.event_id}}` | Event ID for detail query | Ask once; reuse |
| `{{output.event_id}}` | From last API or CLI JSON response | Parse from response per operation |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Sensitive Data Redaction Rule**: When outputting `requestParameters` or `responseElements` from audit event details, the agent MUST apply `mask_sensitive(data)` to redact the following fields to `***` or their SHA-256 prefix:
> - `password`, `passwd`, `pwd`
> - `secret`, `secretKey`, `accessKeySecret`
> - `accessKey`
> - `token`, `authorization`, `credential`
> - `privateKey`, `sessionKey`, `apiKey`
> - PII (手机号、邮箱等) 按策略 mask/hash
>
> 未脱敏的敏感字段出现在输出中将导致 GCL Safety = 0 → ABORT。
>
> 脱敏参考实现详见 [Redaction Reference](references/redaction.md)。

> **Privacy Display Policy**: 以下字段在不同模式下的展示策略：
>
> | 字段 | masked_default | full_internal | forensic_sealed | 外部导出（SIEM/Slack/Email） |
> |---|---|---|---|---|
> | eventId | 原样 | 原样 | 原样 | 原样 |
> | resourceId | 部分 mask（保留前4字符） | 原样 | 原样 | 部分 mask（保留前4字符） |
> | username | 可显示（内部审计） | 可显示 | mask/hash | mask/hash |
> | sourceIpAddress | 公网 /24 mask；私网原样 | 原样 | mask/`/24` hash | mask/hash |
> | userAgent | truncate（保留前80字符） | 可显示 | truncate（保留前40字符） | truncate/mask |
> | requestParameters / responseElements | 始终脱敏 | 始终脱敏（secret 类字段 `***`） | 始终脱敏 | 始终脱敏 |
>
> `masked_default`：默认模式。`full_internal`：受控内网排障。`forensic_sealed`：复盘关联（输出 SHA-256 前缀，不暴露原文）。详见 [Redaction Reference](references/redaction.md)。

> **Security Warning**: **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK, CLI, and debugging scripts).

## Output Parsing Rules (Agent-Readable)

### API and Response Conventions

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://audit.jdcloud-api.com/v1/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec. See [API & SDK Usage](references/api-sdk-usage.md) for error codes.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-06-03T10:00:00+08:00`).
- **Time Range:** Most audit queries require `startTime` and `endTime` parameters. Maximum query window typically 90 days.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Describe Events | `$.result.events[*].eventId` | array | List of event IDs |
| Describe Events | `$.result.events[*].eventTime` | array | Event timestamps |
| Describe Events | `$.result.events[*].eventName` | array | Operation names |
| Describe Events | `$.result.events[*].username` | array | User who performed action |
| Describe Events | `$.result.events[*].resourceType` | array | Type of resource affected |
| Describe Events | `$.result.totalCount` | integer | Total matching events |
| Describe Event Detail | `$.result.eventDetail.eventId` | string | Event ID |
| Describe Event Detail | `$.result.eventDetail.requestParameters` | object | Request parameters |
| Describe Event Detail | `$.result.eventDetail.responseElements` | object | Response data |
| Describe Trails | `$.result.trails[*].trailId` | array | List of trail IDs |

### Pagination Conventions

| Parameter | Type | Description |
|-----------|------|-------------|
| `pageNumber` | integer | Page number (1-based) |
| `pageSize` | integer | Items per page (max 100) |
| `totalCount` | integer | Total matching records |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2026-06-18 | **Complete GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H) and Phase 7 Reflexion Integration. Rubric expanded to 8 dimensions (5 core + 3 Aliyun-specific extensions). Added per-operation Safety sub-rules, worked examples, and H layer prompt template. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with aliyun-skills GCL v1.9.0 pattern. |
| 1.3.0 | 2026-06-09 | **P1 SecOps+AIOps**: Added mask_sensitive reference implementation (`references/redaction.md`), Privacy Display Policy, AIOps runbook scene definitions (`references/aiops-runbooks.md`), tightened external export security (Slack/Email/SIEM), clarified cross-skill delegation & PII display strategy, fixed Quick Reference raw eventDetail output. |
| 1.2.1 | 2026-06-09 | **P0 corrective update**: Marked current CLI/SDK paths as unverified in locked toolchain, switched to SDK/API-only metadata, added documentation-stub status, and tightened redaction / pagination guidance. |
| 1.2.0 | 2026-06-04 | **GCL rollout (optional)**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, read-only audit log query, PII masking guard for `requestParameters`) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=5`. `safety_confirm_required=false` (read-only by definition). |
| 1.1.0 | 2026-06-04 | Optimized SKILL.md structure, created QUICK_REFERENCE.md, split detailed content to references/ directory |
| 1.0.0 | 2026-06-03 | Initial version with audit log query support: describe-events, describe-event-detail, describe-trails |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute → Validate → Recover**. Do not skip phases.

**执行策略说明:** 当前锁定版本 CLI (`jdcloud_cli==1.2.12`) 不支持 `jdc audit`。SDK 模块 (`jdcloud_sdk.services.audit`) 也未在当前锁定版本中找到。以下 CLI 和 SDK 示例均为**期望语法**，Agent SHOULD NOT 直接执行未验证的命令。

> 安全执行路径：通过原始 REST API (`https://audit.jdcloud-api.com/v1/...`) 或确认 SDK 正确服务名后使用 SDK。详见 [API & SDK Usage](references/api-sdk-usage.md)。

### Operation: Describe Events (List Operation Events)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | 当前锁定版本不支持 jdc audit；视为文档参考 |
| SDK / deps | `import requests` | 标准库可用 | 如不可用，安装 `requests`；优先使用 REST API |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Time range | Collect `{{user.start_time}}` and `{{user.end_time}}` | Valid ISO 8601 | Ask user; suggest defaults (last 24h) |

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

> **⚠️ 注意**: `jdc audit` 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例，实际执行前请确认 CLI 版本支持。

**Documentation-only** when `cli_applicability: sdk-or-api-only`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
# NOTE: jdc audit 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例，实际执行前请确认 CLI 版本支持
jdc --output json audit describe-events \
  --region-id "{{user.region}}" \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --page-number 1 \
  --page-size 50
```

**With optional filters:**

```bash
# NOTE: jdc audit 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例，实际执行前请确认 CLI 版本支持
jdc --output json audit describe-events \
  --region-id "{{user.region}}" \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --event-name "{{user.event_name}}" \
  --resource-type "{{user.resource_type}}" \
  --username "{{user.username}}" \
  --page-number 1 \
  --page-size 50
```

#### Execution (SDK/API Expected Syntax — SDK module currently unavailable)

> **⚠️ 注意**: `jdcloud_sdk.services.audit` 模块当前不可用，建议直接通过 OpenAPI REST 调用。以下为 REST API 伪代码。

```python
# REST API 伪代码（当前 SDK 模块不可用，建议直接调用 OpenAPI）
import os, json, requests

# endpoint 路径需按官方 OpenAPI 文档确认；以下为典型格式
endpoint = "https://audit.jdcloud-api.com/v1/regions/{{user.region}}/events"

headers = {
    "Content-Type": "application/json",
    # Authorization / Jdcloud-Date 需按 JD Cloud V3 签名规范生成
    "Authorization": "JDCLOUD <signed>",
    "Jdcloud-Date": "20260609T120000Z",
}

params = {
    "startTime": "{{user.start_time}}",
    "endTime": "{{user.end_time}}",
    "pageNumber": 1,
    "pageSize": 50,
}

# Optional filters (add if provided by user)
if "{{user.event_name}}":
    params["eventName"] = "{{user.event_name}}"
if "{{user.resource_type}}":
    params["resourceType"] = "{{user.resource_type}}"
if "{{user.username}}":
    params["username"] = "{{user.username}}"

resp = requests.get(endpoint, headers=headers, params=params, timeout=30)

if resp.status_code == 200:
    data = resp.json()
    events = data.get("result", {}).get("events", [])
    for event in events:
        safe_event = mask_sensitive(event, mode="masked_default")
        print(f"Event: {safe_event.get('eventId')} | Time: {safe_event.get('eventTime')} | User: {safe_event.get('username')} | Action: {safe_event.get('eventName')}")
else:
    print(f"Error: {resp.status_code} - {resp.text}")
```

#### Post-execution Validation

1. Check `$.result.events` exists and is a non-empty array.
2. If empty array → inform user no events found in specified time range.
3. If error present → extract `$.error.code` and `$.error.message`, go to Failure Recovery.

#### Output to Present to User

| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| Event ID | `$.result.events[*].eventId` | Plain text |
| Event Time | `$.result.events[*].eventTime` | ISO 8601 formatted |
| Username | `$.result.events[*].username` | Plain text |
| Event Name | `$.result.events[*].eventName` | Plain text (operation) |
| Resource Type | `$.result.events[*].resourceType` | Plain text |
| Resource ID | `$.result.events[*].resourceId` | Plain text |
| Source IP | `$.result.events[*].sourceIpAddress` | Plain text |
| Total Count | `$.result.totalCount` | Plain text |

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `InvalidTimeRange` | 0 | — | Inform user of valid time range limits |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 500 | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: Describe Event Detail (Get Single Event Details)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Event ID | Collect `{{user.event_id}}` | Non-empty string | Ask user |
| CLI / deps | `jdc --version` | Exit code 0 | 当前锁定版本不支持 jdc audit；视为文档参考 |

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

```bash
# NOTE: jdc audit 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例，实际执行前请确认 CLI 版本支持
jdc --output json audit describe-event-detail \
  --region-id "{{user.region}}" \
  --event-id "{{user.event_id}}"
```

#### Execution (SDK/API Expected Syntax — SDK module currently unavailable)

> **⚠️ 注意**: `jdcloud_sdk.services.audit` 模块当前不可用，建议直接通过 OpenAPI REST 调用。以下为 REST API 伪代码。

```python
# REST API 伪代码（当前 SDK 模块不可用，建议直接调用 OpenAPI）
import os, json, requests

# endpoint 路径需按官方 OpenAPI 文档确认；以下为典型格式
endpoint = "https://audit.jdcloud-api.com/v1/regions/{{user.region}}/events/{{user.event_id}}"

headers = {
    "Content-Type": "application/json",
    # Authorization / Jdcloud-Date 需按 JD Cloud V3 签名规范生成
    "Authorization": "JDCLOUD <signed>",
    "Jdcloud-Date": "20260609T120000Z",
}

resp = requests.get(endpoint, headers=headers, timeout=30)

if resp.status_code == 200:
    data = resp.json()
    detail = data.get("result", {}).get("eventDetail", {})
    print(f"Event ID: {detail.get('eventId')}")
    print(f"Time: {detail.get('eventTime')}")
    print(f"User: {detail.get('username')}")
    print(f"Action: {detail.get('eventName')}")
    # ⚠️ 敏感字段脱敏：requestParameters / responseElements 中可能包含 password、secretKey、accessKey 等敏感信息，输出前必须脱敏
    print(f"Request Params: {mask_sensitive(detail.get('requestParameters', {}))}")
    print(f"Response: {mask_sensitive(detail.get('responseElements', {}))}")
else:
    print(f"Error: {resp.status_code} - {resp.text}")
```

#### Output to Present to User

| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| Event ID | `$.result.eventDetail.eventId` | Plain text |
| Event Time | `$.result.eventDetail.eventTime` | ISO 8601 formatted |
| Username | `$.result.eventDetail.username` | Plain text |
| Event Name | `$.result.eventDetail.eventName` | Plain text |
| Resource Type | `$.result.eventDetail.resourceType` | Plain text |
| Resource ID | `$.result.eventDetail.resourceId` | Plain text |
| Source IP | `$.result.eventDetail.sourceIpAddress` | Plain text |
| User Agent | `$.result.eventDetail.userAgent` | Plain text |
| Request Parameters | `$.result.eventDetail.requestParameters` | JSON formatted ⚠️ 必须脱敏 |
| Response Elements | `$.result.eventDetail.responseElements` | JSON formatted ⚠️ 必须脱敏 |
| Error Code | `$.result.eventDetail.errorCode` | Red text if present |
| Error Message | `$.result.eventDetail.errorMessage` | Red text if present |

### Operation: Describe Trails (List Audit Trails)

#### Execution — CLI (`jdc`) [期望语法 — 当前锁定版本不可用]

```bash
# NOTE: jdc audit 命令在当前锁定版本 (1.2.12) 中不可用，以下为期望语法示例，实际执行前请确认 CLI 版本支持
jdc --output json audit describe-trails \
  --region-id "{{user.region}}"
```

#### Execution (SDK/API Expected Syntax — SDK module currently unavailable)

> **⚠️ 注意**: `jdcloud_sdk.services.audit` 模块当前不可用，建议直接通过 OpenAPI REST 调用。以下为 REST API 伪代码。

```python
# REST API 伪代码（当前 SDK 模块不可用，建议直接调用 OpenAPI）
import os, json, requests

# endpoint 路径需按官方 OpenAPI 文档确认；以下为典型格式
endpoint = "https://audit.jdcloud-api.com/v1/regions/{{user.region}}/trails"

headers = {
    "Content-Type": "application/json",
    # Authorization / Jdcloud-Date 需按 JD Cloud V3 签名规范生成
    "Authorization": "JDCLOUD <signed>",
    "Jdcloud-Date": "20260609T120000Z",
}

resp = requests.get(endpoint, headers=headers, timeout=30)

if resp.status_code == 200:
    data = resp.json()
    trails = data.get("result", {}).get("trails", [])
    for trail in trails:
        print(f"Trail: {trail.get('trailId')} | Name: {trail.get('trailName')} | Status: {trail.get('status')}")
else:
    print(f"Error: {resp.status_code} - {resp.text}")
```

#### Output to Present to User

| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| Trail ID | `$.result.trails[*].trailId` | Plain text |
| Trail Name | `$.result.trails[*].trailName` | Plain text |
| Status | `$.result.trails[*].status` | Badge: 🟢 active / 🟡 inactive |
| Create Time | `$.result.trails[*].createTime` | ISO 8601 formatted |
| Update Time | `$.result.trails[*].updateTime` | ISO 8601 formatted |

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this read-only skill (per
> `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for `jdcloud-audit-ops` (optional, read-only) |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` (self) |
| `safety_confirm_required` | **false** | read-only by definition |
| `hallucination_check` | **optional** | Phase 6 H layer; recommended for API parameter validation |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► OpenAPI REST (primary) → SDK (after module confirmed)
   │                              generate command/payload (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (optional for audit-ops)      - API parameter existence
   │                                   - JSON structure compliance
   │                                   - time range validity (≤ 90 days)
   │
   ├── PASS → [1a] Execute (run the REST/SDK call)
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
   ├─ iter<5 & not all pass   → RETRY (inject suggestions)
   └─ iter=5 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Optional

> **Purpose**: Catch LLM-generated REST/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud Audit API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Three-Category Check (for audit-ops):**

| Category | Check | Method |
|---|---|---|
| **API Parameter Existence** | Verify every query parameter exists in the Audit API spec | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For `requestParameters` / `responseElements` in event details | Validate field nesting matches OpenAPI schema |
| **Time Range Validity** | Ensure `startTime`/`endTime` ≤ 90 days (retention limit) | Parse ISO 8601 and compute delta |

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
      "api_parameters": { "status": "PASS|FAIL", "unrecognized_params": [] },
      "json_structure": { "status": "PASS|FAIL", "issues": [] },
      "time_range": { "status": "PASS|FAIL", "delta_days": 30 }
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
# 2. Filter patterns by current skill name (jdcloud-audit-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidTimeRange: Limit startTime/endTime ≤ 90 days (retention limit)
- Sensitive data leakage: Apply mask_sensitive() to requestParameters before output
- Large result set timeout: Always use pageNumber/pageSize (≤100) for pagination"
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter" | "skill_generation" | "cross_skill" | "runtime" | "token_efficiency",
    "skill": "jdcloud-audit-ops",
    "command": "GET https://audit.jdcloud-api.com/v1/...",
    "error": "InvalidParameter: InvalidTimeRange",
    "fix": "Adjusted time range to ≤ 90 days",
    "reusable": true
  }
}
```

Reusable patterns (reusable=true) are candidates for `docs/failure-patterns.md` — the centralized Reflexion memory.

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O / H): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): [docs/failure-patterns.md](../docs/failure-patterns.md)

### Integration with existing flows

The GCL **wraps** the SDK/API-first flow defined under
`## Execution Flows` above. The Generator (G) IS the existing REST-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK
access. The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is an optional pre-execution structural check.

### Operation-specific behavior

- **`describe-events`** (list operation events) — Time range + region +
  filter MUST be explicit. Default time range = last 24h. Max = 90d (retention).
  Trace MUST include `pageNumber` / `pageSize` / `totalCount` if paginated.
  H layer validates time range ≤ 90 days before execution.
- **`describe-event-detail`** (get single event details) — Event id MUST
  be explicit. **Sensitive fields in `requestParameters` MUST be
  masked** (password, secret, accessKey, accessKeySecret, privateKey →
  `***` or SHA-256 prefix). Unmasked sensitive data → Safety = 0 → ABORT.
  H layer validates eventId format before execution.
- **`describe-trails`** (list audit trails) — All trails visible to the
  principal. Read-only query; no trail creation/deletion/modification attempted.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

Environment setup follows a **SDK/API 优先（当前 CLI 未验证）** strategy. Complete setup guide is in [CLI Usage](references/cli-usage.md) and [API & SDK Usage](references/api-sdk-usage.md).

### Quick Setup Summary

1. **Attempt OpenAPI REST / confirmed SDK setup** via `uv` (current executable path)
2. **`jdc` CLI** — only after confirming the CLI version supports `jdc audit`
3. If CLI is not supported, use **REST API** directly

### Python Runtime (uv)

Both `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

**Install uv (system-wide, one-time per machine):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or via Homebrew: brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Configure Credentials

**CRITICAL**: The `jdc` CLI reads credentials exclusively from `~/.jdc/config` (INI format). The SDK reads from environment variables. Complete credential setup guide is in [CLI Usage](references/cli-usage.md).

## Reference Directory

- [QUICK_REFERENCE.md](references/QUICK_REFERENCE.md) - Quick reference for users
- [Core Concepts](references/core-concepts.md) - Detailed audit log concepts
- [API & SDK Usage](references/api-sdk-usage.md) - Complete API/SDK documentation
- [CLI Usage](references/cli-usage.md) - Complete CLI command reference
- [Troubleshooting Guide](references/troubleshooting.md) - Detailed troubleshooting
- [Monitoring & Alerts](references/monitoring.md) - Monitoring setup
- [Integration](references/integration.md) - Integration guide
- [Redaction Reference](references/redaction.md) - Sensitive data masking utilities
- [AIOps Runbooks](references/aiops-runbooks.md) - AIOps incident/postmortem scene definitions

## Operational Best Practices

- **Time Range Limits:** Audit log queries typically support a maximum 90-day window. For longer periods, make multiple sequential queries.
- **Pagination:** Use `pageNumber` and `pageSize` parameters for large result sets. Maximum `pageSize` is usually 100.
- **Filtering:** Apply filters (`eventName`, `resourceType`, `username`) to reduce query scope and improve performance.
- **Retention:** Understand your audit log retention policy. Events older than retention period may not be queryable.
- **Security Analysis:** Regularly review audit logs for unusual patterns: access from unexpected IPs, after-hours activity, privilege escalation attempts.
- **Compliance:** Export audit logs periodically for compliance requirements using describe-events with appropriate time ranges.
- **Event Detail:** When investigating security incidents, always retrieve full event details using `describe-event-detail` to see request parameters and response data.
