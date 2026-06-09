---
name: jdcloud-vpn-ops
description: >-
  Use when the user needs to deploy, configure, manage, troubleshoot, or monitor
  JD Cloud VPN (VPN网关/连接) resources via API, SDK, or the `jdc` CLI. Trigger
  when the user mentions VPN, VPN网关, VPN Gateway, VPN连接, VPN Connection,
  Customer Gateway, 客户网关, IPSec VPN, site-to-site VPN, or related networking
  tasks — even if they do not explicitly mention 'JD Cloud' or 'API'. Also use
  when the user asks about `jdc` CLI commands, `jdcloud_sdk` usage, OpenAPI
  operations, or automation scripts for this product. Do not use for billing-only
  or IAM-only tasks; delegate to the appropriate dedicated skill.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (dual-path skills).
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-06-08"
  runtime: Harness AI Agent
  api_profile: "JD Cloud VPN API - https://vpn.jdcloud-api.com/v1"
  cli_applicability: dual-path
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    VPN operations are exposed under the 'vpn' product group in `jdc`.
    Confirmed via `jdc vpn --help` showing describe-vpn-gateways,
    create-vpn-gateway, delete-vpn-gateway, create-customer-gateway,
    describe-customer-gateways, delete-customer-gateway, create-vpn-connection,
    describe-vpn-connections, and delete-vpn-connection subcommands.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
  gcl_classification: recommended
  gcl_max_iter: 3
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud VPN (VPN网关/连接) Operations Skill

## Overview

JD Cloud VPN (VPN网关/连接) provides secure site-to-site IPsec VPN connectivity between JD Cloud VPCs and on-premises networks or other cloud environments. The service comprises three primary resource types:

- **VpnGateway (VPN网关)**: The JD Cloud-side VPN endpoint, bound to a VPC.
- **CustomerGateway (客户网关)**: Represents the on-premises or remote-side VPN endpoint.
- **VpnConnection (VPN连接)**: The IPSec/IKE tunnel between a VpnGateway and a CustomerGateway.

This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **dual-path execution** (official **SDK/API** and matching **`jdc` CLI** flows), response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** Official `jdc` supports this product under the `vpn` subcommand group. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the SDK step **and** the `jdc` step for every operation the CLI exposes. If the CLI covers **only part** of the API, add a **coverage gap** table (SDK-only operations) in `references/cli-usage.md`.

### Path Preference (SDK vs jdc)

When both paths exist, prefer `jdc` for quick ad-hoc operations and shell automation. Prefer SDK for complex multi-step workflows, CI/CD pipelines, and integration tests with conditional logic.

### Critical jdc CLI Behavioral Notes (from empirical testing)

**Failure 1: `--output json` must be TOP-LEVEL, not subcommand-level**
The `--output json` argument is defined in the base controller, not in individual subcommands. Cement's nested argparse structure restricts `--output` to be placed **before** the subcommand.

```
# CORRECT (works):
jdc --output json vpn describe-vpn-gateways --region-id cn-north-1 --page-number 1 --page-size 100

# WRONG (fails with "unrecognized arguments: --output json"):
jdc vpn describe-vpn-gateways --region-id cn-north-1 --page-number 1 --page-size 100 --output json
```

**Failure 2: jdc CLI does NOT support `--no-interactive`**
The `--no-interactive` flag does not exist in the jdc CLI argument definition. Using it will cause an `unrecognized arguments` error. Omit this flag entirely.

**Failure 3: jdc CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables**
The CLI's `ProfileManager` class reads credentials exclusively from `~/.jdc/config` (INI format). Setting environment variables alone is insufficient. The config file must be pre-created.

**Failure 4: `PermissionError` on `~/.jdc/` directory creation**
In sandboxed environments where home is not writable, redirect `HOME` to a writable path and pre-create config files before running `jdc`.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User explicitly mentions "JD Cloud VPN", "VPN网关", "VPN Gateway", "VPN连接", "VPN Connection", "客户网关", "Customer Gateway", "IPSec VPN", "site-to-site VPN"
- User wants to **deploy**, **configure**, **troubleshoot**, or **monitor** VPN resources via automation
- Task involves CRUD operations on VpnGateway, CustomerGateway, or VpnConnection
- Task involves IPSec/IKE parameter configuration or tunnel negotiation issues
- Keywords detected: createVpnGateway, describeVpnGateways, createCustomerGateway, createVpnConnection, deleteVpnConnection, vpn tunnel
- User describes hybrid cloud connectivity, on-premises to cloud VPN, or VPC-to-VPC VPN

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about VPC / subnet / route table / security group management → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms only → delegate to: `jdcloud-cloudmonitor-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If VPN Gateway requires a VPC, verify or create the VPC via `jdcloud-vpc-ops` first.
- If VPN Connection requires route table updates, delegate route table operations to `jdcloud-vpc-ops`.
- Multi-product requests: handle each product with its dedicated skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.vpn_gateway_id}}` | User-supplied VPN gateway ID | Ask once; reuse |
| `{{user.vpn_gateway_name}}` | User-supplied VPN gateway name | Ask once; reuse |
| `{{user.customer_gateway_id}}` | User-supplied customer gateway ID | Ask once; reuse |
| `{{user.customer_gateway_name}}` | User-supplied customer gateway name | Ask once; reuse |
| `{{user.vpn_connection_id}}` | User-supplied VPN connection ID | Ask once; reuse |
| `{{user.vpn_connection_name}}` | User-supplied VPN connection name | Ask once; reuse |
| `{{user.vpc_id}}` | User-supplied VPC ID | Ask once; reuse |
| `{{user.remote_ip}}` | User-supplied remote/public IP of customer gateway | Ask once; reuse |
| `{{output.vpn_gateway_id}}` | From last API or CLI JSON response | Parse from `$.result.vpnGatewayId` |
| `{{output.customer_gateway_id}}` | From last API or CLI JSON response | Parse from `$.result.customerGatewayId` |
| `{{output.vpn_connection_id}}` | From last API or CLI JSON response | Parse from `$.result.vpnConnectionId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. This applies to all execution flows (SDK, CLI, and debugging scripts).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://vpn.jdcloud-api.com/v1/regions/{regionId}/vpnGateways/...`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-06-08T10:00:00+08:00`).
- **Idempotency:** VPN Gateway creation with the same name in the same VPC may result in duplicate names; agent should check for existing resources before creating.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create VpnGateway | `$.result.vpnGatewayId` | string | New VPN gateway ID |
| Describe VpnGateway | `$.result.vpnGateway.state` | string | VPN GW state (available, creating, deleting, etc.) |
| List VpnGateways | `$.result.vpnGateways[*].vpnGatewayId` | array | All VPN gateway IDs |
| Create CustomerGateway | `$.result.customerGatewayId` | string | New customer gateway ID |
| Create VpnConnection | `$.result.vpnConnectionId` | string | New VPN connection ID |
| Modify / Delete | `$.requestId` or `$.error` | string / object | Per spec |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create VpnGateway | — | `available` | 10s | 300s |
| Delete VpnGateway | `available` | (404 on describe) | 10s | 300s |
| Create CustomerGateway | — | `available` | 5s | 120s |
| Delete CustomerGateway | `available` | (404 on describe) | 5s | 120s |
| Create VpnConnection | — | `available` | 10s | 300s |
| Delete VpnConnection | `available` | (404 on describe) | 10s | 300s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-08 | Initial VPN skill (dual-path); covers VpnGateway, CustomerGateway, VpnConnection; GCL recommended (max_iter=3) |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight Checks → Execute (SDK and `jdc`) → Post-execution Validation → Failure Recovery**. Do not skip phases.

**Preference hint:** Prefer `jdc` for quick ad-hoc operations; prefer SDK for complex workflows and CI/CD.

### Execution Strategy (jdc-first with SDK Fallback)

1. **Primary Path**: Attempt `jdc` CLI first for all operations
2. **Retry Logic**: If `jdc` fails, retry up to **3 times** with exponential backoff (0s → 2s → 4s)
3. **Fallback Path**: Only use SDK/API after 3 consecutive `jdc` failures
4. **Output Preference**: When both paths succeed, prefer `jdc` output for consistency

---

### Operation: Create VpnGateway

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| CLI / deps | `jdc --version` | Exit code 0 | Retry up to 3 times; then fall back to SDK |
| SDK / deps | `import jdcloud_sdk.services.vpn.client.VpnClient` | No import error | Document install pin (fallback path) |
| Credentials | Construct credential from env or CLI config | Non-empty keys | HALT; user configures env |
| Region | Call `describeVpnGateways` with small page | `{{user.region}}` supported | Suggest valid region |
| VPC | Verify VPC via `jdcloud-vpc-ops` | VPC exists | HALT; create VPC first |
| Quota | Check VPN gateway quota | Sufficient quota | HALT; user requests quota increase |

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
endpoint = vpn.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json vpn create-vpn-gateway \
  --region-id "{{user.region}}" \
  --vpn-gateway-name "{{user.vpn_gateway_name}}" \
  --vpc-id "{{user.vpc_id}}" \
  --description "{{user.description|default:''}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpn.client.VpnClient import VpnClient
from jdcloud_sdk.services.vpn.apis.CreateVpnGatewayRequest import (
    CreateVpnGatewayRequest, CreateVpnGatewayParameters
)

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = VpnClient(credential)

gw_spec = {
    "vpnGatewayName": "{{user.vpn_gateway_name}}",
    "vpcId": "{{user.vpc_id}}",
    "description": "{{user.description|default:''}}"
}

params = CreateVpnGatewayParameters(
    regionId="{{user.region}}",
    vpnGatewaySpec=gw_spec
)
req = CreateVpnGatewayRequest(parameters=params)
resp = client.send(req)
vpn_gateway_id = resp.result["vpnGatewayId"]
```

#### Post-execution Validation

1. Capture `{{output.vpn_gateway_id}}` from `$.result.vpnGatewayId`.
2. Poll `describeVpnGateway` until `state` == `available` or timeout.

```bash
# CLI poll loop (primary path)
for i in $(seq 1 30); do
  STATE=$(jdc --output json vpn describe-vpn-gateway \
    --region-id "{{user.region}}" \
    --vpn-gateway-id "{{output.vpn_gateway_id}}" | jq -r '.result.vpnGateway.state')
  [ "$STATE" = "available" ] && break
  sleep 10
done
```

```python
# SDK poll loop (fallback)
from jdcloud_sdk.services.vpn.apis.DescribeVpnGatewayRequest import (
    DescribeVpnGatewayRequest, DescribeVpnGatewayParameters
)

for _ in range(30):
    dparams = DescribeVpnGatewayParameters(
        regionId="{{user.region}}",
        vpnGatewayId="{{output.vpn_gateway_id}}"
    )
    dreq = DescribeVpnGatewayRequest(parameters=dparams)
    dresp = client.send(dreq)
    state = dresp.result["vpnGateway"]["state"]
    if state == "available":
        break
    if state in ["error", "deleted"]:
        raise RuntimeError(f"VPN gateway creation failed: {state}")
    sleep(10)
```

3. On success, report VPN Gateway ID, name, VPC, and state to user.
4. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidParameter` / 400 | 0–1 | — | Fix args per OpenAPI; retry once |
| `QuotaExceeded` | 0 | — | HALT; user requests quota increase |
| `InsufficientBalance` | 0 | — | HALT; user tops up account |
| `ResourceAlreadyExists` | 0 | — | Ask reuse vs new name |
| `VpnGateway.VpcNotExists` | 0 | — | HALT; verify VPC ID |
| Throttling / 429 | 3 | exponential | Back off; respect Retry-After |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

---

### Operation: Describe VpnGateway

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn describe-vpn-gateway \
  --region-id "{{user.region}}" \
  --vpn-gateway-id "{{user.vpn_gateway_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DescribeVpnGatewayRequest import (
    DescribeVpnGatewayRequest, DescribeVpnGatewayParameters
)

params = DescribeVpnGatewayParameters(
    regionId="{{user.region}}",
    vpnGatewayId="{{user.vpn_gateway_id}}"
)
req = DescribeVpnGatewayRequest(parameters=params)
resp = client.send(req)
# Access: resp.result["vpnGateway"]
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| VPN Gateway ID | `$.result.vpnGateway.vpnGatewayId` | Plain text |
| Name | `$.result.vpnGateway.vpnGatewayName` | Plain text |
| State | `$.result.vpnGateway.state` | available, creating, deleting, etc. |
| VPC ID | `$.result.vpnGateway.vpcId` | Associated VPC |
| Created Time | `$.result.vpnGateway.createdTime` | ISO 8601 format |

---

### Operation: Describe VpnGateways (List)

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn describe-vpn-gateways \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DescribeVpnGatewaysRequest import (
    DescribeVpnGatewaysRequest, DescribeVpnGatewaysParameters
)

params = DescribeVpnGatewaysParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeVpnGatewaysRequest(parameters=params)
resp = client.send(req)
vpn_gateways = resp.result["vpnGateways"]
```

---

### Operation: Delete VpnGateway

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.vpn_gateway_name}}` (`{{user.vpn_gateway_id}}`).
- **MUST** check if the VPN gateway has active VPN connections — warn user about dependent resources.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn delete-vpn-gateway \
  --region-id "{{user.region}}" \
  --vpn-gateway-id "{{user.vpn_gateway_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DeleteVpnGatewayRequest import (
    DeleteVpnGatewayRequest, DeleteVpnGatewayParameters
)

params = DeleteVpnGatewayParameters(
    regionId="{{user.region}}",
    vpnGatewayId="{{user.vpn_gateway_id}}"
)
req = DeleteVpnGatewayRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until 404 or max wait (300s).

```bash
# CLI poll loop
for i in $(seq 1 30); do
  jdc --output json vpn describe-vpn-gateway \
    --region-id "{{user.region}}" \
    --vpn-gateway-id "{{user.vpn_gateway_id}}" 2>&1 | grep -q "NotFound" && break
  sleep 10
done
```

---

### Operation: Create CustomerGateway

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Remote IP | Validate `{{user.remote_ip}}` | Valid IPv4 address | HALT; ask for valid IP |
| Region | Call `describeCustomerGateways` with small page | `{{user.region}}` supported | Suggest valid region |

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json vpn create-customer-gateway \
  --region-id "{{user.region}}" \
  --customer-gateway-name "{{user.customer_gateway_name}}" \
  --ip-address "{{user.remote_ip}}" \
  --description "{{user.description|default:''}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.CreateCustomerGatewayRequest import (
    CreateCustomerGatewayRequest, CreateCustomerGatewayParameters
)

cg_spec = {
    "customerGatewayName": "{{user.customer_gateway_name}}",
    "ipAddress": "{{user.remote_ip}}",
    "description": "{{user.description|default:''}}"
}

params = CreateCustomerGatewayParameters(
    regionId="{{user.region}}",
    customerGatewaySpec=cg_spec
)
req = CreateCustomerGatewayRequest(parameters=params)
resp = client.send(req)
customer_gateway_id = resp.result["customerGatewayId"]
```

#### Post-execution Validation

1. Capture `{{output.customer_gateway_id}}` from `$.result.customerGatewayId`.
2. Poll `describeCustomerGateway` until `state` == `available`.

---

### Operation: Describe CustomerGateway

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn describe-customer-gateway \
  --region-id "{{user.region}}" \
  --customer-gateway-id "{{user.customer_gateway_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DescribeCustomerGatewayRequest import (
    DescribeCustomerGatewayRequest, DescribeCustomerGatewayParameters
)

params = DescribeCustomerGatewayParameters(
    regionId="{{user.region}}",
    customerGatewayId="{{user.customer_gateway_id}}"
)
req = DescribeCustomerGatewayRequest(parameters=params)
resp = client.send(req)
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| Customer Gateway ID | `$.result.customerGateway.customerGatewayId` | Plain text |
| Name | `$.result.customerGateway.customerGatewayName` | Plain text |
| IP Address | `$.result.customerGateway.ipAddress` | Remote public IP |
| State | `$.result.customerGateway.state` | available, creating, etc. |

---

### Operation: Describe CustomerGateways (List)

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn describe-customer-gateways \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DescribeCustomerGatewaysRequest import (
    DescribeCustomerGatewaysRequest, DescribeCustomerGatewaysParameters
)

params = DescribeCustomerGatewaysParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeCustomerGatewaysRequest(parameters=params)
resp = client.send(req)
customer_gateways = resp.result["customerGateways"]
```

---

### Operation: Delete CustomerGateway

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.customer_gateway_name}}` (`{{user.customer_gateway_id}}`).
- **MUST** check if the customer gateway is referenced by active VPN connections — warn user about dependent resources.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn delete-customer-gateway \
  --region-id "{{user.region}}" \
  --customer-gateway-id "{{user.customer_gateway_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DeleteCustomerGatewayRequest import (
    DeleteCustomerGatewayRequest, DeleteCustomerGatewayParameters
)

params = DeleteCustomerGatewayParameters(
    regionId="{{user.region}}",
    customerGatewayId="{{user.customer_gateway_id}}"
)
req = DeleteCustomerGatewayRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until 404 or max wait (120s).

---

### Operation: Create VpnConnection

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| VPN Gateway | `describeVpnGateway` | `available` | HALT; verify VPN GW ID |
| Customer Gateway | `describeCustomerGateway` | `available` | HALT; verify CG ID |
| No duplicate | `describeVpnConnections` with filters | No existing connection with same GW pair | Warn user |

#### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json vpn create-vpn-connection \
  --region-id "{{user.region}}" \
  --vpn-connection-name "{{user.vpn_connection_name}}" \
  --vpn-gateway-id "{{user.vpn_gateway_id}}" \
  --customer-gateway-id "{{user.customer_gateway_id}}" \
  --ike-version "{{user.ike_version|default:'v2'}}" \
  --psk "{{user.psk}}" \
  --local-subnets '[]' \
  --remote-subnets '[]'
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.CreateVpnConnectionRequest import (
    CreateVpnConnectionRequest, CreateVpnConnectionParameters
)

conn_spec = {
    "vpnConnectionName": "{{user.vpn_connection_name}}",
    "vpnGatewayId": "{{user.vpn_gateway_id}}",
    "customerGatewayId": "{{user.customer_gateway_id}}",
    "ikeVersion": "{{user.ike_version|default:'v2'}}",
    "psk": "{{user.psk}}",
    "localSubnets": {{user.local_subnets|default:[]}},
    "remoteSubnets": {{user.remote_subnets|default:[]}}
}

params = CreateVpnConnectionParameters(
    regionId="{{user.region}}",
    vpnConnectionSpec=conn_spec
)
req = CreateVpnConnectionRequest(parameters=params)
resp = client.send(req)
vpn_connection_id = resp.result["vpnConnectionId"]
```

#### Post-execution Validation

1. Capture `{{output.vpn_connection_id}}` from `$.result.vpnConnectionId`.
2. Poll `describeVpnConnection` until `state` == `available`.

---

### Operation: Describe VpnConnection

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn describe-vpn-connection \
  --region-id "{{user.region}}" \
  --vpn-connection-id "{{user.vpn_connection_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DescribeVpnConnectionRequest import (
    DescribeVpnConnectionRequest, DescribeVpnConnectionParameters
)

params = DescribeVpnConnectionParameters(
    regionId="{{user.region}}",
    vpnConnectionId="{{user.vpn_connection_id}}"
)
req = DescribeVpnConnectionRequest(parameters=params)
resp = client.send(req)
```

#### Present to User

| Field | JSON Path | Notes |
|-------|-----------|-------|
| VPN Connection ID | `$.result.vpnConnection.vpnConnectionId` | Plain text |
| Name | `$.result.vpnConnection.vpnConnectionName` | Plain text |
| State | `$.result.vpnConnection.state` | available, pending, down, etc. |
| VPN Gateway ID | `$.result.vpnConnection.vpnGatewayId` | JD Cloud-side GW |
| Customer Gateway ID | `$.result.vpnConnection.customerGatewayId` | Remote-side GW |
| IKE Version | `$.result.vpnConnection.ikeVersion` | v1 or v2 |
| PSK | `<masked>` | Never display plaintext PSK |
| Local Subnets | `$.result.vpnConnection.localSubnets` | CIDR list |
| Remote Subnets | `$.result.vpnConnection.remoteSubnets` | CIDR list |

---

### Operation: Describe VpnConnections (List)

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn describe-vpn-connections \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DescribeVpnConnectionsRequest import (
    DescribeVpnConnectionsRequest, DescribeVpnConnectionsParameters
)

params = DescribeVpnConnectionsParameters(regionId="{{user.region}}")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeVpnConnectionsRequest(parameters=params)
resp = client.send(req)
vpn_connections = resp.result["vpnConnections"]
```

---

### Operation: Delete VpnConnection

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.vpn_connection_name}}` (`{{user.vpn_connection_id}}`).
- **MUST** warn user: deleting an active VPN connection will **break encrypted connectivity** between the VPC and the remote network.
- **MUST NOT** proceed without clear user assent.

#### Execution (CLI) [Primary Path]

```bash
jdc --output json vpn delete-vpn-connection \
  --region-id "{{user.region}}" \
  --vpn-connection-id "{{user.vpn_connection_id}}"
```

#### Execution (SDK Fallback — after 3 jdc failures)

```python
from jdcloud_sdk.services.vpn.apis.DeleteVpnConnectionRequest import (
    DeleteVpnConnectionRequest, DeleteVpnConnectionParameters
)

params = DeleteVpnConnectionParameters(
    regionId="{{user.region}}",
    vpnConnectionId="{{user.vpn_connection_id}}"
)
req = DeleteVpnConnectionRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Poll describe until 404 or max wait (300s).

```bash
# CLI poll loop
for i in $(seq 1 30); do
  jdc --output json vpn describe-vpn-connection \
    --region-id "{{user.region}}" \
    --vpn-connection-id "{{user.vpn_connection_id}}" 2>&1 | grep -q "NotFound" && break
  sleep 10
done
```

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **recommended** for all operations exposed by this
> skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-vpn-ops` (recommended); VPN connectivity is mission-critical for hybrid cloud |
| `rubric_version` | `v1` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-vpn-gateway`, `delete-customer-gateway`, `delete-vpn-connection` | matches repository safety gate policy |

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
   ├─ iter<3 & not all pass → RETRY (inject suggestions)
   └─ iter=3 & not all pass → RETURN_BEST
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

- **`create vpn gateway`** — Must validate VPC exists. VPN GW must be in `available` state before creating connections.
- **`create customer gateway`** — Remote IP must be a valid public IPv4 address. Must not duplicate existing CG with same IP.
- **`create vpn connection`** — Both VPN GW and CG must be `available`. PSK length and complexity should meet security standards (min 8 chars, avoid dictionary words). Subnet CIDRs must not overlap.
- **`delete vpn gateway`** — Must verify no active VPN connections exist. Deleting a VPN GW with active connections may fail or leave dangling state.
- **`delete customer gateway`** — Must verify no active VPN connections reference this CG.
- **`delete vpn connection`** — **Breaks encrypted tunnel** between VPC and remote network. `confirm=DELETE` required. For prod-tagged resources, `confirm=DELETE_PROD` also required.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

1. **Install uv** (system-wide, one-time per machine):

   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Bootstrap Python environment** (idempotent):

   ```bash
   uv venv --python 3.10
   source .venv/bin/activate
   uv pip install jdcloud_cli jdcloud_sdk
   jdc --version
   ```

3. **Configure Credentials**:

   **Method A: SDK (env vars)**
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```

   **Method B: CLI (`~/.jdc/config` INI)**
   ```bash
   export HOME=/tmp/jdc-home
   mkdir -p /tmp/jdc-home/.jdc
   cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
   [default]
   access_key = {{env.JDC_ACCESS_KEY}}
   secret_key = {{env.JDC_SECRET_KEY}}
   region_id = {{env.JDC_REGION}}
   endpoint = vpn.jdcloud-api.com
   scheme = https
   timeout = 20
   CONFIGEOF
   printf "%s" "default" > /tmp/jdc-home/.jdc/current
   ```

4. **Verify Configuration**:
   ```bash
   jdc --output json vpn describe-vpn-gateways --region-id cn-north-1 --page-number 1 --page-size 1
   ```

> **Security:** Never commit `.env` to version control (already in `.gitignore`). All credentials use `{{env.*}}` placeholders in generated Skills — never real values.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)
- [GCL Rubric](references/rubric.md)
- [GCL Prompt Templates](references/prompt-templates.md)

## Operational Best Practices

- **Least privilege:** IAM policies scoped to required VPN APIs only.
- **High Availability:** For production, consider redundant VPN connections across different customer gateway endpoints.
- **Security:** Use IKEv2 instead of IKEv1 when possible. Use strong PSKs (minimum 16 characters, random) and rotate periodically.
- **Network Planning:** Ensure local and remote subnet CIDRs do not overlap. Update route tables on both sides to route traffic through the VPN tunnel.
- **Monitoring:** Monitor VPN tunnel state and packet loss. Alert on tunnel `down` state.
- **Cost:** Delete unused VPN gateways and connections. VPN gateways incur charges even when idle.