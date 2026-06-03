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
  author: jdcloud
  version: "1.1.0"
  last_updated: "2026-06-04"
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

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `QuotaExceeded` | 0 | — | HALT; user requests quota increase |
| `InsufficientBalance` | 0 | — | HALT; user tops up account |
| `ResourceAlreadyExists` | 0 | — | Ask reuse vs new name |
| `SubnetIpInsufficient` | 0 | — | HALT; user expands subnet |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

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