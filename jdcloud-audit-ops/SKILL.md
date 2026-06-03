---
name: jdcloud-audit-ops
description: >-
  Use when managing JD Cloud Audit Log resources — query operation events,
  describe event details, list operation trails, analyze user activity history,
  and manage event tracking. Works with "审计日志", "操作审计", "云审计",
  "Audit Log", or "操作记录" without saying "audit". Not for CloudTrail
  configurations from other clouds, VPC flow logs, or general monitoring.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: jdcloud
  version: "1.2.0"
  last_updated: "2026-06-04"
  runtime: Harness AI Agent
  api_profile: "JD Cloud Audit Log API v1 - https://docs.jdcloud.com/cn/audit-log"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc audit --help` showing audit log operations:
    describe-events, describe-event-detail, describe-trails, etc.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Audit Log Operations Skill

## Overview

JD Cloud Audit Log (操作审计/云审计) provides comprehensive tracking and recording of user operations and API calls on JD Cloud resources. It enables security auditing, compliance monitoring, operational troubleshooting, and accountability by capturing who did what, when, and from where. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery.

**Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - For commonly used commands and quick lookup.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` supports this product with audit log subcommands. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths are documented in [CLI Usage](references/cli-usage.md) and [API & SDK Usage](references/api-sdk-usage.md).

### Path Preference (jdc-first with SDK Fallback)

The Agent MUST follow this execution priority:

1. **`jdc` CLI (primary path)** — Attempt `jdc` first for every operation
2. **Retry up to 3 times** if `jdc` fails (with exponential backoff: 0s → 2s → 4s)
3. **SDK/API (fallback path, after 3 jdc failures)** — Use only when `jdc` is persistently unavailable

When both paths succeed, prefer `jdc` output for consistency.

### Critical jdc CLI Behavioral Notes (from empirical testing)

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
- Task involves trail management (if supported by API)

### SHOULD NOT Use This Skill When

- Task is about CloudTrail from AWS or other clouds → state this is JD Cloud only
- Task is about VPC flow logs → delegate to appropriate VPC skill
- Task is about Cloud Monitor metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task is purely billing / account management → delegate to appropriate skill
- Task is IAM permission analysis only → delegate to: `jdcloud-iam-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If audit analysis reveals resource issues (e.g., unauthorized VM changes), delegate resource remediation to appropriate skill (e.g., `jdcloud-vm-ops`)
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
| 1.2.0 | 2026-06-04 | **GCL rollout (optional)**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, read-only audit log query, PII masking guard for `requestParameters`) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=5`. `safety_confirm_required=false` (read-only by definition). |
| 1.1.0 | 2026-06-04 | Optimized SKILL.md structure, created QUICK_REFERENCE.md, split detailed content to references/ directory |
| 1.0.0 | 2026-06-03 | Initial version with audit log query support: describe-events, describe-event-detail, describe-trails; jdc-first with SDK fallback |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. Do not skip phases.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Complete examples for both paths are in [CLI Usage](references/cli-usage.md) and [API & SDK Usage](references/api-sdk-usage.md).

### Operation: Describe Events (List Operation Events)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.audit.client.AuditClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Time range | Collect `{{user.start_time}}` and `{{user.end_time}}` | Valid ISO 8601 | Ask user; suggest defaults (last 24h) |

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json audit describe-events \
  --region-id "{{user.region}}" \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --page-number 1 \
  --page-size 50
```

**With optional filters:**

```bash
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

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.audit.client.AuditClient import AuditClient
from jdcloud_sdk.services.audit.apis.DescribeEventsRequest import DescribeEventsRequest, DescribeEventsParameters

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = AuditClient(credential)

params = DescribeEventsParameters(
    regionId="{{user.region}}",
    startTime="{{user.start_time}}",
    endTime="{{user.end_time}}",
    pageNumber=1,
    pageSize=50
)

# Optional filters (add if provided by user)
if "{{user.event_name}}":
    params.eventName = "{{user.event_name}}"
if "{{user.resource_type}}":
    params.resourceType = "{{user.resource_type}}"
if "{{user.username}}":
    params.username = "{{user.username}}"

req = DescribeEventsRequest(parameters=params)
resp = client.send(req)

if resp.error is None:
    events = resp.result.get("events", [])
    for event in events:
        print(f"Event: {event.get('eventId')} | Time: {event.get('eventTime')} | User: {event.get('username')} | Action: {event.get('eventName')}")
else:
    print(f"Error: {resp.error.code} - {resp.error.message}")
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
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json audit describe-event-detail \
  --region-id "{{user.region}}" \
  --event-id "{{user.event_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.audit.apis.DescribeEventDetailRequest import DescribeEventDetailRequest, DescribeEventDetailParameters

params = DescribeEventDetailParameters(
    regionId="{{user.region}}",
    eventId="{{user.event_id}}"
)
req = DescribeEventDetailRequest(parameters=params)
resp = client.send(req)

if resp.error is None:
    detail = resp.result.get("eventDetail", {})
    print(f"Event ID: {detail.get('eventId')}")
    print(f"Time: {detail.get('eventTime')}")
    print(f"User: {detail.get('username')}")
    print(f"Action: {detail.get('eventName')}")
    print(f"Request Params: {detail.get('requestParameters')}")
    print(f"Response: {detail.get('responseElements')}")
else:
    print(f"Error: {resp.error.code} - {resp.error.message}")
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
| Request Parameters | `$.result.eventDetail.requestParameters` | JSON formatted |
| Response Elements | `$.result.eventDetail.responseElements` | JSON formatted |
| Error Code | `$.result.eventDetail.errorCode` | Red text if present |
| Error Message | `$.result.eventDetail.errorMessage` | Red text if present |

### Operation: Describe Trails (List Audit Trails)

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json audit describe-trails \
  --region-id "{{user.region}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.audit.apis.DescribeTrailsRequest import DescribeTrailsRequest, DescribeTrailsParameters

params = DescribeTrailsParameters(
    regionId="{{user.region}}"
)
req = DescribeTrailsRequest(parameters=params)
resp = client.send(req)

if resp.error is None:
    trails = resp.result.get("trails", [])
    for trail in trails:
        print(f"Trail: {trail.get('trailId')} | Name: {trail.get('trailName')} | Status: {trail.get('status')}")
else:
    print(f"Error: {resp.error.code} - {resp.error.message}")
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
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` (self) |
| `safety_confirm_required` | **false** | read-only by definition |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │
   ▼
[1] Generator (G)            ──► jdc audit (primary) → SDK (after 3 fails)
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

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK
access. The Orchestrator (O) owns the loop and persists the GCL trace.

### Operation-specific behavior

- **`describe-events`** (list operation events) — Time range + region +
  filter MUST be explicit. Default time range = last 24h. Trace MUST
  include page token if paginated.
- **`describe-event-detail`** (get single event details) — Event id MUST
  be explicit. **Sensitive fields in `requestParameters` MUST be
  masked** (password, secret, accessKey, accessKeySecret, privateKey →
  `***` or SHA-256 prefix). Unmasked sensitive data → Safety = 0 → ABORT.
- **`describe-trails`** (list audit trails) — All trails visible to the
  principal.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

Environment setup follows a **jdc-first with fallback** strategy. Complete setup guide is in [CLI Usage](references/cli-usage.md) and [API & SDK Usage](references/api-sdk-usage.md).

### Quick Setup Summary

1. **Attempt `jdc` CLI setup** via `uv` (primary path)
2. On failure, **retry up to 3 times** with exponential backoff
3. After **3 consecutive failures**, fall back to **SDK-only** setup

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

- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference for users
- [Core Concepts](references/core-concepts.md) - Detailed audit log concepts
- [API & SDK Usage](references/api-sdk-usage.md) - Complete API/SDK documentation
- [CLI Usage](references/cli-usage.md) - Complete CLI command reference
- [Troubleshooting Guide](references/troubleshooting.md) - Detailed troubleshooting
- [Monitoring & Alerts](references/monitoring.md) - Monitoring setup
- [Integration](references/integration.md) - Integration guide

## Operational Best Practices

- **Time Range Limits:** Audit log queries typically support a maximum 90-day window. For longer periods, make multiple sequential queries.
- **Pagination:** Use `pageNumber` and `pageSize` parameters for large result sets. Maximum `pageSize` is usually 100.
- **Filtering:** Apply filters (`eventName`, `resourceType`, `username`) to reduce query scope and improve performance.
- **Retention:** Understand your audit log retention policy. Events older than retention period may not be queryable.
- **Security Analysis:** Regularly review audit logs for unusual patterns: access from unexpected IPs, after-hours activity, privilege escalation attempts.
- **Compliance:** Export audit logs periodically for compliance requirements using describe-events with appropriate time ranges.
- **Event Detail:** When investigating security incidents, always retrieve full event details using `describe-event-detail` to see request parameters and response data.
