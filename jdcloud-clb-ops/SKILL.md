---
name: jdcloud-clb-ops
description: >-
  Use when you need to deploy, configure, troubleshoot, or monitor JD Cloud
  Load Balancer (CLB) via official API/SDK or official `jdc` CLI; user mentions
  CLB, 负载均衡, Load Balancer, SLB, or tasks target load balancer instances,
  listeners, backend servers, or target groups.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-05-06"
  runtime: Harness AI Agent
  api_profile: "JD Cloud CLB API v1 - https://lb.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing 'lb' in product list.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Load Balancer (CLB) Operations Skill

## Overview

JD Cloud Load Balancer (CLB/负载均衡) is a high-performance traffic distribution service that automatically distributes incoming application traffic across multiple backend servers. It provides Layer 4 (TCP/UDP) and Layer 7 (HTTP/HTTPS) load balancing capabilities with health checks, SSL offloading, and session persistence. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

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
jdc --output json lb describe-load-balancers --region-id cn-north-1 --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc lb describe-load-balancers --region-id cn-north-1 --page-number 1 --page-size 100 --output json
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
endpoint = lb.jdcloud-api.com
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

- User mentions "JD Cloud CLB" OR "负载均衡" OR "Load Balancer" OR "SLB" OR "CLB实例"
- Task involves CRUD operations on load balancers: create, describe, modify, delete, list
- Task involves listener management: create listener, modify listener, delete listener
- Task involves backend server management: register/deregister targets, target groups
- Task involves health check configuration
- Task keywords: createLoadBalancer, describeLoadBalancers, createListener, registerTargets, healthCheck
- User asks to deploy, configure, troubleshoot, or monitor load balancers **via API, SDK, CLI, or automation**

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about VM / ECS instances (backend servers) → delegate to: `jdcloud-vm-ops`
- Task is about SSL certificates → delegate to: `jdcloud-ssl-ops` (when present)
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If CLB requires VPC/subnet, verify or create network resources via `jdcloud-vpc-ops` first.
- If CLB backend targets are VMs, verify VM instances via `jdcloud-vm-ops` first.
- If user asks about CLB monitoring metrics or alarm rules, delegate metric query to `jdcloud-cloudmonitor-ops`.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.lb_id}}` | User-supplied load balancer ID | Ask once; reuse |
| `{{user.lb_name}}` | User-supplied load balancer name | Ask once; reuse |
| `{{user.listener_id}}` | User-supplied listener ID | Ask once; reuse |
| `{{user.backend_server_id}}` | User-supplied backend server ID | Ask once; reuse |
| `{{output.lb_id}}` | From last API or CLI JSON response | Parse from `$.result.loadBalancerId` |
| `{{output.listener_id}}` | From last API or CLI JSON response | Parse from `$.result.listenerId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://lb.jdcloud-api.com/v1/regions/{regionId}/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-05-03T10:00:00+08:00`).
- **Idempotency:** Document duplicate resource name behavior and retry safety per API.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create LB | `$.result.loadBalancerId` | string | New load balancer ID |
| Describe LB | `$.result.loadBalancer.status` | string | LB state (active, inactive, etc.) |
| List LBs | `$.result.loadBalancers[*].loadBalancerId` | array | All LB IDs |
| Create Listener | `$.result.listenerId` | string | New listener ID |
| Modify/Delete | `$.requestId` or `$.error` | string / object | Per spec |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create LB | — | `active` | 10s | 300s |
| Create Listener | — | `active` | 10s | 120s |
| Modify LB | `active` | `active` | 10s | 120s |
| Delete LB | `active`/`inactive` | (404 on describe) | 10s | 300s |
| Register Targets | — | `healthy`/`unhealthy` | 10s | 120s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-06 | Initial version with jdc-first execution and SDK fallback for CLB operations |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (jdc primary / SDK fallback) → Validate → Recover**. Do not skip phases.

**jdc-first strategy:** The Agent MUST attempt `jdc` CLI first (primary path). If `jdc` fails after **3 retries** with exponential backoff, fall back to SDK/API. Documentation below lists `jdc` before SDK to reflect execution priority.

### Operation: Create Load Balancer

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.lb.client.LbClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Call `describeLoadBalancers` with small page | `{{user.region}}` supported | Suggest valid region |
| VPC/Subnet | Verify subnet via `jdcloud-vpc-ops` | Subnet exists and has IP | HALT; create subnet first |
| AZ | Verify AZ availability | Valid AZ in region | Suggest available AZs |

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json lb create-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-name "{{user.lb_name}}" \
  --vpc-id "{{user.vpc_id}}" \
  --subnet-id "{{user.subnet_id}}" \
  --azs '["{{user.az}}"]' \
  --load-balancer-spec "{{user.lb_spec|default:"small"}}"
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
endpoint = lb.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.lb.client.LbClient import LbClient
from jdcloud_sdk.services.lb.apis.CreateLoadBalancerRequest import CreateLoadBalancerRequest, CreateLoadBalancerParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = LbClient(credential)

# Build load balancer spec
lb_spec = {
    "loadBalancerName": "{{user.lb_name}}",
    "vpcId": "{{user.vpc_id}}",
    "subnetId": "{{user.subnet_id}}",
    "azs": ["{{user.az}}"],
    "loadBalancerSpec": "{{user.lb_spec|default:'small'}}"
}

params = CreateLoadBalancerParameters(regionId="{{user.region}}", loadBalancerSpec=lb_spec)
req = CreateLoadBalancerRequest(parameters=params)
resp = client.send(req)
lb_id = resp.result["loadBalancerId"]
```

#### Post-execution Validation

1. Capture `{{output.lb_id}}` from `$.result.loadBalancerId`.
2. Poll `describeLoadBalancer` until `status` == `active` or timeout.

```bash
# CLI poll loop (primary path) — --output json at TOP level
for i in $(seq 1 30); do
  STATUS=$(jdc --output json lb describe-load-balancer \
    --region-id "{{user.region}}" \
    --load-balancer-id "{{output.lb_id}}" | jq -r '.result.loadBalancer.status')
  [ "$STATUS" = "active" ] && break
  sleep 10
done
```

```python
# SDK poll loop (fallback, after 3 jdc failures)
from jdcloud_sdk.services.lb.apis.DescribeLoadBalancerRequest import DescribeLoadBalancerRequest, DescribeLoadBalancerParameters

for _ in range(30):
    dparams = DescribeLoadBalancerParameters(regionId="{{user.region}}", loadBalancerId="{{output.lb_id}}")
    dreq = DescribeLoadBalancerRequest(parameters=dparams)
    dresp = client.send(dreq)
    status = dresp.result["loadBalancer"]["status"]
    if status == "active":
        break
    if status in ["error", "deleted"]:
        raise RuntimeError(f"LB creation failed: {status}")
    sleep(10)
```

3. On success, report LB ID, VIP address, and DNS name to user.
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

### Operation: Describe Load Balancer

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb describe-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.lb.apis.DescribeLoadBalancerRequest import DescribeLoadBalancerRequest, DescribeLoadBalancerParameters

params = DescribeLoadBalancerParameters(regionId="{{user.region}}", loadBalancerId="{{user.lb_id}}")
req = DescribeLoadBalancerRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["loadBalancer"]
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| LB ID | `$.result.loadBalancer.loadBalancerId` | Plain text |
| Name | `$.result.loadBalancer.loadBalancerName` | Plain text |
| Status | `$.result.loadBalancer.status` | active, inactive, etc. |
| VIP | `$.result.loadBalancer.vip` | Virtual IP address |
| VPC ID | `$.result.loadBalancer.vpcId` | Associated VPC |
| Subnet ID | `$.result.loadBalancer.subnetId` | Associated subnet |
| AZs | `$.result.loadBalancer.azs` | Availability zones |
| Created Time | `$.result.loadBalancer.createdTime` | ISO 8601 format |

### Operation: List Load Balancers

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb describe-load-balancers \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.lb.apis.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest, DescribeLoadBalancersParameters

params = DescribeLoadBalancersParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeLoadBalancersRequest(parameters=params)
resp = client.send(req)
lbs = resp.result["loadBalancers"]
```

### Operation: Create Listener

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LB exists | `describeLoadBalancer` | LB found | HALT; verify LB ID |
| LB state | `describeLoadBalancer` | `active` | Wait or suggest appropriate action |
| Protocol | User input | tcp/udp/http/https | Validate protocol |
| Port | User input | 1-65535 | Validate port range |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb create-listener \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --listener-ports '[{{user.listener_port}}]' \
  --protocol "{{user.protocol}}" \
  --backend-port "{{user.backend_port}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.lb.apis.CreateListenerRequest import CreateListenerRequest, CreateListenerParameters

listener_spec = {
    "listenerPorts": [{{user.listener_port}}],
    "protocol": "{{user.protocol}}",
    "backendPort": {{user.backend_port}}
}

params = CreateListenerParameters(
    regionId="{{user.region}}",
    loadBalancerId="{{user.lb_id}}",
    listenerSpec=listener_spec
)
req = CreateListenerRequest(parameters=params)
resp = client.send(req)
listener_id = resp.result["listenerId"]
```

#### Post-execution Validation

Poll describe until listener is active.

### Operation: Register Targets (Backend Servers)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LB exists | `describeLoadBalancer` | LB found | HALT; verify LB ID |
| Target VMs exist | `jdcloud-vm-ops` | VMs found | HALT; verify VM IDs |
| Target ports valid | User input | 1-65535 | Validate port range |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb register-targets \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --target-group-id "{{user.target_group_id}}" \
  --target-specs '[{"instanceId":"{{user.vm_id}}","port":{{user.target_port}},"weight":{{user.weight|default:100}}}]'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.lb.apis.RegisterTargetsRequest import RegisterTargetsRequest, RegisterTargetsParameters

target_specs = [
    {
        "instanceId": "{{user.vm_id}}",
        "port": {{user.target_port}},
        "weight": {{user.weight|default:100}}
    }
]

params = RegisterTargetsParameters(
    regionId="{{user.region}}",
    loadBalancerId="{{user.lb_id}}",
    targetGroupId="{{user.target_group_id}}",
    targetSpecs=target_specs
)
req = RegisterTargetsRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll target health status until healthy or timeout.

### Operation: Modify Load Balancer

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| LB exists | `describeLoadBalancer` | LB found | HALT; verify LB ID |
| LB state | `describeLoadBalancer` | `active` | Wait or suggest appropriate action |

**⚠️ Safety Gate for Production LBs:** Confirm with user before modifying production load balancers as it may cause brief service interruption.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb modify-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --load-balancer-name "{{user.new_name}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.lb.apis.ModifyLoadBalancerRequest import ModifyLoadBalancerRequest, ModifyLoadBalancerParameters

params = ModifyLoadBalancerParameters(
    regionId="{{user.region}}",
    loadBalancerId="{{user.lb_id}}"
)
params.setLoadBalancerName("{{user.new_name}}")
req = ModifyLoadBalancerRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until modification reflects.

### Operation: Delete Load Balancer

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.lb_name}}` (`{{user.lb_id}}`).
- **MUST** check if LB has active listeners or targets — warn user about dependent resources.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json lb delete-load-balancer \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.lb.apis.DeleteLoadBalancerRequest import DeleteLoadBalancerRequest, DeleteLoadBalancerParameters

params = DeleteLoadBalancerParameters(
    regionId="{{user.region}}",
    loadBalancerId="{{user.lb_id}}"
)
req = DeleteLoadBalancerRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until 404 or max wait (300s).

```bash
# CLI poll loop
for i in $(seq 1 30); do
  jdc --output json lb describe-load-balancer \
    --region-id "{{user.region}}" \
    --load-balancer-id "{{user.lb_id}}" 2>&1 | grep -q "NotFound" && break
  sleep 10
done
```

### Operation: Health Check Management

#### Execution (CLI) [Primary Path]

```bash
# Update health check configuration
jdc --output json lb update-health-check \
  --region-id "{{user.region}}" \
  --load-balancer-id "{{user.lb_id}}" \
  --listener-id "{{user.listener_id}}" \
  --health-check-spec '{"protocol":"{{user.hc_protocol}}","port":{{user.hc_port}},"interval":{{user.hc_interval|default:5}},"healthyThreshold":{{user.hc_healthy|default:2}},"unhealthyThreshold":{{user.hc_unhealthy|default:3}}}'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.lb.apis.UpdateHealthCheckRequest import UpdateHealthCheckRequest, UpdateHealthCheckParameters

hc_spec = {
    "protocol": "{{user.hc_protocol}}",
    "port": {{user.hc_port}},
    "interval": {{user.hc_interval|default:5}},
    "healthyThreshold": {{user.hc_healthy|default:2}},
    "unhealthyThreshold": {{user.hc_unhealthy|default:3}}
}

params = UpdateHealthCheckParameters(
    regionId="{{user.region}}",
    loadBalancerId="{{user.lb_id}}",
    listenerId="{{user.listener_id}}",
    healthCheckSpec=hc_spec
)
req = UpdateHealthCheckRequest(parameters=params)
resp = client.send(req)
```

## Prerequisites

1. **Install uv** (system-wide, one-time per machine) — `jdc` CLI and the JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   > **Note:** Installing uv itself is a one-time system setup. The commands below are **idempotent** and safe to re-run.

2. **Bootstrap Python environment** (idempotent — safe to re-run):

   ```bash
   uv venv --python 3.10

   # Activate: macOS/Linux
   source .venv/bin/activate
   # Activate: Windows
   # .venv\Scripts\activate

   uv pip install jdcloud_cli jdcloud_sdk
   jdc --version
   ```

   > `uv venv` is idempotent: re-running on an existing `.venv` is a no-op. `uv pip install` skips already-satisfied packages. Pin versions in `references/integration.md`.

3. **Configure Credentials** — Two methods (CLI vs SDK differ):

   **CRITICAL:** The `jdc` CLI reads credentials **only** from `~/.jdc/config` INI file. Environment variables (`JDC_ACCESS_KEY`, `JDC_SECRET_KEY`) are **ignored** by the CLI. The SDK mode reads from environment variables. Use the appropriate method below.

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
   endpoint = lb.jdcloud-api.com
   scheme = https
   timeout = 20
   CONFIGEOF
   printf "%s" "default" > /tmp/jdc-home/.jdc/current
   ```

4. **Verify Configuration**:
   ```bash
   # Quick validation (--output json BEFORE subcommand)
   jdc --output json lb describe-load-balancers --region-id cn-north-1 --page-number 1 --page-size 1
   ```

> **Security:** Never commit `.env` to version control (already in `.gitignore`). All credentials use `{{env.*}}` placeholders in generated Skills — never real values.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md) (**required** when `cli_applicability: jdc-first-with-fallback`)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Least privilege:** IAM policies scoped to required APIs only.
- **Availability:** Deploy CLB across multiple AZs for high availability.
- **Health Checks:** Configure appropriate health check intervals and thresholds.
- **Security:** Use security groups to restrict access to CLB.
- **Cost:** Delete unused load balancers and listeners to reduce costs.
