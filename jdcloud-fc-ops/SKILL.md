---
name: jdcloud-fc-ops
description: >-
  Use when managing JD Cloud Function Compute (函数计算) resources — create,
  update, delete, and invoke functions; manage services, versions, aliases,
  and triggers; configure environment variables and resource limits. Works
  with "函数计算", "Function Compute", "FC", "serverless", "函数" without
  saying "JD Cloud" explicitly. NOT for VM/container-based workloads, API
  Gateway configuration, or billing management.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints. SDK-only skill; `jdc` CLI does NOT support
  Function Compute as of SDK version 1.6.26.
metadata:
  author: buhaiqing
  version: "1.2.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "Function Compute API v1.0"
  cli_applicability: sdk-only
  cli_support_evidence: >-
    Official `jdc` CLI does NOT support Function Compute operations.
    Verified via `jdc --help` product list and CLI documentation at
    https://docs.jdcloud.com/cn/cli. SDK-only execution path required.
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Function Compute Operations Skill

## Overview
JD Cloud Function Compute (函数计算) is a serverless computing service that allows you to run code without provisioning or managing servers. You simply write and upload your code, and the service automatically handles infrastructure management, auto-scaling, and high availability.

This skill covers:
- **Service Management**: Create, update, delete, and list services
- **Function Management**: Create, update, delete, invoke, and list functions
- **Version & Alias Management**: Publish versions, create aliases for traffic shifting
- **Trigger Management**: Configure HTTP, Timer, and other trigger types
- **Monitoring & Logging**: Query invocation metrics and logs

### CLI applicability (repository policy)

- **`cli_applicability: sdk-only`:** Official `jdc` CLI does **not** support Function Compute. This skill uses **SDK/API only** execution path.
- **SDK Package**: `jdcloud_sdk.services.function` (verify exact package name in official SDK docs)
- **Fallback**: No CLI fallback available; SDK is the only execution path.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When
- User mentions "Function Compute" OR "函数计算" OR "FC" OR "serverless" OR "函数"
- Task involves creating, updating, deleting, or invoking functions
- Task involves managing services, versions, or aliases
- Task involves configuring triggers (HTTP, Timer, OSS, etc.)
- Task keywords: create-service, create-function, invoke-function, publish-version, create-alias, create-trigger, 服务, 函数, 版本, 别名, 触发器

### SHOULD NOT Use This Skill When
- Task is about VM/container-based computing → delegate to: `jdcloud-vm-ops` or `jdcloud-kubernetes-ops`
- Task is about API Gateway configuration → delegate to: `jdcloud-apigateway-ops`
- Task is about Object Storage triggers (OSS events) → delegate to: `jdcloud-oss-ops` for OSS config, then return here for trigger setup
- Task is about monitoring/alarms for functions → delegate to: `jdcloud-cloudmonitor-ops`
- Task is purely about billing / account management → delegate to: `jdcloud-billing-ops`

### Delegation Rules
- If user wants to trigger functions via OSS events, configure OSS first via `jdcloud-oss-ops`, then create trigger here
- If user wants HTTP-triggered functions exposed via custom domain, configure API Gateway via `jdcloud-apigateway-ops` after function creation

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.service_name}}` | Function Compute service name | Ask once; reuse |
| `{{user.function_name}}` | Function name within service | Ask once; reuse |
| `{{user.runtime}}` | Function runtime (python3.10, nodejs18, java11, etc.) | Ask once; reuse |
| `{{output.service_id}}` | Captured from SDK response | Parse from `$.result.serviceId` |
| `{{output.function_arn}}` | Function ARN | Parse from `$.result.functionArn` |
| `{{output.version_id}}` | Published version ID | Parse from `$.result.versionId` |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes.
- **SDK Namespace**: `jdcloud_sdk.services.function`
- **Resource Naming**: Service names and function names must follow `[a-zA-Z][a-zA-Z0-9_-]{1,127}` pattern
- **Supported Runtimes**: python3.10, python3.9, nodejs18, nodejs16, java11, go1.x, dotnet6, php7.4 (verify latest in official docs)

### Example Response Field Table

| Operation | JSON Path | Type | Description |
|-----------|-----------|------|-------------|
| Create Service | `$.result.serviceId` | string | Unique service identifier |
| Create Function | `$.result.functionArn` | string | Function ARN ( Amazon Resource Name style) |
| Invoke Function | `$.result.payload` | string | Base64-encoded response payload |
| Publish Version | `$.result.versionId` | string | Version identifier (e.g., "1", "2") |
| List Services | `$.result.services[*].serviceName` | array | Service names |
| List Functions | `$.result.functions[*].functionName` | array | Function names within service |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Service | — | `Active` | 2s | 30s |
| Create Function | — | `Active` | 2s | 60s |
| Update Function | `Active` | `Active` (new config) | 2s | 60s |
| Invoke Function | — | `Success` / `Error` | — | 300s (timeout) |
| Publish Version | — | `Active` | 2s | 30s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.2.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, recommended) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for SDK method parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.1.0 | 2026-06-18 | Initial GCL v2 content: Added Phase 6 H layer and Phase 7 Reflexion sections to Quality Gate. |
| 1.0.0 | 2026-06-08 | Initial SDK-only skill for JD Cloud Function Compute |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK) → Validate → Recover**. No CLI path available.

### Operation: Create Service

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | `import jdcloud_sdk` | No import error | Document install steps |
| Credentials | `os.environ["JDC_ACCESS_KEY"]` | Non-empty | HALT; user configures env |
| Service name | Validate regex `[a-zA-Z][a-zA-Z0-9_-]{1,127}` | Valid format | Reject; ask for valid name |
| Region | Check region availability | `{{user.region}}` supported | Suggest valid region |

#### Execution (Python SDK)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.function.client import FunctionClient
from jdcloud_sdk.services.function.apis.create_service_request import CreateServiceRequest

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = FunctionClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))

req = CreateServiceRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    description="Created via skill"
)
resp = client.createService(req)
print(f"Service created: {resp.result.serviceId}")
```

#### Post-execution Validation

1. Parse `{{output.service_id}}` from `resp.result.serviceId`
2. Poll **DescribeService** until status is `Active` or timeout
3. Report service ID and ARN to user

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `ServiceAlreadyExists` | 0 | — | Ask user to use existing service or new name |
| `InvalidParameter` | 0 | — | Fix service name validation; retry |
| `QuotaExceeded` | 0 | — | HALT; suggest quota increase |
| Throttling / 429 | 3 | exponential | Back off and retry |

---

### Operation: Create Function

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Service exists | DescribeService API | Service found | HALT; create service first |
| Function name | Validate regex | Valid format | Reject; ask for valid name |
| Runtime | Check supported runtimes | Runtime in supported list | Suggest valid runtime |
| Code package | Verify code.zip exists or inline code provided | Valid code source | HALT; ask for code |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.function.apis.create_function_request import CreateFunctionRequest

req = CreateFunctionRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    functionName="{{user.function_name}}",
    runtime="{{user.runtime}}",
    handler="index.handler",  # or user-provided
    memorySize=512,  # MB
    timeout=30,  # seconds
    code={
        "zipFile": "<base64-encoded-zip>"  # or use OSS bucket
    },
    description="Created via skill"
)
resp = client.createFunction(req)
print(f"Function created: {resp.result.functionArn}")
```

#### Post-execution Validation

1. Parse `{{output.function_arn}}` from `resp.result.functionArn`
2. Poll **DescribeFunction** until state is `Active`
3. Report function ARN and configuration to user

---

### Operation: Invoke Function

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Function exists | DescribeFunction API | Function found and `Active` | HALT; create function first |
| Invocation type | Sync or Async | Valid type | Default to `Sync` |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.function.apis.invoke_function_request import InvokeFunctionRequest
import json

req = InvokeFunctionRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    functionName="{{user.function_name}}",
    qualifier="{{user.qualifier|default('LATEST')}}",  # LATEST, version, or alias
    invocationType="Sync",  # or "Async"
    payload=json.dumps({"key": "value"})  # event payload
)
resp = client.invokeFunction(req)

# Parse response
if resp.result.statusCode == 200:
    payload = base64.b64decode(resp.result.payload).decode('utf-8')
    print(f"Invocation successful: {payload}")
else:
    print(f"Invocation failed: {resp.result.statusCode}")
```

#### Post-execution Validation

1. Check `resp.result.statusCode` for HTTP-style status
2. For sync invocations, decode and return payload
3. For async invocations, return invocation request ID for tracking

---

### Operation: Publish Version

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Service exists | DescribeService | Service found | HALT |
| Function exists | DescribeFunction | Function in `Active` state | HALT |
| Description | Non-empty description | Valid string | Use default description |

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.function.apis.publish_version_request import PublishVersionRequest

req = PublishVersionRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    functionName="{{user.function_name}}",
    description="Version published via skill"
)
resp = client.publishVersion(req)
print(f"Version published: {resp.result.versionId}")
```

#### Post-execution Validation

1. Parse `{{output.version_id}}` from `resp.result.versionId`
2. Verify version appears in **ListVersions** response

---

### Operation: Create Alias

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.function.apis.create_alias_request import CreateAliasRequest

req = CreateAliasRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    functionName="{{user.function_name}}",
    aliasName="prod",  # or user-provided
    version="1",  # version to point to
    description="Production alias"
)
resp = client.createAlias(req)
print(f"Alias created: {resp.result.aliasName}")
```

---

### Operation: Create Trigger

#### Execution (Python SDK) - HTTP Trigger

```python
from jdcloud_sdk.services.function.apis.create_trigger_request import CreateTriggerRequest

req = CreateTriggerRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    functionName="{{user.function_name}}",
    qualifier="{{user.qualifier|default('LATEST')}}",
    triggerType="http",  # http, timer, oss, log, etc.
    triggerName="http-trigger",
    triggerConfig={
        "authType": "anonymous",  # or "function"
        "methods": ["GET", "POST"]
    }
)
resp = client.createTrigger(req)
print(f"Trigger created: {resp.result.triggerId}")
print(f"HTTP URL: {resp.result.httpUrl}")  # for HTTP triggers
```

#### Execution (Python SDK) - Timer Trigger

```python
req = CreateTriggerRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    functionName="{{user.function_name}}",
    qualifier="LATEST",
    triggerType="timer",
    triggerName="daily-job",
    triggerConfig={
        "cron": "0 0 * * * *",  # Every hour at minute 0
        "enable": True
    }
)
resp = client.createTrigger(req)
```

---

### Operation: Delete Function

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: "Delete function `{{user.function_name}}` in service `{{user.service_name}}`? This is irreversible."
- **MUST NOT** proceed without clear user assent
- Check if function has triggers attached; warn user about trigger deletion

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.function.apis.delete_function_request import DeleteFunctionRequest

req = DeleteFunctionRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}",
    functionName="{{user.function_name}}"
)
resp = client.deleteFunction(req)
print(f"Function deleted: {resp.requestId}")
```

#### Post-execution Validation

1. Poll **ListFunctions** until function no longer appears (404 or not in list)
2. Max wait: 60 seconds
3. Confirm deletion to user

---

### Operation: Delete Service

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: "Delete service `{{user.service_name}}` and ALL its functions? This is irreversible."
- Check if service has functions; require `--force` equivalent or user confirmation to cascade delete

#### Execution (Python SDK)

```python
from jdcloud_sdk.services.function.apis.delete_service_request import DeleteServiceRequest

req = DeleteServiceRequest(
    regionId="{{user.region}}",
    serviceName="{{user.service_name}}"
)
resp = client.deleteService(req)
print(f"Service deleted: {resp.requestId}")
```

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

> **Note:** No CLI verification available for Function Compute (SDK-only skill).

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Least privilege:** IAM policies scoped to `function:*` APIs for function developers; `function:InvokeFunction` only for invokers
- **Cold start optimization:** Keep functions warm with scheduled invocations for latency-sensitive workloads
- **Resource limits:** Set appropriate `memorySize` and `timeout` based on workload characteristics
- **Versioning:** Always publish versions for production deployments; use aliases for traffic shifting
- **Monitoring:** Set up CloudMonitor alarms on error rates and latency thresholds

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md`](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).

### Parameters

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for ops skills |
| `rubric_version` | `v2` | see [references/rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** | Delete service/function requires user confirmation |
| `hallucination_check` | **recommended** | Phase 6 H layer; validates SDK method parameters before execution |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► SDK (sole path; no jdc for FC)
   │                              generate SDK call (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (recommended for fc-ops)      - SDK method parameter existence
   │                                   - JSON structure compliance
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
> **before** they reach the JD Cloud Function Compute API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for fc-ops):**

| Category | Check | Method |
|---|---|---|
| **SDK Method Parameter Existence** | Verify every parameter exists in SDK method signature | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads (e.g., function config, trigger config) | Validate field nesting matches OpenAPI schema |

**Key Parameters to Validate:**

| Operation | Critical Parameters |
|---|---|
| `createService` | `regionId`, `serviceName`, `description` |
| `deleteService` | `regionId`, `serviceName` |
| `createFunction` | `regionId`, `serviceName`, `functionName`, `runtime`, `handler`, `memorySize`, `timeout`, `code` |
| `deleteFunction` | `regionId`, `serviceName`, `functionName` |
| `invokeFunction` | `regionId`, `serviceName`, `functionName`, `qualifier`, `invocationType`, `payload` |
| `publishVersion` | `regionId`, `serviceName`, `functionName`, `description` |
| `createAlias` | `regionId`, `serviceName`, `functionName`, `aliasName`, `version` |
| `createTrigger` | `regionId`, `serviceName`, `functionName`, `qualifier`, `triggerType`, `triggerName`, `triggerConfig` |

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
# 2. Filter patterns by current skill name (jdcloud-fc-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidRuntime: Runtime must be in supported list (python3.10, nodejs18, java11, etc.)
- ServiceCascadeDelete: Deleting service cascades to all functions; require explicit confirmation
- InvalidHandler: Handler format must match runtime (e.g., index.handler for Node.js)"
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): `docs/failure-patterns.md` (repository-wide)

### Integration with existing flows

The GCL **wraps** the SDK-only flow defined under `## Execution Flows` above. The Generator (G) IS the existing SDK executor. The Critic (C) is a read-only role with no SDK access. The Orchestrator (O) owns the loop and persists the GCL trace.

### Operation-specific behavior

- **`createService`** — Critic verifies service name uniqueness check was performed (Idempotency = 1 required). Missing → Idempotency = 0.
- **`deleteService`** — Critic checks trace contains both pre-delete snapshot (function count) and post-delete 404. Missing either → Correctness = 0. H layer validates `serviceName` format before execution.
- **`createFunction`** — Critic verifies runtime/handler compatibility (e.g., Node.js handler format `index.handler`). Invalid format → Correctness = 0.
- **`invokeFunction`** — For production invocation, Safety = 0 without explicit confirmation in trace. H layer validates `invocationType` (RequestResponse vs Event) before execution.
- **`publishVersion`** — Version description must be explicit. Missing description → Traceability = 0.5.

---

