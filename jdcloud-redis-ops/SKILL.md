---
name: jdcloud-redis-ops
description: >-
  Manages JD Cloud Redis (JCS for Redis) resources. Use when you need to deploy, 
  configure, troubleshoot, or monitor Redis cache instances on JD Cloud.
  Includes CLI usage, SDK integration, and operational best practices.
license: MIT
compatibility: Requires jdcloud-cli, Python 3.10+, and JD Cloud account credentials
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-04-30"
  runtime: Harness AI Agent
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification) specification.

# JD Cloud Redis Operations Skill

## Overview
JD Cloud Cache Redis (JCS for Redis) is a high-performance online caching service based on Redis protocol. It provides automatic disaster recovery, data backup, online scaling, and instance monitoring. This skill enables efficient operations of Redis cache instances, including automated deployment, configuration management, performance monitoring, and rapid troubleshooting.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "JD Cloud Redis" OR "云缓存Redis" OR "JCS for Redis" OR "distributed cache"
- Task involves CRUD operations on Redis instances: create, describe, modify, delete, list
- Task involves Redis instance management: backup, restore, resize, password reset, whitelist configuration
- Task keywords: create-cache-instance, describe-cache-instances, modify-cache-instance-class, delete-cache-instance
- User asks to deploy, configure, troubleshoot, or monitor Redis cache resources

### SHOULD NOT Use This Skill When
- Task is about monitoring metrics / alarms for Redis → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about VPC / subnet / security group creation → delegate to: `jdcloud-vpc-ops`
- Task is about VM instance management → delegate to: `jdcloud-vm-ops`
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`
- Task is about Redis command syntax (GET, SET, etc.) → this is application-level, not infrastructure

### Delegation Rules
- If the user asks "why is my Redis slow / high memory", use this Skill to describe the instance, then suggest `jdcloud-cloudmonitor-ops` for metrics data
- If user wants a Redis instance in a new VPC, suggest creating VPC first via `jdcloud-vpc-ops`, then return here
- If user asks about Redis application code (Jedis, Lettuce, etc.), provide guidance but note this is outside infrastructure scope

## Variable Convention (Agent-Readable)
This Skill uses structured placeholders to avoid prompt injection and parsing ambiguity:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | Resolved from Agent runtime environment | NEVER prompt user for this; fail if not set |
| `{{env.JDC_SECRET_KEY}}` | Resolved from Agent runtime environment | NEVER prompt user for this; fail if not set |
| `{{env.JDC_REGION}}` | Resolved from Agent runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | Must be collected from user | Ask user once and reuse |
| `{{user.instance_id}}` | Must be collected from user | Ask user once and reuse |
| `{{user.instance_name}}` | Must be collected from user | Ask user once and reuse |
| `{{user.spec}}` | Must be collected from user (e.g., redis.sw.1g) | Ask user once and reuse |
| `{{output.instance_id}}` | Captured from CLI JSON output | Parse from `$.result.instanceId` |

> Rule: Placeholders wrapped in `{{env.*}}` MUST NOT be exposed to or requested from the user. Placeholders wrapped in `{{user.*}}` MUST be collected interactively.

## Output Parsing Rules (Agent-Readable)

### Mandatory CLI Conventions
- All CLI commands MUST append `--output json` for machine-parseable output
- All CLI commands SHOULD append `--no-interactive` (or equivalent) to prevent blocking on user prompts
- Timestamps are in ISO 8601 format with timezone: `2026-04-28T10:00:00+08:00`
- Resource IDs follow pattern: `jcs-redis-[hash]` for instances
- Boolean values: `true` / `false` (lowercase)
- Redis versions: `4.0`, `5.0`, `6.2`

### Key JSON Paths for Common Operations
| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create | `$.result.instanceId` | string | Instance ID to track |
| Describe | `$.result.cacheInstance.status` | string | Current state (creating, running, changing, deleted) |
| List | `$.result.cacheInstances[*].instanceId` | array | All instance IDs |
| Modify | `$.requestId` | string | Non-empty means accepted |
| Delete | `$.requestId` | string | Non-empty means accepted |

### Expected State Transitions
| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | - | `running` | 10s | 600s |
| Resize | `running` | `running` | 10s | 900s |
| Restart | `running` | `running` | 10s | 300s |
| Delete | `running` | (404 on describe) | 10s | 300s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-30 | Initial version, includes Redis instance lifecycle management, backup/restore, configuration, and monitoring guide |

## Execution Flows (Agent-Readable)
Every operation follows the pattern: Pre-flight → Execute → Validate → Recover. The Agent MUST NOT skip any phase.

### Operation: Create Redis Instance

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| CLI installed | `jdc --version` | exit code 0 | Guide user to install jdcloud-cli |
| Credentials valid | `jdc config validate --output json` | `$.valid == true` | Prompt user to run `jdc config init` |
| Region available | `jdc redis describe-available-region --output json` | `{{user.region}}` in list | Suggest nearest available region |
| Spec available | `jdc redis describe-spec-config --region-id {{user.region}} --output json` | `{{user.spec}}` in list | Suggest available specs |
| VPC/Subnet exists | `jdc vpc describe-vpc --region-id {{user.region}} --vpc-id {{user.vpc_id}} --output json` | returns VPC | Suggest creating VPC first |
| Quota available | `jdc redis describe-user-quota --region-id {{user.region}} --output json` | `$.result.available > 0` | Inform user of quota limit |

#### Execution
```bash
jdc redis create-cache-instance \
  --region-id {{user.region}} \
  --az-id "{{user.az_id}}" \
  --cache-instance-name "{{user.instance_name}}" \
  --instance-class "{{user.spec}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --password "{{user.password}}" \
  --redis-version "{{user.redis_version}}" \
  --charge-mode "postpaid_by_duration" \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Capture `{{output.instance_id}}` from `$.result.instanceId`
2. Poll until ready:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc redis describe-cache-instance \
       --region-id {{user.region}} \
       --cache-instance-id {{output.instance_id}} \
       --output json | jq -r '.result.cacheInstance.status')
     [ "$STATUS" = "running" ] && break
     sleep 10
   done
   ```
3. If status is `running` → operation succeeded, report instance ID and connection info to user
4. If status is `error` → capture error, go to Failure Recovery

#### Failure Recovery
| Exit Code | Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|-----------|-----------------------|-------------|---------|--------------|
| 1 | `InvalidParameter` | 1 | - | Re-check parameter format against API spec, retry with corrected params |
| 1 | `QuotaExceeded` | 0 | - | HALT. Inform user quota is full, suggest requesting increase |
| 1 | `InsufficientBalance` | 0 | - | HALT. Inform user to top up account |
| 2 | `ResourceAlreadyExists` | 0 | - | Ask user if they want to reuse existing instance or use a different name |
| 2 | `InsufficientResource` | 1 | - | Suggest switching to another AZ via `jdc redis describe-available-resource` |
| 3 | `InternalError` | 3 | 2s, 4s, 8s | Retry with exponential backoff. After 3rd failure, report to user |
| Other | `.*` | 3 | 5s, 10s, 15s | Retry. On final failure, extract full error message and present to user |

### Operation: Describe Redis Instance

#### Execution
```bash
jdc redis describe-cache-instance \
  --region-id {{env.JDC_REGION}} \
  --cache-instance-id {{user.instance_id}} \
  --output json
```

#### Output to Present to User
| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| ID | `$.result.cacheInstance.instanceId` | Plain text |
| Name | `$.result.cacheInstance.cacheInstanceName` | Plain text |
| Status | `$.result.cacheInstance.status` | Badge: 🟢 running / 🟡 creating / 🔴 error / ⚪ stopped |
| Spec | `$.result.cacheInstance.instanceClass` | Plain text (e.g., redis.sw.1g) |
| Version | `$.result.cacheInstance.redisVersion` | Plain text (e.g., 6.2) |
| Connection | `$.result.cacheInstance.connectionDomain` | Plain text |
| Port | `$.result.cacheInstance.connectionPort` | Plain text |
| Memory | `$.result.cacheInstance.capacityMB` | Plain text (MB) |
| Created At | `$.result.cacheInstance.createTime` | ISO 8601 → human-readable |

### Operation: Resize Redis Instance

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to resize `{{user.instance_name}}` ({{user.instance_id}}) from `{{user.current_spec}}` to `{{user.target_spec}}`? This may cause brief connection interruption."
- **MUST** wait for explicit "yes" / "confirm" before proceeding
- **MUST** verify target spec is compatible with current architecture

#### Execution
```bash
jdc redis modify-cache-instance-class \
  --region-id {{env.JDC_REGION}} \
  --cache-instance-id {{user.instance_id}} \
  --instance-class "{{user.target_spec}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Poll until status returns to `running` (max 900s)
2. Verify new spec is applied: `describe-cache-instance` and check `instanceClass`

### Operation: Delete Redis Instance

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to delete Redis instance `{{user.instance_name}}` ({{user.instance_id}})? This is IRREVERSIBLE and all data will be lost."
- **MUST** wait for explicit "yes" / "confirm" before proceeding
- **SHOULD** suggest creating a backup first: `jdc redis create-backup`

#### Execution
```bash
jdc redis delete-cache-instance \
  --region-id {{env.JDC_REGION}} \
  --cache-instance-id {{user.instance_id}} \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Poll `describe-cache-instance` until HTTP 404 or status shows deleted (max 300s)

### Operation: Create Backup

#### Execution
```bash
jdc redis create-backup \
  --region-id {{env.JDC_REGION}} \
  --cache-instance-id {{user.instance_id}} \
  --backup-name "{{user.backup_name}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Verify backup created: `jdc redis describe-backups --region-id {{env.JDC_REGION}} --cache-instance-id {{user.instance_id}} --output json`
2. Check backup status in `$.result.backups[*].status`

### Operation: Reset Password

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to reset the password for `{{user.instance_name}}`? All existing connections will be disconnected."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution
```bash
jdc redis reset-cache-instance-password \
  --region-id {{env.JDC_REGION}} \
  --cache-instance-id {{user.instance_id}} \
  --new-password "{{user.new_password}}" \
  --output json \
  --no-interactive
```

## Prerequisites
1. **Install JD Cloud CLI**:
   ```bash
   pip install jdcloud-cli
   jdc config init
   ```

2. **Configure Credentials**:
   
   The Agent runtime MUST have the following environment variables set. These map to `{{env.*}}` placeholders used throughout this Skill:
   
   | Variable | Description | Required | Agent Behavior |
   |----------|-------------|----------|----------------|
   | `{{env.JDC_ACCESS_KEY}}` | JD Cloud Access Key | Yes | Resolved from runtime environment, NEVER ask the user |
   | `{{env.JDC_SECRET_KEY}}` | JD Cloud Secret Key | Yes | Resolved from runtime environment, NEVER ask the user |
   | `{{env.JDC_REGION}}` | Default region ID | No | Default `cn-north-1` |
   
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```
   
   > The Agent MUST verify these are set before any operation. If missing, instruct user to configure via `jdc config init`.
   > ⚠️ **Security Note**: Do not hardcode credentials in code or configuration files. Use `{{env.*}}` placeholders injected by the Agent harness.

## Reference Directory
- [Core Concepts](references/core-concepts.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration (MCP/SDK)](references/integration.md)

## Operational Best Practices
- **High Availability**: Use cluster or master-slave architecture for production workloads
- **Security**: Enable whitelist, use strong passwords, and apply IAM policies with least privilege
- **Memory Management**: Monitor memory usage, avoid big keys, and configure maxmemory-policy appropriately
- **Backup Strategy**: Schedule regular backups and test restore procedures
- **Performance**: Use connection pooling, avoid blocking commands (KEYS, FLUSHALL), and monitor slow logs
- **Cost Optimization**: Right-size instances based on actual usage, consider reserved instances for stable workloads
- **Monitoring**: Set up alerts for memory usage, CPU, connections, and replication lag
