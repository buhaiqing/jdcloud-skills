---
name: jdcloud-billing-ops
description: >-
  JD Cloud billing operations: balance, consumption, bill details, vouchers,
  cost estimation. Trigger: billing,账单,费用,cost, expense, balance, voucher.
  SDK-only (jdc CLI doesn't support billing).
license: MIT
compatibility: >-
  JD Cloud Python SDK (3.10+), network access to billing endpoints.
metadata:
  author: jdcloud
  version: "1.1.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile:
    name: "JD Cloud Billing API v1"
    endpoint: "https://billing.jdcloud-api.com/v1"
  cli_applicability: sdk-only
  cli_version_locked: "N/A"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    JD Cloud Billing is SDK-only (not exposed via `jdc` CLI).
    SDK documentation: https://docs.jdcloud.com/cn/billing/api
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

# JD Cloud Billing Operations

## Overview

JD Cloud Billing cost management skill. **Read-only** operations only.

### CLI applicability

- **SDK-only**: `jdc` CLI does not expose billing operations. SDK is mandatory.

## Trigger & Scope

### SHOULD Use

- Keywords: billing,账单,费用,cost, expense, balance, voucher, coupon, invoice
- Operations: balance query, consumption records, bill details, vouchers, cost estimation

### SHOULD NOT Use

| Task | Delegate |
|------|----------|
| Resource CRUD | `jdcloud-vm-ops`, `jdcloud-rds-ops`, etc. |
| IAM | `jdcloud-iam-ops` |
| Expiry cruise | `jdcloud-routines-ops` |
| Cost architecture review | `jdcloud-arch-advisor` |
| Recharge/top-up | Console only |

### Delegation Rules

- Cost estimation before resource creation → this skill
- Expiry alerts → `jdcloud-routines-ops`
- Multi-product billing aggregation → this skill

## Variable Convention

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{{env.JDC_ACCESS_KEY}}` | Runtime | — |
| `{{env.JDC_SECRET_KEY}}` | Runtime | `<masked>` |
| `{{env.JDC_REGION}}` | Runtime | `cn-north-1` |
| `{{user.start_time}}` | User input | `2026-06-01` |
| `{{user.end_time}}` | User input | `2026-06-30` |

> **Security**: Never log `JDC_SECRET_KEY`. Check existence only.

## API Conventions

- **Timestamps**: ISO 8601 (`2026-04-28T10:00:00Z`)
- **Currency**: CNY (decimal strings)
- **Error mapping**: `code` / `status` / `message` per spec
- **All request classes use `parameters` dict + `client.send(req)` pattern**

## Execution Flows

Template: **Pre-flight → Execute → Validate → Recover**

### SDK Initialization (Common)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.billing.client.BillingClient import BillingClient
from jdcloud_sdk.services.asset.client.AssetClient import AssetClient
from jdcloud_sdk.services.instancevoucher.client.InstancevoucherClient import InstancevoucherClient

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])

billing_client = BillingClient(credential)
asset_client = AssetClient(credential)
voucher_client = InstancevoucherClient(credential)
```

### Operation: Query Account Balance

Uses **Asset Service** (`jdcloud_sdk.services.asset`).

```python
from jdcloud_sdk.services.asset.apis.DescribeAccountAmountRequest import (
    DescribeAccountAmountRequest,
    DescribeAccountAmountParameters,
)

params = DescribeAccountAmountParameters(regionId="{{env.JDC_REGION}}")
req = DescribeAccountAmountRequest(parameters=params)
resp = asset_client.send(req)

# Response fields: totalAmount, availableAmount, frozenAmount, withdrawAmount, withdrawingAmount
total = resp.result.totalAmount
available = resp.result.availableAmount
frozen = resp.result.frozenAmount
```

### Operation: Query Consumption Summary

Uses **Billing Service** — `QueryBillSummaryRequest`.

```python
from jdcloud_sdk.services.billing.apis.QueryBillSummaryRequest import (
    QueryBillSummaryRequest,
    QueryBillSummaryParameters,
)

params = QueryBillSummaryParameters(
    regionId="{{env.JDC_REGION}}",
    startTime="{{user.start_time}} 00:00:00",  # yyyy-MM-dd HH:mm:ss
    endTime="{{user.end_time}} 23:59:59",
)
params.setPageIndex(1)
params.setPageSize(100)

req = QueryBillSummaryRequest(parameters=params)
resp = billing_client.send(req)

# Response: BillSummary list with totalFee, discountFee, realTotalFee, etc.
summaries = resp.result.data  # list of BillSummary
```

### Operation: Query Bill Details

Uses **Billing Service** — `QueryBillDetailRequest`.

```python
from jdcloud_sdk.services.billing.apis.QueryBillDetailRequest import (
    QueryBillDetailRequest,
    QueryBillDetailParameters,
)

params = QueryBillDetailParameters(
    regionId="{{env.JDC_REGION}}",
    startTime="{{user.start_time}} 00:00:00",
    endTime="{{user.end_time}} 23:59:59",
)
params.setBillingType(3)  # 1=按配置 2=按用量 3=包年包月 4=按次
params.setPageIndex(1)
params.setPageSize(100)

req = QueryBillDetailRequest(parameters=params)
resp = billing_client.send(req)

# Response: ConsumeBillQueryResultItem list
details = resp.result.data  # list of ConsumeBillQueryResultItem
```

### Operation: Query Vouchers

Uses **InstanceVoucher Service** (`jdcloud_sdk.services.instancevoucher`).

```python
from jdcloud_sdk.services.instancevoucher.apis.DescribeInstanceVouchersRequest import (
    DescribeInstanceVouchersRequest,
)

req = DescribeInstanceVouchersRequest(parameters={
    'regionId': '{{env.JDC_REGION}}',
    'pageNumber': 1,
    'pageSize': 100,
})
resp = voucher_client.send(req)

# Response: list of instance vouchers
vouchers = resp.result.instanceVouchers  # [voucherId, name, status, balance, expireTime]
```

### Operation: Cost Estimation

Uses **Billing Service** — `CalculateTotalPriceRequest`.

```python
from jdcloud_sdk.services.billing.apis.CalculateTotalPriceRequest import (
    CalculateTotalPriceRequest,
    CalculateTotalPriceParameters,
)

params = CalculateTotalPriceParameters(
    regionId="{{env.JDC_REGION}}",
    cmd=1,        # 1=创建 2=续费 3=升配 4=删除
    packageCount=1,
)
params.setOrderList([{
    "appCode": "jcloud",
    "serviceCode": "vm",
    "region": "{{env.JDC_REGION}}",
    "billingType": 3,  # 包年包月
    "timeSpan": 1,
    "timeUnit": "month",
    "spec": "c.n1.large",
}])

req = CalculateTotalPriceRequest(parameters=params)
resp = billing_client.send(req)

# Response: OrderPrice with totalPrice, discountedTotalPrice, totalDiscount
total_price = resp.result.totalPrice
discounted = resp.result.discountedTotalPrice
```

## Pre-flight Checks

| Check | Expected | On Failure |
|-------|----------|------------|
| SDK import | No error | HALT; install SDK |
| Credentials | Non-empty | HALT; configure env |
| Date range | start ≤ end, ≤1 month per query | Ask to correct |
| Date format | yyyy-MM-dd HH:mm:ss | Ask to reformat |

## Failure Recovery

| Error | Retries | Backoff | Action |
|-------|---------|---------|--------|
| `InvalidCredentials` | 0 | — | HALT |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT |
| `Throttling` / 429 | 3 | exponential | Back off |
| `InvalidParameter` | 0 | — | Fix params |

## Prerequisites

See [references/integration.md](references/integration.md) for:
- `uv` setup
- SDK installation
- Credential configuration

Quick start:
```bash
uv venv --python 3.10 && source .venv/bin/activate
uv pip install jdcloud_sdk
export JDC_ACCESS_KEY="..." JDC_SECRET_KEY="..."
```

## Safety Gates

| Operation | Check | Confirm |
|-----------|-------|---------|
| All queries | None | No |
| Recharge | ❌ Not supported | Console only |

**Read-only skill.** No mutations.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting](references/troubleshooting.md)
- [Monitoring](references/monitoring.md)
- [Integration](references/integration.md)
- [Cost Optimization](references/cost-optimization.md)
- [Rubric](references/rubric.md)
- [Prompt Templates](references/prompt-templates.md)

## Scripts

- [Cost Optimizer](scripts/cost_optimizer.py) — Multi-plan cost comparison (A/B/C)

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this read-only skill (per `AGENTS.md` §8).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for optional skills |
| `rubric_version` | `v2` | see [references/rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified trace path |
| `safety_confirm_required` | **false** | read-only billing queries; SDK-only |
| `hallucination_check` | **optional** | Phase 6 H layer; optional for this read-only skill |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, select SDK operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► SDK-only (billing not exposed via jdc CLI)
   │                              generate SDK call (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (optional for billing-ops)     - SDK method existence
   │                                   - JSON parameter structure compliance
   │                                   - date range validity
   │
   ├── PASS → [1a] Execute (run the SDK call)
   ├── FAIL → [1b] Regenerate (H retriggers G with hallucination report; max 1 retry)
   │         still FAIL → HALT with "HALLUCINATION_ABORT"
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │                              score every rubric dimension
   │                              assess test accuracy + regression gate
   ▼
[3] Orchestrator decider
   ├─ HALLUCINATION_ABORT     → ABORT (no partial)
   ├─ Safety=0 / blocking     → ABORT
   ├─ all pass                → RETURN
   ├─ iter<5 & not all pass   → RETRY (inject suggestions)
   └─ iter=5 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Optional

> **Purpose**: Catch LLM-generated SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud Billing API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Check Categories (for billing-ops):**

| Category | Check | Method |
|---|---|---|
| **SDK Method Existence** | Verify SDK method exists in billing module | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Parameter Structure** | For SDK call parameters | Validate field names match Billing API spec |
| **Date Range Validity** | Ensure date ranges are within billing query limits | Parse dates and compute delta |

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
      "sdk_methods": { "status": "PASS|FAIL", "unrecognized_methods": [] },
      "json_structure": { "status": "PASS|FAIL", "issues": [] },
      "date_range": { "status": "PASS|FAIL", "delta_days": 30 }
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
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    Pre-flight retrieval (optional)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Prevention (next session)                           │
│   Inject known patterns into Generator context                  │
└─────────────────────────────────────────────────────────────────┘
```

**Pre-flight Retrieval (Optional):**

During GCL Pre-flight (step [0]), the Orchestrator MAY:

```bash
# 1. Load docs/failure-patterns.md (lazy-load, ~150 lines)
# 2. Filter patterns by current skill name (jdcloud-billing-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "runtime|cross_skill",
    "skill": "jdcloud-billing-ops",
    "command": "billing_client.describe_balance(...)",
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

The GCL **wraps** the SDK-only execution flow. Generator (G) IS the existing SDK executor.
Critic (C) is read-only. The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is an optional pre-execution structural check.

### Operation-specific behavior

- **Balance query** — Read-only. Safety = 1 automatically. No mutation risk. H layer validates SDK method existence.
- **Consumption summary** — Read-only. Date range must be ≤ 1 month. H layer validates date range.
- **Bill details** — Read-only. Same date range constraint. H layer validates date range.
- **Voucher query** — Read-only. Never log voucher amounts in combination with identifiable info.
- **Cost estimation** — Read-only. No actual resource changes; just price calculation. H layer validates no mutation parameters.
- **Automated report** — Aggregates multiple queries. Ensure total amounts match sum of parts. H layer validates all sub-query parameters.

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, optional) and Phase 7 Reflexion Integration. Added pre-execution structural validity check. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.0.1 | 2026-06-10 | Fix frontmatter: add cli_version_locked, sdk_version_locked, cli_support_evidence, structured api_profile with endpoint URL. Expand GCL Quality Gate from stub to full section. Create scripts/cost_optimizer.py with executable plan_a/b/c functions. |
| 1.0.0 | 2026-06-10 | Initial release |

## See Also

- `jdcloud-routines-ops` — Expiry cruise
- `jdcloud-arch-advisor` — Cost optimization
- `jdcloud-cloudmonitor-ops` — Billing alerts
