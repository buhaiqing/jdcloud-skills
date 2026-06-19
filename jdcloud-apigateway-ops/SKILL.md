---
name: jdcloud-apigateway-ops
description: >-
  Use when managing JD Cloud API Gateway (API网关) resources — create and manage
  API groups, APIs, deployments, throttling policies, and authentication.
  Works with "API Gateway", "API网关", "apigateway", "API分组", "流控策略"
  without saying "JD Cloud" explicitly. NOT for Function Compute triggers,
  load balancer routing, or general network ACLs.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints. SDK-only skill; `jdc` CLI does NOT support
  API Gateway as of SDK version 1.6.26.
metadata:
  author: buhaiqing
  version: "1.1.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "API Gateway API v1.0 - https://docs.jdcloud.com/cn/apigateway/api"
  cli_applicability: sdk-only
  cli_version_locked: null
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Official `jdc` CLI does NOT support API Gateway operations.
    Verified via `jdc --help` product list and CLI documentation at
    https://docs.jdcloud.com/cn/cli. SDK-only execution path required.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud API Gateway Operations Skill

## Overview
JD Cloud API Gateway (API网关) is a fully managed service that makes it easy for developers to create, publish, maintain, monitor, and secure APIs at any scale. It acts as a "front door" for applications to access data, business logic, or functionality from backend services.

This skill covers:
- **API Group Management**: Create, update, delete, and list API groups
- **API Management**: Create, update, delete, describe, and list APIs within groups
- **Deployment Management**: Deploy APIs to stages (environments), rollback deployments
- **Throttling Policy**: Create, bind, and manage rate limiting policies
- **Authentication**: Configure API key, IAM, or open authentication
- **Monitoring & Logs**: Query API call metrics and access logs

### CLI applicability (repository policy)

- **`cli_applicability: sdk-only`:** Official `jdc` CLI does **not** support API Gateway. This skill uses **SDK/API only** execution path.
- **SDK Package**: `jdcloud_sdk.services.apigateway`
- **Fallback**: No CLI fallback available; SDK is the only execution path.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "API Gateway" OR "API网关" OR "apigateway" OR "API分组"
- Task involves creating, updating, deleting, or describing APIs or API groups
- Task involves deploying APIs to stages or managing deployments
- Task involves configuring throttling policies (流控策略), rate limiting
- Task involves setting up API authentication (API key, IAM, open)
- Task keywords: create-api-group, create-api, deploy-api, throttling-policy, api-key, stage, 分组, 接口, 发布, 流控, 限流

### SHOULD NOT Use This Skill When
- Task is about Function Compute service/function management → delegate to: `jdcloud-fc-ops`
- Task is about load balancer configuration → delegate to: `jdcloud-clb-ops`
- Task is about WAF / web application firewall → delegate to: `jdcloud-waf-ops`
- Task is about VM/container-based computing → delegate to: `jdcloud-vm-ops` or `jdcloud-kubernetes-ops`
- Task is about monitoring/alarms for APIs → delegate to: `jdcloud-cloudmonitor-ops`
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`

### Delegation Rules
- If user wants API Gateway to trigger Function Compute functions, create function first via `jdcloud-fc-ops`, then configure API route here
- If user wants API Gateway behind WAF, configure WAF via `jdcloud-waf-ops` after API Gateway setup
- If user wants custom domain for APIs, domain/DNS management may be needed first

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.api_group_name}}` | API group name | Ask once; reuse |
| `{{user.api_group_id}}` | API group ID | Ask or parse from output |
| `{{user.api_name}}` | API name within group | Ask once; reuse |
| `{{user.api_id}}` | API ID | Parse from output |
| `{{user.stage_name}}` | Deployment stage (e.g., prod, test) | Ask once; reuse; default `test` |
| `{{user.backend_type}}` | Backend type (http, fc, mock) | Ask once; reuse |
| `{{user.backend_url}}` | Backend service URL | Ask once; reuse |
| `{{user.policy_name}}` | Throttling policy name | Ask once; reuse |
| `{{user.policy_id}}` | Throttling policy ID | Parse from output |
| `{{output.api_group_id}}` | Created API group ID | Parse from `$.result.apiGroupId` |
| `{{output.api_id}}` | Created API ID | Parse from `$.result.apiId` |
| `{{output.policy_id}}` | Created policy ID | Parse from `$.result.policyId` |
| `{{output.deployment_id}}` | Deployment ID | Parse from `$.result.deploymentId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes.
- **SDK Namespace**: `jdcloud_sdk.services.apigateway`
- **Endpoint**: `apigateway.jdcloud-api.com`

### Example Response Field Table

| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create ApiGroup | `$.result.apiGroupId` | string | Unique API group identifier |
| Describe ApiGroups | `$.result.apiGroups[*].apiGroupId` | array | API group IDs |
| Create Api | `$.result.apiId` | string | Unique API identifier |
| Describe Apis | `$.result.apis[*].apiId` | array | API IDs in group |
| Deploy Api | `$.result.deploymentId` | string | Deployment identifier |
| Create Throttling Policy | `$.result.policyId` | string | Policy identifier |
| Bind Throttling Policy | `$.result.requestId` | string | Request ID for confirmation |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create ApiGroup | — | `Active` | 2s | 30s |
| Create Api | — | `UnDeployed` | 2s | 30s |
| Deploy Api | `UnDeployed` / `PreviousStage` | `Deployed` | 5s | 60s |
| Delete Api | any | absent | 2s | 30s |
| Delete ApiGroup | any | absent | 5s | 60s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, recommended) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for SDK parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.0.0 | 2026-06-08 | Initial SDK-only skill for JD Cloud API Gateway |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK) → Validate → Recover**. No CLI path available.

### Operation: Create ApiGroup

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | `import jdcloud_sdk` | No import error | Document install steps |
| Credentials | `os.environ["JDC_ACCESS_KEY"]` | Non-empty | HALT; user configures env |
| Group name | Validate format | Valid string (1–128 chars) | Reject; ask for valid name |
| Region | Check region availability | `{{user.region}}` supported | Suggest valid region |

#### Execution (Python SDK)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.apigateway.client import ApigatewayClient
from jdcloud_sdk.services.apigateway.apis.create_api_group_request import CreateApiGroupRequest

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = ApigatewayClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

req = CreateApiGroupRequest(
    regionId="{{user.region}}",
    groupName="{{user.api_group_name}}",
    description="Created via skill"
)
resp = client.createApiGroup(req)
print(f"API Group created: {resp.result.apiGroupId}")
```

#### Post-execution Validation

1. Parse `{{output.api_group_id}}` from `resp.result.apiGroupId`
2. Poll **DescribeApiGroups** until group appears with status `Active`
3. Report group ID and name to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `GroupAlreadyExists` | 0 | — | Ask user to use existing group or new name |
| `InvalidParameter` | 0 | — | Fix group name; retry |
| `QuotaExceeded` | 0 | — | HALT; suggest quota increase |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Describe ApiGroups

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.describe_api_groups_request import DescribeApiGroupsRequest

req = DescribeApiGroupsRequest(
    regionId="{{user.region}}",
    pageNumber=1,
    pageSize=50
)
resp = client.describeApiGroups(req)

for group in resp.result.apiGroups:
    print(f"{group.apiGroupId} | {group.groupName} | {group.status}")
```

#### Present to User

| Field | Path | Notes |
|-------|------|-------|
| ID | `apiGroupId` | Plain text |
| Name | `groupName` | Plain text |
| Status | `status` | `Active`, `Deleting`, etc. |
| Created time | `createTime` | ISO 8601 format |

---

### Operation: Delete ApiGroup

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: "Delete API group `{{user.api_group_name}}` (`{{user.api_group_id}}`)? All APIs within this group will also be deleted. This is irreversible."
- **MUST NOT** proceed without clear user assent
- Check if group contains APIs; warn user about cascade deletion

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Group exists | DescribeApiGroups | Group found | Already deleted |
| No active deployments | DescribeApis in group | No `Deployed` APIs | HALT; undeploy APIs first |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.delete_api_group_request import DeleteApiGroupRequest

req = DeleteApiGroupRequest(
    regionId="{{user.region}}",
    apiGroupId="{{user.api_group_id}}"
)
resp = client.deleteApiGroup(req)
print(f"API Group deleted: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeApiGroups** until group no longer appears (404 or not in list)
2. Max wait: 60 seconds
3. Confirm deletion to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `GroupNotFound` | 0 | — | Already deleted; report success |
| `GroupHasDeployedApis` | 0 | — | HALT; undeploy APIs first |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Create Api

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| API group exists | DescribeApiGroups | Group found | HALT; create group first |
| API name | Validate format | Valid string (1–128 chars) | Reject; ask for valid name |
| Backend type | Validate | `http`, `fc`, or `mock` | Suggest valid type |
| Backend URL | Validate URL format | Valid URL (for http type) | Reject; ask for valid URL |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.create_api_request import CreateApiRequest

req = CreateApiRequest(
    regionId="{{user.region}}",
    apiGroupId="{{user.api_group_id}}",
    apiName="{{user.api_name}}",
    description="Created via skill",
    requestConfig={
        "requestPath": "/hello",
        "requestMethod": "GET",
        "requestProtocol": "HTTP"
    },
    serviceConfig={
        "serviceProtocol": "HTTP",
        "serviceAddress": "{{user.backend_url}}",
        "servicePath": "/backend/hello",
        "serviceMethod": "GET",
        "serviceTimeout": 10000
    },
    authType="no_auth"  # or "app_auth", "jdcloud_auth"
)
resp = client.createApi(req)
print(f"API created: {resp.result.apiId}")
```

#### Post-execution Validation

1. Parse `{{output.api_id}}` from `resp.result.apiId`
2. Poll **DescribeApis** until API appears with status `UnDeployed`
3. Report API ID, name, and request path to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `ApiAlreadyExists` | 0 | — | Ask user to use existing API or new name |
| `InvalidParameter` | 0 | — | Fix request config; retry |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Deploy Api

#### Pre-flight (Safety Gate)

- **MUST** warn user: "Deploying API `{{user.api_name}}` to stage `{{user.stage_name}}` will make it live and accessible to callers."
- For `prod` stage, **MUST** obtain explicit confirmation

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| API exists | DescribeApis | API found | HALT; create API first |
| Stage valid | Check supported stages | `test`, `pre`, `prod`, etc. | Suggest valid stages |
| API not already deployed to stage | DescribeDeployments | No active deployment to stage | Warn about overwrite |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.deploy_api_request import DeployApiRequest

req = DeployApiRequest(
    regionId="{{user.region}}",
    apiGroupId="{{user.api_group_id}}",
    apiId="{{user.api_id}}",
    stageName="{{user.stage_name}}",
    description="Deployed via skill"
)
resp = client.deployApi(req)
print(f"API deployed: {resp.result.deploymentId}")
```

#### Post-execution Validation

1. Parse `{{output.deployment_id}}` from `resp.result.deploymentId`
2. Poll **DescribeDeployments** until status is `Deployed`
3. Report deployment ID and invoke URL to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `ApiNotFound` | 0 | — | HALT; create API first |
| `InvalidStage` | 0 | — | Suggest valid stage names |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Describe Apis

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.describe_apis_request import DescribeApisRequest

req = DescribeApisRequest(
    regionId="{{user.region}}",
    apiGroupId="{{user.api_group_id}}",
    pageNumber=1,
    pageSize=50
)
resp = client.describeApis(req)

for api in resp.result.apis:
    print(f"{api.apiId} | {api.apiName} | {api.status} | {api.requestConfig.requestPath}")
```

#### Present to User

| Field | Path | Notes |
|-------|------|-------|
| ID | `apiId` | Plain text |
| Name | `apiName` | Plain text |
| Status | `status` | `UnDeployed`, `Deployed`, `Deleting` |
| Request Path | `requestConfig.requestPath` | e.g., `/hello` |
| Method | `requestConfig.requestMethod` | GET, POST, etc. |
| Auth Type | `authType` | `no_auth`, `app_auth`, `jdcloud_auth` |

---

### Operation: Delete Api

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: "Delete API `{{user.api_name}}` (`{{user.api_id}}`)? If deployed, it will be removed from all stages. This is irreversible."
- **MUST NOT** proceed without clear user assent
- Check if API is deployed; warn about production impact

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| API exists | DescribeApis | API found | Already deleted |
| Undeployed or confirmed | DescribeDeployments | Not deployed or user confirmed | HALT; undeploy first |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.delete_api_request import DeleteApiRequest

req = DeleteApiRequest(
    regionId="{{user.region}}",
    apiGroupId="{{user.api_group_id}}",
    apiId="{{user.api_id}}"
)
resp = client.deleteApi(req)
print(f"API deleted: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **DescribeApis** until API no longer appears (404 or not in list)
2. Max wait: 30 seconds
3. Confirm deletion to user

---

### Operation: Create Throttling Policy

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Policy name | Validate format | Valid string | Reject; ask for valid name |
| Rate limit values | Validate | Positive integers | Reject; ask for valid values |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.create_throttling_policy_request import CreateThrottlingPolicyRequest

req = CreateThrottlingPolicyRequest(
    regionId="{{user.region}}",
    policyName="{{user.policy_name}}",
    description="Created via skill",
    throttleConfig={
        "apiThrottleConfig": {
            "apiId": "{{user.api_id}}",
            "unit": "second",  # second, minute, hour, day
            "apiLimit": 1000,
            "appLimit": 100
        }
    }
)
resp = client.createThrottlingPolicy(req)
print(f"Throttling policy created: {resp.result.policyId}")
```

#### Post-execution Validation

1. Parse `{{output.policy_id}}` from `resp.result.policyId`
2. Verify policy appears in **DescribeThrottlingPolicies** response
3. Report policy ID and configuration to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `PolicyAlreadyExists` | 0 | — | Ask user to use existing policy or new name |
| `InvalidParameter` | 0 | — | Fix throttle config; retry |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Bind Throttling Policy

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Policy exists | DescribeThrottlingPolicies | Policy found | HALT; create policy first |
| API exists | DescribeApis | API found | HALT; create API first |
| Stage valid | Check supported stages | Valid stage | Suggest valid stages |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.apigateway.apis.bind_throttling_policy_request import BindThrottlingPolicyRequest

req = BindThrottlingPolicyRequest(
    regionId="{{user.region}}",
    apiGroupId="{{user.api_group_id}}",
    apiId="{{user.api_id}}",
    stageName="{{user.stage_name}}",
    policyId="{{user.policy_id}}"
)
resp = client.bindThrottlingPolicy(req)
print(f"Throttling policy bound: {resp.requestId}")
```

#### Post-execution Validation

1. Verify binding via **DescribeApiThrottling** or equivalent API
2. Report confirmation to user

---

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12.

1. **Install uv** (system-wide, one-time):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv
   ```

2. **Bootstrap Python environment**:
   ```bash
   uv venv --python 3.10
   source .venv/bin/activate
   uv pip install jdcloud_sdk
   ```

3. **Configure Credentials** (SDK uses environment variables):
   ```bash
   export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
   export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
   export JDC_REGION="cn-north-1"
   ```

4. **Verify Configuration**:
   ```python
   python -c "
   import os
   from jdcloud_sdk.core.credential import Credential
   credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
   print('SDK credentials OK')
   "
   ```

> **Note:** No CLI verification available for API Gateway (SDK-only skill).

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)
- [Rubric](references/rubric.md)
- [Prompt Templates](references/prompt-templates.md)

## Operational Best Practices

- **Least privilege:** Use `app_auth` or `jdcloud_auth` instead of `no_auth` for production APIs
- **Staging:** Always deploy to `test` or `pre` stage first before promoting to `prod`
- **Throttling:** Set conservative rate limits initially; monitor and adjust based on traffic patterns
- **Versioning:** Use API group naming conventions (e.g., `service-v1`, `service-v2`) for major changes
- **Monitoring:** Set up CloudMonitor alarms on API error rates and latency thresholds
- **Backend protection:** Ensure backend services can handle API Gateway traffic; configure circuit breakers
- **HTTPS:** Use HTTPS protocol for production APIs; upload valid SSL certificates if needed

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **recommended** for this skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for recommended skills |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified trace path |
| `safety_confirm_required` | **true** for API publish / unpublish / delete | API publish / unpublish / delete are reversible but affect live traffic |
| `hallucination_check` | **recommended** | Phase 6 H layer; recommended for SDK parameter validation |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► SDK (sole path; no jdc for API Gateway)
   │                              generate command (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (recommended for apigateway-ops) - SDK parameter existence
   │                                     - JSON structure compliance
   │
   ├── PASS → [1a] Execute (run the SDK call)
   ├── FAIL → [1b] Regenerate (H retriggers G with hallucination report; max 1 retry)
   │         still FAIL → HALT with "HALLUCINATION_ABORT"
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │                              score every rubric dimension (5+3)
   │                              assess test accuracy + regression gate
   ▼
[3] Orchestrator decider
   ├─ HALLUCINATION_ABORT     → ABORT (no partial)
   ├─ Safety=0 / blocking     → ABORT
   ├─ all pass                → RETURN
   ├─ iter<3 & not all pass   → RETRY (inject suggestions)
   └─ iter=3 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Recommended

> **Purpose**: Catch LLM-generated SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud API Gateway API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for apigateway-ops):**

| Category | Check | Method |
|---|---|---|
| **SDK Parameter Existence** | Verify every parameter exists in the SDK request class | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads (e.g., `requestConfig`, `serviceConfig`, `throttleConfig`) | Validate field nesting matches OpenAPI schema |

**Key Parameters to Validate:**

| Operation | Critical Parameters |
|---|---|
| `createApiGroup` | `regionId`, `groupName` |
| `deleteApiGroup` | `regionId`, `apiGroupId` |
| `createApi` | `regionId`, `apiGroupId`, `apiName`, `requestConfig`, `serviceConfig`, `authType` |
| `deployApi` | `regionId`, `apiGroupId`, `apiId`, `stageName` |
| `deleteApi` | `regionId`, `apiGroupId`, `apiId` |
| `createThrottlingPolicy` | `regionId`, `policyName`, `throttleConfig` |
| `bindThrottlingPolicy` | `regionId`, `apiGroupId`, `apiId`, `stageName`, `policyId` |

**Termination:**

| Condition | Exit Code | Action |
|---|---|---|
| **H_PASS** | — | Continue to [1a] Execute |
| **H_FAIL → Regenerate** | — | Inject hallucination report into G; max 1 regeneration attempt |
| **HALLUCINATION_ABORT** | 5 | HALT — structural hallucinations persist after regeneration |

**Trace Integration:**

The H result is embedded in the GCL trace JSON under `iterations[].hallucination_detector`:

```json
{
  "iter": 1,
  "hallucination_detector": {
    "status": "PASS|FAIL",
    "checks": {
      "sdk_parameters": { "status": "PASS|FAIL", "unrecognized_params": [] },
      "json_structure": { "status": "PASS|FAIL", "issues": [] }
    },
    "report": "..."
  },
  "regenerated": false,
  "generator": { ... },
  "critic": { ... }
}
```

### Reflexion Integration (Lightweight Reflexion)

> **Purpose**: Enable cross-session learning from failure patterns, complementing the within-session
> GCL loop with persistent failure memory.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCL Execution (per-session)                   │
│   [0] Pre-flight → [1] Generate → [1.5] H → [2] C → [3] Decide │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    failure_pattern (in trace)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Reflexion Memory (cross-session)                    │
│   docs/failure-patterns.md (structured text, ≤200 lines)        │
│   §1 SDK Parameter Errors | §2 Skill Generation | §3 Cross-Skill│
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    Pre-flight retrieval (optional)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prevention (next session)                           │
│   Inject known patterns into Generator context                  │
│   Agent avoids repeating known mistakes                          │
└─────────────────────────────────────────────────────────────────┘
```

**Pre-flight Retrieval (Optional):**

During GCL Pre-flight (step [0]), the Orchestrator MAY:

```bash
# 1. Load docs/failure-patterns.md (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name (jdcloud-apigateway-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "sdk_parameter|runtime|cross_skill",
    "skill": "jdcloud-apigateway-ops",
    "command": "createApi / deployApi / ...",
    "error": "...",
    "fix": "...",
    "reusable": true
  }
}
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O / H): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): [docs/failure-patterns.md](../docs/failure-patterns.md)

### Integration with existing flows

The GCL **wraps** the SDK-only flow defined under
`## Execution Flows` above. The Generator (G) IS the existing SDK
executor. The Critic (C) is a new, read-only role with no SDK access.
The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is a recommended pre-execution structural check.

### Operation-specific behavior

- **`createApiGroup`** — Group name must be valid (1–128 chars). Check quota first.
- **`createApi`** — `requestConfig`, `serviceConfig`, `authType` must be valid. Backend URL required for `http` type.
- **`deployApi`** — Stage must be valid (`test`, `pre`, `prod`). Deploying to `prod` requires explicit confirmation.
- **`deleteApiGroup`** — **Cascade deletes all APIs** within the group. `confirm=DELETE` required.
- **`deleteApi`** — Removes API from all stages if deployed. `confirm=DELETE` required.
- **`bindThrottlingPolicy`** — Policy and API must exist. Stage must be valid.
