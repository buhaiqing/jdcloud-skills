---
name: jdcloud-dns-ops
description: >-
  Use this skill to manage JD Cloud DNS (Cloud DNS Service / 云解析):
  deploy, configure, troubleshoot, or monitor DNS domains and resource
  records via API/SDK or `jdc` CLI. Trigger for DNS, 云解析, 域名解析,
  Domain Name Service, or tasks involving domain management, A/AAAA/CNAME/
  MX/TXT/SRV/NS records, DNS monitoring, custom DNS lines, or DNS traffic
  analysis — even without explicit "DNS" mention.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.1.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "JD Cloud DNS API v1 - https://domainservice.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing both 'clouddnsservice' (legacy)
    and 'domainservice' (newer) in product list.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud DNS (Cloud DNS Service) Operations Skill

## Overview

JD Cloud DNS (云解析 / Cloud DNS Service) is a high-availability, scalable DNS hosting service that provides domain name resolution with intelligent routing, health monitoring, and traffic analysis. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** Official `jdc` supports this product via two CLI modules: `domainservice` (newer, recommended) and `clouddnsservice` (legacy). The Agent MUST attempt `jdc domainservice` as primary path. Retry up to 3 times with exponential backoff, then fall back to SDK/API.

### CLI Module Selection

| Module | Status | Convention | Recommendation |
|--------|--------|------------|----------------|
| `domainservice` | **Newer** | `describe-*` / `create-*` / `modify-*` / `delete-*` | **Use as primary** |
| `clouddnsservice` | Legacy | `get-*` / `add-*` / `update-*` / `del-*` | Fallback only |

> **Always prefer `domainservice`**. Use `clouddnsservice` only when `domainservice` is unavailable.

### Path Preference (jdc-first with SDK Fallback)

1. **`jdc` CLI (primary)** — Attempt `jdc domainservice` first
2. **Retry up to 3 times** (exponential backoff: 0s → 2s → 4s)
3. **SDK/API (fallback)** — After 3 consecutive jdc failures

See [CLI Usage](references/cli-usage.md) for critical jdc behavioral notes.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud DNS", "云解析", "域名解析", "Domain Name Service", or "DNS解析"
- CRUD operations on DNS domains (主域名) and resource records (解析记录): A, AAAA, CNAME, MX, TXT, SRV, NS
- Batch import/update DNS records, enable/disable/delete records
- DNS monitoring (网站监控), custom DNS lines (自定义解析线路), DNS resolution statistics
- DNS operation logs (操作记录), DNS view tree (基础解析线路)
- Keywords: addDomain, createDomain, addRR, createResourceRecord, searchRR, operateRR, A record, CNAME, MX record, 解析, 域名

### SHOULD NOT Use This Skill When

- Domain **registration** (购买域名) → delegate to: `jdcloud-domain-ops` (when present)
- **SSL certificate** management → delegate to: `jdcloud-cert-ops`
- **HTTPDNS** → delegate to: `jdcloud-httpdns-ops` (when present)
- **CDN** configuration → delegate to: `jdcloud-cdn-ops` (when present)
- **WAF** domain protection → delegate to: `jdcloud-waf-ops`
- **Load balancer** DNS → delegate to: `jdcloud-clb-ops`
- **Monitoring/alarms** → delegate to: `jdcloud-cloudmonitor-ops`

### Delegation Rules

- If DNS points to CLB/VM/CDN, verify target exists via respective skill first
- For SSL certificate association, coordinate with `jdcloud-cert-ops`

## Variable Convention (Agent-Readable)

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime | NEVER ask user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime | NEVER ask user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime | Use `cn-north-1` as default |
| `{{user.domain_id}}` | User-supplied domain ID | Ask once; reuse |
| `{{user.domain_name}}` | User-supplied domain name | Ask once; reuse |
| `{{user.record_id}}` | User-supplied resource record ID | Ask once; reuse |
| `{{user.rr_type}}` | DNS record type (A/AAAA/CNAME/MX/TXT/SRV/NS) | Ask once; reuse |
| `{{user.rr_value}}` | DNS record value | Ask once; reuse |
| `{{user.host_rr}}` | Host record (e.g. "www", "@") | Ask once; reuse |
| `{{output.domain_id}}` | From API/CLI response | Parse from `$.result.data.domainId` |
| `{{output.record_id}}` | From API/CLI response | Parse from `$.result.data.id` |

> **Security Warning:** NEVER log, print, or expose `JDC_SECRET_KEY`. Check existence only.

## API and Response Conventions

- **OpenAPI is canonical**: Base path `https://domainservice.jdcloud-api.com/v1/regions/{regionId}/...`
- **Timestamps**: ISO 8601 with timezone
- See [API & SDK Usage](references/api-sdk-usage.md) for detailed schemas

### Response Field Table

| Operation | JSON Path | Type |
|-----------|-----------|------|
| Create Domain | `$.result.data.domainId` | int |
| Describe Domains | `$.result.dataList[*].id` | array |
| Describe Domains | `$.result.dataList[*].domainName` | array |
| Create RR | `$.result.data.id` | int |
| Search RR | `$.result.dataList[*].id` | array |
| Search RR | `$.result.dataList[*].hostRecord` | array |
| Search RR | `$.result.dataList[*].hostValue` | array |
| Search RR | `$.result.dataList[*].type` | array |

### Expected State Transitions

| Operation | Initial | Target | Poll Interval | Max Wait |
|-----------|---------|--------|---------------|----------|
| Create Domain | — | Domain appears in list | 5s | 30s |
| Create RR | — | RR appears in search | 5s | 30s |
| Enable RR | `disabled` | `enabled` | 5s | 30s |
| Disable RR | `enabled` | `disabled` | 5s | 30s |
| Delete Domain | — | (removed from list) | 5s | 60s |
| Delete RR | — | (removed from search) | 5s | 30s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, recommended) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for CLI parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.0.0 | 2026-06-10 | Initial version with jdc-first execution and SDK fallback. Covers domain CRUD, resource record CRUD, batch operations, DNS monitoring, custom DNS lines, view tree, action log, and query statistics. GCL recommended (max_iter=3). |

## Execution Flows (Agent-Readable)

All operations follow: **Pre-flight → Execute (jdc/SDK) → Validate → Recover**

### Execution Strategy

1. **Primary Path**: `jdc domainservice` first
2. **Retry**: Up to 3 times with exponential backoff (0s → 2s → 4s)
3. **Fallback**: SDK after 3 consecutive jdc failures

### Sandbox Config (before any jdc command)

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = cn-north-1
endpoint = domainservice.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### Operation: Add Domain (Create Domain)

#### Pre-flight

| Check | Expected | On Failure |
|-------|----------|------------|
| CLI deps | `jdc --version` exit 0 | Retry 3x; fallback to SDK |
| Credentials | Non-empty keys | HALT |
| Domain name | Valid FQDN | HALT; fix |
| Pack ID | 0 (free), 1 (enterprise), 2 (advanced) | HALT; fix |

#### Execution — CLI [Primary]

```bash
# Free domain
jdc --output json domainservice create-domain \
  --pack-id 0 --domain-name "{{user.domain_name}}"

# Paid domain
jdc --output json domainservice create-domain \
  --pack-id "{{user.pack_id|default:1}}" \
  --domain-name "{{user.domain_name}}" \
  --buy-type 1 --time-span "{{user.time_span|default:1}}" \
  --time-unit "{{user.time_unit|default:4}}"
```

#### Execution — SDK [Fallback]

```python
from jdcloud_sdk.services.domainservice.client.DomainserviceClient import DomainserviceClient
from jdcloud_sdk.services.domainservice.apis.CreateDomainRequest import CreateDomainRequest, CreateDomainParameters

client = DomainserviceClient(credential)
params = CreateDomainParameters(packId=0, domainName="{{user.domain_name}}")
resp = client.send(CreateDomainRequest(parameters=params))
domain_id = resp.result["data"]["domainId"]
```

#### Validation & Recovery

1. Capture `{{output.domain_id}}` from `$.result.data.domainId`
2. Verify domain appears in `describe-domains` list

| Error | Retries | Action |
|-------|---------|--------|
| `InvalidParameter` / 400 | 0-1 | Fix args |
| `QuotaExceeded` | 0 | HALT |
| `InsufficientBalance` | 0 | HALT |
| Throttling / 429 | 3 | Exponential backoff |
| `InternalError` / 5xx | 3 | Retry then HALT |

### Operation: Describe Domains (List)

```bash
jdc --output json domainservice describe-domains \
  --page-number 1 --page-size 100
```

SDK: see [API & SDK Usage](references/api-sdk-usage.md).

| Field | JSON Path |
|-------|-----------|
| Domain ID | `$.result.dataList[*].id` |
| Domain Name | `$.result.dataList[*].domainName` |
| Pack ID | `$.result.dataList[*].packId` |
| Expiry Date | `$.result.dataList[*].expirationDate` |

### Operation: Delete Domain

#### Safety Gate

- **MUST** obtain explicit confirmation
- **MUST** list all resource records under this domain — warn user
- **MUST NOT** proceed without user assent

```bash
jdc --output json domainservice delete-domain \
  --domain-id "{{user.domain_id}}"
```

SDK: `DeleteDomainRequest(DeleteDomainParameters(domainId="..."))`.

#### Validation

Verify domain no longer appears in `describe-domains` list.

### Operation: Create Resource Record

#### Pre-flight

| Check | Expected | On Failure |
|-------|----------|------------|
| Domain exists | Found in list | HALT |
| Record type | A/AAAA/CNAME/MX/TXT/SRV/NS | Validate |
| Value | Type-appropriate format | Validate per type |
| Host record | Valid subdomain or "@" | Validate |

#### Execution — CLI [Primary]

```bash
jdc --output json domainservice create-resource-record \
  --domain-id "{{user.domain_id}}" \
  --req '{"hostRecord":"{{user.host_rr}}","hostValue":"{{user.rr_value}}","type":"{{user.rr_type}}","ttl":{{user.ttl|default:600}},"viewValue":{{user.view_value|default:1}}}'
```

#### Execution — SDK [Fallback]

```python
from jdcloud_sdk.services.domainservice.apis.CreateResourceRecordRequest import CreateResourceRecordRequest, CreateResourceRecordParameters

req_spec = {"hostRecord": "{{user.host_rr}}", "hostValue": "{{user.rr_value}}",
            "type": "{{user.rr_type}}", "ttl": {{user.ttl|default:600}}}
params = CreateResourceRecordParameters(domainId="{{user.domain_id}}", req=req_spec)
resp = client.send(CreateResourceRecordRequest(parameters=params))
record_id = resp.result["data"]["id"]
```

#### Validation

1. Capture `{{output.record_id}}` from `$.result.data.id`
2. Verify via `describe-resource-record`

### Operation: Search Resource Records

```bash
jdc --output json domainservice describe-resource-record \
  --domain-id "{{user.domain_id}}" \
  --page-number 1 --page-size 100
```

SDK: `DescribeResourceRecordRequest(DescribeResourceRecordParameters(domainId="..."))`.

### Operation: Modify Resource Record

```bash
jdc --output json domainservice modify-resource-record \
  --domain-id "{{user.domain_id}}" \
  --req '{"id":{{user.record_id}},"hostRecord":"{{user.host_rr}}","hostValue":"{{user.rr_value}}","type":"{{user.rr_type}}","ttl":{{user.ttl|default:600}}}'
```

SDK: `ModifyResourceRecordRequest(ModifyResourceRecordParameters(domainId="...", req={...}))`.

### Operation: Enable / Disable / Delete Resource Record

```bash
jdc --output json domainservice modify-resource-record-status \
  --domain-id "{{user.domain_id}}" \
  --ids '[{{user.record_id}}]' \
  --action "{{user.action}}"   # on=enable, off=disable, del=delete
```

SDK: `ModifyResourceRecordStatusRequest(ModifyResourceRecordStatusParameters(domainId="...", ids=[...], action="..."))`.

### Operation: Batch Set Resource Records

#### Safety Gate

- **MUST** obtain explicit confirmation
- **MUST** snapshot existing records before batch operation

```bash
jdc --output json domainservice batch-set-resource-records \
  --domain-id "{{user.domain_id}}" \
  --req '[{"id":0,"hostRecord":"www","hostValue":"1.2.3.4","type":"A","ttl":600}]'
```

SDK: `BatchSetResourceRecordsRequest(BatchSetResourceRecordsParameters(domainId="...", req=[...]))`.

### Operation: DNS Monitoring

```bash
# Create monitor
jdc --output json domainservice create-monitor \
  --domain-id "{{user.domain_id}}" \
  --sub-domain-name "{{user.sub_domain}}"

# Describe monitors
jdc --output json domainservice describe-monitor \
  --domain-id "{{user.domain_id}}" \
  --page-number 1 --page-size 100

# Modify monitor status (start/stop)
jdc --output json domainservice modify-monitor-status \
  --domain-id "{{user.domain_id}}" \
  --sub-domain-name "{{user.sub_domain}}" \
  --status "{{user.monitor_status}}"   # 1=start, 2=stop

# Delete monitor
jdc --output json domainservice delete-monitor \
  --domain-id "{{user.domain_id}}" \
  --sub-domain-name "{{user.sub_domain}}"
```

### Operation: Custom DNS Lines (User Views)

```bash
# Create custom line
jdc --output json domainservice create-user-view \
  --domain-id "{{user.domain_id}}" \
  --req '{"viewName":"{{user.view_name}}","isDelete":0}'

# Describe custom lines
jdc --output json domainservice describe-user-view \
  --domain-id "{{user.domain_id}}" \
  --page-number 1 --page-size 100

# Delete custom line
jdc --output json domainservice delete-user-view \
  --domain-id "{{user.domain_id}}" \
  --req '{"viewId":{{user.view_id}},"viewName":"{{user.view_name}}"}'
```

### Operation: View Tree & Statistics

```bash
# View tree (all base DNS lines)
jdc --output json domainservice describe-view-tree

# Query resolution count
jdc --output json domainservice describe-domain-query-count \
  --domain-id "{{user.domain_id}}" \
  --start "{{user.start_time}}" --end "{{user.end_time}}"

# Query resolution traffic
jdc --output json domainservice describe-domain-query-traffic \
  --domain-id "{{user.domain_id}}" \
  --start "{{user.start_time}}" --end "{{user.end_time}}"

# Action log
jdc --output json domainservice describe-action-log \
  --page-number 1 --page-size 100 \
  --start-time "{{user.start_time}}" --end-time "{{user.end_time}}"
```

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
| `safety_confirm_required` | **true** for delete domain / batch set | delete domain removes all records irreversibly; batch set can overwrite all records |
| `hallucination_check` | **recommended** | Phase 6 H layer; recommended for CLI/SDK parameter validation |
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
   │   (recommended for dns-ops)     - CLI parameter existence
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
   ├─ iter<3 & not all pass   → RETRY (inject suggestions)
   └─ iter=3 & not all pass   → RETURN_BEST
```

### Hallucination Detection Layer (H) — Recommended

> **Purpose**: Catch LLM-generated CLI/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud DNS API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for dns-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in `jdc domainservice <operation>` | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads (e.g., `--req` for resource records) | Validate field nesting matches OpenAPI schema |

**Key Parameters to Validate:**

| Operation | Critical Parameters |
|---|---|
| `create-domain` | `--pack-id`, `--domain-name` |
| `delete-domain` | `--domain-id` |
| `create-resource-record` | `--domain-id`, `--req` (hostRecord, hostValue, type, ttl, viewValue) |
| `modify-resource-record` | `--domain-id`, `--req` (id, hostRecord, hostValue, type, ttl) |
| `modify-resource-record-status` | `--domain-id`, `--ids`, `--action` |
| `batch-set-resource-records` | `--domain-id`, `--req` (array of record objects) |

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
# 2. Filter patterns by current skill name (jdcloud-dns-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter|runtime|cross_skill",
    "skill": "jdcloud-dns-ops",
    "command": "jdc domainservice create-resource-record ...",
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

The GCL **wraps** the jdc-first / SDK-fallback flow defined under
`## Execution Flows` above. The Generator (G) IS the existing jdc-or-SDK
executor. The Critic (C) is a new, read-only role with no `jdc` / SDK
access. The Orchestrator (O) owns the loop and persists the GCL trace.
The Hallucination Detector (H) is a recommended pre-execution structural check.

### Operation-specific behavior

- **`create-domain`** — Pack ID must be valid (0/1/2). Domain name must be valid FQDN.
- **`delete-domain`** — **IRREVERSIBLE** (all records deleted). Safety = 0 without `confirm=DELETE` → ABORT. For prod-tagged domains, `confirm=DELETE_PROD` required. Must include pre-delete snapshot of all records.
- **`create-resource-record`** — Type-specific value validation: A=IPv4, AAAA=IPv6, CNAME=FQDN, MX=priority+host, TXT=string, SRV=priority+weight+port+target. **CNAME at apex** (`hostRecord="@"`) → refuse.
- **`modify-resource-record`** — Same validation as create.
- **`delete-resource-record`** — Safety = 0 without `confirm=DELETE_RR` for production domains.
- **`enable/disable-resource-record`** — Safety = 0 if disabling critical records (`www`, `@`, `mail`) on production domains without confirm.
- **`batch-set-resource-records`** — Safety = 0 without `confirm=BATCH`. Must include pre-batch snapshot of existing records.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`.

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
- [GCL Rubric](references/rubric.md)
- [GCL Prompt Templates](references/prompt-templates.md)

## Operational Best Practices

- **Least privilege**: IAM policies scoped to required DNS APIs only
- **Record integrity**: Validate record types and values before creation
- **CNAME at apex**: Never create CNAME at zone apex — violates RFC
- **TTL planning**: Use appropriate TTLs (shorter for dynamic, longer for static)
- **Backup**: Snapshot records before batch operations
- **Monitoring**: Enable DNS monitoring for critical subdomains
- **Cost**: Use free package for dev/test; paid for production SLA