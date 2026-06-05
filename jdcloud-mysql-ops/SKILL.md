---
name: jdcloud-mysql-ops
description: >-
  Use this skill for JD Cloud RDS MySQL database management — create, configure, and
  manage MySQL instances; backup and restore data; analyze performance;
  troubleshoot connection or latency issues. Apply when the user mentions MySQL,
  RDS, 关系型数据库, 云数据库, 数据库, or asks about database, MySQL instances on JD Cloud,
  even without explicit "MySQL" mentions.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.2.0"
  last_updated: "2026-06-05"
  runtime: Harness AI Agent
  api_profile: "JD Cloud RDS MySQL API v1 - https://rds.jdcloud-api.com/v1"
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

# JD Cloud RDS MySQL Operations Skill

## Overview

JD Cloud RDS MySQL (云数据库 RDS MySQL) is a fully managed relational database service compatible with MySQL protocol. It provides high availability, automatic backup, read replicas, and flexible scaling. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

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

- User mentions "JD Cloud MySQL" OR "RDS MySQL" OR "云数据库 MySQL" OR "关系型数据库" OR "MySQL实例"
- Task involves CRUD operations on MySQL instances: create, describe, modify, delete, list, backup, restore, config
- Task keywords: createInstance, describeInstances, modifyInstance, backup, restore, slowlog, database
- User asks to deploy, configure, troubleshoot, or monitor MySQL instances **via API, SDK, CLI, or automation**
- Task involves MySQL performance analysis (slow query log, connection pool)

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about PostgreSQL → delegate to: `jdcloud-postgresql-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If MySQL instance requires VPC/subnet, verify or create network resources via `jdcloud-vpc-ops` first.
- If user asks about MySQL monitoring metrics or alarm rules, delegate metric query to `jdcloud-cloudmonitor-ops`.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.instance_id}}` | User-supplied MySQL instance ID | Ask once; reuse |
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
| Create Instance | `$.result.instanceId` | string | New MySQL instance ID |
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
| 1.2.0 | 2026-06-05 | **Added Describe Slow Logs operations**: (1) `describeSlowLogs` — query slow query summaries by time range for single instance. (2) `describeSlowLogsByTags` — two-phase composite operation: filter instances by tags (环境=生产, 客户=xxx), then parallel query slow logs across all matching instances. Both support pagination, filtering (account/keyword), sorting (execution metrics), with safety guards (max_instances limit, parallel execution control). |
| 1.1.0 | 2026-06-04 | **GCL rollout**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, instance-level + DDL/DML paths, op-specific overrides including storage shrink and SQL `WHERE` check) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=2`. `safety_confirm_required=true` for delete, restore, storage shrink, DDL `DROP`/`TRUNCATE`, DML `UPDATE`/`DELETE` without WHERE. |
| 1.0.0 | 2026-06-03 | Initial version with API/SDK and `jdc` CLI dual-path support |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. Do not skip phases.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Documentation below lists `jdc` before SDK to reflect execution priority.

### Operation: Create MySQL Instance

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
  --engine "MySQL" \
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
    "engine": "MySQL",
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

### Operation: Describe MySQL Slow Logs

> 查询指定时段的 MySQL 慢日志概要信息 — 仅支持 MySQL 实例。

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.rds.client.RdsClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Instance exists | `describeInstance` | Instance found | HALT; verify instance ID |
| Instance engine | `describeInstance` | `MySQL` | HALT; operation only supports MySQL |
| Time window validation | Parse user input | Start time ≤ End time, duration ≤ 7 days | Suggest valid time range |

#### Input Variables

| Variable | Required | Format | Example | Description |
|----------|----------|--------|---------|-------------|
| `{{user.region}}` | yes | string | `cn-north-1` | Region ID |
| `{{user.instance_id}}` | yes | string | `rds-xxxx` | MySQL instance ID |
| `{{user.start_time}}` | yes | `YYYY-MM-DD HH:mm:ss` | `2026-06-01 00:00:00` | 查询开始时间 |
| `{{user.end_time}}` | yes | `YYYY-MM-DD HH:mm:ss` | `2026-06-03 23:59:59` | 查询结束时间 |
| `{{user.db_name}}` | no | string | `mydb` | 数据库名过滤(废弃字段) |
| `{{user.page_number}}` | no | int | `1` | 页码,默认 1 |
| `{{user.page_size}}` | no | int | `10` | 每页条数,范围[10,100],默认 10 |
| `{{user.filters}}` | no | array | `[{"name":"account","operator":"eq","values":["root"]}]` | 过滤条件(账号/关键词) |
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
        "values": ["root"]
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
MySQL Slow Log Summary for {{user.instance_id}} ({{user.start_time}} ~ {{user.end_time}})

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

### Operation: Describe MySQL Slow Logs by Tags

> 按标签过滤 MySQL 实例，并查询符合条件的实例在指定时段的慢日志。这是一个组合操作：先按标签查找实例，再并行查询每个实例的慢日志。

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
| `{{user.slowlog_filters}}` | no | array | `[{"name":"account","operator":"eq","values":["root"]}]` | 慢日志过滤条件(账号/关键词) |
| `{{user.sorts}}` | no | array | `[{"name":"executionTimeSum","direction":"DESC"}]` | 排序字段 |
| `{{user.max_instances}}` | no | int | `10` | 最大查询实例数(防止过多),默认 10 |

> **Time window constraint:** 开始时间到当前时间不能大于 **7 天**,开始时间不能大于结束时间。

> **Tag filter format:** `{"name": "tag:<tag_key>", "operator": "eq|in", "values": ["value1", "value2"]}`

#### Execution Flow

这是一个**两阶段组合操作**：

**阶段 1: 按标签查找实例** → **阶段 2: 并行查询慢日志** → **阶段 3: 聚合结果**

#### Phase 1: 按标签查找 MySQL 实例

##### Execution — CLI (`jdc`) [Primary Path]

```bash
# 按标签过滤查找 MySQL 实例
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

# 提取 MySQL 实例列表
instances = [
    inst for inst in resp.result.get("instances", [])
    if inst.get("engine") == "MySQL"
]
instance_ids = [inst["instanceId"] for inst in instances]

print(f"Found {len(instance_ids)} MySQL instances matching tags: {instance_ids}")
```

##### Phase 1 Output JSON Paths

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| Total count | `$.result.totalCount` | int | 符合条件的实例总数 |
| Instances array | `$.result.instances` | array | 实例列表 |
| Instance ID | `$.result.instances[*].instanceId` | string | 实例ID |
| Engine | `$.result.instances[*].engine` | string | 数据库引擎(MySQL) |
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
      "instance_id": "rds-mysql-001",
      "total_count": 15,
      "slow_logs": [
        {
          "sql": "SELECT * FROM orders WHERE created_at > ?",
          "executionCount": 120,
          "executionTimeAvg": 1500,
          "executionTimeMax": 3500,
          "executionTimeSum": 180000,
          "rowsExaminedSum": 500000,
          "instance_id": "rds-mysql-001"
        }
      ]
    },
    {
      "instance_id": "rds-mysql-002",
      "total_count": 0,
      "slow_logs": []
    }
  ],
  "aggregated_slowlogs": [
    {
      "sql": "SELECT * FROM orders WHERE created_at > ?",
      "executionCount": 120,
      "executionTimeSum": 180000,
      "rowsExaminedSum": 500000,
      "instance_id": "rds-mysql-001"
    }
  ],
  "top_queries_by_instance": {
    "rds-mysql-001": [
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
MySQL Slow Logs by Tags Summary
================================
Tags: 环境=生产, 客户=xxx
Time: 2026-06-01 00:00:00 ~ 2026-06-03 23:59:59
Region: cn-north-1

Instances Queried: 3
Instances with Slow Queries: 2

─────────────────────────────────────
Instance: rds-mysql-001 (15 patterns)
─────────────────────────────────────
1. [120x] SELECT * FROM orders WHERE created_at > ?
   Avg: 1500ms | Max: 3500ms | Total: 180000ms
   Rows examined: 500000 | Lock time: 120ms

2. [85x] UPDATE inventory SET stock = stock - ? WHERE sku = ?
   Avg: 800ms | Max: 2000ms | Total: 68000ms
   Rows examined: 85000 | Lock time: 450ms

─────────────────────────────────────
Instance: rds-mysql-002 (0 patterns)
─────────────────────────────────────
No slow queries found.

─────────────────────────────────────
Instance: rds-mysql-003 (8 patterns)
─────────────────────────────────────
1. [45x] DELETE FROM logs WHERE created_at < ?
   Avg: 2200ms | Max: 5000ms | Total: 99000ms
   Rows examined: 2000000 | Lock time: 800ms

🔥 Top 3 Slowest Queries Across All Instances:
1. [rds-mysql-001] SELECT * FROM orders... (180000ms total)
2. [rds-mysql-003] DELETE FROM logs... (99000ms total)
3. [rds-mysql-001] UPDATE inventory... (68000ms total)
```

#### Common Use Cases

**Case 1: 查询生产环境所有客户的慢日志**
```bash
# 步骤1: 查找标签为 环境=生产 的所有 MySQL 实例
INSTANCES=$(jdc --output json rds describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"tag:环境","operator":"eq","values":["生产"]}]' \
  | jq -r '.result.instances[] | select(.engine == "MySQL") | .instanceId')

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
    按标签查询 MySQL 实例慢日志
    
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
    
    # Filter MySQL instances only
    mysql_instances = [
        inst for inst in resp.result.get("instances", [])
        if inst.get("engine") == "MySQL"
    ]
    
    if len(mysql_instances) > max_instances:
        raise ValueError(f"Found {len(mysql_instances)} instances, exceeds max {max_instances}. "
                        f"Please refine tag filters or increase max_instances.")
    
    instance_ids = [inst["instanceId"] for inst in mysql_instances]
    print(f"Found {len(instance_ids)} MySQL instances: {instance_ids}")
    
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
                "instance_name": next((i["instanceName"] for i in mysql_instances 
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
| `UnsupportedEngine` / 400 | 0 | — | 跳过该实例（非 MySQL） |
| Throttling / 429 | 3 | exponential | 指数退避后重试 |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | 重试；持续失败则记录错误但继续其他实例 |

#### Safety Considerations

1. **实例数量限制:** 默认 `max_instances=10`，防止意外查询过多实例
2. **并行度控制:** 使用 ThreadPoolExecutor(max_workers=5) 控制并发
3. **部分失败处理:** 单个实例查询失败不影响其他实例
4. **数据聚合上限:** 跨实例聚合结果限制返回数量，避免过大响应

### Operation: Describe MySQL Instance

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
| Engine Version | `$.result.instance.engineVersion` | 5.7, 8.0 |
| Instance Type | `$.result.instance.instanceClass` | e.g., rds.mysql.s1.small |
| Connection Address | `$.result.instance.connectionDomain` | MySQL connection string |
| Port | `$.result.instance.port` | Default 3306 |

### Operation: List MySQL Instances

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

### Operation: Modify MySQL Instance

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

### Operation: Delete MySQL Instance

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

### Operation: Backup MySQL Instance

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

### Operation: Restore MySQL Instance

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
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete`, `restore`, storage shrink, `DROP`, `TRUNCATE`, `DELETE`/`UPDATE` without WHERE | matches repository safety gate policy |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │
   ▼
[1] Generator (G)            ──► jdc (primary) → SDK / pymysql (after 3 fails)
   │
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │
   ▼
[3] Orchestrator decider
   ├─ Safety=0 / blocking   → ABORT
   ├─ all pass              → RETURN
   ├─ iter<2 & not all pass → RETRY (inject suggestions)
   └─ iter=2 & not all pass → RETURN_BEST
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)

### Integration with existing flows

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK / SQL
access. The Orchestrator (O) owns the loop and persists the GCL trace.

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
- **DDL `CREATE TABLE`** — Prefer `IF NOT EXISTS`. Full DDL must appear in
  trace or Traceability = 0.
- **DDL `DROP TABLE` / `DROP DATABASE` / `TRUNCATE`** — Always Safety = 0
  without `confirm=DROP` / `confirm=TRUNCATE` in trace → ABORT.
- **DDL `ALTER TABLE`** — Full ALTER must appear in trace; online DDL
  preferred for production.
- **DML `UPDATE` / `DELETE`** — SQL text MUST have a `WHERE` clause. Missing
  WHERE → Safety = 0 → ABORT. Pre-check: `SELECT COUNT(*)` with the same
  WHERE to predict `affected_rows`.
- **DML `SELECT`** — Read-only; Safety = 1.0 by default.
- **All DDL/DML** — Always pre-check via `SHOW DATABASES` / `SHOW TABLES` /
  `DESCRIBE` and include result in trace; full SQL text must appear verbatim.

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