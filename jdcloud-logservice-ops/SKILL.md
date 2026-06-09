---
name: jdcloud-logservice-ops
description: >-
  Use when managing JD Cloud LogService (日志服务) resources — create and manage
  LogSets (日志集), LogTopics (日志主题), configure retention and indexing,
  search and analyze logs. Works with "LogService", "日志服务", "日志集",
  "日志主题", "日志检索", "log search", "log topic" without saying "JD Cloud"
  explicitly. NOT for CloudMonitor alarm rules, SLS (Alibaba Cloud), or
  third-party log aggregation tools.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints. SDK-only skill; `jdc` CLI does NOT support
  LogService operations.
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent
  api_profile: "LogService API v1.0 — https://docs.jdcloud.com/cn/logservice/api"
  cli_applicability: sdk-only
  cli_support_evidence: >-
    Official `jdc` CLI does NOT support LogService operations.
    Verified via `jdc --help` product list and CLI documentation at
    https://docs.jdcloud.com/cn/cli. LogService is accessible only via
    SDK/API. SDK namespace: `jdcloud_sdk.services.logs`.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud LogService Operations Skill

## Overview

JD Cloud LogService (日志服务) is a centralized log management platform that enables collection, storage, indexing, search, and analysis of logs across JD Cloud resources. It is organized around two primary resources:

- **LogSet (日志集)**: A logical container that groups related LogTopics. LogSets control retention policies and access boundaries.
- **LogTopic (日志主题)**: A log stream within a LogSet. Each LogTopic receives logs from one or more sources (VMs, containers, LB, etc.) and supports indexing for fast search.

This skill covers:
- **LogSet Management**: Create, describe, list, and delete LogSets
- **LogTopic Management**: Create, describe, list, and delete LogTopics
- **Log Search**: Query logs with Lucene-like syntax, time ranges, and filters
- **Configuration**: Retention days, indexing fields, and collection agents

### CLI applicability (repository policy)

- **`cli_applicability: sdk-only`:** Official `jdc` CLI does **not** support LogService. This skill uses **SDK/API only** execution path.
- **SDK Namespace**: `jdcloud_sdk.services.logs`
- **API Endpoint**: `logs.jdcloud-api.com`
- **Fallback**: No CLI fallback available; SDK is the only execution path.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "LogService" OR "日志服务" OR "日志集" OR "日志主题" OR "日志检索"
- Task involves creating, updating, deleting, or listing LogSets or LogTopics
- Task involves searching, querying, or analyzing logs stored in JD Cloud LogService
- Task involves configuring log collection, retention, or indexing
- Task keywords: create-logset, create-logtopic, search-log, describe-logsets,
  delete-logtopic, log retention, log index, 日志采集, 日志查询, 日志存储

### SHOULD NOT Use This Skill When

- Task is about CloudMonitor alarm rules or metrics → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about VM lifecycle operations → delegate to: `jdcloud-vm-ops`
- Task is about container / Kubernetes log collection setup → delegate to: `jdcloud-kubernetes-ops`
- Task is about Object Storage (OSS) log archiving → delegate to: `jdcloud-oss-ops`
- Task is about Function Compute logs → delegate to: `jdcloud-fc-ops` for function management; use this skill only for querying the logs after FC setup
- Task is purely billing / account management → delegate to: `jdcloud-billing-ops`

### Delegation Rules

- If user wants to collect VM logs, ensure VM exists via `jdcloud-vm-ops` first, then create LogTopic and configure collection agent here
- If user wants K8s log collection, configure cluster first via `jdcloud-kubernetes-ops`, then create LogTopic here
- Multi-product log pipeline: Source (VM/K8s/CLB) → LogTopic (this skill) → Analysis / OSS archive (this skill + `jdcloud-oss-ops`)

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.logset_name}}` | LogSet name | Ask once; reuse |
| `{{user.logset_uid}}` | LogSet unique ID (UID) | Parse from output or ask |
| `{{user.logtopic_name}}` | LogTopic name | Ask once; reuse |
| `{{user.logtopic_uid}}` | LogTopic unique ID (UID) | Parse from output or ask |
| `{{user.retention_days}}` | Log retention period in days | Ask once; default 7 |
| `{{user.query}}` | Log search query string | Ask once; reuse |
| `{{user.start_time}}` | Search start time (ISO 8601) | Ask once; reuse |
| `{{user.end_time}}` | Search end time (ISO 8601) | Ask once; reuse |
| `{{output.logset_uid}}` | Created LogSet UID | Parse from `$.result.uid` |
| `{{output.logtopic_uid}}` | Created LogTopic UID | Parse from `$.result.uid` |
| `{{output.search_results}}` | Log search result set | Parse from `$.result.data` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes.
- **SDK Namespace**: `jdcloud_sdk.services.logs`
- **Endpoint**: `logs.jdcloud-api.com`
- **Resource Naming**: LogSet and LogTopic names support UTF-8; UIDs are system-generated alphanumeric strings.

### Key JSON Paths

| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create LogSet | `$.result.uid` | string | LogSet unique identifier |
| Describe LogSet | `$.result.logset.uid` | string | LogSet UID |
| Describe LogSet | `$.result.logset.name` | string | LogSet name |
| Describe LogSet | `$.result.logset.retention` | int | Retention days |
| List LogSets | `$.result.logsets[*].uid` | array | LogSet UIDs |
| Create LogTopic | `$.result.uid` | string | LogTopic unique identifier |
| Describe LogTopic | `$.result.logtopic.uid` | string | LogTopic UID |
| Describe LogTopic | `$.result.logtopic.name` | string | LogTopic name |
| Describe LogTopic | `$.result.logtopic.logsetUID` | string | Parent LogSet UID |
| List LogTopics | `$.result.logtopics[*].uid` | array | LogTopic UIDs |
| Search Logs | `$.result.data[*].content` | array | Log entries |
| Search Logs | `$.result.total` | int | Total matching entries |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create LogSet | — | `active` | 2s | 30s |
| Create LogTopic | — | `active` | 2s | 30s |
| Delete LogTopic | `active` | absent | 2s | 60s |
| Delete LogSet | `active` | absent | 2s | 60s |
| Search Logs | — | results | — | 30s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-08 | Initial SDK-only skill for JD Cloud LogService |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK) → Validate → Recover**. No CLI path available.

---

### Operation: Create LogSet

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | `import jdcloud_sdk.services.logs` | No import error | Document install steps |
| Credentials | `os.environ["JDC_ACCESS_KEY"]` | Non-empty | HALT; user configures env |
| LogSet name | Validate non-empty, ≤ 128 chars | Valid format | Reject; ask for valid name |
| Region | Check region availability | `{{user.region}}` supported | Suggest valid region |
| Retention | `{{user.retention_days}}` ≥ 1 and ≤ 3650 | Valid range | Default to 7 |

#### Execution (Python SDK)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.logs.client import LogsClient
from jdcloud_sdk.services.logs.apis.create_log_set_request import CreateLogSetRequest

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = LogsClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

req = CreateLogSetRequest(
    regionId="{{user.region}}",
    name="{{user.logset_name}}",
    description="Created via skill",
    retention={{user.retention_days|default(7)}}
)
resp = client.createLogSet(req)
print(f"LogSet created: {resp.result.uid}")
```

#### Post-execution Validation

1. Parse `{{output.logset_uid}}` from `resp.result.uid`
2. Poll **DescribeLogSet** until response confirms the LogSet exists and is active
3. Report LogSet UID, name, and retention to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix name or retention; retry once |
| `LogSetAlreadyExists` | 0 | — | Ask to reuse existing or use new name |
| `QuotaExceeded` | 0 | — | HALT; suggest quota increase |
| Throttling / 429 | 3 | exponential | Back off and retry |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; then HALT with request ID |

---

### Operation: Describe LogSets

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.logs.apis.describe_log_sets_request import DescribeLogSetsRequest

req = DescribeLogSetsRequest(
    regionId="{{user.region}}",
    pageNumber=1,
    pageSize=50
)
resp = client.describeLogSets(req)

for ls in resp.result.logsets:
    print(f"{ls.uid} | {ls.name} | retention={ls.retention}d")
```

#### Present to User

| Field | Path | Notes |
|-------|------|-------|
| UID | `$.result.logsets[*].uid` | Unique identifier |
| Name | `$.result.logsets[*].name` | Human-readable name |
| Retention | `$.result.logsets[*].retention` | Days |
| Create Time | `$.result.logsets[*].createTime` | ISO 8601 |

---

### Operation: Delete LogSet

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: "Delete LogSet `{{user.logset_name}}` (`{{user.logset_uid}}`)? All contained LogTopics and their logs will be deleted. This is irreversible."
- **MUST** list all LogTopics within the LogSet and warn that they will be cascade-deleted
- **MUST NOT** proceed without clear user assent

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LogSet exists | DescribeLogSet | Found | Already deleted |
| Empty or acknowledged | ListLogTopics by LogSet | Empty OR user confirmed cascade | HALT; remove LogTopics first or confirm |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.logs.apis.delete_log_set_request import DeleteLogSetRequest

req = DeleteLogSetRequest(
    regionId="{{user.region}}",
    logsetUID="{{user.logset_uid}}"
)
resp = client.deleteLogSet(req)
print(f"LogSet deleted: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeLogSets** until the LogSet no longer appears (or DescribeLogSet returns 404)
2. Max wait: 60 seconds
3. Confirm deletion to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `LogSetNotFound` / 404 | 0 | — | Already deleted; report success |
| `LogSetNotEmpty` / 409 | 0 | — | HALT; delete contained LogTopics first |
| `InvalidParameter` / 400 | 0 | — | Fix UID; retry once if typo suspected |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Create LogTopic

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LogSet exists | DescribeLogSet | Found and active | HALT; create LogSet first |
| LogTopic name | Non-empty, ≤ 128 chars | Valid format | Reject; ask for valid name |
| Region | Check availability | Supported | Suggest valid region |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.logs.apis.create_log_topic_request import CreateLogTopicRequest

req = CreateLogTopicRequest(
    regionId="{{user.region}}",
    logsetUID="{{user.logset_uid}}",
    name="{{user.logtopic_name}}",
    description="Created via skill",
    collectionInfo={
        "type": "cloud_vm",  # or container, clb, custom
        "paths": ["/var/log/messages"]
    }
)
resp = client.createLogTopic(req)
print(f"LogTopic created: {resp.result.uid}")
```

#### Post-execution Validation

1. Parse `{{output.logtopic_uid}}` from `resp.result.uid`
2. Poll **DescribeLogTopic** until the LogTopic exists and is active
3. Report LogTopic UID, name, and parent LogSet UID to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args; retry once |
| `LogTopicAlreadyExists` | 0 | — | Ask to reuse or rename |
| `LogSetNotFound` / 404 | 0 | — | HALT; verify LogSet UID |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Describe LogTopics

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.logs.apis.describe_log_topics_request import DescribeLogTopicsRequest

req = DescribeLogTopicsRequest(
    regionId="{{user.region}}",
    logsetUID="{{user.logset_uid}}",
    pageNumber=1,
    pageSize=50
)
resp = client.describeLogTopics(req)

for lt in resp.result.logtopics:
    print(f"{lt.uid} | {lt.name} | logset={lt.logsetUID}")
```

#### Present to User

| Field | Path | Notes |
|-------|------|-------|
| UID | `$.result.logtopics[*].uid` | Unique identifier |
| Name | `$.result.logtopics[*].name` | Human-readable name |
| LogSet UID | `$.result.logtopics[*].logsetUID` | Parent LogSet |
| Create Time | `$.result.logtopics[*].createTime` | ISO 8601 |

---

### Operation: Delete LogTopic

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: "Delete LogTopic `{{user.logtopic_name}}` (`{{user.logtopic_uid}}`)? All logs in this topic will be permanently deleted. This is irreversible."
- **MUST NOT** proceed without clear user assent

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LogTopic exists | DescribeLogTopic | Found | Already deleted |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.logs.apis.delete_log_topic_request import DeleteLogTopicRequest

req = DeleteLogTopicRequest(
    regionId="{{user.region}}",
    logsetUID="{{user.logset_uid}}",
    logtopicUID="{{user.logtopic_uid}}"
)
resp = client.deleteLogTopic(req)
print(f"LogTopic deleted: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeLogTopics** until the LogTopic no longer appears (or DescribeLogTopic returns 404)
2. Max wait: 60 seconds
3. Confirm deletion to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `LogTopicNotFound` / 404 | 0 | — | Already deleted; report success |
| `InvalidParameter` / 400 | 0 | — | Fix UID; retry once if typo suspected |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Search Logs

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LogTopic exists | DescribeLogTopic | Found and active | HALT |
| Query syntax | Validate non-empty | Valid string | Ask for query |
| Time range | `startTime` < `endTime`, within retention | Valid range | Adjust to retention window |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.logs.apis.search_log_request import SearchLogRequest

req = SearchLogRequest(
    regionId="{{user.region}}",
    logtopicUID="{{user.logtopic_uid}}",
    query="{{user.query}}",
    startTime="{{user.start_time}}",
    endTime="{{user.end_time}}",
    pageNumber=1,
    pageSize=100
)
resp = client.searchLog(req)

print(f"Total matches: {resp.result.total}")
for entry in resp.result.data:
    print(f"[{entry.time}] {entry.content}")
```

#### Query Syntax Notes

- Full-text search: `error` matches any field containing "error"
- Field search: `level:error` or `status:500`
- Range search: `response_time:[100 TO 500]`
- Boolean: `error AND NOT debug`
- Wildcard: `host:web-*`

#### Post-execution Validation

1. Verify `resp.result.total` is a non-negative integer
2. If `resp.result.data` is empty but `total > 0`, warn user about pagination
3. If `total == 0`, suggest broadening query or checking time range
4. Report total count and sample entries to user

#### Pagination Handling

```python
total = resp.result.total
page_size = 100
page = 1
all_entries = []

while len(all_entries) < total:
    req = SearchLogRequest(
        regionId="{{user.region}}",
        logtopicUID="{{user.logtopic_uid}}",
        query="{{user.query}}",
        startTime="{{user.start_time}}",
        endTime="{{user.end_time}}",
        pageNumber=page,
        pageSize=page_size
    )
    resp = client.searchLog(req)
    all_entries.extend(resp.result.data)
    if len(resp.result.data) < page_size:
        break
    page += 1
```

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidQuery` / 400 | 0 | — | Fix query syntax; retry |
| `TimeRangeExceeded` / 400 | 0 | — | Shrink time range to retention window |
| `LogTopicNotFound` / 404 | 0 | — | HALT; verify LogTopic UID |
| Throttling / 429 | 3 | exponential | Back off and retry |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; then HALT |

---

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12.

1. **Install uv** (system-wide, one-time):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv
   ```

2. **Bootstrap Python environment**:
   ```bash
   uv venv --python 3.10
   source .venv/bin/activate
   uv pip install jdcloud_sdk
   ```

3. **Configure Credentials** (SDK uses environment variables):
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```

4. **Verify Configuration**:
   ```python
   python -c "
   import os
   from jdcloud_sdk.core.credential import Credential
   from jdcloud_sdk.services.logs.client import LogsClient
   credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
   client = LogsClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
   print('SDK credentials and Logs client OK')
   "
   ```

> **Note:** No CLI verification available for LogService (SDK-only skill).

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)
- [Rubric (GCL)](references/rubric.md)
- [Prompt Templates (GCL)](references/prompt-templates.md)

## Operational Best Practices

- **Retention planning**: Set LogSet retention based on compliance requirements. Longer retention = higher cost.
- **Index fields**: Configure index on frequently queried fields (e.g., `level`, `status`, `service`) for faster search.
- **Log collection agents**: Use JD Cloud official agents for VM/container collection to ensure reliable delivery.
- **Query optimization**: Use field filters (`level:error`) instead of full-text search for large datasets.
- **Time range**: Always constrain search to the smallest useful time range to reduce latency and cost.
- **Security**: Do not log sensitive data (passwords, tokens) to LogService; use masking rules in collection agents.
- **Naming convention**: Use descriptive LogSet/LogTopic names with environment suffixes (e.g., `prod-web-logs`).

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md`](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).

### Parameters

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for LogService ops (recommended) |
| `rubric_version` | `v1` | see [references/rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** | Delete LogSet / LogTopic requires confirmation |

### Rubric Dimensions

| Dimension | Threshold | Notes |
|-----------|-----------|-------|
| Correctness | ≥ 0.5 | LogSet/LogTopic UID/state matches request |
| Safety | = 1 | Delete operations confirmed; cascade deletion warned |
| Idempotency | ≥ 0.5 | Create with same name returns error consistently |
| Traceability | ≥ 0.5 | All SDK calls logged with request IDs |
| Spec Compliance | ≥ 0.5 | Follows LogService API conventions (retention range, query syntax) |

---
