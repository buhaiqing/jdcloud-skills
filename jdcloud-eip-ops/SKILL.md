---
name: jdcloud-eip-ops
description: >-
  Use this skill to manage JD Cloud Elastic IP (EIP): deploy, configure,
  troubleshoot, or monitor via API/SDK or `jdc` CLI. Trigger for EIP, 弹性公网IP,
  Elastic IP, or tasks involving EIP instances, bandwidth, associations, or
  billing — even without explicit "EIP" mention.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.2.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "JD Cloud EIP API v1 - https://eip.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing 'eip' in product list.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Elastic IP (EIP) Operations Skill

## Overview

JD Cloud Elastic IP (EIP/弹性公网IP) provides a static public IP address that can be dynamically associated with or detached from cloud resources. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** The Agent MUST attempt `jdc` as primary execution path. If `jdc` fails, retry up to 3 times with exponential backoff, then fall back to SDK/API. Both paths MUST be documented.

### Path Preference (jdc-first with SDK Fallback)

1. **`jdc` CLI (primary)** — Quick ad-hoc operations, shell automation
2. **Retry up to 3 times** (exponential backoff: 0s → 2s → 4s)
3. **SDK/API (fallback)** — Complex workflows, CI/CD pipelines

See [CLI Usage](references/cli-usage.md) for critical jdc behavioral notes.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud EIP", "弹性公网IP", "Elastic IP", or "EIP实例"
- Task involves CRUD operations on EIP addresses
- Task involves associating/dissociating EIPs with VMs, CLB, or NAT Gateways
- Task involves bandwidth adjustment or billing method changes
- Keywords: allocateAddress, describeAddresses, associateAddress, dissociateAddress, elasticIp, publicIp, bandwidth

### SHOULD NOT Use This Skill When

- Purely billing/account management → delegate to `jdcloud-billing-ops`
- IAM/permission only → delegate to `jdcloud-iam-ops`
- VPC/subnet/security group → delegate to `jdcloud-vpc-ops`
- VM management → delegate to `jdcloud-vm-ops`
- CLB management → delegate to `jdcloud-clb-ops`
- Monitoring/alarms → delegate to `jdcloud-cloudmonitor-ops`

### Delegation Rules

- Verify dependent resources via their dedicated skills before EIP operations
- Delegate metric queries to `jdcloud-cloudmonitor-ops`

## Variable Convention (Agent-Readable)

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime | NEVER ask user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime | NEVER ask user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime | Use `cn-north-1` as default |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.eip_id}}` | User-supplied EIP ID | Ask once; reuse |
| `{{user.eip_name}}` | User-supplied EIP name | Ask once; reuse |
| `{{user.bandwidth}}` | Bandwidth in Mbps | Ask once; reuse |
| `{{user.instance_id}}` | Target instance ID | Ask once; reuse |
| `{{output.eip_id}}` | From API/CLI response | Parse from `$.result.addressId` |
| `{{output.public_ip}}` | From API/CLI response | Parse from `$.result.publicIp` |

> **Security Warning:** NEVER log, print, or expose `JDC_SECRET_KEY`. Check existence only.

## API and Response Conventions

- **OpenAPI is canonical**: Base path `https://eip.jdcloud-api.com/v1/regions/{regionId}/...`
- **Timestamps**: ISO 8601 with timezone
- See [API & SDK Usage](references/api-sdk-usage.md) for detailed schemas

### Response Field Table

| Operation | JSON Path | Type |
|-----------|-----------|------|
| Allocate | `$.result.addressId` | string |
| Allocate | `$.result.publicIp` | string |
| Describe | `$.result.address.status` | string |
| List | `$.result.addresses[*].addressId` | array |

### Expected State Transitions

| Operation | Initial | Target | Poll Interval | Max Wait |
|-----------|---------|--------|---------------|----------|
| Allocate | — | `available` | 5s | 60s |
| Associate | `available` | `in-use` | 5s | 60s |
| Dissociate | `in-use` | `available` | 5s | 60s |
| Delete | `available` | 404 | 5s | 120s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.2.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, mandatory) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for CLI parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.1.0 | 2026-06-04 | **GCL rollout**: Added `## Quality Gate (GCL)` chapter wiring this skill into the repository-wide Generator-Critic-Loop. Added `references/rubric.md` (5-dimension rubric, EIP-specific rules for irreversible `release EIP`, prod-tagged `dissociate` / `release` confirm, `associate` force-rebind guard) and `references/prompt-templates.md` (G/C/O prompt skeletons). `max_iterations=2`. `safety_confirm_required=true` for `dissociate EIP`, `release EIP`, `associate EIP` (force-rebind). |
| 1.0.0 | 2026-06-03 | Initial version with jdc-first execution and SDK fallback |

## Execution Flows (Agent-Readable)

All operations follow: **Pre-flight → Execute (jdc/SDK) → Validate → Recover**

### Operation: Allocate EIP

#### Pre-flight Checks

| Check | Expected | On Failure |
|-------|----------|------------|
| CLI deps | `jdc --version` exit 0 | Retry 3x; fallback to SDK |
| SDK deps | No import error | Document install pin |
| Credentials | Non-empty keys | HALT; user configures |
| Region | Supported | Suggest valid region |
| Quota | Sufficient | HALT; user raises quota |

#### Execution — CLI [Primary]

```bash
jdc --output json eip allocate-address \
  --region-id "{{user.region}}" \
  --address-name "{{user.eip_name}}" \
  --bandwidth "{{user.bandwidth|default:5}}"
```

#### Execution — SDK [Fallback]

```python
from jdcloud_sdk.services.eip.client.EipClient import EipClient
from jdcloud_sdk.services.eip.apis.AllocateAddressRequest import AllocateAddressRequest

client = EipClient(credential, "{{user.region}}")
params = AllocateAddressParameters(regionId="{{user.region}}")
params.setAddressName("{{user.eip_name}}")
params.setBandwidth({{user.bandwidth|default:5}})
resp = client.send(AllocateAddressRequest(parameters=params))
```

#### Post-execution Validation

1. Capture `{{output.eip_id}}` from `$.result.addressId`
2. Poll until status == `available` (max 12 attempts, 5s interval)
3. Report EIP ID and public IP to user

#### Failure Recovery

| Error | Retries | Action |
|-------|---------|--------|
| `InvalidParameter` | 0-1 | Fix args per OpenAPI |
| `QuotaExceeded` | 0 | HALT |
| `InsufficientBalance` | 0 | HALT |
| Throttling / 429 | 3 | Exponential backoff |
| `InternalError` / 5xx | 3 | Retry then HALT |

### Operation: Describe EIP

#### Execution (CLI)

```bash
jdc --output json eip describe-address \
  --region-id "{{user.region}}" \
  --address-id "{{user.eip_id}}"
```

#### Execution (SDK)

See [API & SDK Usage](references/api-sdk-usage.md) for details.

#### Present to User

| Field | JSON Path |
|-------|-----------|
| EIP ID | `$.result.address.addressId` |
| Name | `$.result.address.addressName` |
| Status | `$.result.address.status` |
| Public IP | `$.result.address.publicIp` |
| Bandwidth | `$.result.address.bandwidth` |

### Operation: List EIPs

#### Execution (CLI)

```bash
jdc --output json eip describe-addresses \
  --region-id "{{user.region}}" \
  --page-number 1 \
  --page-size 100
```

### Operation: Associate EIP

#### Pre-flight

Verify EIP is `available` and target instance exists.

#### Execution (CLI)

```bash
jdc --output json eip associate-address \
  --region-id "{{user.region}}" \
  --address-id "{{user.eip_id}}" \
  --instance-id "{{user.instance_id}}" \
  --instance-type "{{user.instance_type|default:"vm"}}"
```

#### Validation

Poll until status == `in-use`

### Operation: Dissociate EIP

#### Pre-flight

Verify EIP is `in-use`.

#### Execution (CLI)

```bash
jdc --output json eip dissociate-address \
  --region-id "{{user.region}}" \
  --address-id "{{user.eip_id}}"
```

#### Validation

Poll until status == `available`

### Operation: Delete EIP

#### Safety Gate

- MUST obtain explicit confirmation
- MUST check if EIP is associated — warn and dissociate first
- MUST NOT proceed without user assent

#### Execution (CLI)

```bash
jdc --output json eip release-address \
  --region-id "{{user.region}}" \
  --address-id "{{user.eip_id}}"
```

#### Validation

Poll until 404 (max 24 attempts, 5s interval)

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **required** for this skill (per `AGENTS.md` §8 — destructive ops).

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **2** | `release EIP` is irreversible; `dissociate EIP` can break production traffic; do not retry repeatedly |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `dissociate EIP`, `release EIP`, `associate EIP` (force-rebind) | matches repository safety gate policy |
| `hallucination_check` | **mandatory** | Phase 6 H layer; validates CLI parameters before execution |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `docs/failure-patterns.md` |

### Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► jdc (primary) → SDK (after 3 fails)
   │                              generate command (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (mandatory for eip-ops)       - CLI parameter existence
   │                                   - JSON structure compliance
   │
   ├── PASS → [1a] Execute (run the jdc/SDK call)
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
   ├─ iter<2 & not all pass   → RETRY (inject suggestions)
   └─ iter=2 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Mandatory

> **Purpose**: Catch LLM-generated CLI/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud EIP API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for eip-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in `jdc eip <operation>` | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads (if any) | Validate field nesting matches OpenAPI schema |

**Key Parameters to Validate:**

| Operation | Critical Parameters |
|---|---|
| `allocate-address` | `--region-id`, `--address-name`, `--bandwidth` |
| `describe-address` | `--region-id`, `--address-id` |
| `describe-addresses` | `--region-id`, `--page-number`, `--page-size` |
| `associate-address` | `--region-id`, `--address-id`, `--instance-id`, `--instance-type` |
| `dissociate-address` | `--region-id`, `--address-id` |
| `release-address` | `--region-id`, `--address-id` |

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
      "cli_parameters": { "status": "PASS|FAIL", "unrecognized_params": [] },
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
│   §1 CLI Parameter Errors | §2 Skill Generation | §3 Cross-Skill│
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
# 2. Filter patterns by current skill name (jdcloud-eip-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidAddressId: EIP ID must be valid format
- EIPInUse: Cannot release EIP that is currently associated
- InvalidInstanceState: Target instance must be in running state"
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter" | "skill_generation" | "cross_skill" | "runtime" | "token_efficiency",
    "skill": "jdcloud-eip-ops",
    "command": "jdc eip release-address ...",
    "error": "InvalidParameter: InvalidAddressId",
    "fix": "EIP ID must be valid format",
    "reusable": true
  }
}
```

Reusable patterns (reusable=true) are candidates for `docs/failure-patterns.md` — the centralized Reflexion memory.

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O / H): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): [docs/failure-patterns.md](../docs/failure-patterns.md)

### Integration with existing flows

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK access.
The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is a mandatory pre-execution structural check.

### Operation-specific behavior

- **`allocate EIP`** — Bandwidth + ISP must be explicit. Check quota first.
  H layer validates `--region-id`, `--address-name`, `--bandwidth` before execution.
- **`associate EIP`** — Target instance MUST be in `running` state. EIP MUST
  be in `Available` state. Refuse to force-rebind an EIP in `InUse` state
  without explicit opt-in. H layer validates `--address-id`, `--instance-id`, `--instance-type` before execution.
- **`dissociate EIP`** — Can break production traffic. Always `describe-eip`
  first. Safety = 0 without `confirm=DISSOCIATE` → ABORT. For prod-tagged
  EIPs, additional `confirm=DISSOCIATE_PROD` required. H layer validates `--address-id` before execution.
- **`release EIP`** — **IRREVERSIBLE** (public IP returns to pool, may be
  allocated to another tenant). EIP MUST be in `Available` state (not
  `InUse`); refuse if still attached. Safety = 0 without `confirm=RELEASE`
  → ABORT. For prod-tagged EIPs, additional `confirm=RELEASE_PROD` required. H layer validates `--address-id` before execution.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

See [Integration](references/integration.md) for detailed setup:
- Install `uv` for environment management
- Bootstrap Python environment with `jdcloud_cli` and `jdcloud_sdk`
- Configure credentials for CLI (INI file) or SDK (env vars)

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)

## Operational Best Practices

- **Least privilege**: IAM policies scoped to required APIs only
- **Cost Optimization**: Release unused EIPs; right-size bandwidth
- **Availability**: Use EIP association/dissociation for failover
- **Security**: Use security groups to restrict access
- **Monitoring**: Set up alarms for bandwidth usage and state changes
