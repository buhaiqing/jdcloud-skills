---
name: jdcloud-[product-name]-ops
description: >-
  Use when you need to deploy, configure, troubleshoot, or monitor JD Cloud
  [Product Name] via official API/SDK or official `jdc` CLI; user mentions
  [Product Name], [Product Chinese Name], or [Product Alias], or tasks target
  [Resource Type].
license: MIT
compatibility: >-
  Official JD Cloud SDK (e.g. Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (dual-path skills).
metadata:
  author: jdcloud
  version: "1.0.0"
  last_updated: "2026-05-03"
  runtime: Harness AI Agent
  api_profile: "[Paste OpenAPI title/version or doc link]"
  cli_applicability: dual-path
  cli_support_evidence: >-
    [If dual-path: cite how you confirmed CLI coverage, e.g. official CLI doc
    URL or `jdc <product> --help`. If sdk-only: cite proof that `jdc` does NOT
    expose this product; omit references/cli-usage.md only in that case.]
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This template follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud [Product Name] Operations Skill

## Overview

[Product Name] on JD Cloud provides [brief description]. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **dual-path execution** (official **SDK/API** and, when the product is supported by official **`jdc`**, the matching **CLI** flows), response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: dual-path`:** Official `jdc` supports this product. You **MUST** ship **`references/cli-usage.md`** and, in **each** execution flow below, document **both** the SDK step **and** the `jdc` step for every operation the CLI exposes. If the CLI covers **only part** of the API, add a **coverage gap** table (SDK-only operations) in `references/cli-usage.md`.
- **`cli_applicability: sdk-only`:** Official `jdc` does **not** expose this product. **Omit** `references/cli-usage.md`. Keep **`cli_support_evidence`** pointing at official proof (e.g. CLI product list, `jdc help`, or documentation). SDK/API remains mandatory for all operations.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud [Product Name]" OR "[Product Chinese Name]" OR "[Product Alias]"
- Task involves CRUD or lifecycle operations on **[Resource Type]** (create, describe, modify, delete, list, and product-specific actions)
- Task keywords: [keyword1], [keyword2], [keyword3], …
- User asks to deploy, configure, troubleshoot, or monitor [Product Name] **via API, SDK, CLI, or automation**

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops` (when present)
- Task is about **[related product]** → delegate to: `jdcloud-[other]-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If resource B depends on resource A, complete or verify A (via the A skill) before B’s SDK or CLI steps.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use documented default only if skill explicitly allows |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.resource_name}}` | User-supplied name | Ask once; reuse |
| `{{output.resource_id}}` | From last API or CLI JSON response | Parse per **OpenAPI** (SDK) or **verified `jdc --output json`** path for this operation |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Replace generic JSON paths below with **real** schema field names.
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec. Do not assume a single global shape across products.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-04-28T10:00:00+08:00`).
- **Idempotency:** Document client request tokens, duplicate names, and `ResourceAlreadyExists` behavior per API.

### Example Response Field Table (Replace with OpenAPI-Accurate Paths)

| Operation | JSON Path (example) | Type | Description |
|-----------|---------------------|------|-------------|
| Create | `$.result.resourceId` | string | New resource ID (verify name in spec) |
| Describe | `$.result.status` | string | Lifecycle state |
| List | `$.result.resources[*].resourceId` | array | IDs (verify array structure) |
| Modify / Delete | `$.requestId` or `$.error` | string / object | Per spec |

### Expected State Transitions (Adjust to Product)

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create | — | `running` or product equivalent | 5s | 300s |
| Start | `stopped` | `running` | 5s | 120s |
| Stop | `running` | `stopped` | 5s | 120s |
| Delete | any stable state | absent or `deleted` per describe | 5s | 300s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-03 | Initial API/SDK-oriented template |
| 1.0.1 | 2026-05-03 | Document optional official `jdc` CLI alongside SDK/API |
| 1.0.2 | 2026-05-03 | Require dual-path (SDK + `jdc`) when CLI supports product; sdk-only exception documented |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK/API and, when applicable, `jdc`) → Validate → Recover**. Do not skip phases.

**Preference hint:** When both paths exist, state when to prefer SDK vs `jdc` (e.g. no Python runtime → `jdc`; integration tests → SDK).

### Operation: Create [Resource]

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | Import client; version matches `metadata.api_profile` | No import error | Document install pin |
| CLI / deps | `jdc --version` (**required** when `cli_applicability: dual-path`) | Exit code 0 | Document CLI install / `jdc config init` |
| Credentials | Construct credential from env (SDK) or CLI config/env per official CLI docs | Non-empty keys / valid config | HALT; user configures env |
| Region | Call **DescribeRegions** (or equivalent) if applicable | `{{user.region}}` supported | Suggest valid region |
| Quota | Call quota/describe API per OpenAPI | Sufficient quota | HALT; user raises quota |

#### Execution (Python SDK — illustrative)

Replace service/client/method names with **generated SDK symbols** for this product:

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.[product].client import [Product]Client
from jdcloud_sdk.services.[product].apis.[module] import CreateRequest

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = [Product]Client(credential, os.environ.get("JDC_REGION", "cn-north-1"))

req = CreateRequest(
    regionId="<region-from-user>",
    # add remaining fields per OpenAPI request schema
)
resp = client.create_method(req)  # replace with real SDK method name
```

#### Execution — CLI (`jdc`) (**required** when `cli_applicability: dual-path`)

**Omit this subsection only** when `cli_applicability: sdk-only` (and `references/cli-usage.md` is omitted). Otherwise use the [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli). Every command MUST use **`--output json`** (or documented equivalent) and **`--no-interactive`** (or equivalent) when supported. **Verify** JSON paths against a real run; CLI wrappers may not match raw API field names.

```bash
jdc [product] create-[resource] \
  --region-id "<region-from-user>" \
  --output json \
  --no-interactive
  # add flags per official `jdc [product] create-[resource] --help`
```

#### Post-execution Validation

1. Read `{{output.resource_id}}` from the **documented** response path (SDK JSON path and, when dual-path, **CLI JSON path** if they differ).
2. Poll **Describe** until terminal success state or timeout—**implement for both paths** when `cli_applicability: dual-path` (SDK loop below; CLI loop e.g. `jdc … describe-… --output json` with `jq` until terminal state or max wait).

```python
# Pseudocode: use real describe request/response types from the SDK
for _ in range(max_attempts):
    dresp = client.describe_[resource](describe_request)
    status = parse_status(dresp)  # per OpenAPI
    if status in success_states:
        break
    if status in failure_states:
        raise RuntimeError(parse_error(dresp))
    sleep(poll_interval_seconds)
```

```bash
# Dual-path example: poll with jdc (adjust jq paths after verification)
# for i in $(seq 1 60); do
#   STATUS=$(jdc [product] describe-[resource] ... --output json | jq -r '.path.to.status')
#   [ "$STATUS" = "running" ] && break
#   sleep 5
# done
```

3. On success, report `{{output.resource_id}}` and key fields to the user.
4. On terminal failure, go to **Failure Recovery**.

#### Failure Recovery

| Error pattern (from API/SDK or parsed CLI JSON) | Max retries | Backoff | Agent Action |
|------------------------------|-------------|---------|--------------|
| `InvalidParameter` / 400 invalid input | 0–1 | — | Fix args from OpenAPI; retry once if safe |
| `QuotaExceeded` | 0 | — | HALT |
| `InsufficientBalance` | 0 | — | HALT |
| `ResourceAlreadyExists` | 0 | — | Ask reuse vs new name |
| Throttling / 429 | 3 | exponential | Back off; respect `Retry-After` if present |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; then HALT with correlation id if any |

### Operation: Describe [Resource]

#### Execution

Use the SDK **describe** or **get** API matching OpenAPI. When **`cli_applicability: dual-path`**, also document the equivalent `jdc [product] describe-[resource] ... --output json`, passing `{{user.resource_id}}` and region.

#### Present to User

| Field | Path (example) | Notes |
|-------|----------------|-------|
| ID | from describe | Plain text |
| Name | from describe | Plain text |
| Status | from describe | Human-readable state |
| Created time | from describe | Format ISO per API |

### Operation: Delete [Resource]

#### Pre-flight (Safety Gate)

- **MUST** obtain explicit confirmation: irreversible delete of `{{user.resource_name}}` (`{{user.resource_id}}`).
- **MUST NOT** proceed without clear user assent.

#### Execution

Call delete API per OpenAPI. When **`cli_applicability: dual-path`**, also document the `jdc` delete subcommand with `--output json`; capture `requestId`, success flag, or error per **verified** output shape for **each** path.

#### Post-execution Validation

Poll describe (or head/get) until **404**, **NotFound**, or status indicates deleted—per API semantics—within **max wait**.

## Prerequisites

1. **Install** the JD Cloud SDK package(s) and, when **`cli_applicability: dual-path`**, the **CLI** (pin versions in `references/integration.md`; `jdc` install is **required** for dual-path).

2. **Configure Credentials** — Three methods:

   **Method 1: `.env` File (Recommended for Local Development)**
   Create `.env` in project root (copy from `.env.example`):
   ```ini
   JDC_ACCESS_KEY=your_access_key_here
   JDC_SECRET_KEY=your_secret_key_here
   JDC_REGION=cn-north-1
   ```
   
   > **Note:** Agent Runtime auto-loads `.env` if present. Shell env vars have **higher priority** (won't be overridden by `.env`).

   **Method 2: Shell Environment Variables (Recommended for Production)**
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
   # Quick validation
   jdc [product] describe-... --region-id cn-north-1 --output json
   ```

> **Security:** Never commit `.env` to version control (already in `.gitignore`). All credentials use `{{env.*}}` placeholders in generated Skills — never real values.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md) (**required** when `cli_applicability: dual-path`; omit only for `sdk-only` with evidence in frontmatter)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Least privilege:** IAM policies scoped to required APIs only.
- **Availability:** Multi-AZ or product-specific HA patterns per docs.
- **Cost:** Right-size resources; use product cost controls where applicable.

---

# Appendix: Reference File Templates

## references/troubleshooting.md

```markdown
# Troubleshooting [Product Name]

## Common API Error Codes
| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| InvalidParameter | Request failed validation | Align body with OpenAPI |
| InsufficientBalance | Account balance | HALT; user tops up |

## Diagnostic Order
1. Describe resource by ID.
2. List related resources if API supports filters.
3. Check regional endpoint and `regionId` consistency.
```

## references/api-sdk-usage.md

```markdown
# API & SDK — [Product Name]

## OpenAPI
- Spec: [link or path]
- Base path and version: …

## SDK Operations Map
| Goal | API operationId | SDK method (if known) |
|------|-----------------|------------------------|
| Create | … | … |
| Describe | … | … |

## Request / Response Notes
- Required fields: …
- Pagination: …
```

## references/cli-usage.md

```markdown
# CLI — [Product Name] (`jdc`)

## Install and config
- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- `jdc config init` / env vars per official docs

## Conventions (agent execution)
- Append `--output json` (or documented equivalent) for every command used in automation.
- Append `--no-interactive` (or equivalent) when supported.
- Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API).

## CLI vs API coverage gap
| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| Create | yes / no | … |
| Describe | yes / no | … |

## Command map
| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Create | `jdc [product] create-…` | … |
| Describe | `jdc [product] describe-…` | … |
```

## references/monitoring.md

```markdown
# Monitoring [Product Name]

## Key Metrics (examples — replace with product namespaces)
- Metric A: `namespace/service/metric_a`
- Metric B: `namespace/service/metric_b`

## Alert Example (structure only)
{ "metric": "metric_a", "threshold": 80, "period": 300 }
```

## references/integration.md

````markdown
# Integration

## Python SDK bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.[product].client import [Product]Client

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = [Product]Client(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.
````
