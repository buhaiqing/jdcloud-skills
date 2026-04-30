---
name: jdcloud-vpc-ops
description: >-
  Manages JD Cloud Virtual Private Cloud (VPC) resources. Use when you need to deploy, 
  configure, troubleshoot, or monitor VPC instances on JD Cloud.
  Includes CLI usage, SDK integration, and operational best practices.
---

# JD Cloud Virtual Private Cloud (VPC) Operations Skill

## Overview
Virtual Private Cloud (VPC) is a core service on JD Cloud that provides isolated cloud resources within a virtual network. This skill enables efficient operations, including automated deployment, real-time monitoring, and rapid troubleshooting of VPC resources.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "JD Cloud VPC" OR "私有网络" OR "Virtual Private Cloud"
- Task involves CRUD operations on VPC resources: create, describe, modify, delete, list
- Task keywords: vpc, subnet, network acl, security group, route table, vpc peering, nat gateway
- User asks to deploy, configure, troubleshoot, or monitor VPC resources

### SHOULD NOT Use This Skill When
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`
- Task is about IAM / user permission management → delegate to: `jdcloud-iam-ops`
- Task is about load balancing → delegate to: `jdcloud-clb-ops`
- Task is about virtual machines → delegate to: `jdcloud-vm-ops`

### Delegation Rules
- If the user asks about resource B that depends on resource A created/managed here, create A first then suggest chaining to the B-specific Skill
- If the request spans multiple unrelated products, process each with its corresponding Skill independently

## Variable Convention (Agent-Readable)
This Skill uses structured placeholders to avoid prompt injection and parsing ambiguity:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | Resolved from Agent runtime environment | NEVER prompt user for this; fail if not set |
| `{{env.JDC_SECRET_KEY}}` | Resolved from Agent runtime environment | NEVER prompt user for this; fail if not set |
| `{{env.JDC_REGION}}` | Resolved from Agent runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | Must be collected from user | Ask user once and reuse |
| `{{user.vpc_name}}` | Must be collected from user | Ask user once and reuse |
| `{{user.subnet_name}}` | Must be collected from user | Ask user once and reuse |
| `{{output.vpc_id}}` | Captured from CLI JSON output | Parse from `$.data.vpcId` |
| `{{output.subnet_id}}` | Captured from CLI JSON output | Parse from `$.data.subnetId` |

> Rule: Placeholders wrapped in `{{env.*}}` MUST NOT be exposed to or requested from the user. Placeholders wrapped in `{{user.*}}` MUST be collected interactively.

## Output Parsing Rules (Agent-Readable)

### Mandatory CLI Conventions
- All CLI commands MUST append `--output json` for machine-parseable output
- All CLI commands SHOULD append `--no-interactive` (or equivalent) to prevent blocking on user prompts
- Timestamps are in ISO 8601 format with timezone: `2026-04-28T10:00:00+08:00`
- Resource IDs follow pattern: `[prefix]-[hash]` (e.g., `vpc-abc123def`)
- Boolean values: `true` / `false` (lowercase)

### Key JSON Paths for Common Operations
| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create VPC | `$.data.vpcId` | string | VPC ID to track |
| Create Subnet | `$.data.subnetId` | string | Subnet ID to track |
| Describe VPC | `$.data.status` | string | Current state (e.g. `running`, `stopped`) |
| List VPCs | `$.data[*].vpcId` | array | All VPC IDs |
| Modify VPC | `$.data.success` | boolean | Whether modification succeeded |
| Delete VPC | `$.data.success` | boolean | Whether deletion succeeded |

### Expected State Transitions
| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create VPC | - | `running` | 5s | 300s |
| Create Subnet | - | `running` | 5s | 300s |
| Delete VPC | `running` | (404 on describe) | 5s | 300s |
| Delete Subnet | `running` | (404 on describe) | 5s | 300s |

## Changelog

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0.0 | 2026-04-28 | 初始版本，包含VPC基础运维指南和参考模板 |

## Execution Flows (Agent-Readable)
Every operation follows the pattern: Pre-flight → Execute → Validate → Recover. The Agent MUST NOT skip any phase.

### Operation: Create VPC (Idempotent)

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| CLI installed | `jdc --version` | exit code 0 | Guide user to install jdcloud-cli |
| Credentials valid | `jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 1 --output json` | `$.error == null` | Prompt user to run `jdc config init` |
| Region available | `jdc vpc describe-regions --output json` | `{{user.region}}` in list | Suggest nearest available region |
| Quota available | `jdc vpc describe-quota --region {{user.region}} --output json` | `$.available > 0` | Inform user of quota limit, suggest increase |

#### Idempotent Execution
```bash
# Step 1: Check if VPC already exists (by name tag)
EXISTING_VPC=$(jdc vpc describe-vpcs \
  --region {{user.region}} \
  --output json | jq -r '.data[] | select(.vpcName == "{{user.vpc_name}}") | .vpcId' | head -n 1)

if [ -n "$EXISTING_VPC" ]; then
  echo "VPC '{{user.vpc_name}}' already exists with ID: $EXISTING_VPC"
  {{output.vpc_id}}="$EXISTING_VPC"
else
  # Step 2: Create new VPC
  CREATE_OUTPUT=$(jdc vpc create-vpc \
    --region {{user.region}} \
    --vpc-name "{{user.vpc_name}}" \
    --cidr-block "{{user.cidr_block}}" \
    --output json \
    --no-interactive)
  
  # Step 3: Extract VPC ID from output
  {{output.vpc_id}}=$(echo "$CREATE_OUTPUT" | jq -r '.data.vpcId')
fi
```

#### Post-execution Validation
1. Validate `{{output.vpc_id}}` is not empty
2. Poll until ready:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc vpc describe-vpc \
       --vpc-id {{output.vpc_id}} \
       --region {{user.region}} \
       --output json | jq -r '.data.status')
     [ "$STATUS" = "running" ] && break
     sleep 5
   done
   ```
3. If status is `running` → operation succeeded, report `{{output.vpc_id}}` to user
4. If status is `error` → capture error from `$.data.errorMessage`, go to Failure Recovery
5. **Idempotency Note**: If VPC already exists, operation returns existing VPC ID without error

#### Failure Recovery
| Exit Code | Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|-----------|-----------------------|-------------|---------|--------------|
| 1 | `InvalidParameter` | 1 | - | Re-check parameter format against API spec, retry with corrected params |
| 1 | `QuotaExceeded` | 0 | - | HALT. Inform user quota is full, suggest requesting increase |
| 1 | `InsufficientBalance` | 0 | - | HALT. Inform user to top up account |
| 2 | `ResourceAlreadyExists` | 0 | - | **Idempotent**: Fetch existing resource ID and continue (see Idempotent Execution) |
| 3 | `InternalError` | 3 | 2s, 4s, 8s | Retry with exponential backoff. After 3rd failure, report to user |
| Other | `.*` | 3 | 5s, 10s, 15s | Retry. On final failure, extract full error message and present to user |

### Operation: Create Subnet (Idempotent)

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| VPC exists | `jdc vpc describe-vpc --vpc-id {{user.vpc_id}} --region {{user.region}} --output json` | `$.data.vpcId` exists | Create VPC first or verify VPC ID |
| CIDR valid | Manual validation | CIDR format correct | Reject invalid CIDR, ask user for valid one |

#### Idempotent Execution
```bash
# Step 1: Check if Subnet already exists (by name in VPC)
EXISTING_SUBNET=$(jdc vpc describe-subnets \
  --region {{user.region}} \
  --vpc-id {{user.vpc_id}} \
  --output json | jq -r '.data[] | select(.subnetName == "{{user.subnet_name}}") | .subnetId' | head -n 1)

if [ -n "$EXISTING_SUBNET" ]; then
  echo "Subnet '{{user.subnet_name}}' already exists with ID: $EXISTING_SUBNET"
  {{output.subnet_id}}="$EXISTING_SUBNET"
else
  # Step 2: Create new Subnet
  CREATE_OUTPUT=$(jdc vpc create-subnet \
    --region {{user.region}} \
    --vpc-id {{user.vpc_id}} \
    --subnet-name "{{user.subnet_name}}" \
    --cidr-block "{{user.subnet_cidr}}" \
    --availability-zone "{{user.availability_zone}}" \
    --output json \
    --no-interactive)
  
  # Step 3: Extract Subnet ID from output
  {{output.subnet_id}}=$(echo "$CREATE_OUTPUT" | jq -r '.data.subnetId')
fi
```

#### Post-execution Validation
1. Validate `{{output.subnet_id}}` is not empty
2. Poll until ready:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc vpc describe-subnet \
       --subnet-id {{output.subnet_id}} \
       --region {{user.region}} \
       --output json | jq -r '.data.status')
     [ "$STATUS" = "running" ] && break
     sleep 5
   done
   ```
3. If status is `running` → operation succeeded, report `{{output.subnet_id}}` to user
4. If status is `error` → capture error from `$.data.errorMessage`, go to Failure Recovery
5. **Idempotency Note**: If Subnet already exists, operation returns existing Subnet ID without error

### Operation: Delete Subnet (Idempotent)

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to delete `{{user.subnet_name}}` ({{user.subnet_id}})? This is irreversible."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Idempotent Execution
```bash
# Step 1: Check if Subnet exists
SUBNET_EXISTS=$(jdc vpc describe-subnet \
  --subnet-id {{user.subnet_id}} \
  --region {{env.JDC_REGION}} \
  --output json 2>&1)

if echo "$SUBNET_EXISTS" | jq -e '.error' > /dev/null 2>&1; then
  echo "Subnet {{user.subnet_id}} does not exist or already deleted. Operation is idempotent."
  exit 0
fi

# Step 2: Delete Subnet if it exists
jdc vpc delete-subnet \
  --subnet-id {{user.subnet_id}} \
  --region {{env.JDC_REGION}} \
  --output json \
  --no-interactive

# Step 3: Wait for deletion to complete
for i in $(seq 1 60); do
  if jdc vpc describe-subnet --subnet-id {{user.subnet_id}} --region {{env.JDC_REGION}} --output json 2>&1 | jq -e '.error' > /dev/null 2>&1; then
    echo "Subnet {{user.subnet_id}} successfully deleted"
    break
  fi
  sleep 5
done
```

#### Post-execution Validation
1. Poll `describe` until it returns HTTP 404 or `status: "deleted"` (max 300s)
2. **Idempotency Note**: If Subnet already deleted, operation succeeds without error
3. **Verification**: Confirm resource is no longer accessible

### Operation: Describe VPC

#### Execution
```bash
jdc vpc describe-vpc \
  --vpc-id {{user.vpc_id}} \
  --region {{env.JDC_REGION}} \
  --output json
```

#### Output to Present to User
| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| ID | `$.data.vpcId` | Plain text |
| Name | `$.data.vpcName` | Plain text |
| Status | `$.data.status` | Badge: 🟢 running / 🟡 pending / 🔴 error |
| Created At | `$.data.createTime` | ISO 8601 → human-readable |
| CIDR Block | `$.data.cidrBlock` | Plain text |

### Operation: Delete VPC (Idempotent)

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to delete `{{user.vpc_name}}` ({{user.vpc_id}})? This is irreversible."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Idempotent Execution
```bash
# Step 1: Check if VPC exists
VPC_EXISTS=$(jdc vpc describe-vpc \
  --vpc-id {{user.vpc_id}} \
  --region {{env.JDC_REGION}} \
  --output json 2>&1)

if echo "$VPC_EXISTS" | jq -e '.error' > /dev/null 2>&1; then
  echo "VPC {{user.vpc_id}} does not exist or already deleted. Operation is idempotent."
  exit 0
fi

# Step 2: Delete VPC if it exists
jdc vpc delete-vpc \
  --vpc-id {{user.vpc_id}} \
  --region {{env.JDC_REGION}} \
  --output json \
  --no-interactive

# Step 3: Wait for deletion to complete
for i in $(seq 1 60); do
  if jdc vpc describe-vpc --vpc-id {{user.vpc_id}} --region {{env.JDC_REGION}} --output json 2>&1 | jq -e '.error' > /dev/null 2>&1; then
    echo "VPC {{user.vpc_id}} successfully deleted"
    break
  fi
  sleep 5
done
```

#### Post-execution Validation
1. Poll `describe` until it returns HTTP 404 or `status: "deleted"` (max 300s)
2. **Idempotency Note**: If VPC already deleted, operation succeeds without error
3. **Verification**: Confirm resource is no longer accessible

## Prerequisites
1. **Install JD Cloud CLI**:
   ```bash
   pip install jdcloud_cli
   jdc config init
   ```
2. **Configure Credentials**:
   The Agent runtime MUST have the following environment variables set. These map to `{{env.*}}` placeholders used throughout this Skill:
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```
   > The Agent MUST verify these are set before any operation. If missing, instruct user to configure via `jdc config init`.

## Reference Directory
- [Core Concepts](references/core-concepts.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration (MCP/SDK)](references/integration.md)

## Operational Best Practices
- **High Availability**: Always deploy across multiple availability zones.
- **Security**: Apply least-privilege security group rules and network ACLs.
- **Cost Optimization**: Monitor VPC resource usage and optimize CIDR allocation.
- **Network Planning**: Plan CIDR blocks carefully to avoid overlaps and allow for growth.
- **Idempotency**: All create and delete operations are designed to be idempotent. Safe to retry without side effects.
- **Resource Naming**: Use consistent naming conventions with unique identifiers for idempotent resource lookup.
- **State Verification**: Always verify resource state before and after operations to ensure idempotency.
- **Error Handling**: Treat "ResourceAlreadyExists" and "ResourceNotFound" as expected outcomes in idempotent operations.
- **Atomic Operations**: Each operation should be atomic - either complete successfully or fail without partial state changes.
- **Consistent Results**: Multiple executions of the same operation should produce identical results.


---

# Appendix: Reference File Templates

## references/troubleshooting.md Template
```markdown
# Troubleshooting VPC

## Common Error Codes
| Error Code | Description | Solution |
|------------|-------------|----------|
| `InvalidParameter` | A required parameter is missing. | Check the CLI command syntax. |
| `InsufficientBalance` | Account balance is insufficient. | Top up your JD Cloud account.
| `ResourceAlreadyExists` | A resource with the same name already exists. | Use a different name or delete the existing resource. |
| `QuotaExceeded` | You have reached the maximum number of resources allowed. | Request a quota increase or delete unused resources. |

## Diagnostic Steps
1. **Check VPC Status**: `jdc vpc describe-vpcs --region {{user.region}}`
2. **Check Subnet Status**: `jdc vpc describe-subnets --vpc-id {{user.vpc_id}} --region {{user.region}}`
3. **Network Connectivity**: Use `ping` and `telnet` from a bastion host to verify network access.
4. **Security Group Rules**: Verify security group rules allow required traffic.
```

## references/monitoring.md Template
```markdown
# Monitoring VPC

## Key Metrics
- **VPC Resource Count**: Track number of VPCs, subnets, and related resources
- **Network Traffic**: Monitor inbound/outbound traffic patterns
- **Security Group Rules**: Track rule changes and effectiveness

## Alert Configuration Example
```json
{
  "metricName": "vpc_count",
  "threshold": 10,
  "comparisonOperator": ">",
  "period": 300
}
```
```

## references/integration.md Template
```markdown
# Integration & Tooling

## SDK Initialization (Python)
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpc.client import VpcClient

credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = VpcClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```
> Rule: Use `os.environ['KEY']` (not `.get()`) for credentials to fail-fast if missing. Use `os.environ.get('KEY', default)` for optional config like region.
```