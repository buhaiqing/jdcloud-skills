---
name: jdcloud-postgresql-ops
description: >-
  Use this skill for JD Cloud RDS PostgreSQL database management — create, configure, and
  manage PostgreSQL instances; backup and restore data; analyze performance;
  troubleshoot connection or latency issues. Apply when the user mentions PostgreSQL,
  RDS, 关系型数据库, 云数据库, 数据库, or asks about database, PostgreSQL instances on JD Cloud,
  even without explicit "PostgreSQL" mentions.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.4.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "JD Cloud RDS PostgreSQL API v1 - https://rds.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing 'rds' in product list:
    `{mps,cps,rds,jke,vpc,xdata,mongodb,configure,streambus,ipanti,baseanti,datastar,redis,nc,monitor,iam,disk,cr,streamcomputer,sop,clouddnsservice,vm,oss}`.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud RDS PostgreSQL Operations Skill

## Overview

JD Cloud RDS PostgreSQL (云数据库 RDS PostgreSQL) is a fully managed relational database service compatible with PostgreSQL protocol. It provides high availability, automatic backup, read replicas, and flexible scaling. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` supports this product. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the `jdc` step **and** the SDK fallback step for every operation the CLI exposes.

### Path Preference (jdc-first with SDK Fallback)

The Agent MUST follow this execution priority:

1. **`jdc` CLI (primary path)** — Attempt `jdc` first for every operation. Quick ad-hoc operations, shell automation, and single-operation tasks benefit most from CLI.
2. **Retry up to 3 times** if `jdc` fails (with exponential backoff: 0s → 2s → 4s).
3. **SDK/API (fallback path, after 3 jdc failures)** — Use only when `jdc` is persistently unavailable. Complex multi-step workflows with conditional logic, CI/CD pipelines with Python tooling, and integration tests may require SDK.

When both paths succeed, prefer `jdc` output for consistency with the primary path.

### Critical jdc CLI Behavioral Notes (from empirical testing)

**Failure 1: `--output json` must be TOP-LEVEL, not subcommand-level**
The `--output json` argument is defined in the base controller (`base_controller.py`), not in individual subcommands. Cement's nested argparse structure restricts `--output` to be placed **before** the subcommand.

```
# CORRECT (works):
jdc --output json rds describe-instances --region-id cn-north-1 --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc rds describe-instances --region-id cn-north-1 --page-number 1 --page-size 100 --output json
```

**Failure 2: jdc CLI does NOT support `--no-interactive`**
The `--no-interactive` flag does not exist in the jdc CLI argument definition. Using it will cause an `unrecognized arguments` error. Omit this flag entirely.

**Failure 3: jdc CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables**
The CLI's `ProfileManager` class reads credentials exclusively from `~/.jdc/config` (INI format). Setting environment variables alone is insufficient. The config file must be pre-created with the following structure:
```ini
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = rds.jdcloud-api.com
scheme = https
timeout = 20
```

Plus a `~/.jdc/current` file containing just `default` (no newline at end).

**Failure 4: `PermissionError` on `~/.jdc/` directory creation**
The CLI's `ProfileManager.__init__()` calls `__make_config_dir()` which does `os.makedirs(os.path.expanduser("~") + "/.jdc")`. In sandboxed environments (trae-sandbox, containers) where home is not writable, this crashes with `PermissionError`. The fix is:
1. Set `HOME` to a writable path: `export HOME=/tmp/jdc-home`
2. Pre-create `~/.jdc/config` and `~/.jdc/current` files before running `jdc`

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud PostgreSQL" OR "RDS PostgreSQL" OR "云数据库 PostgreSQL" OR "关系型数据库" OR "PostgreSQL实例"
- Task involves CRUD operations on PostgreSQL instances: create, describe, modify, delete, list, backup, restore, config
- Task keywords: createInstance, describeInstances, modifyInstance, backup, restore, database, postgres
- User asks to deploy, configure, troubleshoot, or monitor PostgreSQL instances **via API, SDK, CLI, or automation**
- Task involves PostgreSQL performance analysis (slow query log, connection pool)

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about MySQL → delegate to: `jdcloud-mysql-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If PostgreSQL instance requires VPC/subnet, verify or create network resources via `jdcloud-vpc-ops` first.
- If user asks about PostgreSQL monitoring metrics or alarm rules, delegate metric query to `jdcloud-cloudmonitor-ops`.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.instance_id}}` | User-supplied PostgreSQL instance ID | Ask once; reuse |
| `{{user.instance_name}}` | User-supplied instance name | Ask once; reuse |
| `{{output.instance_id}}` | From last API or CLI JSON response | Parse from `$.result.instanceId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK, CLI, and debugging scripts).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://rds.jdcloud-api.com/v1/regions/{regionId}/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-06-03T10:00:00+08:00`).
- **Idempotency:** Document duplicate instance name behavior and retry safety per API.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Instance | `$.result.instanceId` | string | New PostgreSQL instance ID |
| Describe Instance | `$.result.instance.status` | string | Instance state (running, creating, etc.) |
| List Instances | `$.result.instances[*].instanceId` | array | All instance IDs |
| Modify/Delete | `$.requestId` or `$.error` | string / object | Per spec |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | — | `running` | 10s | 600s |
| Modify Config | `running` | `running` | 10s | 300s |
| Delete | `running`/`stopped` | (404 on describe) | 10s | 600s |
| Backup | `running` | backup available | 10s | 300s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, mandatory) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for CLI parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.3.0 | 2026-06-08 | **Enhanced slow query capabilities**: (1) **Automated Perception**: Added CloudMonitor alarm integration for automatic slow query detection and alert-triggered analysis. (2) **Scheduled Audit**: Added `scheduled_pg_slowquery_audit` for daily/weekly automated patrol with trend analysis, optimization tracking, and PG-specific autovacuum health checks. (3) **PG-specific enhancements**: Enhanced `analyzeSlowQueries` with 9 root cause patterns (including PG-specific: Sequential Scan, Autovacuum/Bloat, Work Mem/Temp, Inefficient Nested Loop, Parameter Tuning). |
| 1.2.0 | 2026-06-05 | **Added Describe Slow Logs operations**: (1) `describeSlowLogs` — query slow query summaries by time range for single instance. (2) `describeSlowLogsByTags` — two-phase composite operation: filter instances by tags, then parallel query slow logs across all matching instances. Both support pagination, filtering (account/keyword), sorting (execution metrics), with safety guards (max_instances limit, parallel execution control). |
| 1.1.0 | 2026-06-04 | **GCL rollout**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, instance-level + DDL/DML paths, PG-specific rules for `VACUUM FULL`, `DROP SCHEMA`, sequence reset) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=2`. `safety_confirm_required=true` for delete, restore, storage shrink, DDL `DROP`/`TRUNCATE`, DML `UPDATE`/`DELETE` without WHERE. |
| 1.0.0 | 2026-06-03 | Initial version with API/SDK and `jdc` CLI dual-path support |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. Do not skip phases.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Documentation below lists `jdc` before SDK to reflect execution priority.

### Operation: Create PostgreSQL Instance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.rds.client.RdsClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Call `describeAvailableRegion` API | `{{user.region}}` supported | Suggest valid region |
| VPC/Subnet | Verify subnet via `jdcloud-vpc-ops` | Subnet exists and has IP | HALT; create subnet first |
| Instance Class | Call `describeInstanceClass` or `describeSpecConfig` | Valid spec code | Suggest available specs |

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json rds create-instance \
  --region-id "{{user.region}}" \
  --instance-name "{{user.instance_name}}" \
  --instance-class "{{user.instance_class}}" \
  --engine "PostgreSQL" \
  --engine-version "{{user.engine_version}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --az-id "{{user.az_id}}" \
  --storage-type "{{user.storage_type}}" \
  --storage-size "{{user.storage_size}}" \
  --username "{{user.username}}" \
  --password "{{user.password}}"
```

#### Pre-flight: Configure jdc Config File for Sandbox

Before running any `jdc` command in sandboxed environments, ensure the config file exists:

```bash
# Setup jdc config in a writable location (sandbox-safe)
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[{{user.profile_name|default:"default"}}]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{user.region}}
endpoint = rds.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.rds.client.RdsClient import RdsClient
from jdcloud_sdk.services.rds.apis.CreateInstanceRequest import CreateInstanceRequest, CreateInstanceParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = RdsClient(credential)

instance_spec = {
    "instanceName": "{{user.instance_name}}",
    "instanceClass": "{{user.instance_class}}",
    "engine": "PostgreSQL",
    "engineVersion": "{{user.engine_version}}",
    "vpcId": "{{user.vpc_id}}",
    "subnetId": "{{user.subnet_id}}",
    "azId": "{{user.az_id}}",
    "storageType": "{{user.storage_type}}",
    "storageSize": "{{user.storage_size}}",
    "username": "{{user.username}}",
    "password": "{{user.password}}"
}

params = CreateInstanceParameters(regionId="{{user.region}}", instance=instance_spec)
req = CreateInstanceRequest(parameters=params)
resp = client.send(req)
instance_id = resp.result["instanceId"]
```

#### Post-execution Validation

1. Capture `{{output.instance_id}}` from `$.result.instanceId`.
2. Poll `describeInstance` until `status` == `running` or timeout.

```bash
# CLI poll loop (primary path) — --output json at TOP level
for i in $(seq 1 60); do
  STATUS=$(jdc --output json rds describe-instance \
    --region-id "{{user.region}}" \
    --instance-id "{{output.instance_id}}" | jq -r '.result.instance.status')
  [ "$STATUS" = "running" ] && break
  sleep 10
done
```

```python
# SDK poll loop (fallback, after 3 jdc failures)
from jdcloud_sdk.services.rds.apis.DescribeInstanceRequest import DescribeInstanceRequest, DescribeInstanceParameters

for _ in range(60):
    dparams = DescribeInstanceParameters(regionId="{{user.region}}", instanceId="{{output.instance_id}}")
    dreq = DescribeInstanceRequest(parameters=dparams)
    dresp = client.send(dreq)
    status = dresp.result["instance"]["status"]
    if status == "running":
        break
    if status in ["error", "deleted"]:
        raise RuntimeError(f"Instance creation failed: {status}")
    sleep(10)
```

3. On success, report instance ID, connection address, and port to user.
4. On terminal failure, go to **Failure Recovery**.

### Operation: Describe PostgreSQL Slow Logs

> 查询指定时段的 PostgreSQL 慢日志概要信息 — 仅支持 PostgreSQL 实例。

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.rds.client.RdsClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Instance exists | `describeInstance` | Instance found | HALT; verify instance ID |
| Instance engine | `describeInstance` | `PostgreSQL` | HALT; operation only supports PostgreSQL |
| Time window validation | Parse user input | Start time ≤ End time, duration ≤ 7 days | Suggest valid time range |

#### Input Variables

| Variable | Required | Format | Example | Description |
|----------|----------|--------|---------|-------------|
| `{{user.region}}` | yes | string | `cn-north-1` | Region ID |
| `{{user.instance_id}}` | yes | string | `rds-xxxx` | PostgreSQL instance ID |
| `{{user.start_time}}` | yes | `YYYY-MM-DD HH:mm:ss` | `2026-06-01 00:00:00` | 查询开始时间 |
| `{{user.end_time}}` | yes | `YYYY-MM-DD HH:mm:ss` | `2026-06-03 23:59:59` | 查询结束时间 |
| `{{user.db_name}}` | no | string | `mydb` | 数据库名过滤(废弃字段) |
| `{{user.page_number}}` | no | int | `1` | 页码,默认 1 |
| `{{user.page_size}}` | no | int | `10` | 每页条数,范围[10,100],默认 10 |
| `{{user.filters}}` | no | array | `[{"name":"account","operator":"eq","values":["postgres"]}]` | 过滤条件(账号/关键词) |
| `{{user.sorts}}` | no | array | `[{"name":"executionTimeSum","direction":"DESC"}]` | 排序字段 |

> **Time window constraint:** 开始时间到当前时间不能大于 **7 天**,开始时间不能大于结束时间。

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json rds describe-slow-logs \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}" \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --page-number {{user.page_number|default:1}} \
  --page-size {{user.page_size|default:10}}

# With optional filters (account or keyword)
jdc --output json rds describe-slow-logs \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}" \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --filters '[{"name":"account","operator":"eq","values":["app_user"]}]' \
  --page-number 1 \
  --page-size 50

# With sorting by execution time (descending)
jdc --output json rds describe-slow-logs \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}" \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --sorts '[{"name":"executionTimeSum","direction":"DESC"}]' \
  --page-number 1 \
  --page-size 20
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.rds.apis.DescribeSlowLogsRequest import DescribeSlowLogsRequest, DescribeSlowLogsParameters

params = DescribeSlowLogsParameters(
    regionId="{{user.region}}",
    instanceId="{{user.instance_id}}",
    startTime="{{user.start_time}}",
    endTime="{{user.end_time}}"
)

# Optional: set pagination
params.setPageNumber({{user.page_number|default:1}})
params.setPageSize({{user.page_size|default:10}})

# Optional: filter by account or SQL keyword
filters = [
    {
        "name": "account",
        "operator": "eq",  # or "in"
        "values": ["postgres"]
    },
    {
        "name": "keyword",
        "operator": "eq",  # SQL关键词模糊查询
        "values": ["SELECT * FROM users"]
    }
]
params.setFilters(filters)

# Optional: sort by execution metrics
sorts = [
    {
        "name": "executionTimeSum",  # or rowsExaminedSum, rowsSentSum, lockTimeSum, executionCount
        "direction": "DESC"  # or "ASC"
    }
]
params.setSorts(sorts)

req = DescribeSlowLogsRequest(parameters=params)
resp = client.send(req)

# Access slow log summaries
slow_logs = resp.result.get("slowLogs", [])
for log in slow_logs:
    print(f"SQL: {log.get('sql', 'N/A')[:100]}...")
    print(f"Execution count: {log.get('executionCount', 0)}")
    print(f"Avg execution time: {log.get('executionTimeAvg', 0)} ms")
    print(f"Max execution time: {log.get('executionTimeMax', 0)} ms")
    print(f"Total execution time: {log.get('executionTimeSum', 0)} ms")
    print(f"Rows examined sum: {log.get('rowsExaminedSum', 0)}")
    print("---")
```

#### Post-execution Validation

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Response structure | Parse JSON | `$.result.slowLogs` exists | Log error; suggest time window check |
| Data presence | Check array length | `len(slowLogs) >= 0` | Empty result is valid (no slow queries) |
| Pagination | Check `$.result.totalCount` | Matches expected total | Adjust pagination |

#### Output JSON Paths

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| Total count | `$.result.totalCount` | int | Total slow log entries matching criteria |
| Slow logs array | `$.result.slowLogs` | array | List of slow log summaries |
| SQL text | `$.result.slowLogs[*].sql` | string | SQL statement (truncated for display) |
| Execution count | `$.result.slowLogs[*].executionCount` | int | Number of times this SQL pattern executed |
| Execution time avg | `$.result.slowLogs[*].executionTimeAvg` | int | Average execution time (ms) |
| Execution time max | `$.result.slowLogs[*].executionTimeMax` | int | Maximum execution time (ms) |
| Execution time sum | `$.result.slowLogs[*].executionTimeSum` | int | Total execution time (ms) |
| Rows examined sum | `$.result.slowLogs[*].rowsExaminedSum` | int | Total rows examined |
| Rows sent sum | `$.result.slowLogs[*].rowsSentSum` | int | Total rows returned |
| Lock time sum | `$.result.slowLogs[*].lockTimeSum` | int | Total lock wait time (ms) |
| First occurrence | `$.result.slowLogs[*].startTime` | string | First occurrence timestamp |
| Last occurrence | `$.result.slowLogs[*].finishTime` | string | Last occurrence timestamp |

#### Present to User

**Summary format:**
```
PostgreSQL Slow Log Summary for {{user.instance_id}} ({{user.start_time}} ~ {{user.end_time}})

Total slow query patterns: {{output.total_count}}

Top slow queries (sorted by {{user.sort_field|default:"execution time"}}):
1. [{{output.slow_logs[0].executionCount}}x] {{output.slow_logs[0].sql[:80]}}...
   Avg: {{output.slow_logs[0].executionTimeAvg}}ms | Max: {{output.slow_logs[0].executionTimeMax}}ms | Total: {{output.slow_logs[0].executionTimeSum}}ms
   Rows examined: {{output.slow_logs[0].rowsExaminedSum}} | Lock time: {{output.slow_logs[0].lockTimeSum}}ms

2. [{{output.slow_logs[1].executionCount}}x] {{output.slow_logs[1].sql[:80]}}...
   ...
```

#### Common Use Cases

**Case 1: 查询最近 24 小时的慢日志**
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-xxx \
  --start-time "$(date -v-1d '+%Y-%m-%d %H:%M:%S')" \
  --end-time "$(date '+%Y-%m-%d %H:%M:%S')" \
  --page-size 100
```

**Case 2: 查找特定用户的慢查询**
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-xxx \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --filters '[{"name":"account","operator":"eq","values":["app_user"]}]'
```

**Case 3: 按执行时间排序,找出最慢的 SQL**
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-xxx \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --sorts '[{"name":"executionTimeMax","direction":"DESC"}]' \
  --page-size 20
```

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidTimeRange` / 400 | 0–1 | — | Fix time format (must be `YYYY-MM-DD HH:mm:ss`); ensure duration ≤ 7 days |
| `InstanceNotFound` / 404 | 0 | — | HALT; verify instance ID via `describe-instances` |
| `UnsupportedEngine` / 400 | 0 | — | HALT; operation only supports PostgreSQL, not MySQL or other engines |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: Describe PostgreSQL Slow Logs by Tags

> 按标签过滤 PostgreSQL 实例，并查询符合条件的实例在指定时段的慢日志。这是一个组合操作：先按标签查找实例，再并行查询每个实例的慢日志。

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.rds.client.RdsClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Tag filters | Validate user input | At least one tag filter provided | HALT; require at least one tag condition |
| Time window validation | Parse user input | Start time ≤ End time, duration ≤ 7 days | Suggest valid time range |

#### Input Variables

| Variable | Required | Format | Example | Description |
|----------|----------|--------|---------|-------------|
| `{{user.region}}` | yes | string | `cn-north-1` | Region ID |
| `{{user.tag_filters}}` | yes | array | `[{"name":"tag:环境","operator":"eq","values":["生产"]},{"name":"tag:客户","operator":"eq","values":["xxx"]}]` | 实例标签过滤条件 |
| `{{user.start_time}}` | yes | `YYYY-MM-DD HH:mm:ss` | `2026-06-01 00:00:00` | 查询开始时间 |
| `{{user.end_time}}` | yes | `YYYY-MM-DD HH:mm:ss` | `2026-06-03 23:59:59` | 查询结束时间 |
| `{{user.page_number}}` | no | int | `1` | 页码,默认 1 |
| `{{user.page_size}}` | no | int | `10` | 每页条数,范围[10,100],默认 10 |
| `{{user.slowlog_filters}}` | no | array | `[{"name":"account","operator":"eq","values":["postgres"]}]` | 慢日志过滤条件(账号/关键词) |
| `{{user.sorts}}` | no | array | `[{"name":"executionTimeSum","direction":"DESC"}]` | 排序字段 |
| `{{user.max_instances}}` | no | int | `10` | 最大查询实例数(防止过多),默认 10 |

> **Time window constraint:** 开始时间到当前时间不能大于 **7 天**,开始时间不能大于结束时间。

> **Tag filter format:** `{"name": "tag:<tag_key>", "operator": "eq|in", "values": ["value1", "value2"]}`

#### Execution Flow

这是一个**两阶段组合操作**：

**阶段 1: 按标签查找实例** → **阶段 2: 并行查询慢日志** → **阶段 3: 聚合结果**

#### Phase 1: 按标签查找 PostgreSQL 实例

##### Execution — CLI (`jdc`) [Primary Path]

```bash
# 按标签过滤查找 PostgreSQL 实例
jdc --output json rds describe-instances \
  --region-id "{{user.region}}" \
  --filters '{{user.tag_filters}}' \
  --page-number 1 \
  --page-size 100

# 示例: 环境=生产, 客户=xxx
jdc --output json rds describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"tag:环境","operator":"eq","values":["生产"]},{"name":"tag:客户","operator":"eq","values":["xxx"]}]' \
  --page-number 1 \
  --page-size 100
```

##### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.rds.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

params = DescribeInstancesParameters(regionId="{{user.region}}")

# 设置标签过滤器
filters = [
    {"name": "tag:环境", "operator": "eq", "values": ["生产"]},
    {"name": "tag:客户", "operator": "eq", "values": ["xxx"]}
]
params.setFilters(filters)
params.setPageNumber(1)
params.setPageSize(100)

req = DescribeInstancesRequest(parameters=params)
resp = client.send(req)

# 提取 PostgreSQL 实例列表
instances = [
    inst for inst in resp.result.get("instances", [])
    if inst.get("engine") == "PostgreSQL"
]
instance_ids = [inst["instanceId"] for inst in instances]

print(f"Found {len(instance_ids)} PostgreSQL instances matching tags: {instance_ids}")
```

##### Phase 1 Output JSON Paths

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| Total count | `$.result.totalCount` | int | 符合条件的实例总数 |
| Instances array | `$.result.instances` | array | 实例列表 |
| Instance ID | `$.result.instances[*].instanceId` | string | 实例ID |
| Engine | `$.result.instances[*].engine` | string | 数据库引擎(PostgreSQL) |
| Instance Name | `$.result.instances[*].instanceName` | string | 实例名称 |
| Tags | `$.result.instances[*].tags` | array | 实例标签列表 |

#### Phase 2: 并行查询每个实例的慢日志

> **Safety guard:** 如果匹配的实例数 > `{{user.max_instances}}`，必须向用户确认是否继续。

##### Execution — CLI (`jdc`) [Primary Path]

```bash
# 对每个实例并行执行(使用 subshell/background)
for instance_id in {{output.instance_ids}}; do
  jdc --output json rds describe-slow-logs \
    --region-id "{{user.region}}" \
    --instance-id "$instance_id" \
    --start-time "{{user.start_time}}" \
    --end-time "{{user.end_time}}" \
    --filters '{{user.slowlog_filters}}' \
    --sorts '{{user.sorts}}' \
    --page-number {{user.page_number|default:1}} \
    --page-size {{user.page_size|default:10}} > "slowlog_${instance_id}.json" &
done
wait

# 合并结果
cat slowlog_*.json | jq -s '{aggregated: map(.result.slowLogs[]) | sort_by(.executionTimeSum) | reverse}' > aggregated_slowlogs.json
```

##### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.rds.apis.DescribeSlowLogsRequest import DescribeSlowLogsRequest, DescribeSlowLogsParameters
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

def query_slow_logs_for_instance(instance_id, region, start_time, end_time, 
                                  filters=None, sorts=None, page_number=1, page_size=10):
    """Query slow logs for a single instance"""
    params = DescribeSlowLogsParameters(
        regionId=region,
        instanceId=instance_id,
        startTime=start_time,
        endTime=end_time
    )
    params.setPageNumber(page_number)
    params.setPageSize(page_size)
    
    if filters:
        params.setFilters(filters)
    if sorts:
        params.setSorts(sorts)
    
    req = DescribeSlowLogsRequest(parameters=params)
    resp = client.send(req)
    
    return {
        "instance_id": instance_id,
        "total_count": resp.result.get("totalCount", 0),
        "slow_logs": resp.result.get("slowLogs", [])
    }

# 并行查询所有实例的慢日志
results = []
with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_instance = {
        executor.submit(
            query_slow_logs_for_instance,
            instance_id,
            "{{user.region}}",
            "{{user.start_time}}",
            "{{user.end_time}}",
            {{user.slowlog_filters}},
            {{user.sorts}},
            {{user.page_number|default:1}},
            {{user.page_size|default:10}}
        ): instance_id for instance_id in instance_ids
    }
    
    for future in as_completed(future_to_instance):
        instance_id = future_to_instance[future]
        try:
            result = future.result()
            results.append(result)
        except Exception as e:
            results.append({
                "instance_id": instance_id,
                "error": str(e),
                "total_count": 0,
                "slow_logs": []
            })

# 聚合结果
aggregated = {
    "query_info": {
        "region": "{{user.region}}",
        "tag_filters": {{user.tag_filters}},
        "time_range": {"start": "{{user.start_time}}", "end": "{{user.end_time}}"},
        "instances_queried": len(instance_ids),
        "instances_with_slowlogs": sum(1 for r in results if r["total_count"] > 0)
    },
    "results": results,
    "aggregated_slowlogs": []
}

# 跨实例聚合慢日志(按 SQL 模式合并)
all_slowlogs = []
for r in results:
    for log in r["slow_logs"]:
        log["instance_id"] = r["instance_id"]  # 添加实例标识
        all_slowlogs.append(log)

# 按执行时间总和排序
aggregated["aggregated_slowlogs"] = sorted(
    all_slowlogs, 
    key=lambda x: x.get("executionTimeSum", 0), 
    reverse=True
)[:{{user.page_size|default:10}} * len(instance_ids)]

print(json.dumps(aggregated, indent=2, ensure_ascii=False))
```

#### Phase 3: Post-execution Validation & Result Presentation

```python
# 验证每个实例的查询结果
for result in results:
    if "error" in result:
        print(f"⚠️ Instance {result['instance_id']}: Query failed - {result['error']}")
    else:
        print(f"✅ Instance {result['instance_id']}: {result['total_count']} slow query patterns")

# 汇总统计
total_patterns = sum(r["total_count"] for r in results)
total_instances_with_data = sum(1 for r in results if r["total_count"] > 0)

print(f"\n📊 Summary:")
print(f"   Total instances queried: {len(instance_ids)}")
print(f"   Instances with slow queries: {total_instances_with_data}")
print(f"   Total unique slow query patterns: {total_patterns}")
```

#### Output JSON Structure

```json
{
  "query_info": {
    "region": "cn-north-1",
    "tag_filters": [
      {"name": "tag:环境", "operator": "eq", "values": ["生产"]},
      {"name": "tag:客户", "operator": "eq", "values": ["xxx"]}
    ],
    "time_range": {
      "start": "2026-06-01 00:00:00",
      "end": "2026-06-03 23:59:59"
    },
    "instances_queried": 3,
    "instances_with_slowlogs": 2
  },
  "results": [
    {
      "instance_id": "rds-pg-001",
      "total_count": 15,
      "slow_logs": [
        {
          "sql": "SELECT * FROM orders WHERE created_at > $1",
          "executionCount": 120,
          "executionTimeAvg": 1500,
          "executionTimeMax": 3500,
          "executionTimeSum": 180000,
          "rowsExaminedSum": 500000,
          "instance_id": "rds-pg-001"
        }
      ]
    },
    {
      "instance_id": "rds-pg-002",
      "total_count": 0,
      "slow_logs": []
    }
  ],
  "aggregated_slowlogs": [
    {
      "sql": "SELECT * FROM orders WHERE created_at > $1",
      "executionCount": 120,
      "executionTimeSum": 180000,
      "rowsExaminedSum": 500000,
      "instance_id": "rds-pg-001"
    }
  ],
  "top_queries_by_instance": {
    "rds-pg-001": [
      {
        "sql": "SELECT * FROM orders...",
        "executionTimeSum": 180000
      }
    ]
  }
}
```

#### Present to User

```
PostgreSQL Slow Logs by Tags Summary
====================================
Tags: 环境=生产, 客户=xxx
Time: 2026-06-01 00:00:00 ~ 2026-06-03 23:59:59
Region: cn-north-1

Instances Queried: 3
Instances with Slow Queries: 2

─────────────────────────────────────
Instance: rds-pg-001 (15 patterns)
─────────────────────────────────────
1. [120x] SELECT * FROM orders WHERE created_at > $1
   Avg: 1500ms | Max: 3500ms | Total: 180000ms
   Rows examined: 500000 | Lock time: 120ms

2. [85x] UPDATE inventory SET stock = stock - $1 WHERE sku = $2
   Avg: 800ms | Max: 2000ms | Total: 68000ms
   Rows examined: 85000 | Lock time: 450ms

─────────────────────────────────────
Instance: rds-pg-002 (0 patterns)
─────────────────────────────────────
No slow queries found.

─────────────────────────────────────
Instance: rds-pg-003 (8 patterns)
─────────────────────────────────────
1. [45x] DELETE FROM logs WHERE created_at < $1
   Avg: 2200ms | Max: 5000ms | Total: 99000ms
   Rows examined: 2000000 | Lock time: 800ms

🔥 Top 3 Slowest Queries Across All Instances:
1. [rds-pg-001] SELECT * FROM orders... (180000ms total)
2. [rds-pg-003] DELETE FROM logs... (99000ms total)
3. [rds-pg-001] UPDATE inventory... (68000ms total)
```

#### Common Use Cases

**Case 1: 查询生产环境所有客户的慢日志**
```bash
# 步骤1: 查找标签为 环境=生产 的所有 PostgreSQL 实例
INSTANCES=$(jdc --output json rds describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"tag:环境","operator":"eq","values":["生产"]}]' \
  | jq -r '.result.instances[] | select(.engine == "PostgreSQL") | .instanceId')

# 步骤2: 对每个实例查询最近24小时慢日志
for id in $INSTANCES; do
  echo "=== Instance: $id ==="
  jdc --output json rds describe-slow-logs \
    --region-id cn-north-1 \
    --instance-id "$id" \
    --start-time "$(date -d '1 day ago' '+%Y-%m-%d %H:%M:%S')" \
    --end-time "$(date '+%Y-%m-%d %H:%M:%S')" \
    --sorts '[{"name":"executionTimeSum","direction":"DESC"}]' \
    --page-size 10
done
```

**Case 2: Python SDK 完整示例**
```python
from jdcloud_sdk.services.rds.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
from jdcloud_sdk.services.rds.apis.DescribeSlowLogsRequest import DescribeSlowLogsRequest, DescribeSlowLogsParameters
from concurrent.futures import ThreadPoolExecutor

def query_slowlogs_by_tags(client, region_id, tag_filters, start_time, end_time, 
                           slowlog_filters=None, sorts=None, max_instances=10):
    """
    按标签查询 PostgreSQL 实例慢日志
    
    Args:
        client: RdsClient instance
        region_id: Region ID
        tag_filters: List of tag filter dicts, e.g. [{"name": "tag:环境", "values": ["生产"]}]
        start_time: Slow log start time (YYYY-MM-DD HH:mm:ss)
        end_time: Slow log end time (YYYY-MM-DD HH:mm:ss)
        slowlog_filters: Optional slow log filters (account/keyword)
        sorts: Optional sort conditions
        max_instances: Max instances to query (safety guard)
    """
    # Phase 1: Find instances by tags
    params = DescribeInstancesParameters(regionId=region_id)
    params.setFilters(tag_filters)
    params.setPageNumber(1)
    params.setPageSize(100)
    
    req = DescribeInstancesRequest(parameters=params)
    resp = client.send(req)
    
    # Filter PostgreSQL instances only
    pg_instances = [
        inst for inst in resp.result.get("instances", [])
        if inst.get("engine") == "PostgreSQL"
    ]
    
    if len(pg_instances) > max_instances:
        raise ValueError(f"Found {len(pg_instances)} instances, exceeds max {max_instances}. "
                        f"Please refine tag filters or increase max_instances.")
    
    instance_ids = [inst["instanceId"] for inst in pg_instances]
    print(f"Found {len(instance_ids)} PostgreSQL instances: {instance_ids}")
    
    # Phase 2: Parallel query slow logs
    def query_one(instance_id):
        try:
            p = DescribeSlowLogsParameters(
                regionId=region_id,
                instanceId=instance_id,
                startTime=start_time,
                endTime=end_time
            )
            if slowlog_filters:
                p.setFilters(slowlog_filters)
            if sorts:
                p.setSorts(sorts)
            p.setPageNumber(1)
            p.setPageSize(50)
            
            r = DescribeSlowLogsRequest(parameters=p)
            res = client.send(r)
            
            return {
                "instance_id": instance_id,
                "instance_name": next((i["instanceName"] for i in pg_instances 
                                        if i["instanceId"] == instance_id), ""),
                "total_count": res.result.get("totalCount", 0),
                "slow_logs": res.result.get("slowLogs", [])
            }
        except Exception as e:
            return {
                "instance_id": instance_id,
                "error": str(e),
                "total_count": 0,
                "slow_logs": []
            }
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(query_one, instance_ids))
    
    # Aggregate
    all_logs = []
    for r in results:
        for log in r.get("slow_logs", []):
            log["instance_id"] = r["instance_id"]
            log["instance_name"] = r.get("instance_name", "")
            all_logs.append(log)
    
    # Sort by total execution time
    all_logs.sort(key=lambda x: x.get("executionTimeSum", 0), reverse=True)
    
    return {
        "query_info": {
            "region": region_id,
            "tag_filters": tag_filters,
            "time_range": {"start": start_time, "end": end_time},
            "instances_queried": len(instance_ids),
            "instances_with_slowlogs": sum(1 for r in results if r["total_count"] > 0)
        },
        "results": results,
        "aggregated_slowlogs": all_logs[:50],  # Top 50 across all instances
        "top_queries_by_instance": {
            r["instance_id"]: r["slow_logs"][:5] for r in results  # Top 5 per instance
        }
    }

# Usage
result = query_slowlogs_by_tags(
    client=client,
    region_id="cn-north-1",
    tag_filters=[
        {"name": "tag:环境", "operator": "eq", "values": ["生产"]},
        {"name": "tag:客户", "operator": "eq", "values": ["xxx"]}
    ],
    start_time="2026-06-01 00:00:00",
    end_time="2026-06-03 23:59:59",
    slowlog_filters=[{"name": "account", "operator": "eq", "values": ["app_user"]}],
    sorts=[{"name": "executionTimeSum", "direction": "DESC"}],
    max_instances=10
)

# Print summary
print(f"Instances with slow queries: {result['query_info']['instances_with_slowlogs']}")
for log in result['aggregated_slowlogs'][:10]:
    print(f"[{log['instance_id']}] {log['sql'][:60]}... "
          f"(Total: {log['executionTimeSum']}ms, Count: {log['executionCount']})")
```

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| **Phase 1: 按标签查找实例** ||||
| `InvalidFilter` / 400 | 0–1 | — | 修正标签过滤器格式 |
| No instances found | 0 | — | HALT; 提示用户检查标签值 |
| Too many instances (> max_instances) | 0 | — | 提示用户细化标签或增加 max_instances |
| **Phase 2: 查询慢日志** ||||
| `InvalidTimeRange` / 400 | 0–1 | — | 修正时间格式；确保 ≤ 7 天 |
| `InstanceNotFound` / 404 | 0 | — | 跳过该实例；记录警告 |
| `UnsupportedEngine` / 400 | 0 | — | 跳过该实例（非 PostgreSQL） |
| Throttling / 429 | 3 | exponential | 指数退避后重试 |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | 重试；持续失败则记录错误但继续其他实例 |

#### Safety Considerations

1. **实例数量限制:** 默认 `max_instances=10`，防止意外查询过多实例
2. **并行度控制:** 使用 ThreadPoolExecutor(max_workers=5) 控制并发
3. **部分失败处理:** 单个实例查询失败不影响其他实例
4. **数据聚合上限:** 跨实例聚合结果限制返回数量，避免过大响应

### Operation: Analyze PostgreSQL Slow Queries（分析定位与优化建议）

> 基于慢日志查询结果（`describeSlowLogs`），自动分析 PostgreSQL 慢查询根因并给出优化建议。
> 这是一个**分析型组合操作**：先调用 `describeSlowLogs` 获取原始数据，再基于指标模式匹配诊断规则。

#### Input Variables

本操作直接复用 `describeSlowLogs` 的查询参数，在查询结果上叠加分析层：

| 变量 | 类型 | 说明 |
|------|------|------|
| `{{user.instance_id}}` | string | PostgreSQL 实例 ID |
| `{{user.start_time}}` | string | 开始时间 (`YYYY-MM-DD HH:mm:ss`) |
| `{{user.end_time}}` | string | 结束时间 (`YYYY-MM-DD HH:mm:ss`) |
| `{{user.analysis_depth}}` | string | 分析深度: `basic`(默认,汇总) / `deep`(逐条分析+建议) |
| `{{user.focus}}` | string | (可选) 关注重点: `all`(默认) / `most_time`(最耗时) / `most_freq`(最频繁) / `seq_scan`(顺序扫描) / `lock`(锁等待) / `bloat`(表膨胀) |

#### Analysis Pipeline（三阶段分析）

```
原始慢日志数据
    │
    ▼
[Phase 1] 严重度分级 ──► 将每条慢查询标记为 Critical / Major / Minor
    │
    ▼
[Phase 2] 根因分析 ──► 基于 rowsExamined/rowsSent/lockTime 等指标推断 PG 特有根因
    │
    ▼
[Phase 3] 优化建议 ──► 根据根因类型生成 PG 特定的优化方案
    │
    ▼
输出：结构化的分析报告 + 可执行建议
```

---

#### Phase 1：严重度分级

| 严重度 | 判定条件 | 颜色标记 | Agent 行动 |
|--------|----------|----------|------------|
| 🔴 **Critical** | `executionTimeAvg ≥ 5000ms` 或 `executionTimeSum ≥ 300000ms` 或 `executionCount ≥ 10000` | 红色 | 立即告警，建议优先处理 |
| 🟡 **Major** | `executionTimeAvg ≥ 1000ms` 或 `rowsExaminedSum ≥ 500000` 或 `executionCount ≥ 1000` | 黄色 | 标记为需要优化 |
| 🔵 **Minor** | 其他慢查询 | 蓝色 | 记录在案，作为潜在优化目标 |

**Python 实现示例：**

```python
def classify_slow_query(log: dict) -> str:
    """Classify slow query by severity."""
    avg_time = log.get("executionTimeAvg", 0)
    total_time = log.get("executionTimeSum", 0)
    count = log.get("executionCount", 0)
    rows_examined = log.get("rowsExaminedSum", 0)

    if avg_time >= 5000 or total_time >= 300_000 or count >= 10000:
        return "🔴 Critical"
    if avg_time >= 1000 or rows_examined >= 500_000 or count >= 1000:
        return "🟡 Major"
    return "🔵 Minor"
```

---

#### Phase 2：根因分析（PostgreSQL 专用规则）

PostgreSQL 的慢查询根因与 MySQL 有显著区别。以下规则针对 PG 的执行引擎、查询规划器（planner）和 MVCC 机制设计：

| 根因类型 | 判定规则 | 说明 |
|---------|----------|------|
| 🏷️ **Missing Index（缺少索引）** | `rowsExaminedSum > rowsSentSum × 100` 且 `executionTimeAvg > 500` | 扫描大量行但返回少量行，典型的 seq scan → index scan 转换机会 |
| 📊 **Sequential Scan（顺序扫描）** | `rowsExaminedSum > 100000` 且 SQL 无过滤条件或条件列无索引 | PG 规划器选择了 Seq Scan 而非 Index Scan |
| 🔒 **Lock Contention（锁竞争）** | `lockTimeSum > executionTimeSum × 0.3` 或 `lockTimeSum > 60000` | PG 的 RowExclusiveLock 或 AccessExclusiveLock 导致阻塞 |
| 🧹 **Autovacuum / Bloat（表膨胀）** | `executionTimeAvg > 2000` 且 `rowsExaminedSum > 500000` 且 SQL 含 `UPDATE`/`DELETE` | MVCC 死元组未及时回收导致表膨胀，扫描更多页面 |
| 🔗 **Inefficient Nested Loop（低效嵌套循环）** | `rowsExaminedSum > 300000` 且 SQL 含多个 `JOIN` 且 `rowsSentSum < 1000` | PG 规划器选择了 Nested Loop，但内表未走索引扫描 |
| 📦 **Large Result Set（大结果集）** | `rowsSentSum > 10000` 且 `executionTimeAvg > 2000` | 返回过多行导致网络/内存开销 |
| 💾 **Work Mem / Temp File（临时文件溢出）** | `executionTimeAvg > 3000` 且 SQL 含 `ORDER BY`/`DISTINCT`/`GROUP BY`/`JOIN` 且 `rowsExaminedSum > 100000` | `work_mem` 不足导致排序/哈希操作溢出到磁盘临时文件 |
| ⏰ **Frequent Small Query（频繁小查询/N+1）** | `executionCount > 1000` 且 `executionTimeAvg < 500` | 频繁执行但单次不慢，PG 中常见于 ORM 生成的 N+1 查询 |
| ⚙️ **Parameter Tuning（参数配置不当）** | `executionTimeAvg > 3000` 且 `rowsExaminedSum > 200000` 且 SQL 模式为简单扫描 | `shared_buffers`/`effective_cache_size`/`work_mem` 可能低于建议值 |

**Python 实现示例：**

```python
import re

def analyze_root_cause_pg(log: dict) -> list:
    """Analyze root cause(s) of a PostgreSQL slow query."""
    findings = []
    sql = log.get("sql", "").lower()
    avg_time = log.get("executionTimeAvg", 0)
    rows_examined = log.get("rowsExaminedSum", 0)
    rows_sent = log.get("rowsSentSum", 0)
    lock_time = log.get("lockTimeSum", 0)
    total_time = log.get("executionTimeSum", 0)
    count = log.get("executionCount", 0)

    # 1. Missing Index: scanned >> sent
    if rows_examined > rows_sent * 100 and rows_examined > 10000:
        findings.append({
            "type": "missing_index",
            "label": "🏷️ Missing Index",
            "confidence": "high" if rows_examined > rows_sent * 1000 else "medium",
            "detail": f"Scanned {rows_examined} rows but only returned {rows_sent} "
                      f"(ratio {rows_examined // max(rows_sent, 1)}:1)"
        })

    # 2. Lock Contention
    if total_time > 0 and lock_time > total_time * 0.3:
        findings.append({
            "type": "lock_contention",
            "label": "🔒 Lock Contention",
            "confidence": "high",
            "detail": f"Lock wait time {lock_time}ms is {lock_time * 100 // total_time}% of total"
        })

    # 3. Sequential Scan (no WHERE clause or non-indexed filter)
    if "where" not in sql and rows_examined > 50000:
        findings.append({
            "type": "sequential_scan",
            "label": "📊 Sequential Scan",
            "confidence": "high",
            "detail": "Query has no WHERE clause. PG planner chose Seq Scan over Index Scan."
        })

    # 4. Autovacuum / Bloat (UPDATE/DELETE-heavy with high scan)
    if ("update" in sql or "delete" in sql) and rows_examined > 500000 and avg_time > 2000:
        findings.append({
            "type": "bloat",
            "label": "🧹 Autovacuum / Table Bloat",
            "confidence": "medium",
            "detail": "High row scan count on UPDATE/DELETE. Dead tuples may cause table bloat, "
                      "increasing scan pages. Check pg_stat_user_tables.n_dead_tup."
        })

    # 5. Inefficient Nested Loop
    join_count = len(re.findall(r'\bjoin\b', sql))
    if join_count >= 2 and rows_examined > 200000 and rows_sent < 1000:
        findings.append({
            "type": "inefficient_join",
            "label": "🔗 Inefficient Nested Loop",
            "confidence": "medium",
            "detail": f"Query joins {join_count} tables, examined {rows_examined} rows. "
                      "PG planner chose Nested Loop but inner table may lack index."
        })

    # 6. Large Result Set
    if rows_sent > 10000 and avg_time > 2000:
        findings.append({
            "type": "large_result_set",
            "label": "📦 Large Result Set",
            "confidence": "medium",
            "detail": f"Returned {rows_sent} rows. Consider LIMIT/OFFSET pagination."
        })

    # 7. Work Mem / Temp File (sort/hash/group without index)
    has_sort = "order by" in sql or "distinct" in sql
    has_agg = "group by" in sql
    if (has_sort or has_agg) and rows_examined > 100000 and avg_time > 2000:
        findings.append({
            "type": "work_mem_temp",
            "label": "💾 Work Mem / Temp File",
            "confidence": "medium",
            "detail": "ORDER BY/DISTINCT/GROUP BY without index — PG spill to disk if work_mem insufficient."
        })

    # 8. Frequent Small Query (N+1 pattern)
    if count > 1000 and avg_time < 500:
        findings.append({
            "type": "frequent_small_query",
            "label": "⏰ Frequent Small Query (N+1)",
            "confidence": "medium",
            "detail": f"Executed {count} times, avg {avg_time}ms each — typical N+1 from ORM layer."
        })

    return findings
```

---

#### Phase 3：优化建议生成（PostgreSQL 专用）

| 根因类型 | 优化建议 | PostgreSQL 特有说明 |
|---------|---------|-------------------|
| 🏷️ Missing Index | `CREATE INDEX CONCURRENTLY idx_<table>_<cols> ON <table>(<cols>)` | 生产环境使用 `CONCURRENTLY` 避免锁表 |
| 📊 Sequential Scan | `CREATE INDEX ON <table>(<cols>)` 或使用 `pg_hint_plan` 强制索引 | 用 `EXPLAIN (ANALYZE, BUFFERS)` 验证 |
| 🔒 Lock Contention | 缩短事务；使用 `SET lock_timeout = '5s'`；避免 DDL 长事务 | PG 无 `NOWAIT`/`SKIP LOCKED` 可用于高并发 |
| 🧹 Autovacuum / Bloat | 调大 `autovacuum_vacuum_scale_factor`；执行 `VACUUM VERBOSE` 或 `pg_repack` | 检查 `pg_stat_user_tables.n_dead_tup` / `n_live_tup` 比例 |
| 🔗 Inefficient Nested Loop | 添加 JOIN 列索引；调大 `random_page_cost` 鼓励 Hash Join | `SET enable_nestloop = off` 可临时禁用（不推荐长期） |
| 📦 Large Result Set | 添加 `LIMIT` 分页；使用游标（`DECLARE CURSOR`）处理大数据集 | PG 游标支持 `SCROLL` 和 `WITH HOLD` |
| 💾 Work Mem / Temp File | 增加 `work_mem`（会话级: `SET work_mem = '64MB'`） | 监控 `pg_stat_database.temp_files` / `temp_bytes` |
| ⏰ Frequent Small Query | 使用批量查询 `WHERE id = ANY($1)` 替代 N+1；应用层加缓存 | Rails/Sequelize ORM 常见 N+1，使用 `includes`/`preload` |
| ⚙️ Parameter Tuning | 检查 `shared_buffers`(推荐 25% RAM)、`effective_cache_size`(75% RAM)、`work_mem`、`maintenance_work_mem` | 用 `pg_settings` 视图和 `EXPLAIN (BUFFERS)` 综合判断 |

**Python 实现示例：**

```python
def generate_optimization_advice_pg(findings: list, log: dict) -> list:
    """Generate actionable optimization advice based on PG-specific root causes."""
    sql = log.get("sql", "")
    advice_list = []

    for finding in findings:
        advice = {"type": finding["type"], "priority": finding.get("confidence", "medium")}

        if finding["type"] == "missing_index":
            tables = re.findall(r'from\s+(\w+)', sql, re.IGNORECASE)
            where_cols = re.findall(r'where\s+(\w+(?:\.\w+)?)\s*[=<>]', sql, re.IGNORECASE)
            table = tables[0] if tables else "<table>"
            cols = [c.split(".")[-1] for c in where_cols[:3]]
            idx_name = f"idx_{table}_{'_'.join(cols)}" if cols else f"idx_{table}_<columns>"
            idx_cols = ", ".join(cols) if cols else "<columns>"

            advice["action"] = f"Add index: CREATE INDEX CONCURRENTLY {idx_name} ON {table}({idx_cols})"
            advice["rationale"] = (
                f"Query examines {log.get('rowsExaminedSum', 0)} rows but only returns "
                f"{log.get('rowsSentSum', 0)}. PG planner will switch from Seq Scan to Index Scan."
            )

        elif finding["type"] == "sequential_scan":
            advice["action"] = (
                "Add WHERE clause on indexed column, or CREATE INDEX CONCURRENTLY "
                "for the filter column(s)"
            )
            advice["rationale"] = (
                "PG planner chose Seq Scan due to missing index. "
                "Use EXPLAIN (ANALYZE, BUFFERS) to confirm."
            )

        elif finding["type"] == "lock_contention":
            advice["action"] = (
                "1. Shorten transaction boundaries\n"
                "2. Set lock_timeout = '5s' to prevent indefinite waiting\n"
                "3. Use NOWAIT or SKIP LOCKED for high-concurrency queues\n"
                "4. Avoid long-running DDL (use pg_repack for online DDL)"
            )
            advice["rationale"] = (
                f"Lock wait time ({log.get('lockTimeSum', 0)}ms) dominates. "
                "PG locks are heavy — even RowExclusiveLock blocks concurrent DDL."
            )

        elif finding["type"] == "bloat":
            advice["action"] = (
                "1. Check autovacuum: SHOW autovacuum_vacuum_scale_factor;\n"
                "2. Monitor bloat: SELECT n_dead_tup, n_live_tup FROM pg_stat_user_tables;\n"
                "3. Tune: ALTER TABLE <t> SET (autovacuum_vacuum_scale_factor = 0.01);\n"
                "4. If severe bloat: consider pg_repack or VACUUM FULL (table-level lock)"
            )
            advice["rationale"] = (
                "Dead tuple accumulation from MVCC. PG needs VACUUM to reclaim space. "
                "Check n_dead_tup / n_live_tup ratio in pg_stat_user_tables."
            )

        elif finding["type"] == "inefficient_join":
            advice["action"] = (
                "1. Add indexes on JOIN columns\n"
                "2. Increase random_page_cost to encourage Hash Join over Nested Loop\n"
                "3. ANALYZE to update table statistics\n"
                "4. Consider SET enable_nestloop = off (session-level, temporary)"
            )
            advice["rationale"] = (
                f"PG planner chose Nested Loop scanning {log.get('rowsExaminedSum', 0)} rows. "
                "Missing statistics or outdated ANALYZE may cause bad plan choices."
            )

        elif finding["type"] == "large_result_set":
            advice["action"] = (
                "Add LIMIT clause, or use server-side cursors (DECLARE CURSOR) "
                "for large data processing"
            )
            advice["rationale"] = (
                f"Query returns {log.get('rowsSentSum', 0)} rows. "
                "In PG, large result sets also consume shared_buffers."
            )

        elif finding["type"] == "work_mem_temp":
            advice["action"] = (
                "Increase work_mem: SET work_mem = '64MB' (session) or "
                "ALTER SYSTEM SET work_mem = '64MB';\n"
                "Or add index on ORDER BY / GROUP BY columns"
            )
            advice["rationale"] = (
                "Temp file spill detected. Check pg_stat_database.temp_bytes. "
                "Each sort/hash operation can use up to work_mem before spilling to disk."
            )

        elif finding["type"] == "frequent_small_query":
            advice["action"] = (
                "1. Use batch query: WHERE id = ANY($1)\n"
                "2. Use JOIN/EAGER loading to eliminate N+1\n"
                "3. Add pgpool-II / PgBouncer for connection pooling\n"
                "4. Use prepared statements to avoid repeated planning"
            )
            advice["rationale"] = (
                f"Executed {log.get('executionCount', 0)} times. "
                "PG parsing/planning overhead adds up — use prepared statements."
            )

        advice_list.append(advice)

    return advice_list
```

---

#### End-to-End Analysis Report（完整分析报告模板）

```json
{
  "analysis_summary": {
    "instance_id": "rds-pg-xxx",
    "engine": "PostgreSQL",
    "time_range": {"start": "2026-06-01 00:00:00", "end": "2026-06-03 23:59:59"},
    "total_patterns": 25,
    "by_severity": {
      "🔴 Critical": 3,
      "🟡 Major": 8,
      "🔵 Minor": 14
    },
    "by_root_cause": {
      "missing_index": {"count": 5, "total_time_ms": 450000},
      "sequential_scan": {"count": 3, "total_time_ms": 280000},
      "lock_contention": {"count": 2, "total_time_ms": 120000},
      "bloat": {"count": 2, "total_time_ms": 200000},
      "inefficient_join": {"count": 1, "total_time_ms": 95000},
      "work_mem_temp": {"count": 2, "total_time_ms": 180000},
      "large_result_set": {"count": 2, "total_time_ms": 150000},
      "frequent_small_query": {"count": 1, "total_time_ms": 180000}
    },
    "top_issues": [
      {
        "sql_truncated": "SELECT * FROM orders WHERE ...",
        "severity": "🔴 Critical",
        "findings": ["🏷️ Missing Index", "📦 Large Result Set"],
        "recommended_action": "CREATE INDEX CONCURRENTLY idx_orders_created ON orders(created_at)",
        "estimated_impact": "Reduce execution time by ~80% (Seq Scan → Index Scan)"
      }
    ],
    "quick_wins": [
      {
        "sql_truncated": "UPDATE inventory SET stock = ... WHERE sku = ?",
        "severity": "🟡 Major",
        "finding": "🔒 Lock Contention",
        "action": "Shorten transaction, add sku index, check work_mem"
      }
    ]
  }
}
```

#### Present to User（中文展示模板）

```
📊 PostgreSQL 慢查询分析报告
══════════════════════════
实例: rds-pg-xxx | 引擎: PostgreSQL | 时间范围: 2026-06-01 ~ 2026-06-03
───────────────────────────────────────

📈 概览
────────────────
总慢查询模式数: 25

按严重度分布:
  🔴 Critical: 3 条
  🟡 Major: 8 条
  🔵 Minor: 14 条

🔴 严重问题 (Critical) — 建议立即处理
────────────────────────────────────
1. SELECT * FROM orders WHERE created_at > ?
   执行次数: 120 | 平均耗时: 1500ms | 总耗时: 180000ms
   扫描行数: 500000 | 返回行数: 50

   分析结果:
   ├─ 🏷️ Missing Index: 扫描500000行，返回50行(10000:1)
   │   PG 规划器选择了 Seq Scan，应当使用 Index Scan
   └─ 📦 Large Result Set: 返回全部行，缺少 LIMIT

   优化建议:
   ├─ 🎯 添加索引 (CONCURRENTLY 避免锁表):
   │   CREATE INDEX CONCURRENTLY idx_orders_created ON orders(created_at);
   │   预期效果: Seq Scan → Index Scan，预计降至 ~50ms
   └─ 🎯 添加 LIMIT:
       SELECT * FROM orders WHERE created_at > ? LIMIT 100;

🟡 重点关注 (Major) — 建议近期优化
─────────────────────────────────────
2. UPDATE inventory SET stock = stock - ? WHERE sku = ?
   执行次数: 85 | 平均耗时: 800ms | 总耗时: 68000ms

   分析结果:
   ├─ 🔒 Lock Contention: 锁等待时间 22000ms，占 32%
   └─ 🧹 Autovacuum / Bloat: UPDATE 频繁，死元组可能影响性能

   优化建议:
   ├─ 🎯 检查 autovacuum 状态:
   │   SELECT relname, n_dead_tup, n_live_tup, last_autovacuum
   │   FROM pg_stat_user_tables WHERE relname = 'inventory';
   └─ 🎯 缩短事务范围，批量提交

📊 根因分布汇总 (按总耗时排序)
─────────────────────────────────────
   🏷️ Missing Index:       5 条 (45.0%)
   📊 Sequential Scan:     3 条 (28.0%)
   💾 Work Mem / Temp:     2 条 (18.0%)
   🧹 Autovacuum / Bloat:  2 条 (20.0%)
   🔒 Lock Contention:     2 条 (12.0%)
   🔗 Inefficient Nested:  1 条 (9.5%)
   ⏰ Frequent Query:      1 条 (18.0%)

🏆 Quick Wins（低投入高回报）
──────────────────────────────
1. [Missing Index] 为 orders.created_at 添加 CONCURRENTLY 索引
   → 消除 #1 慢查询，预计降低总慢查询耗时 30%

2. [Work Mem] 检查 work_mem 设置，ORDER BY 查询溢出到 temp 文件
   → 修改 postgresql.conf: work_mem = '64MB'（当前可能仅 4MB）

3. [Bloat] 监视 inventory 表的死元组比例
   → VACUUM VERBOSE inventory; 或设置更积极的 autovacuum
```

#### Failure Recovery

| 错误模式 | 重试 | Agent 行动 |
|---------|:----:|-----------|
| 慢日志数据为空 | 0 | 报告"该时段无慢查询"; 建议缩小时间范围或检查 `log_min_duration_statement` 配置 |
| SQL 文本过短(截断) | 0 | 基于可用的执行指标进行分析; 提示用户通过 `pg_stat_statements` 获取完整 SQL |
| 指标数据缺失(如 lockTime) | 0 | 基于已有指标进行分析; 标注"部分分析因数据缺失受限" |
| 实例不存在 | 0 | HALT; 提示检查实例 ID |

#### PostgreSQL 慢查询感知自动化（监控联动）

将 PostgreSQL 慢查询分析与 CloudMonitor 告警联动，实现自动化的慢查询感知：

**Step 1: 配置慢查询告警规则**（通过 `jdcloud-cloudmonitor-ops`）
```bash
# 当慢查询数量超过阈值时触发告警
jdc --output json cm create-alarm-rule \
  --region-id "{{user.region}}" \
  --alarm-rule-name "postgresql-slow-query-alert" \
  --metric-name "SlowQueries" \
  --resource-type "rds" \
  --resource-id "{{user.instance_id}}" \
  --threshold "10" \
  --comparison-operator "GreaterThan" \
  --evaluation-periods "2" \
  --period "300"
```

**Step 2: 告警响应自动分析**（告警回调触发）
```python
# 告警回调接收到的信息
alert_payload = {
    "instance_id": "pg-xxxx",
    "metric": "SlowQueries",
    "current_value": 15,
    "threshold": 10,
    "timestamp": "2026-06-08T10:30:00+08:00"
}

# 自动触发慢日志查询（告警触发前15分钟窗口）
auto_start_time = alert_timestamp - timedelta(minutes=15)
auto_end_time = alert_timestamp

# 调用 describeSlowLogs 获取告警时段慢日志
# 调用 analyzeSlowQueries 生成分析报告（含 PG 特有根因：Autovacuum/Bloat/Work Mem）
# 发送分析报告到指定渠道（钉钉/邮件/短信）
```

**Step 3: 分析报告输出格式（PG 专用）**
```
🚨 PostgreSQL 慢查询告警自动分析报告
═══════════════════════════════════════
告警实例: pg-xxxx
告警时间: 2026-06-08 10:30:00
触发条件: 慢查询数 15 > 阈值 10

📊 告警时段慢查询概况 (10:15:00 ~ 10:30:00)
───────────────────────────────────────
慢查询模式数: 3 条
Critical: 1 条 | Major: 2 条

🔴 Critical 问题
────────────────
SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at
执行次数: 8 | 平均耗时: 3200ms | 总耗时: 25600ms

根因: 🏷️ Missing Index + 💾 Work Mem / Temp File
建议: CREATE INDEX CONCURRENTLY idx_orders_status_created ON orders(status, created_at)
PG 专用: 检查 work_mem 设置，当前可能不足导致排序溢出到磁盘
预期收益: 降低查询时间 ~95%

完整报告: [查看详情]
```

#### PostgreSQL 慢查询定期巡检（Scheduled Audit）

**使用场景**: 每日/每周自动巡检生产环境 PostgreSQL 慢查询，生成趋势报告。

**Execution Flow**:
```python
def scheduled_pg_slowquery_audit(tag_filters, time_window_hours=24):
    """
    PostgreSQL 定期慢查询巡检
    
    Args:
        tag_filters: 标签过滤，如 [{"name": "tag:环境", "values": ["生产"]}]
        time_window_hours: 巡检时间窗口，默认24小时
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=time_window_hours)
    
    # Phase 1: 按标签查询所有 PostgreSQL 实例慢日志
    slowlog_results = query_slowlogs_by_tags(
        tag_filters=tag_filters,
        start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
        max_instances=50,
        engine="PostgreSQL"  # 关键：只查 PostgreSQL 引擎
    )
    
    # Phase 2: 分析所有实例的慢查询（PG 特有根因分析）
    analysis_results = []
    for instance_result in slowlog_results["results"]:
        if instance_result["total_count"] > 0:
            analysis = analyze_pg_slow_queries_batch(
                instance_id=instance_result["instance_id"],
                slow_logs=instance_result["slow_logs"]
            )
            # PG 特有：检查 autovacuum 状态
            analysis["autovacuum_status"] = check_autovacuum_status(
                instance_result["instance_id"]
            )
            analysis_results.append(analysis)
    
    # Phase 3: 生成趋势报告
    trend_report = generate_pg_trend_report(analysis_results)
    
    return {
        "audit_time": end_time.isoformat(),
        "time_window": f"{time_window_hours}h",
        "instances_audited": len(slowlog_results["results"]),
        "instances_with_issues": len(analysis_results),
        "trend_report": trend_report,
        "top_priorities": extract_pg_top_priorities(analysis_results, top_n=5),
        "autovacuum_recommendations": generate_autovacuum_recommendations(
            analysis_results
        )
    }
```

**输出示例（PG 专用）**:
```
📋 PostgreSQL 慢查询巡检报告 (2026-06-08)
═══════════════════════════════════════════
巡检时间范围: 过去 24 小时
巡检实例数: 8 个 (标签: 环境=生产)
存在慢查询实例: 3 个

📈 趋势对比 (vs 昨日)
─────────────────────
慢查询模式总数: 38 → 32 (-15.8%) ✅
Critical 级别: 2 → 1 (-50.0%) ✅
总执行耗时: 980,000ms → 750,000ms (-23.5%) ✅
🧹 Autovacuum 延迟实例: 2 → 1 (-50%) ✅

🔥 Top 5 优化优先级
───────────────────
1. [pg-prod-01] orders 表缺少索引 (impact: 高)
   SQL: SELECT * FROM orders WHERE user_id = ?
   建议: CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id)
   预计收益: 减少 ~380s 日累计耗时

2. [pg-prod-03] inventory UPDATE 锁竞争 + 表膨胀 (impact: 高)
   根因: 🧹 Autovacuum / Bloat: n_dead_tup/n_live_tup = 35%
   建议: 
   ├─ 立即: VACUUM VERBOSE inventory;
   └─ 长期: 调整 autovacuum_vacuum_scale_threshold = 0.1

3. [pg-prod-02] 复杂 JOIN 溢出到 temp 文件 (impact: 中)
   根因: 💾 Work Mem / Temp: ORDER BY + GROUP BY 溢出
   建议: 增加 work_mem = '64MB'（当前 4MB）

4. [pg-prod-01] products 表 Sequential Scan (impact: 中)
   建议: 为 WHERE category_id = ? 添加索引

5. [pg-prod-05] 分页查询深翻页 (impact: 低)
   建议: 使用 keyset pagination 替代 OFFSET

📊 根因分布 (PG 特有)
───────────
🏷️ Missing Index:         12 条 (40%)
📊 Sequential Scan:        8 条 (26%)
🧹 Autovacuum / Bloat:     4 条 (13%) ⚠️ PG 特有
💾 Work Mem / Temp:        3 条 (10%) ⚠️ PG 特有
🔒 Lock Contention:        2 条 (7%)
🔗 Inefficient Nested:     1 条 (3%)

🧹 Autovacuum 健康检查
──────────────────────
pg-prod-03: 表 inventory 死元组比例 35% > 20%阈值 ⚠️
pg-prod-07: 表 logs 超过 24 小时未 autovacuum ⚠️

✅ 已优化确认
─────────────
昨日建议 #1 (pg-prod-02): 已添加 CONCURRENTLY 索引 ✅
昨日建议 #2 (pg-prod-01): 已调整 work_mem 64MB ✅
```

#### Failure Recovery
#### Failure Recovery\n\n| 错误模式 | 重试 | Agent 行动 |\n|---------|:----:|-----------|\n| 慢日志数据为空 | 0 | 报告"该时段无慢查询"; 建议缩小时间范围或检查 `log_min_duration_statement` 配置 |\n| SQL 文本过短(截断) | 0 | 基于可用的执行指标进行分析; 提示用户通过 `pg_stat_statements` 获取完整 SQL |\n| 指标数据缺失(如 lockTime) | 0 | 基于已有指标进行分析; 标注"部分分析因数据缺失受限" |\n| 实例不存在 | 0 | HALT; 提示检查实例 ID |\n\n#### 与 describeSlowLogs 的关系\n\n| 方面 | describeSlowLogs | analyzeSlowQueries（本操作） |\n|------|-----------------|---------------------------|\n| 输出 | 原始慢日志数据 | 结构化分析报告 + 优化建议 |\n| 目的 | 数据查询 | 智能诊断 |\n| 是否调用 API | 是（必须） | 否（纯计算层，基于 API 返回数据） |\n| 依赖 | 无 | 依赖 describeSlowLogs 的返回数据 |\n| 可组合性 | 独立使用 | 先 query → 后 analyze |\n\n> **组合使用建议：** 推荐先执行 `describeSlowLogs` 获取数据，再将结果输入本分析操作。\n> 当用户问"慢查询怎么办"时，应该：感知 → 分析 → 优化，三步联动。\n\n---\n\n### Operation: Describe PostgreSQL Instance"}]

#### Execution (CLI) [Primary Path]

```bash
jdc --output json rds describe-instance \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.rds.apis.DescribeInstanceRequest import DescribeInstanceRequest, DescribeInstanceParameters

params = DescribeInstanceParameters(regionId="{{user.region}}", instanceId="{{user.instance_id}}")
req = DescribeInstanceRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["instance"]
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| Instance ID | `$.result.instance.instanceId` | Plain text |
| Name | `$.result.instance.instanceName` | Plain text |
| Status | `$.result.instance.status` | running, creating, error, etc. |
| Engine Version | `$.result.instance.engineVersion` | 10, 11, 12, 13, 14 |
| Instance Type | `$.result.instance.instanceClass` | e.g., rds.pg.s1.small |
| Connection Address | `$.result.instance.connectionDomain` | PostgreSQL connection string |
| Port | `$.result.instance.port` | Default 5432 |

### Operation: List PostgreSQL Instances

#### Execution (CLI) [Primary Path]

```bash
jdc --output json rds describe-instances \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.rds.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters

params = DescribeInstancesParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeInstancesRequest(parameters=params)
resp = client.send(req)
instances = resp.result["instances"]
```

### Operation: Modify PostgreSQL Instance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Instance exists | `describeInstance` | Instance found | HALT; verify instance ID |
| Instance state | `describeInstance` | `running` | Wait or suggest appropriate action |

**⚠️ For `modifyInstanceClass` (scaling)**: Confirm with user as it may cause brief service interruption.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json rds modify-instance-attribute \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}" \
  --instance-name "{{user.new_name}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.rds.apis.ModifyInstanceAttributeRequest import ModifyInstanceAttributeRequest, ModifyInstanceAttributeParameters

params = ModifyInstanceAttributeParameters(
    regionId="{{user.region}}",
    instanceId="{{user.instance_id}}"
)
params.setInstanceName("{{user.new_name}}")
req = ModifyInstanceAttributeRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until modification reflects (depends on modification type).

### Operation: Delete PostgreSQL Instance

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.instance_name}}` (`{{user.instance_id}}`).
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
# Confirm deletion with user first
jdc --output json rds delete-instance \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before calling SDK delete method.

```python
from jdcloud_sdk.services.rds.apis.DeleteInstanceRequest import DeleteInstanceRequest, DeleteInstanceParameters

# Confirm deletion with user: "Are you sure you want to delete {{user.instance_name}} ({{user.instance_id}})? This is IRREVERSIBLE."
# Proceed only after explicit "yes" / "confirm" response

params = DeleteInstanceParameters(regionId="{{user.region}}", instanceId="{{user.instance_id}}")
req = DeleteInstanceRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll `describeInstance` until HTTP 404 / `status` indicates deleted (max 600s).

### Operation: Backup PostgreSQL Instance

#### Execution (CLI) [Primary Path]

```bash
jdc --output json rds create-backup \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.rds.apis.CreateBackupRequest import CreateBackupRequest, CreateBackupParameters

params = CreateBackupParameters(
    regionId="{{user.region}}",
    instanceId="{{user.instance_id}}",
    fileName="manual-backup-{{user.instance_id}}",
    backupType=1
)
req = CreateBackupRequest(parameters=params)
resp = client.send(req)
backup_id = resp.result["backupId"]
```

### Operation: Restore PostgreSQL Instance

#### Pre-flight (Safety Gate)

- **MUST** warn user: Restore will overwrite current data in `{{user.instance_name}}` (`{{user.instance_id}}`) with backup `{{user.backup_id}}`.
- **MUST** obtain explicit confirmation before proceeding.

#### Execution (CLI) [Primary Path]

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
# Confirm restore with user first
jdc --output json rds restore-instance \
  --region-id "{{user.region}}" \
  --instance-id "{{user.instance_id}}" \
  --backup-id "{{user.backup_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before calling SDK restore method.

```python
from jdcloud_sdk.services.rds.apis.RestoreInstanceRequest import RestoreInstanceRequest, RestoreInstanceParameters

# Confirm restore with user: "Restoring backup {{user.backup_id}} will overwrite current data. Are you sure?"
# Proceed only after explicit "yes" / "confirm" response

params = RestoreInstanceParameters(
    regionId="{{user.region}}",
    instanceId="{{user.instance_id}}",
    backupId="{{user.backup_id}}"
)
req = RestoreInstanceRequest(parameters=params)
resp = client.send(req)
```

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **mandatory** for all operations exposed by this skill.

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **2** | `delete` / `restore` / DDL `DROP` / DML `DELETE`/`UPDATE` without WHERE are all destructive; do not retry repeatedly on production data |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete`, `restore`, storage shrink, `DROP`, `TRUNCATE`, `VACUUM FULL`, `DELETE`/`UPDATE` without WHERE | matches repository safety gate policy |
| `hallucination_check` | **mandatory** | Phase 6 H layer; validates CLI parameters and JSON structure before execution |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► jdc (primary) → SDK / psycopg2 (after 3 fails)
   │                              generate command/payload (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (mandatory for postgresql-ops) - CLI parameter existence
   │                                   - JSON structure compliance
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
   ├─ iter<2 & not all pass   → RETRY (inject suggestions)
   └─ iter=2 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Mandatory

> **Purpose**: Catch LLM-generated CLI/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud RDS PostgreSQL API. This is a **pre-execution** gate placed
> between G's generation and actual API execution.

**Three-Category Check (for postgresql-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in the jdc rds operation spec | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For SDK request payloads | Validate field nesting matches OpenAPI schema |
| **Operation-Specific Validation** | PostgreSQL-specific constraints | Time range ≤ 7 days for slow logs; instanceId format; engine="PostgreSQL" |

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
      "json_structure": { "status": "PASS|FAIL", "issues": [] },
      "operation_specific": { "status": "PASS|FAIL", "issues": [] }
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
# 2. Filter patterns by current skill name (jdcloud-postgresql-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidTimeRange: Limit slow log query time range ≤ 7 days
- Missing WHERE clause: DML UPDATE/DELETE without WHERE → Safety=0
- VACUUM FULL requires confirm: Destructive table rewrite operation"
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter" | "skill_generation" | "cross_skill" | "runtime" | "token_efficiency",
    "skill": "jdcloud-postgresql-ops",
    "command": "jdc --output json rds describe-slow-logs ...",
    "error": "InvalidTimeRange: time range > 7 days",
    "fix": "Adjusted time range to ≤ 7 days",
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

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK / SQL
access. The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is a mandatory pre-execution structural check.

### Operation-specific behavior

- **`create-instance`** — Critic verifies `--client-token` was set
  (Idempotency = 1 required). Missing → Idempotency = 0.
- **`delete-instance`** — Critic checks the trace contains both a pre-delete
  `describe-instance` snapshot and a post-delete 404. Missing either →
  Correctness = 0.
- **`restore-instance`** — `backupId` must belong to the same `instanceId`;
  cross-instance restore requires explicit user confirm in trace or Safety = 0.
- **`modify-instance` (storage)** — Storage shrink is **forbidden** without
  user opt-in. Safety = 0 otherwise.
- **DDL `CREATE TABLE` / `CREATE INDEX`** — Prefer `IF NOT EXISTS`. Full DDL
  must appear in trace or Traceability = 0.
- **DDL `DROP TABLE` / `DROP SCHEMA` / `TRUNCATE`** — Always Safety = 0
  without `confirm=*` in trace → ABORT.
- **DDL `ALTER TABLE`** — For PG 10+ prefer `ADD COLUMN ... DEFAULT`
  (non-blocking); full ALTER must appear in trace.
- **`VACUUM FULL`** — Destructive (rewrites table); Safety = 0 without
  `confirm=VACUUM_FULL` → ABORT.
- **DML `UPDATE` / `DELETE`** — SQL text MUST have a `WHERE` clause. Missing
  WHERE → Safety = 0 → ABORT. Pre-check: `SELECT count(*) ... WHERE ...` to
  predict `rowcount`.
- **DML `SELECT`** — Read-only; Safety = 1.0 by default. **EXCEPTION**: if
  SELECT text contains `FOR UPDATE` / `FOR NO KEY UPDATE` / `FOR SHARE` /
  `INTO OUTFILE` → Safety must be re-scored.
- **All DDL/DML** — Always pre-check via `pg_catalog` and include result in
  trace; full SQL text must appear verbatim.
- **H layer operation-specific checks**:
  - `describe-slow-logs` — H validates time range ≤ 7 days before execution
  - `delete-instance` — H validates instanceId format and existence check
  - DDL/DML — H validates SQL structure (WHERE clause presence for DML)

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

Environment setup follows a **jdc-first with fallback** strategy:

1. **Attempt `jdc` CLI setup** via `uv` (primary path)
2. On failure, **retry up to 3 times** with exponential backoff (0s → 2s → 4s)
3. After **3 consecutive failures**, fall back to **SDK-only** setup

### Python Runtime (uv)

Both `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management:

**Install uv (system-wide, one-time per machine):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or via Homebrew: brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Phase 1: jdc CLI Setup (Primary Path)

```bash
# Create and activate virtual environment (idempotent)
uv venv --python 3.10
source .venv/bin/activate

# Install jdc CLI and SDK
uv pip install jdcloud_cli jdcloud_sdk

# Verify
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

#### Retry Logic (Up to 3 Attempts)

If `jdc --version` or any `jdc` command fails:

```bash
# Retry 1: re-run pip install
uv pip install jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"

# Retry 2 (wait 2s)
sleep 2
uv pip install --force-reinstall jdcloud_cli
jdc --version && echo "OK" || echo "FAIL"

# Retry 3 (wait 4s)
sleep 4
uv pip install --force-reinstall jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"
```

If all **3 retries** fail, proceed to **Phase 2: SDK Fallback**.

### Phase 2: SDK Fallback (After 3 jdc Failures)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
python -c "import jdcloud_sdk; print('SDK OK')"
```

### Configure jdc Credentials (Sandbox-Safe)

**CRITICAL**: The `jdc` CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables. It reads credentials exclusively from `~/.jdc/config` (INI format). In sandboxed environments where `~` is not writable, follow these steps:

```bash
# 1. Set HOME to a writable location
export HOME=/tmp/jdc-home

# 2. Pre-create the config directory and files
mkdir -p /tmp/jdc-home/.jdc

cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{user.region}}
endpoint = rds.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

# 3. Write current profile WITHOUT trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# 4. Run jdc with --output json at TOP level
jdc --output json rds describe-instances --region-id "{{user.region}}" --page-number 1 --page-size 100
```

### Configure Credentials for SDK (Environment Variables)

SDK reads credentials from environment variables — no config file needed:

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> Security: Never commit `.env` files to version control.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Architecture selection:** Choose appropriate instance class based on workload; consider read replicas for high read traffic.
- **High availability:** Multi-AZ deployment for production; enable automatic failover.
- **Security:** Enable IP whitelist, use VPC isolation, rotate passwords regularly, enable SSL/TLS.
- **Performance:** Analyze slow query logs regularly; optimize indexes; monitor connection pool.
- **Backup:** Configure automatic backup policy; test restore procedures; set appropriate retention period.