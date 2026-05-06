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
  version: "1.3.0"
  last_updated: "2026-05-06"
  runtime: Harness AI Agent
  api_profile: "VM API v1.0 - https://docs.jdcloud.com/cn/virtual-machines/api"
  cli_applicability: jdc-first-with-fallback
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

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` CLI supports VM operations. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented.
- **Path Preference:** Follow **jdc-first with SDK fallback** strategy. See [API & SDK Usage](references/api-sdk-usage.md) for detailed comparison.

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
- All CLI commands MUST place `--output json` BEFORE the subcommand: `jdc --output json vm <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Credentials: CLI reads from `~/.jdc/config` INI only (NOT from env vars). SDK uses env vars.
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
| 1.3.0 | 2026-05-06 | **Critical CLI behavioral fixes**: Fixed `--output json` positioning (must be BEFORE subcommand), removed non-existent `--no-interactive` flag, corrected credential docs (CLI uses `~/.jdc/config` INI, NOT env vars), added sandbox config workaround |
| 1.2.0 | 2026-05-06 | **jdc-first with fallback strategy**: execution flows now prioritize `jdc` CLI (primary) with SDK/API fallback after 3 retries; Prerequisites updated to `uv`-based bootstrap with Phase 1 (jdc) / Phase 2 (SDK fallback); Path Preference flipped to jdc-first; pre-flight checks reordered |
| 1.1.0 | 2026-05-03 | Added dual-path execution (SDK + CLI), complete frontmatter, api-sdk-usage.md, path preference |
| 1.0.0 | 2026-04-28 | Initial version, includes basic operational guide and reference templates |
| 1.0.1 | 2026-04-28 | Added VM instance management, network configuration, and security group operations guide |

## Execution Flows (Agent-Readable)
Every operation follows the pattern: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. The Agent MUST NOT skip any phase.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Documentation below lists `jdc` before SDK to reflect execution priority.

### Operation: Create VM Instance

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| CLI installed | `jdc --version` | exit code 0 | Retry up to 3 times; then fall back to SDK |
| Credentials valid | `jdc --output json vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 1` | `$.error == null` | Prompt user to config CLI credentials (`~/.jdc/config`) or set SDK env vars |
| SDK available | `python -c "import jdcloud_sdk"` | No import error | Document install pin (fallback path) |
| Instance types available | `jdc --output json vm describe-instance-types --region-id {{user.region}}` | list non-empty | Suggest another region |
| Image exists | `jdc --output json vm describe-images --region-id {{user.region}} --image-ids '["{{user.image_id}}"]'` | returns image | Suggest available public image |
| Subnet exists | `jdc --output json vpc describe-subnet --region-id {{user.region}} --subnet-id {{user.subnet_id}}` | returns subnet | Suggest creating subnet first |

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json vm create-instances \
  --region-id {{user.region}} \
  --az "{{user.az}}" \
  --instance-type "{{user.instance_type}}" \
  --image-id "{{user.image_id}}" \
  --name "{{user.instance_name}}" \
  --primary-network-interface "{\"subnetId\":\"{{user.subnet_id}}\",\"securityGroupIds\":[\"{{user.sg_id}}\"]}" \
  --system-disk "{\"diskCategory\":\"cloud_ssd\",\"diskSizeGB\":{{user.disk_size}}}" \
  --charge-mode "postpaid_by_duration"
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Post-execution Validation
1. Capture `{{output.instance_id}}` from `$.result.instanceIds[0]`
2. Poll until running:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc --output json vm describe-instances \
       --region-id {{user.region}} \
       --instance-ids '["{{output.instance_id}}"]' | jq -r '.result.instances[0].status')
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

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json vm describe-instances \
  --region-id {{env.JDC_REGION}} \
  --instance-ids '["{{user.instance_id}}"]'
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json vm stop-instance \
  --region-id {{env.JDC_REGION}} \
  --instance-id {{user.instance_id}}
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Post-execution Validation
1. Poll until status == `stopped` (max 120s)

### Operation: Delete VM Instance

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to delete `{{user.instance_name}}` ({{user.instance_id}})? This is IRREVERSIBLE and will release all associated resources."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json vm delete-instance \
  --region-id {{env.JDC_REGION}} \
  --instance-id {{user.instance_id}}
```

#### Execution (SDK Fallback — after 3 jdc failures)

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

#### Post-execution Validation
1. Poll `describe-instances` until HTTP 404 (max 300s)

## Prerequisites

Environment setup follows a **jdc-first with fallback** strategy:

1. **Attempt `jdc` CLI setup** via `uv` (primary path)
2. On failure, **retry up to 3 times** with exponential backoff (0s → 2s → 4s)
3. After **3 consecutive failures**, fall back to **SDK-only** setup

### Python Runtime (uv)

Both `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

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
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

#### Retry Logic (Up to 3 Attempts)

If `jdc --version` or any `jdc` command fails:

```bash
# Retry 1
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

### Configure Credentials

> **CRITICAL:** The `jdc` CLI reads credentials **only** from `~/.jdc/config` INI file. Environment variables (`JDC_ACCESS_KEY`, `JDC_SECRET_KEY`) are **ignored** by the CLI. The SDK mode reads from environment variables. Use the appropriate method below.

**Method A: Configure Credentials for SDK (env vars)**
```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

**Method B: Configure Credentials for CLI (`~/.jdc/config` INI)**
```bash
# For sandbox environments, redirect HOME to a writable location
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{env.JDC_REGION}}
endpoint = vm.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
# CRITICAL: ~/.jdc/current must contain exactly "default" with NO trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

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
