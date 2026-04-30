---
name: jdcloud-[product-name]-ops
description: >-
  Manages JD Cloud [Product Name] resources. Use when you need to deploy, 
  configure, troubleshoot, or monitor [Product Name] instances on JD Cloud.
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

> This template follows the [Agent Skill OpenSpec](https://agentskills.io/specification) specification.

# JD Cloud [Product Name] Operations Skill

## Overview
[Product Name] is a core service on JD Cloud that provides [brief description of functionality]. This skill enables efficient operations, including automated deployment, real-time monitoring, and rapid troubleshooting.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "JD Cloud [Product Name]" OR "[Product Chinese Name]" OR "[Product Alias]"
- Task involves CRUD operations on [Resource Type]: create, describe, modify, delete, list
- Task keywords: [keyword1], [keyword2], [keyword3], ...
- User asks to deploy, configure, troubleshoot, or monitor [Product Name] resources

### SHOULD NOT Use This Skill When
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`
- Task is about IAM / user permission management → delegate to: `jdcloud-iam-ops`
- Task is about [related but different product] → delegate to: `jdcloud-[other]-ops`

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
| `{{user.resource_name}}` | Must be collected from user | Ask user once and reuse |
| `{{output.resource_id}}` | Captured from CLI JSON output | Parse from `$.data.[resource]Id` |

> Rule: Placeholders wrapped in `{{env.*}}` MUST NOT be exposed to or requested from the user. Placeholders wrapped in `{{user.*}}` MUST be collected interactively.

## Output Parsing Rules (Agent-Readable)

### Mandatory CLI Conventions
- All CLI commands MUST append `--output json` for machine-parseable output
- All CLI commands SHOULD append `--no-interactive` (or equivalent) to prevent blocking on user prompts
- Timestamps are in ISO 8601 format with timezone: `2026-04-28T10:00:00+08:00`
- Resource IDs follow pattern: `[prefix]-[hash]` (e.g., `vm-abc123def`)
- Boolean values: `true` / `false` (lowercase)

### Key JSON Paths for Common Operations
| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create | `$.data.[resource]Id` | string | Resource ID to track |
| Describe | `$.data.status` | string | Current state (e.g. `running`, `stopped`) |
| List | `$.data[*].[resource]Id` | array | All resource IDs |
| Modify | `$.data.success` | boolean | Whether modification succeeded |
| Delete | `$.data.success` | boolean | Whether deletion succeeded |

### Expected State Transitions
| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | - | `running` | 5s | 300s |
| Start | `stopped` | `running` | 5s | 120s |
| Stop | `running` | `stopped` | 5s | 120s |
| Delete | `running`/`stopped` | (404 on describe) | 5s | 300s |

## Changelog

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0.0 | 2026-04-28 | 初始版本，包含基础运维指南和参考模板 |

## Execution Flows (Agent-Readable)
Every operation follows the pattern: Pre-flight → Execute → Validate → Recover. The Agent MUST NOT skip any phase.

### Operation: Create [Resource]

#### Pre-flight Checks
| Check | Command | Expected | On Failure |
|-------|---------|----------|------------|
| CLI installed | `jdc --version` | exit code 0 | Guide user to install jdcloud-cli |
| Credentials valid | `jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 1 --output json` | `$.error == null` | Prompt user to run `jdc config init` |
| Region available | `jdc [product] describe-regions --output json` | `{{user.region}}` in list | Suggest nearest available region |
| Quota available | `jdc [product] describe-quota --region {{user.region}} --output json` | `$.available > 0` | Inform user of quota limit, suggest increase |

#### Execution
```bash
jdc [product] create-[resource] \
  --region {{user.region}} \
  --[resource]-name "{{user.resource_name}}" \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Capture `{{output.resource_id}}` from `$.data.[resource]Id`
2. Poll until ready:
   ```bash
   for i in $(seq 1 60); do
     STATUS=$(jdc [product] describe-[resource] \
       --[resource]-id {{output.resource_id}} \
       --region {{user.region}} \
       --output json | jq -r '.data.status')
     [ "$STATUS" = "running" ] && break
     sleep 5
   done
   ```
3. If status is `running` → operation succeeded, report `{{output.resource_id}}` to user
4. If status is `error` → capture error from `$.data.errorMessage`, go to Failure Recovery

#### Failure Recovery
| Exit Code | Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|-----------|-----------------------|-------------|---------|--------------|
| 1 | `InvalidParameter` | 1 | - | Re-check parameter format against API spec, retry with corrected params |
| 1 | `QuotaExceeded` | 0 | - | HALT. Inform user quota is full, suggest requesting increase |
| 1 | `InsufficientBalance` | 0 | - | HALT. Inform user to top up account |
| 2 | `ResourceAlreadyExists` | 0 | - | Ask user if they want to reuse existing resource or use a different name |
| 3 | `InternalError` | 3 | 2s, 4s, 8s | Retry with exponential backoff. After 3rd failure, report to user |
| Other | `.*` | 3 | 5s, 10s, 15s | Retry. On final failure, extract full error message and present to user |

### Operation: Describe [Resource]

#### Execution
```bash
jdc [product] describe-[resource] \
  --[resource]-id {{user.resource_id}} \
  --region {{env.JDC_REGION}} \
  --output json
```

#### Output to Present to User
| Field | JSON Path | Display Format |
|-------|-----------|----------------|
| ID | `$.data.[resource]Id` | Plain text |
| Name | `$.data.[resource]Name` | Plain text |
| Status | `$.data.status` | Badge: 🟢 running / 🟡 pending / 🔴 error |
| Created At | `$.data.createTime` | ISO 8601 → human-readable |
| Public IP | `$.data.publicIp` | `-` if null |

### Operation: Delete [Resource]

#### Pre-flight (Safety Gate)
- **MUST** ask user: "Are you sure you want to delete `{{user.resource_name}}` ({{user.resource_id}})? This is irreversible."
- **MUST** wait for explicit "yes" / "confirm" before proceeding

#### Execution
```bash
jdc [product] delete-[resource] \
  --[resource]-id {{user.resource_id}} \
  --region {{env.JDC_REGION}} \
  --output json \
  --no-interactive
```

#### Post-execution Validation
1. Poll `describe` until it returns HTTP 404 or `status: "deleted"` (max 300s)

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
- **Security**: Apply least-privilege IAM policies.
- **Cost Optimization**: Utilize auto-scaling and reserved instances where applicable.


---

# Appendix: Reference File Templates

## references/troubleshooting.md Template
```markdown
# Troubleshooting [Product Name]

## Common Error Codes
| Error Code | Description | Solution |
|------------|-------------|----------|
| `InvalidParameter` | A required parameter is missing. | Check the CLI command syntax. |
| `InsufficientBalance` | Account balance is insufficient. | Top up your JD Cloud account. |

## Diagnostic Steps
1. **Check Resource Status**: `jdc [product] describe-[resource]s --[resource]-ids [ID]`
2. **View System Logs**: Access via JD Cloud Console -> VNC (for VM) or product-specific log service.
3. **Network Connectivity**: Use `ping` and `telnet` from a bastion host to verify network access.
```

## references/monitoring.md Template
```markdown
# Monitoring [Product Name]

## Key Metrics
- **CPU Utilization**: `namespace/jcs.vm/cpu_usage`
- **Memory Usage**: `namespace/jcs.vm/memory_usage`
- **Disk I/O**: `namespace/jcs.vm/disk_read_bytes`

## Alert Configuration Example
```json
{
  "metricName": "cpu_usage",
  "threshold": 80,
  "comparisonOperator": ">",
  "period": 300
}
```
```

## references/integration.md Template
```markdown
# Integration & Tooling

## MCP Server Configuration
```json
{
  "mcpServers": {
    "jdcloud-[product]": {
      "command": "uvx", 
      "args": ["run", "--python", "3.10", "@jdcloud/[product]-mcp"],
      "env": {
        "JDC_ACCESS_KEY": "{{env.JDC_ACCESS_KEY}}",
        "JDC_SECRET_KEY": "{{env.JDC_SECRET_KEY}}",
        "JDC_REGION": "{{env.JDC_REGION}}"
      }
    }
  }
}
```
> Note: MCP servers are developed with Python 3.10+ and launched using `uvx` command. Environment variables MUST be set in the Agent runtime environment. NEVER hardcode credentials in configuration files. The `{{env.*}}` placeholders are resolved by the Agent harness at runtime.

## SDK Initialization (Python)
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.[product].client import [Product]Client

credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = [Product]Client(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```
> Rule: Use `os.environ['KEY']` (not `.get()`) for credentials to fail-fast if missing. Use `os.environ.get('KEY', default)` for optional config like region.
```
