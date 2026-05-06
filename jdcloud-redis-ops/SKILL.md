---
name: jdcloud-redis-ops
description: >-
  Use when you need to deploy, configure, troubleshoot, or monitor JD Cloud
  Redis (distributed cache compatible with Redis) via official API/SDK or 
  official `jdc` CLI; user mentions Redis, 云缓存, 分布式缓存, JCS for Redis,
  or tasks target Redis cache instances.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: jdcloud
  version: "1.2.0"
  last_updated: "2026-05-06"
  runtime: Harness AI Agent
  api_profile: "JD Cloud Redis API v1 - https://redis.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing 'redis' in product list:
    `{mps,cps,rds,jke,vpc,xdata,mongodb,configure,streambus,ipanti,baseanti,datastar,redis,nc,monitor,iam,disk,cr,streamcomputer,sop,clouddnsservice,vm,oss}`.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Redis Operations Skill

## Overview

JD Cloud Redis (分布式缓存/云缓存 Redis) is a high-performance distributed cache service compatible with open-source Redis protocol. It provides elastic, scalable, and reliable caching capabilities with automatic failover, data backup, and online scaling. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

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
jdc --output json redis describe-cache-instances --region-id cn-north-1 --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc redis describe-cache-instances --region-id cn-north-1 --page-number 1 --page-size 100 --output json
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
endpoint = redis.jdcloud-api.com
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

- User mentions "JD Cloud Redis" OR "云缓存" OR "分布式缓存" OR "JCS for Redis" OR "Redis实例"
- Task involves CRUD operations on Redis instances: create, describe, modify, delete, list, backup, restore, config
- Task keywords: createCacheInstance, describeCacheInstances, modifyCacheInstance, backup, restore, slowlog, cache-analysis
- User asks to deploy, configure, troubleshoot, or monitor Redis instances **via API, SDK, CLI, or automation**
- Task involves Redis performance analysis (hot key, big key, slow log)

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If Redis instance requires VPC/subnet, verify or create network resources via `jdcloud-vpc-ops` first.
- If user asks about Redis monitoring metrics or alarm rules, delegate metric query to `jdcloud-cloudmonitor-ops`.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.instance_id}}` | User-supplied Redis instance ID | Ask once; reuse |
| `{{user.instance_name}}` | User-supplied instance name | Ask once; reuse |
| `{{output.instance_id}}` | From last API or CLI JSON response | Parse from `$.result.cacheInstanceId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://redis.jdcloud-api.com/v1/regions/{regionId}/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-05-03T10:00:00+08:00`).
- **Idempotency:** Document duplicate instance name behavior and retry safety per API.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Instance | `$.result.cacheInstanceId` | string | New Redis instance ID |
| Describe Instance | `$.result.cacheInstance.status` | string | Instance state (running, creating, etc.) |
| List Instances | `$.result.cacheInstances[*].cacheInstanceId` | array | All instance IDs |
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
| 1.2.0 | 2026-05-06 | **Empirical CLI fixes**: Fixed `--output json` placement (must be top-level, before subcommand); removed `--no-interactive` (unsupported); fixed jdc credential config (must use `~/.jdc/config` INI file, env vars unsupported); fixed PermissionError via `HOME=/tmp/jdc-home`; fixed all SDK import paths (PascalCase module names) and API call patterns (Parameters objects + `client.send()`); fixed Backup parameters (requires `fileName`/`backupType`); fixed Restore parameter name (`baseId` not `backupId`) |
| 1.1.0 | 2026-05-06 | **jdc-first with fallback strategy**: execution flows now prioritize `jdc` CLI (primary) with SDK/API fallback after 3 retries; Prerequisites updated to `uv`-based bootstrap with Phase 1 (jdc) / Phase 2 (SDK fallback); Path Preference flipped to jdc-first; pre-flight checks reordered |
| 1.0.1 | 2026-05-03 | Added safety gates for Delete/Restore/Modify operations; added Path Preference section |
| 1.0.0 | 2026-05-03 | Initial version with API/SDK and `jdc` CLI dual-path support |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. Do not skip phases.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Documentation below lists `jdc` before SDK to reflect execution priority.

### Operation: Create Redis Instance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.redis.client.RedisClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Call `describeAvailableRegion` API | `{{user.region}}` supported | Suggest valid region |
| VPC/Subnet | Verify subnet via `jdcloud-vpc-ops` | Subnet exists and has IP | HALT; create subnet first |
| Instance Class | Call `describeInstanceClass` or `describeSpecConfig` | Valid spec code | Suggest available specs |

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json redis create-cache-instance \
  --region-id "{{user.region}}" \
  --cache-instance-name "{{user.instance_name}}" \
  --cache-instance-class "{{user.instance_class}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --az-id-spec '{"azSpecifyType":"SpecifyByReplicaGroup","master":"{{user.az_master}}","slave":"{{user.az_slave}}"}' \
  --cache-instance-type "{{user.cache_instance_type}}" \
  --redis-version "{{user.redis_version}}"
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
endpoint = redis.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.redis.client.RedisClient import RedisClient
from jdcloud_sdk.services.redis.apis.CreateCacheInstanceRequest import CreateCacheInstanceRequest, CreateCacheInstanceParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = RedisClient(credential)

# Build full cacheInstance spec dict (not individual setters)
az_spec = {
    "azSpecifyType": "SpecifyByReplicaGroup",
    "master": "{{user.az_master}}",
    "slave": "{{user.az_slave}}"
}

cache_instance_spec = {
    "cacheInstanceName": "{{user.instance_name}}",
    "cacheInstanceClass": "{{user.instance_class}}",
    "vpcId": "{{user.vpc_id}}",
    "subnetId": "{{user.subnet_id}}",
    "azIdSpec": az_spec,
    "cacheInstanceType": "{{user.cache_instance_type}}",
    "redisVersion": "{{user.redis_version}}"
}

params = CreateCacheInstanceParameters(regionId="{{user.region}}", cacheInstance=cache_instance_spec)
req = CreateCacheInstanceRequest(parameters=params)
resp = client.send(req)
instance_id = resp.result["cacheInstanceId"]
```

#### Post-execution Validation

1. Capture `{{output.instance_id}}` from `$.result.cacheInstanceId`.
2. Poll `describeCacheInstance` until `status` == `running` or timeout.

```bash
# CLI poll loop (primary path) — --output json at TOP level
for i in $(seq 1 60); do
  STATUS=$(jdc --output json redis describe-cache-instance \
    --region-id "{{user.region}}" \
    --cache-instance-id "{{output.instance_id}}" | jq -r '.result.cacheInstance.status')
  [ "$STATUS" = "running" ] && break
  sleep 10
done
```

```python
# SDK poll loop (fallback, after 3 jdc failures)
from jdcloud_sdk.services.redis.apis.DescribeCacheInstanceRequest import DescribeCacheInstanceRequest, DescribeCacheInstanceParameters

for _ in range(60):
    dparams = DescribeCacheInstanceParameters(regionId="{{user.region}}", cacheInstanceId="{{output.instance_id}}")
    dreq = DescribeCacheInstanceRequest(parameters=dparams)
    dresp = client.send(dreq)
    status = dresp.result["cacheInstance"]["status"]
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

### Operation: Describe Redis Instance

#### Execution (CLI) [Primary Path]

```bash
jdc --output json redis describe-cache-instance \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.redis.apis.DescribeCacheInstanceRequest import DescribeCacheInstanceRequest, DescribeCacheInstanceParameters

params = DescribeCacheInstanceParameters(regionId="{{user.region}}", cacheInstanceId="{{user.instance_id}}")
req = DescribeCacheInstanceRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["cacheInstance"]
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| Instance ID | `$.result.cacheInstance.cacheInstanceId` | Plain text |
| Name | `$.result.cacheInstance.cacheInstanceName` | Plain text |
| Status | `$.result.cacheInstance.status` | running, creating, error, etc. |
| Redis Version | `$.result.cacheInstance.redisVersion` | 4.0, 5.0, 6.2 |
| Instance Type | `$.result.cacheInstance.cacheInstanceType` | master-slave, cluster, native-cluster |
| Connection Address | `$.result.cacheInstance.connectionDomain` | Redis connection string |
| Port | `$.result.cacheInstance.port` | Default 6379 |

### Operation: List Redis Instances

#### Execution (CLI) [Primary Path]

```bash
jdc --output json redis describe-cache-instances \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.redis.apis.DescribeCacheInstancesRequest import DescribeCacheInstancesRequest, DescribeCacheInstancesParameters

params = DescribeCacheInstancesParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeCacheInstancesRequest(parameters=params)
resp = client.send(req)
instances = resp.result["cacheInstances"]
```

### Operation: Modify Redis Instance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Instance exists | `describeCacheInstance` | Instance found | HALT; verify instance ID |
| Instance state | `describeCacheInstance` | `running` | Wait or suggest appropriate action |

**⚠️ For `modifyCacheInstanceClass` (scaling)**: Confirm with user as it may cause brief service interruption.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json redis modify-cache-instance-attribute \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --cache-instance-name "{{user.new_name}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.redis.apis.ModifyCacheInstanceAttributeRequest import ModifyCacheInstanceAttributeRequest, ModifyCacheInstanceAttributeParameters

params = ModifyCacheInstanceAttributeParameters(
    regionId="{{user.region}}",
    cacheInstanceId="{{user.instance_id}}"
)
params.setCacheInstanceName("{{user.new_name}}")
req = ModifyCacheInstanceAttributeRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until modification reflects (depends on modification type).

### Operation: Delete Redis Instance

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.instance_name}}` (`{{user.instance_id}}`).
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
# Confirm deletion with user first
jdc --output json redis delete-cache-instance \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before calling SDK delete method.

```python
from jdcloud_sdk.services.redis.apis.DeleteCacheInstanceRequest import DeleteCacheInstanceRequest, DeleteCacheInstanceParameters

# Confirm deletion with user: "Are you sure you want to delete {{user.instance_name}} ({{user.instance_id}})? This is IRREVERSIBLE."
# Proceed only after explicit "yes" / "confirm" response

params = DeleteCacheInstanceParameters(regionId="{{user.region}}", cacheInstanceId="{{user.instance_id}}")
req = DeleteCacheInstanceRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll `describeCacheInstance` until HTTP 404 / `status` indicates deleted (max 600s).

### Operation: Backup Redis Instance

#### Execution (CLI) [Primary Path]

```bash
jdc --output json redis create-backup \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.redis.apis.CreateBackupRequest import CreateBackupRequest, CreateBackupParameters

params = CreateBackupParameters(
    regionId="{{user.region}}",
    cacheInstanceId="{{user.instance_id}}",
    fileName="manual-backup-{{user.instance_id}}",
    backupType=1  # 1=manual backup
)
req = CreateBackupRequest(parameters=params)
resp = client.send(req)
backup_id = resp.result["backupId"]
```

### Operation: Restore Redis Instance

#### Pre-flight (Safety Gate)

- **MUST** warn user: Restore will overwrite current data in `{{user.instance_name}}` (`{{user.instance_id}}`) with backup `{{user.backup_id}}`.
- **MUST** obtain explicit confirmation before proceeding.

#### Execution (CLI) [Primary Path]

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
# Confirm restore with user first
jdc --output json redis restore-instance \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --base-id "{{user.backup_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before calling SDK restore method.

```python
from jdcloud_sdk.services.redis.apis.RestoreInstanceRequest import RestoreInstanceRequest, RestoreInstanceParameters

# Confirm restore with user: "Restoring backup {{user.backup_id}} will overwrite current data. Are you sure?"
# Proceed only after explicit "yes" / "confirm" response

params = RestoreInstanceParameters(
    regionId="{{user.region}}",
    cacheInstanceId="{{user.instance_id}}",
    baseId="{{user.backup_id}}"  # baseId = backup task ID
)
req = RestoreInstanceRequest(parameters=params)
resp = client.send(req)
```

## Prerequisites

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
endpoint = redis.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

# 3. Write current profile WITHOUT trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# 4. Run jdc with --output json at TOP level
jdc --output json redis describe-cache-instances --region-id "{{user.region}}" --page-number 1 --page-size 100
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

- **Architecture selection:** Choose master-slave (standard) for small-scale, cluster (proxy) for mid-scale, native-cluster for large-scale with direct connection.
- **High availability:** Multi-AZ deployment for production; use at least 2 replicas.
- **Security:** Enable IP whitelist, use VPC isolation, rotate passwords regularly.
- **Performance:** Analyze hot keys and big keys periodically; monitor slow logs.
- **Backup:** Configure automatic backup policy; test restore procedures.