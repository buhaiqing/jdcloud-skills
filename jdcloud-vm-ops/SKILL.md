---
name: jdcloud-vm-ops
description: >-
  Manages JD Cloud Virtual Machine resources. Use when you need to deploy, 
  configure, troubleshoot, or monitor VM instances on JD Cloud.
  Includes CLI usage, SDK integration, and operational best practices.
---

# JD Cloud VM Operations Skill

## Overview
JD Cloud Virtual Machine (VM) is a core computing service that provides elastic, scalable, and secure cloud servers. This skill enables efficient operations, including automated deployment, real-time monitoring, and rapid troubleshooting of VM resources.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "JD Cloud VM" OR "云主机" OR "Virtual Machine" OR "CVM" OR "VM"
- Task involves CRUD operations on VM instances: create, describe, start, stop, reboot, delete, resize
- Task involves image management, disk management, keypair management
- Task keywords: create-instances, describe-instances, start-instance, stop-instance, delete-instance

### SHOULD NOT Use This Skill When
- Task is about monitoring metrics / alarms for VMs → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about VPC / subnet / security group creation → delegate to: `jdcloud-vpc-ops`
- Task is about load balancer configuration → delegate to: `jdcloud-lb-ops`
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`

### Delegation Rules
- If user asks "why is my VM slow / high CPU", use this Skill to describe the VM, then suggest `jdcloud-cloudmonitor-ops` for metrics data
- If user wants a VM in a new VPC, suggest creating VPC first via `jdcloud-vpc-ops`, then return here

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
| `{{output.instance_id}}` | Captured from CLI JSON output | Parse from `$.result.instanceIds[0]` |

> Rule: Placeholders wrapped in `{{env.*}}` MUST NOT be exposed to or requested from the user. Placeholders wrapped in `{{user.*}}` MUST be collected interactively.

## Output Parsing Rules (Agent-Readable)

### Mandatory CLI Conventions
- All CLI commands MUST append `--output json` for machine-parseable output
- All CLI commands SHOULD append `--no-interactive` (or equivalent) to prevent blocking on user prompts
- Timestamps are in ISO 8601 format with timezone: `2026-04-28T10:00:00+08:00`
- Resource IDs follow pattern: `i-[hash]` for instances, `img-[hash]` for images, `vol-[hash]` for disks

### Key JSON Paths for Common Operations
| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create | `$.result.instanceIds[0]` | string | Instance ID to track |
| Describe | `$.result.instances[0].status` | string | Current state (running, stopped, etc.) |
| List | `$.result.instances[*].instanceId` | array | All instance IDs |
| Start/Stop | `$.requestId` | string | Non-empty means accepted |

### Expected State Transitions
| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | - | `running` | 5s | 300s |
| Start | `stopped` | `running` | 5s | 120s |
| Stop | `running` | `stopped` | 5s | 120s |
| Reboot | `running` | `running` | 5s | 180s |
| Delete | `running`/`stopped` | (404 on describe) | 5s | 300s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-28 | Initial version, includes basic operational guide and reference templates |
| 1.0.1 | 2026-04-28 | Added VM instance management, network configuration, and security group operations guide |

## Execution Flows (Agent-Readable)
Every operation follows the pattern: Pre-flight → Execute → Validate → Recover. The Agent MUST NOT skip any phase.

### Operation: Create VM Instance

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| CLI installed | `jdc --version` | exit code 0 | Guide user to install jdcloud-cli |
| Credentials valid | `jdc config validate --output json` | `$.valid == true` | Prompt user to run `jdc config init` |
| Instance types available | `jdc vm describe-instance-types --region-id {{user.region}} --output json` | list non-empty | Suggest another region |
| Image exists | `jdc vm describe-images --region-id {{user.region}} --image-ids '["{{user.image_id}}"]' --output json` | returns image | Suggest available public image |
| Subnet exists | `jdc vpc describe-subnet --region-id {{user.region}} --subnet-id {{user.subnet_id}} --output json` | returns subnet | Suggest creating subnet first |

#### Execution
```bash
jdc vm create-instances \
  --region-id {{user.region}} \
  --az "{{user.az}}" \
  --instance-type "{{user.instance_type}}" \
  --image-id "{{user.image_id}}" \
  --name "{{user.instance_name}}" \
  --primary-network-interface "{\"subnetId\":\"{{user.subnet_id}}\",\"securityGroupIds\":[\"{{user.sg_id}}\"]}" \
  --system-disk "{\"diskCategory\":\"cloud_ssd\",\"diskSizeGB\":{{user.disk_size}}}" \
  --charge-mode "postpaid_by_duration" \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Capture `{{output.instance_id}}` from `$.result.instanceIds[0]`
2. Poll until running:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc vm describe-instances \
       --region-id {{user.region}} \
       --instance-ids '["{{output.instance_id}}"]' \
       --output json | jq -r '.result.instances[0].status')
     [ "$STATUS" = "running" ] && break
     sleep 5
   done
   ```
3. If status is `running` → operation succeeded, report instance ID, public IP, private IP to user
4. If status is `error` → capture error from `$.result.instances[0].errorMessage`, go to Failure Recovery

#### Failure Recovery
| Exit Code | Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|-----------|-----------------------|-------------|---------|--------------|
| 1 | `InvalidParameter` | 1 | - | Re-check parameter format, retry with corrected params |
| 1 | `QuotaExceeded` | 0 | - | HALT. Inform user quota is full, suggest requesting increase |
| 1 | `InsufficientBalance` | 0 | - | HALT. Inform user to top up account |
| 1 | `InsufficientResource` | 1 | - | Suggest switching to another AZ via `jdc vm describe-azs` |
| 3 | `InternalError` | 3 | 2s, 4s, 8s | Retry with exponential backoff. After 3rd failure, report to user |
| Other | `.*` | 3 | 5s, 10s, 15s | Retry. On final failure, extract full error message and present to user |

### Operation: Describe VM Instance

#### Execution
```bash
jdc vm describe-instances \
  --region-id {{env.JDC_REGION}} \
  --instance-ids '["{{user.instance_id}}"]' \
  --output json
```

#### Output to Present to User
| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| ID | `$.result.instances[0].instanceId` | Plain text |
| Name | `$.result.instances[0].name` | Plain text |
| Status | `$.result.instances[0].status` | Badge: 🟢 running / 🟡 starting / 🔴 stopped |
| Type | `$.result.instances[0].instanceType` | Plain text |
| Private IP | `$.result.instances[0].primaryNetworkInterface.privateIpAddress` | Plain text |
| Public IP | `$.result.instances[0].primaryNetworkInterface.elasticIp.publicIpAddress` | `-` if null |

### Operation: Stop VM Instance

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to stop `{{user.instance_name}}` ({{user.instance_id}})? Running services will be interrupted."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution
```bash
jdc vm stop-instance \
  --region-id {{env.JDC_REGION}} \
  --instance-id {{user.instance_id}} \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Poll until status == `stopped` (max 120s)

### Operation: Delete VM Instance

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to delete `{{user.instance_name}}` ({{user.instance_id}})? This is IRREVERSIBLE and will release all associated resources."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution
```bash
jdc vm delete-instance \
  --region-id {{env.JDC_REGION}} \
  --instance-id {{user.instance_id}} \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Poll `describe-instances` until HTTP 404 (max 300s)

## Prerequisites
1. **Install JD Cloud CLI**:
   ```bash
   # Install JD Cloud CLI
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
- **High Availability**: Always deploy across multiple availability zones.
- **Security**: Apply least-privilege IAM policies and regularly update security groups.
- **Cost Optimization**: Utilize auto-scaling and reserved instances where applicable.
- **Backup Strategy**: Regularly create snapshots of critical VM instances.
- **Resource Tagging**: Tag VM resources for better organization and cost tracking.
