---
name: jdcloud-mongodb-ops
description: >-
  Use when you need to deploy, configure, troubleshoot, or monitor JD Cloud
  MongoDB instances via official API/SDK or official `jdc` CLI; user mentions
  MongoDB, 云数据库 MongoDB, JCS for MongoDB, or tasks target MongoDB instances
  (replica sets or sharded clusters).
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network access to
  JD Cloud endpoints, and official JD Cloud CLI (`jdc`) for MongoDB operations.
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-05-03"
  runtime: Harness AI Agent
  api_profile: "JCS for MongoDB API v1.0"
  cli_applicability: dual-path
  cli_support_evidence: >-
    Confirmed via `jdc --help` showing mongodb in product list and official JD
    Cloud CLI documentation. Full CLI coverage for MongoDB instance lifecycle
    operations.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud MongoDB Operations Skill

## Overview

JD Cloud MongoDB (JCS for MongoDB) is a high-performance NoSQL database service based on MongoDB protocol, supporting both replica set and sharded cluster architectures. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **dual-path execution** (official **SDK/API** and official **`jdc` CLI**), response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### Supported MongoDB Versions

- **MongoDB 3.6**: Stable version with basic features
- **MongoDB 4.0**: Recommended version with enhanced features and performance

### Deployment Architectures

- **Replica Set (副本集)**: 3-node architecture with automatic failover, suitable for most production workloads
- **Sharded Cluster (分片集群)**: Horizontal scaling with multiple shards, suitable for large-scale data and high throughput scenarios

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** Official `jdc` supports MongoDB operations. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the SDK step **and** the `jdc` step for every operation the CLI exposes.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud MongoDB" OR "云数据库 MongoDB" OR "JCS for MongoDB" OR "MongoDB 实例"
- Task involves CRUD or lifecycle operations on **MongoDB instances** (create, describe, modify, delete, list, backup, restore)
- Task involves MongoDB instance management: backup, restore, resize, password reset, whitelist configuration, node management
- Task keywords: create-mongodb-instance, describe-mongodb-instances, modify-mongodb-instance-spec, delete-mongodb-instance, replica-set, sharded-cluster
- User asks to deploy, configure, troubleshoot, or monitor MongoDB resources **via API, SDK, CLI, or automation**

### SHOULD NOT Use This Skill When

- Task is about monitoring metrics / alarms for MongoDB → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about VPC / subnet creation → delegate to: `jdcloud-vpc-ops`
- Task is about VM instance management → delegate to: `jdcloud-vm-ops`
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`
- Task is about MongoDB query syntax or application-level operations (find, update, aggregate) → this is database usage, not infrastructure
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If user wants a MongoDB instance in a new VPC, suggest creating VPC first via `jdcloud-vpc-ops`, then return here
- If user asks "why is my MongoDB slow / high CPU", use this Skill to describe the instance, then suggest `jdcloud-cloudmonitor-ops` for metrics data
- If user asks about MongoDB application code (MongoDB driver, connection strings), provide guidance but note this is outside infrastructure scope

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.instance_id}}` | MongoDB instance ID | Ask once; reuse |
| `{{user.instance_name}}` | MongoDB instance name | Ask once; reuse |
| `{{user.spec}}` | Instance spec (e.g., mongodb.s.1.small) | Ask once; reuse |
| `{{user.mongo_version}}` | MongoDB version (3.6 or 4.0) | Ask once; reuse |
| `{{user.architecture}}` | Deployment type (replica-set or sharded-cluster) | Ask once; reuse |
| `{{output.instance_id}}` | From last API or CLI JSON response | Parse per OpenAPI or verified `jdc --output json` path |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes.
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-05-03T10:00:00+08:00`).
- **Idempotency:** Document client request tokens, duplicate names, and `ResourceAlreadyExists` behavior per API.

### Example Response Field Table

| Operation | JSON Path (example) | Type | Description |
|-----------|---------------------|------|-------------|
| Create | `$.result.instanceId` | string | New MongoDB instance ID |
| Describe | `$.result.instance.status` | string | Lifecycle state (creating, running, changing, deleted) |
| List | `$.result.instances[*].instanceId` | array | All instance IDs |
| Modify | `$.requestId` | string | Non-empty means accepted |
| Delete | `$.requestId` | string | Non-empty means accepted |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | — | `running` | 10s | 600s |
| Modify Spec | `running` | `running` | 10s | 900s |
| Restart | `running` | `running` | 10s | 300s |
| Delete | `running` | (404 on describe) | 10s | 300s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-03 | Initial version, includes MongoDB instance lifecycle management, backup/restore, node management, and monitoring guide |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK/API and `jdc`) → Validate → Recover**. Do not skip phases.

**Preference hint:** When both paths exist, use SDK for integration tests and batch operations; use `jdc` for quick ad-hoc operations and when Python runtime is unavailable.

### Operation: Create MongoDB Instance (Replica Set)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | Import client; version matches metadata | No import error | Document install pin in `references/integration.md` |
| CLI / deps | `jdc --version` | Exit code 0 | Document CLI install / `jdc config init` |
| Credentials | Construct credential from env or CLI config | Non-empty keys / valid config | HALT; user configures env |
| Region | `jdc mongodb describe-available-zones --region-id {{user.region}} --output json` | `{{user.region}}` supported | Suggest valid region |
| Spec | `jdc mongodb describe-flavors --region-id {{user.region}} --output json` | `{{user.spec}}` in list | Suggest available specs |
| VPC/Subnet | `jdc vpc describe-vpc --vpc-id {{user.vpc_id}} --output json` | returns VPC | Suggest creating VPC first via `jdcloud-vpc-ops` |
| Quota | Check account quota (via describe user quota if available) | Sufficient quota | HALT; user raises quota |

#### Execution (Python SDK — illustrative)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.mongodb.client import MongodbClient
from jdcloud_sdk.services.mongodb.apis.CreateInstanceRequest import CreateInstanceRequest

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = MongodbClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

req = CreateInstanceRequest(
    regionId="{{user.region}}",
    instanceName="{{user.instance_name}}",
    instanceClass="{{user.spec}}",
    engineVersion="{{user.mongo_version}}",
    vpcId="{{user.vpc_id}}",
    subnetId="{{user.subnet_id}}",
    azId="{{user.az_id}}",
    # Additional parameters per OpenAPI spec
)
resp = client.create_instance(req)
```

#### Execution — CLI (`jdc`)

**Use the [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)**. Every command MUST use **`--output json`** and **non-interactive mode**.

```bash
jdc mongodb create-instance \
  --region-id "{{user.region}}" \
  --instance-name "{{user.instance_name}}" \
  --instance-class "{{user.spec}}" \
  --engine-version "{{user.mongo_version}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --az-id "{{user.az_id}}" \
  --charge-mode "postpaid_by_duration" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

1. Read `{{output.instance_id}}` from `$.result.instanceId` (SDK) or CLI JSON output.
2. Poll **Describe** until terminal success state or timeout:

```python
# SDK polling (illustrative)
for _ in range(60):
    dresp = client.describe_instances(describe_request)
    status = parse_status(dresp)  # per OpenAPI
    if status == "running":
        break
    if status in ["error", "deleted"]:
        raise RuntimeError(parse_error(dresp))
    sleep(10)
```

```bash
# CLI polling
for i in $(seq 1 60); do
  STATUS=$(jdc mongodb describe-instances \
    --region-id "{{user.region}}" \
    --instance-id "{{output.instance_id}}" \
    --output json | jq -r '.result.instance.status')
  [ "$STATUS" = "running" ] && break
  sleep 10
done
```

3. On success, report instance ID, connection domain, and ports to the user.
4. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern (from API/SDK or CLI) | Max retries | Backoff | Agent Action |
|------------------------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 1 | — | Fix args from OpenAPI; retry once if safe |
| `QuotaExceeded` | 0 | — | HALT; user raises quota |
| `InsufficientBalance` | 0 | — | HALT; user tops up account |
| `ResourceAlreadyExists` | 0 | — | Ask reuse vs new name |
| Throttling / 429 | 3 | exponential | Back off; respect `Retry-After` |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; then HALT with requestId |

### Operation: Create MongoDB Instance (Sharded Cluster)

#### Pre-flight Checks

Same as replica set, but verify sharding support in the selected region and spec.

#### Execution — CLI

```bash
jdc mongodb create-sharding-instance \
  --region-id "{{user.region}}" \
  --instance-name "{{user.instance_name}}" \
  --engine-version "{{user.mongo_version}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --mongos-spec "{{user.mongos_spec}}" \
  --mongos-node-num "{{user.mongos_nodes}}" \
  --shard-spec "{{user.shard_spec}}" \
  --shard-node-num "{{user.shard_nodes}}" \
  --shard-storage "{{user.shard_storage}}" \
  --config-server-spec "{{user.config_spec}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

Poll until `running` state (max 900s for sharded clusters).

### Operation: Describe MongoDB Instance

#### Execution

```bash
jdc mongodb describe-instances \
  --region-id "{{env.JDC_REGION}}" \
  --instance-id "{{user.instance_id}}" \
  --output json
```

#### Present to User

| Field | Path (example) | Notes |
|-------|----------------|-------|
| Instance ID | `$.result.instance.instanceId` | Plain text |
| Instance Name | `$.result.instance.instanceName` | Plain text |
| Status | `$.result.instance.status` | Badge: 🟢 running / 🟡 creating / 🔴 error |
| Architecture | `$.result.instance.instanceType` | replica-set or sharded-cluster |
| Engine Version | `$.result.instance.engineVersion` | 3.6 or 4.0 |
| Connection Domain | `$.result.instance.connectionDomain` | Internal connection address |
| Port | `$.result.instance.port` | Default 27017 |
| Created Time | `$.result.instance.createTime` | ISO 8601 format |

### Operation: Modify Instance Specification

#### Pre-flight (Safety Gate)

- **MUST** ask user: "Are you sure you want to resize MongoDB instance `{{user.instance_name}}` (`{{user.instance_id}}`) from `{{user.current_spec}}` to `{{user.target_spec}}`? This may cause brief connection interruption."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution — CLI

```bash
jdc mongodb modify-instance-spec \
  --region-id "{{env.JDC_REGION}}" \
  --instance-id "{{user.instance_id}}" \
  --instance-class "{{user.target_spec}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

Poll until status returns to `running` (max 900s).

### Operation: Restart MongoDB Instance

#### Pre-flight (Safety Gate)

- **MUST** ask user: "Are you sure you want to restart MongoDB instance `{{user.instance_name}}` (`{{user.instance_id}}`)? This will temporarily interrupt service."
- **MUST** wait for explicit confirmation

#### Execution — CLI

```bash
jdc mongodb restart-instance \
  --region-id "{{env.JDC_REGION}}" \
  --instance-id "{{user.instance_id}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

Poll until `running` state (max 300s).

### Operation: Delete MongoDB Instance

#### Pre-flight (Safety Gate)

- **MUST** ask user: "Are you sure you want to delete MongoDB instance `{{user.instance_name}}` (`{{user.instance_id}}`)? This is **IRREVERSIBLE** and all data will be lost."
- **MUST** wait for explicit "yes" / "confirm" before proceeding
- **SHOULD** suggest creating a backup first

#### Execution — CLI

```bash
jdc mongodb delete-instance \
  --region-id "{{env.JDC_REGION}}" \
  --instance-id "{{user.instance_id}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

Poll describe until HTTP 404 or deleted status (max 300s).

### Operation: Create Backup

#### Execution — CLI

```bash
jdc mongodb create-backup \
  --region-id "{{env.JDC_REGION}}" \
  --instance-id "{{user.instance_id}}" \
  --backup-name "{{user.backup_name}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation

Verify backup created via `jdc mongodb describe-backups`.

### Operation: Restore from Backup

#### Execution — CLI

```bash
jdc mongodb restore-instance \
  --region-id "{{env.JDC_REGION}}" \
  --instance-id "{{user.instance_id}}" \
  --backup-id "{{user.backup_id}}" \
  --output json \
  --no-interactive
```

### Operation: Reset Password

#### Pre-flight (Safety Gate)

- **MUST** ask user: "Are you sure you want to reset the password for MongoDB instance `{{user.instance_name}}`? All existing connections will be disconnected."
- **MUST** wait for explicit confirmation

#### Execution — CLI

```bash
jdc mongodb reset-password \
  --region-id "{{env.JDC_REGION}}" \
  --instance-id "{{user.instance_id}}" \
  --password "{{user.new_password}}" \
  --output json \
  --no-interactive
```

## Prerequisites

1. **Install JD Cloud SDK and CLI**:
   ```bash
   pip install jdcloud-sdk-python
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

   **Method 2: Shell Environment Variables (Production)**
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```

   **Method 3: CLI Interactive Config**
   ```bash
   jdc config init
   ```

   > Security: Never commit `.env` to version control.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **High Availability**: Use replica set or sharded cluster for production; avoid single-node deployments
- **Security**: Enable IP whitelist, use strong passwords, deploy in VPC, apply IAM policies
- **Backup Strategy**: Configure automated daily backups, test restore procedures regularly
- **Performance**: Right-size instances based on workload, monitor slow queries via SmartDBA
- **Cost Optimization**: Use reserved instances for stable workloads, monitor resource utilization
- **Monitoring**: Set up alerts for CPU, memory, connections, disk usage, and replication lag

---