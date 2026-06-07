---
name: jdcloud-nat-ops
description: >-
  Use this skill to manage JD Cloud NAT Gateway (NAT网关): deploy, configure,
  troubleshoot, or monitor via API/SDK or `jdc` CLI. Trigger for NAT, NAT网关,
  NAT Gateway, or tasks involving NAT gateway instances, SNAT rules, DNAT rules,
  or outbound/inbound traffic forwarding — even without explicit "NAT" mention.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent
  api_profile: "JD Cloud VPC API v1 - https://vpc.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    NAT Gateway operations are exposed under the 'vpc' product group in `jdc`.
    Confirmed via `jdc vpc --help` showing describe-nat-gateways,
    create-nat-gateway, delete-nat-gateway, associate-nat-gateway, and
    disassociate-nat-gateway subcommands.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
  gcl_classification: required
  gcl_max_iter: 2
  waf_rules:
    - WAF-REL-010 (NAT HA — deploy at least 2 SNAT EIPs for production NAT gateways)
    - WAF-PERF-049 (NAT bandwidth — monitor bandwidth utilization and right-size spec)
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud NAT Gateway (NAT网关) Operations Skill

## Overview

JD Cloud NAT Gateway (NAT网关) is a managed network address translation service that enables instances within a Virtual Private Cloud (VPC) to access the internet (SNAT) or allows external access to instances within the VPC (DNAT) without exposing private IPs directly. It supports elastic IP association, SNAT/DNAT rule management, and bandwidth control. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` supports this product under the `vpc` subcommand group. The Agent MUST attempt to use `jdc` as the **primary execution path**. If `jdc` installation or command execution fails, the Agent MUST retry up to **3 times** (with exponential backoff). Only after **3 consecutive failures** should the Agent fall back to **SDK/API**. Both paths MUST be documented. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the `jdc` step **and** the SDK fallback step for every operation the CLI exposes.

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
jdc --output json vpc describe-nat-gateways --region-id cn-north-1 --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc vpc describe-nat-gateways --region-id cn-north-1 --page-number 1 --page-size 100 --output json
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
endpoint = vpc.jdcloud-api.com
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

- User explicitly mentions "JD Cloud NAT Gateway", "NAT网关", "NAT Gateway", "NAT实例", or "NAT"
- User wants to **deploy**, **configure**, **troubleshoot**, or **monitor** NAT gateways via automation
- Task involves CRUD operations: create, describe, modify, delete, or list NAT gateway instances
- Task involves SNAT rule management: create, describe, or delete SNAT rules for outbound internet access
- Task involves DNAT rule management: create, describe, or delete DNAT rules for inbound port forwarding
- Task involves Elastic IP association/disassociation with NAT gateways
- Task involves NAT gateway bandwidth or specification changes
- Keywords detected: createNatGateway, describeNatGateways, createSnatRule, createDnatRule, associateNatGateway, elasticIp
- User describes outbound/inbound traffic management without naming "NAT" (e.g., "let my VMs access the internet", "forward external traffic to my private servers", "set up internet gateway for private subnet")

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / route table / security group management → delegate to: `jdcloud-vpc-ops`
- Task is about Elastic IP (EIP) management only (no NAT context) → delegate to: `jdcloud-eip-ops`
- Task is about VM / ECS instance management → delegate to: `jdcloud-vm-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If NAT Gateway requires VPC/subnet resources, verify or create them via `jdcloud-vpc-ops` first.
- If NAT Gateway requires Elastic IPs, allocate or verify them via `jdcloud-eip-ops` first.
- If user asks about NAT monitoring metrics or alarm rules, delegate metric queries to `jdcloud-cloudmonitor-ops`.
- For SNAT rules, verify the associated subnet exists via `jdcloud-vpc-ops`.
- Multi-product requests: handle each product with its dedicated skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.nat_id}}` | User-supplied NAT gateway ID | Ask once; reuse |
| `{{user.nat_name}}` | User-supplied NAT gateway name | Ask once; reuse |
| `{{user.vpc_id}}` | User-supplied VPC ID | Ask once; reuse |
| `{{user.subnet_id}}` | User-supplied subnet ID (SNAT) | Ask once; reuse |
| `{{user.eip_id}}` | User-supplied Elastic IP ID | Ask once; reuse |
| `{{output.nat_id}}` | From last API or CLI JSON response | Parse from `$.result.natGatewayId` |
| `{{output.snat_id}}` | From last API or CLI JSON response | Parse from `$.result.snatRuleId` |
| `{{output.dnat_id}}` | From last API or CLI JSON response | Parse from `$.result.dnatRuleId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK, CLI, and debugging scripts).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://vpc.jdcloud-api.com/v1/regions/{regionId}/natGateways/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-06-08T10:00:00+08:00`).
- **Idempotency:** NAT Gateway creation with the same name in the same VPC may result in duplicate names; agent should check for existing resources before creating.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create NAT | `$.result.natGatewayId` | string | New NAT gateway ID |
| Describe NAT | `$.result.natGateway.state` | string | NAT state (available, creating, deleting, etc.) |
| List NATs | `$.result.natGateways[*].natGatewayId` | array | All NAT gateway IDs |
| Create SNAT Rule | `$.result.snatRuleId` | string | New SNAT rule ID |
| Create DNAT Rule | `$.result.dnatRuleId` | string | New DNAT rule ID |
| Modify/Delete | `$.requestId` or `$.error` | string / object | Per spec |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create NAT | — | `available` | 10s | 300s |
| Associate EIP | `available` | `available` | 10s | 120s |
| Disassociate EIP | `available` | `available` | 10s | 120s |
| Modify NAT | `available` | `available` | 10s | 120s |
| Delete NAT | `available` | (404 on describe) | 10s | 300s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-08 | Initial NAT Gateway skill with jdc-first execution and SDK fallback; GCL rollout (required, max_iter=2); covers NAT GW, SNAT rules, DNAT rules, EIP association |

## Execution Flows (Agent-Readable)

All operations follow this standardized workflow:  
**Pre-flight Checks → Execute (jdc primary / SDK fallback) → Post-execution Validation → Failure Recovery**  
Do not skip any phase.

### Execution Strategy (jdc-first with SDK Fallback)

1. **Primary Path**: Attempt `jdc` CLI first for all operations
2. **Retry Logic**: If `jdc` fails, retry up to **3 times** with exponential backoff (0s → 2s → 4s)
3. **Fallback Path**: Only use SDK/API after 3 consecutive `jdc` failures
4. **Output Preference**: When both paths succeed, prefer `jdc` output for consistency

### Operation: Create NAT Gateway

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.vpc.client.VpcClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Call `describeNatGateways` with small page | `{{user.region}}` supported | Suggest valid region |
| VPC | Verify VPC via `jdcloud-vpc-ops` | VPC exists | HALT; create VPC first |
| Elastic IPs | Verify or allocate EIPs via `jdcloud-eip-ops` | EIPs available | HALT; allocate EIPs first |
| Quota | Check NAT gateway quota | Sufficient quota | HALT; user requests quota increase |
| WAF | Validate NAT HA: at least 2 SNAT EIPs for production | WAF-REL-010 | Warn user about single-EIP risk |

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
endpoint = vpc.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution — CLI (`jdc`) [Primary Path]

**Required** when `cli_applicability: jdc-first-with-fallback`. Use `--output json` at the **top level** (before the subcommand). Do NOT use `--no-interactive` — it is not supported by jdc CLI.

```bash
jdc --output json vpc create-nat-gateway \
  --region-id "{{user.region}}" \
  --nat-gateway-name "{{user.nat_name}}" \
  --vpc-id "{{user.vpc_id}}" \
  --elastic-ip-ids '["{{user.eip_id}}"]'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpc.client.VpcClient import VpcClient
from jdcloud_sdk.services.vpc.apis.CreateNatGatewayRequest import CreateNatGatewayRequest, CreateNatGatewayParameters

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = VpcClient(credential)

nat_spec = {
    "natGatewayName": "{{user.nat_name}}",
    "vpcId": "{{user.vpc_id}}",
    "elasticIpIds": ["{{user.eip_id}}"]
}

params = CreateNatGatewayParameters(regionId="{{user.region}}", natGatewaySpec=nat_spec)
req = CreateNatGatewayRequest(parameters=params)
resp = client.send(req)
nat_id = resp.result["natGatewayId"]
```

#### Post-execution Validation

1. Capture `{{output.nat_id}}` from `$.result.natGatewayId`.
2. Poll `describeNatGateway` until `state` == `available` or timeout.

```bash
# CLI poll loop (primary path) — --output json at TOP level
for i in $(seq 1 30); do
  STATE=$(jdc --output json vpc describe-nat-gateway \
    --region-id "{{user.region}}" \
    --nat-gateway-id "{{output.nat_id}}" | jq -r '.result.natGateway.state')
  [ "$STATE" = "available" ] && break
  sleep 10
done
```

```python
# SDK poll loop (fallback, after 3 jdc failures)
from jdcloud_sdk.services.vpc.apis.DescribeNatGatewayRequest import DescribeNatGatewayRequest, DescribeNatGatewayParameters

for _ in range(30):
    dparams = DescribeNatGatewayParameters(regionId="{{user.region}}", natGatewayId="{{output.nat_id}}")
    dreq = DescribeNatGatewayRequest(parameters=dparams)
    dresp = client.send(dreq)
    state = dresp.result["natGateway"]["state"]
    if state == "available":
        break
    if state in ["error", "deleted"]:
        raise RuntimeError(f"NAT gateway creation failed: {state}")
    sleep(10)
```

3. On success, report NAT ID, name, associated EIPs, and VPC to user.
4. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `QuotaExceeded` | 0 | — | HALT; user requests quota increase |
| `InsufficientBalance` | 0 | — | HALT; user tops up account |
| `ResourceAlreadyExists` | 0 | — | Ask reuse vs new name |
| `NatGateway.VpcNotExists` | 0 | — | HALT; verify VPC ID |
| `NatGateway.ElasticIpNotExists` | 0 | — | HALT; allocate EIP first |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: Describe NAT Gateway

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc describe-nat-gateway \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.DescribeNatGatewayRequest import DescribeNatGatewayRequest, DescribeNatGatewayParameters

params = DescribeNatGatewayParameters(regionId="{{user.region}}", natGatewayId="{{user.nat_id}}")
req = DescribeNatGatewayRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["natGateway"]
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| NAT ID | `$.result.natGateway.natGatewayId` | Plain text |
| Name | `$.result.natGateway.natGatewayName` | Plain text |
| State | `$.result.natGateway.state` | available, creating, deleting, etc. |
| VPC ID | `$.result.natGateway.vpcId` | Associated VPC |
| Elastic IPs | `$.result.natGateway.elasticIpAddresses` | List of associated EIP addresses |
| SNAT Rule Count | `$.result.natGateway.snatRuleCount` | Number of SNAT rules |
| DNAT Rule Count | `$.result.natGateway.dnatRuleCount` | Number of DNAT rules |
| Description | `$.result.natGateway.description` | User description |
| Created Time | `$.result.natGateway.createdTime` | ISO 8601 format |

### Operation: List NAT Gateways

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc describe-nat-gateways \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.DescribeNatGatewaysRequest import DescribeNatGatewaysRequest, DescribeNatGatewaysParameters

params = DescribeNatGatewaysParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeNatGatewaysRequest(parameters=params)
resp = client.send(req)
nat_gateways = resp.result["natGateways"]
```

### Operation: Create SNAT Rule

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| NAT exists | `describeNatGateway` | NAT found | HALT; verify NAT ID |
| NAT state | `describeNatGateway` | `available` | Wait or suggest appropriate action |
| Subnet exists | `jdcloud-vpc-ops` | Subnet found and belongs to same VPC | HALT; verify subnet |
| EIP exists | `jdcloud-eip-ops` | EIP found | HALT; allocate EIP first |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc create-snat-rule \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}" \
  --snat-rule-spec '{"subnetId":"{{user.subnet_id}}","elasticIpIds":["{{user.eip_id}}"]}'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.CreateSnatRuleRequest import CreateSnatRuleRequest, CreateSnatRuleParameters

snat_spec = {
    "subnetId": "{{user.subnet_id}}",
    "elasticIpIds": ["{{user.eip_id}}"]
}

params = CreateSnatRuleParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}",
    snatRuleSpec=snat_spec
)
req = CreateSnatRuleRequest(parameters=params)
resp = client.send(req)
snat_id = resp.result["snatRuleId"]
```

#### Post-execution Validation

1. Capture `{{output.snat_id}}` from `$.result.snatRuleId`.
2. Poll describe NAT and verify `snatRuleCount` incremented.

### Operation: Create DNAT Rule

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| NAT exists | `describeNatGateway` | NAT found | HALT; verify NAT ID |
| NAT state | `describeNatGateway` | `available` | Wait or suggest appropriate action |
| EIP exists | `jdcloud-eip-ops` | EIP found | HALT; allocate EIP first |
| Internal port | User input | 1-65535 | Validate port range |
| External port | User input | 1-65535 | Validate port range |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc create-dnat-rule \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}" \
  --dnat-rule-spec '{"protocol":"{{user.protocol}}","privateIp":"{{user.private_ip}}","privatePort":"{{user.private_port}}","elasticIpId":"{{user.eip_id}}","publicPort":"{{user.public_port}}"}'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.CreateDnatRuleRequest import CreateDnatRuleRequest, CreateDnatRuleParameters

dnat_spec = {
    "protocol": "{{user.protocol}}",
    "privateIp": "{{user.private_ip}}",
    "privatePort": "{{user.private_port}}",
    "elasticIpId": "{{user.eip_id}}",
    "publicPort": "{{user.public_port}}"
}

params = CreateDnatRuleParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}",
    dnatRuleSpec=dnat_spec
)
req = CreateDnatRuleRequest(parameters=params)
resp = client.send(req)
dnat_id = resp.result["dnatRuleId"]
```

#### Post-execution Validation

1. Capture `{{output.dnat_id}}` from `$.result.dnatRuleId`.
2. Poll describe NAT and verify `dnatRuleCount` incremented.

### Operation: Associate Elastic IP to NAT Gateway

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| NAT exists | `describeNatGateway` | NAT found | HALT; verify NAT ID |
| NAT state | `describeNatGateway` | `available` | Wait or suggest appropriate action |
| EIP exists | `jdcloud-eip-ops` | EIP found and unassociated | HALT; allocate or disassociate EIP first |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc associate-nat-gateway \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}" \
  --elastic-ip-ids '["{{user.eip_id}}"]'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.AssociateNatGatewayRequest import AssociateNatGatewayRequest, AssociateNatGatewayParameters

params = AssociateNatGatewayParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}",
    elasticIpIds=["{{user.eip_id}}"]
)
req = AssociateNatGatewayRequest(parameters=params)
resp = client.send(req)
```

**⚠️ WAF-REL-010 Compliance:** For production NAT gateways, verify at least 2 EIPs are associated for HA. If only 1 EIP is associated, warn the user about single-point-of-failure risk.

### Operation: Disassociate Elastic IP from NAT Gateway

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: disassociating an EIP from `{{user.nat_name}}` (`{{user.nat_id}}`) will reduce outbound bandwidth and may break connectivity for SNAT/DNAT rules using this EIP.
- **MUST check** if SNAT or DNAT rules reference the EIP to be disassociated — warn user about dependent rules.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc disassociate-nat-gateway \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}" \
  --elastic-ip-ids '["{{user.eip_id}}"]'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.DisassociateNatGatewayRequest import DisassociateNatGatewayRequest, DisassociateNatGatewayParameters

params = DisassociateNatGatewayParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}",
    elasticIpIds=["{{user.eip_id}}"]
)
req = DisassociateNatGatewayRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe NAT and verify the EIP is no longer in `elasticIpAddresses`.

### Operation: Delete NAT Gateway

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.nat_name}}` (`{{user.nat_id}}`).
- **MUST** check if NAT has active SNAT/DNAT rules — warn user about dependent resources.
- **MUST check** if deleting the NAT will break internet connectivity for VPC resources — warn user about impact.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc delete-nat-gateway \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.DeleteNatGatewayRequest import DeleteNatGatewayRequest, DeleteNatGatewayParameters

params = DeleteNatGatewayParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}"
)
req = DeleteNatGatewayRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until 404 or max wait (300s).

```bash
# CLI poll loop
for i in $(seq 1 30); do
  jdc --output json vpc describe-nat-gateway \
    --region-id "{{user.region}}" \
    --nat-gateway-id "{{user.nat_id}}" 2>&1 | grep -q "NotFound" && break
  sleep 10
done
```

### Operation: Modify NAT Gateway

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| NAT exists | `describeNatGateway` | NAT found | HALT; verify NAT ID |
| NAT state | `describeNatGateway` | `available` | Wait or suggest appropriate action |

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc modify-nat-gateway \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}" \
  --nat-gateway-name "{{user.new_name}}" \
  --description "{{user.description}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.ModifyNatGatewayRequest import ModifyNatGatewayRequest, ModifyNatGatewayParameters

params = ModifyNatGatewayParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}"
)
params.setNatGatewayName("{{user.new_name}}")
params.setDescription("{{user.description}}")
req = ModifyNatGatewayRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until modification reflects.

## Other NAT Gateway Operations

### Operation: Delete SNAT Rule

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: deleting SNAT rule will break outbound internet access for the associated subnet.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc delete-snat-rule \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}" \
  --snat-rule-id "{{user.snat_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.DeleteSnatRuleRequest import DeleteSnatRuleRequest, DeleteSnatRuleParameters

params = DeleteSnatRuleParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}",
    snatRuleId="{{user.snat_id}}"
)
req = DeleteSnatRuleRequest(parameters=params)
resp = client.send(req)
```

### Operation: Delete DNAT Rule

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: deleting DNAT rule will break inbound port forwarding for the configured private IP and port.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpc delete-dnat-rule \
  --region-id "{{user.region}}" \
  --nat-gateway-id "{{user.nat_id}}" \
  --dnat-rule-id "{{user.dnat_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpc.apis.DeleteDnatRuleRequest import DeleteDnatRuleRequest, DeleteDnatRuleParameters

params = DeleteDnatRuleParameters(
    regionId="{{user.region}}",
    natGatewayId="{{user.nat_id}}",
    dnatRuleId="{{user.dnat_id}}"
)
req = DeleteDnatRuleRequest(parameters=params)
resp = client.send(req)
```

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **required** for all operations exposed by this
> skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-nat-ops` (required); `delete-nat` breaks ALL VPC internet connectivity — high risk |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-nat`, `disassociate-eip` (last EIP), `delete-snat-rule`, `delete-dnat-rule` | matches repository safety gate policy |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │
   ▼
[1] Generator (G)            ──► jdc (primary) → SDK (after 3 fails)
   │
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │
   ▼
[3] Orchestrator decider
   ├─ Safety=0 / blocking   → ABORT
   ├─ all pass              → RETURN
   ├─ iter<2 & not all pass → RETRY (inject suggestions)
   └─ iter=2 & not all pass → RETURN_BEST
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)

### Integration with existing flows

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK
access. The Orchestrator (O) owns the loop and persists the GCL trace.

### Operation-specific behavior

- **`create nat gateway`** — Must validate EIPs exist and VPC exists. WAF-REL-010: warn if fewer than 2 EIPs for production NAT.
- **`create snat rule`** — Subnet must belong to same VPC as the NAT gateway.
- **`create dnat rule`** — Protocol must be TCP/UDP. Private IP must be reachable within the VPC.
- **`disassociate eip`** — If disassociating the last EIP, SNAT/DNAT traffic will fail. Require explicit `confirm=EIP_LAST`.
- **`delete nat gateway`** — **Breaks ALL internet connectivity** for VPC resources. `confirm=DELETE` required; for prod-tagged NATs, `confirm=DELETE_PROD` also required. Must include pre-delete snapshot of SNAT/DNAT rules + associated EIPs.
- **`delete snat rule`** — Breaks outbound internet for the associated subnet. Require explicit confirmation.
- **`delete dnat rule`** — Breaks inbound port forwarding. Require explicit confirmation.
- **WAF-PERF-049** — Monitor NAT bandwidth utilization. If bandwidth exceeds 80% of spec, recommend upsizing.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

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
   endpoint = vpc.jdcloud-api.com
   scheme = https
   timeout = 20
   CONFIGEOF
   printf "%s" "default" > /tmp/jdc-home/.jdc/current
   ```

4. **Verify Configuration**:
   ```bash
   # Quick validation (--output json BEFORE subcommand)
   jdc --output json vpc describe-nat-gateways --region-id cn-north-1 --page-number 1 --page-size 1
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
- **High Availability (WAF-REL-010):** Associate at least 2 EIPs with production NAT gateways for SNAT HA. A single EIP is a single point of failure for outbound internet access.
- **Bandwidth Planning (WAF-PERF-049):** Monitor NAT gateway bandwidth utilization. When utilization exceeds 80% for sustained periods, upgrade the NAT specification.
- **SNAT vs DNAT:** Use SNAT for outbound internet access from private subnets. Use DNAT for inbound port forwarding to private instances.
- **Security:** Only expose necessary ports via DNAT rules. Audit SNAT rules periodically to ensure only required subnets have internet access.
- **Cost:** Delete unused NAT gateways and rules. Right-size NAT specifications based on actual bandwidth usage.