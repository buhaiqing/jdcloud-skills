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
  product is supported by the CLI (dual-path skills).
metadata:
  author: jdcloud
  version: "1.0.1"
  last_updated: "2026-05-03"
  runtime: Harness AI Agent
  api_profile: "JD Cloud Redis API v1 - https://redis.jdcloud-api.com/v1"
  cli_applicability: dual-path
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

JD Cloud Redis (分布式缓存/云缓存 Redis) is a high-performance distributed cache service compatible with open-source Redis protocol. It provides elastic, scalable, and reliable caching capabilities with automatic failover, data backup, and online scaling. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **dual-path execution** (official **SDK/API** and official **`jdc` CLI**), response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** Official `jdc` supports this product. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the SDK step **and** the `jdc` step for every operation the CLI exposes. The CLI covers most common Redis instance operations (create, describe, modify, delete, backup, restore, etc.).

### Path Preference (SDK vs CLI)

When both paths are available:

- **Prefer SDK** when:
  - Complex multi-step workflows with conditional logic
  - Python application integration or scripts
  - CI/CD pipelines with Python tooling
  - Need for advanced error handling and retry logic
  - Integration tests or automated verification

- **Prefer CLI (`jdc`)** when:
  - Quick ad-hoc operations from terminal
  - No Python runtime available in environment
  - Shell script automation or bash pipelines
  - Simple single-operation tasks
  - Debugging or troubleshooting from command line

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
| 1.0.1 | 2026-05-03 | Added safety gates for Delete/Restore/Modify operations; added Path Preference section |
| 1.0.0 | 2026-05-03 | Initial version with API/SDK and `jdc` CLI dual-path support |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK/API and `jdc`) → Validate → Recover**. Do not skip phases.

### Operation: Create Redis Instance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | Import `jdcloud_sdk.services.redis.client.RedisClient` | No import error | Document install pin |
| CLI / deps | `jdc --version` | Exit code 0 | Document CLI install / `jdc config init` |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Call `describeAvailableRegion` API | `{{user.region}}` supported | Suggest valid region |
| VPC/Subnet | Verify subnet via `jdcloud-vpc-ops` | Subnet exists and has IP | HALT; create subnet first |
| Instance Class | Call `describeInstanceClass` or `describeSpecConfig` | Valid spec code | Suggest available specs |

#### Execution (Python SDK — illustrative)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.redis.client import RedisClient
from jdcloud_sdk.services.redis.apis.create_cache_instance_request import CreateCacheInstanceRequest

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = RedisClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

# Build AzIdSpec and CacheInstanceSpec per API spec
az_spec = {
    "azSpecifyType": "SpecifyByReplicaGroup",
    "master": "{{user.az_master}}",
    "slave": "{{user.az_slave}}"
}

cache_instance_spec = {
    "cacheInstanceName": "{{user.instance_name}}",
    "cacheInstanceClass": "{{user.instance_class}}",  # e.g., "redis.cluster.g.micro"
    "vpcId": "{{user.vpc_id}}",
    "subnetId": "{{user.subnet_id}}",
    "azIdSpec": az_spec,
    "cacheInstanceType": "{{user.cache_instance_type}}",  # master-slave, cluster, native-cluster
    "redisVersion": "{{user.redis_version}}",  # 4.0, 5.0, 6.2
    # optional: dbNum, replicaNumber, password, etc.
}

req = CreateCacheInstanceRequest(regionId="{{user.region}}", cacheInstance=cache_instance_spec)
resp = client.create_cache_instance(req)
instance_id = resp.result.cacheInstanceId
```

#### Execution — CLI (`jdc`)

**Required** when `cli_applicability: dual-path`. Use `--output json` and non-interactive mode.

```bash
jdc redis create-cache-instance \
  --region-id "{{user.region}}" \
  --cache-instance-name "{{user.instance_name}}" \
  --cache-instance-class "{{user.instance_class}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --az-id-spec '{"azSpecifyType":"SpecifyByReplicaGroup","master":"{{user.az_master}}","slave":"{{user.az_slave}}"}' \
  --cache-instance-type "{{user.cache_instance_type}}" \
  --redis-version "{{user.redis_version}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

1. Capture `{{output.instance_id}}` from `$.result.cacheInstanceId`.
2. Poll `describeCacheInstance` until `status` == `running` or timeout.

```python
# SDK poll loop
for _ in range(60):
    dresp = client.describe_cache_instance(regionId="{{user.region}}", cacheInstanceId="{{output.instance_id}}")
    status = dresp.result.cacheInstance.status
    if status == "running":
        break
    if status in ["error", "deleted"]:
        raise RuntimeError(f"Instance creation failed: {status}")
    sleep(10)
```

```bash
# CLI poll loop
for i in $(seq 1 60); do
  STATUS=$(jdc redis describe-cache-instance \
    --region-id "{{user.region}}" \
    --cache-instance-id "{{output.instance_id}}" \
    --output json | jq -r '.result.cacheInstance.status')
  [ "$STATUS" = "running" ] && break
  sleep 10
done
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

#### Execution (SDK)

```python
from jdcloud_sdk.services.redis.apis.describe_cache_instance_request import DescribeCacheInstanceRequest

req = DescribeCacheInstanceRequest(regionId="{{user.region}}", cacheInstanceId="{{user.instance_id}}")
resp = client.describe_cache_instance(req)
# Access: resp.result.cacheInstance
```

#### Execution (CLI)

```bash
jdc redis describe-cache-instance \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
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

#### Execution (SDK)

```python
from jdcloud_sdk.services.redis.apis.describe_cache_instances_request import DescribeCacheInstancesRequest

req = DescribeCacheInstancesRequest(regionId="{{user.region}}", pageNumber=1, pageSize=100)
resp = client.describe_cache_instances(req)
instances = resp.result.cacheInstances
```

#### Execution (CLI)

```bash
jdc redis describe-cache-instances \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100 \
  --output json
```

### Operation: Modify Redis Instance

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Instance exists | `describeCacheInstance` | Instance found | HALT; verify instance ID |
| Instance state | `describeCacheInstance` | `running` | Wait or suggest appropriate action |

**⚠️ For `modifyCacheInstanceClass` (scaling)**: Confirm with user as it may cause brief service interruption.

#### Execution (SDK)

```python
from jdcloud_sdk.services.redis.apis.modify_cache_instance_attribute_request import ModifyCacheInstanceAttributeRequest

req = ModifyCacheInstanceAttributeRequest(
    regionId="{{user.region}}",
    cacheInstanceId="{{user.instance_id}}",
    cacheInstanceName="{{user.new_name}}"  # optional fields per API
)
resp = client.modify_cache_instance_attribute(req)
```

#### Execution (CLI)

```bash
jdc redis modify-cache-instance-attribute \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --cache-instance-name "{{user.new_name}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

Poll describe until modification reflects (depends on modification type).

### Operation: Delete Redis Instance

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.instance_name}}` (`{{user.instance_id}}`).
- **MUST NOT** proceed without clear user assent.

#### Execution (SDK)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before calling SDK delete method.

```python
from jdcloud_sdk.services.redis.apis.delete_cache_instance_request import DeleteCacheInstanceRequest

# Confirm deletion with user: "Are you sure you want to delete {{user.instance_name}} ({{user.instance_id}})? This is IRREVERSIBLE."
# Proceed only after explicit "yes" / "confirm" response

req = DeleteCacheInstanceRequest(regionId="{{user.region}}", cacheInstanceId="{{user.instance_id}}")
resp = client.delete_cache_instance(req)
```

#### Execution (CLI)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
# Confirm deletion with user first
jdc redis delete-cache-instance \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

Poll `describeCacheInstance` until HTTP 404 / `status` indicates deleted (max 600s).

### Operation: Backup Redis Instance

#### Execution (SDK)

```python
from jdcloud_sdk.services.redis.apis.create_backup_request import CreateBackupRequest

req = CreateBackupRequest(regionId="{{user.region}}", cacheInstanceId="{{user.instance_id}}")
resp = client.create_backup(req)
backup_id = resp.result.backupId
```

#### Execution (CLI)

```bash
jdc redis create-backup \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json \
  --no-interactive
```

### Operation: Restore Redis Instance

#### Pre-flight (Safety Gate)

- **MUST** warn user: Restore will overwrite current data in `{{user.instance_name}}` (`{{user.instance_id}}`) with backup `{{user.backup_id}}`.
- **MUST** obtain explicit confirmation before proceeding.

#### Execution (SDK)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before calling SDK restore method.

```python
from jdcloud_sdk.services.redis.apis.restore_instance_request import RestoreInstanceRequest

# Confirm restore with user: "Restoring backup {{user.backup_id}} will overwrite current data. Are you sure?"
# Proceed only after explicit "yes" / "confirm" response

req = RestoreInstanceRequest(
    regionId="{{user.region}}",
    cacheInstanceId="{{user.instance_id}}",
    backupId="{{user.backup_id}}"
)
resp = client.restore_instance(req)
```

#### Execution (CLI)

**⚠️ Safety Gate**: MUST obtain explicit user confirmation before executing CLI command.

```bash
# Confirm restore with user first
jdc redis restore-instance \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --backup-id "{{user.backup_id}}" \
  --output json \
  --no-interactive
```

## Prerequisites

1. **Install** JD Cloud SDK and CLI:
   ```bash
   pip install jdcloud-sdk
   pip install jdcloud_cli
   jdc config init
   ```

2. **Configure Credentials** — Three methods:

   **Method 1: `.env` File (Recommended for Local Development)**
   ```ini
   JDC_ACCESS_KEY=your_access_key_here
   JDC_SECRET_KEY=your_secret_key_here
   JDC_REGION=cn-north-1
   ```
   > Agent Runtime auto-loads `.env` if present.

   **Method 2: Shell Environment Variables**
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```

   **Method 3: CLI Interactive Config**
   ```bash
   jdc config init
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