---
name: jdcloud-vm-ops
description: >-
  Use when you need to deploy, configure, troubleshoot, or monitor JD Cloud
  Virtual Machine (VM) via official API/SDK or official `jdc` CLI; user mentions
  VM, 云主机, CVM, or tasks target VM instances.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`).
metadata:
  author: jdcloud
  version: "1.1.0"
  last_updated: "2026-05-03"
  runtime: Harness AI Agent
  api_profile: "VM API v1.0 - https://docs.jdcloud.com/cn/virtual-machines/api"
  cli_applicability: dual-path
  cli_support_evidence: >-
    Official `jdc` CLI supports VM operations. Verified via `jdc vm --help`
    and documentation at https://docs.jdcloud.com/cn/cli
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud VM Operations Skill

## Overview
JD Cloud Virtual Machine (VM) is a core computing service that provides elastic, scalable, and secure cloud servers. This skill enables efficient operations, including automated deployment, real-time monitoring, and rapid troubleshooting of VM resources.

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** Official `jdc` CLI supports VM operations. This skill provides **both SDK/API and CLI execution paths** for every operation.
- **Path Preference:** For automated agent execution, prefer **SDK** for complex workflows (better error handling, retry logic); prefer **CLI** for simple queries and quick operations. See [API & SDK Usage](references/api-sdk-usage.md) for detailed comparison.

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
| 1.1.0 | 2026-05-03 | Added dual-path execution (SDK + CLI), complete frontmatter, api-sdk-usage.md, path preference |
| 1.0.0 | 2026-04-28 | Initial version, includes basic operational guide and reference templates |
| 1.0.1 | 2026-04-28 | Added VM instance management, network configuration, and security group operations guide |

## Execution Flows (Agent-Readable)
Every operation follows the pattern: Pre-flight → Execute → Validate → Recover. The Agent MUST NOT skip any phase.

### Operation: Create VM Instance

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| CLI installed | `jdc --version` | exit code 0 | Guide user to install jdcloud-cli |
| Credentials valid | `jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 1 --output json` | `$.error == null` | Prompt user to run `jdc config init` |
| Instance types available | `jdc vm describe-instance-types --region-id {{user.region}} --output json` | list non-empty | Suggest another region |
| Image exists | `jdc vm describe-images --region-id {{user.region}} --image-ids '["{{user.image_id}}"]' --output json` | returns image | Suggest available public image |
| Subnet exists | `jdc vpc describe-subnet --region-id {{user.region}} --subnet-id {{user.subnet_id}} --output json` | returns subnet | Suggest creating subnet first |

#### Execution — SDK (Python)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.client import VmClient
from jdcloud_sdk.services.vm.apis.CreateInstancesRequest import CreateInstancesRequest

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = VmClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

request = CreateInstancesRequest({
    "regionId": "{{user.region}}",
    "az": "{{user.az}}",
    "instanceType": "{{user.instance_type}}",
    "imageId": "{{user.image_id}}",
    "name": "{{user.instance_name}}",
    "primaryNetworkInterface": {
        "subnetId": "{{user.subnet_id}}",
        "securityGroupIds": ["{{user.sg_id}}"]
    },
    "systemDisk": {
        "diskCategory": "cloud_ssd",
        "diskSizeGB": {{user.disk_size}}
    },
    "chargeMode": "postpaid_by_duration"
})

response = client.create_instances(request)
if response.error is None:
    instance_id = response.result.instanceIds[0]
    print(f"Created instance: {instance_id}")
else:
    print(f"Error: {response.error.code} - {response.error.message}")
```

#### Execution — CLI (`jdc`)
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

#### Execution — SDK (Python)

```python
from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import DescribeInstancesRequest

request = DescribeInstancesRequest({
    "regionId": os.environ.get('JDC_REGION', 'cn-north-1'),
    "instanceIds": ["{{user.instance_id}}"]
})

response = client.describe_instances(request)
if response.error is None:
    instance = response.result.instances[0]
    print(f"ID: {instance.instanceId}")
    print(f"Name: {instance.name}")
    print(f"Status: {instance.status}")
    print(f"Private IP: {instance.primaryNetworkInterface.privateIpAddress}")
else:
    print(f"Error: {response.error.message}")
```

#### Execution — CLI (`jdc`)
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

#### Execution — SDK (Python)

```python
from jdcloud_sdk.services.vm.apis.StopInstanceRequest import StopInstanceRequest

request = StopInstanceRequest({
    "regionId": os.environ.get('JDC_REGION', 'cn-north-1'),
    "instanceId": "{{user.instance_id}}"
})

response = client.stop_instance(request)
if response.error is None:
    print(f"Stop request accepted: {response.requestId}")
else:
    print(f"Error: {response.error.message}")
```

#### Execution — CLI (`jdc`)
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

#### Execution — SDK (Python)

```python
from jdcloud_sdk.services.vm.apis.DeleteInstanceRequest import DeleteInstanceRequest

request = DeleteInstanceRequest({
    "regionId": os.environ.get('JDC_REGION', 'cn-north-1'),
    "instanceId": "{{user.instance_id}}"
})

response = client.delete_instance(request)
if response.error is None:
    print(f"Delete request accepted: {response.requestId}")
else:
    print(f"Error: {response.error.message}")
```

#### Execution — CLI (`jdc`)
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
1. **Install JD Cloud SDK (Python)**:
   ```bash
   pip install jdcloud_sdk
   ```
   See [Integration](references/integration.md) for SDK version pinning.

2. **Install JD Cloud CLI (for dual-path)**:
   ```bash
   pip install jdcloud_cli
   jdc config init
   ```

2. **Configure Credentials** — Three methods:

   **Method 1: `.env` File (Recommended for Local Development)**
   Create `.env` in working directory (copy from project's `.env.example`):
   ```ini
   JDC_ACCESS_KEY=your_access_key_here
   JDC_SECRET_KEY=your_secret_key_here
   JDC_REGION=cn-north-1
   ```
   
   > **Note:** Agent Runtime auto-loads `.env` if present. Shell env vars have **higher priority**.

   **Method 2: Shell Environment Variables (Recommended for Production)**
   
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

   **Method 3: CLI Interactive Config**
   ```bash
   jdc config init
   ```

3. **Verify Configuration**:
   ```bash
   jdc vm describe-instance-types --region-id cn-north-1 --output json --page-number 1 --page-size 1
   ```

   > The Agent MUST verify these are set before any operation. If missing, instruct user to configure credentials.
   > ⚠️ **Security Note**: Never commit `.env` files to version control. Use `{{env.*}}` placeholders for credentials.

## Reference Directory
- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
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
