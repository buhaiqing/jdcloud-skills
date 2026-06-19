---
name: jdcloud-cert-ops
description: >-
  Use this skill to manage JD Cloud SSL Certificates (SSL 数字证书):
  upload, query, download, update, or delete certificates via API/SDK or
  `jdc` CLI. Trigger for SSL, 证书, Certificate, HTTPS, TLS, or tasks
  involving certificate lifecycle management — even without explicit
  "SSL" mention. Also supports certificate expiry cruise (证书到期巡检)
  with cross-service binding discovery.
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
  api_profile: "JD Cloud SSL API v1 - https://ssl.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc` help output showing 'ssl' in product list.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud SSL Certificate Operations Skill

## Overview

JD Cloud SSL Certificate Service (SSL 数字证书) provides digital certificate management including upload, query, download, update, and deletion. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **jdc-first execution with SDK/API fallback**, response validation, and failure recovery. Also includes a **certificate expiry cruise** flow for proactive cert lifecycle management.

### CLI applicability (repository policy)

- **`cli_applicability: jdc-first-with-fallback`:** The Agent MUST attempt `jdc ssl` as primary execution path. Retry up to 3 times with exponential backoff, then fall back to SDK/API.

### Path Preference (jdc-first with SDK Fallback)

1. **`jdc` CLI (primary)** — `jdc ssl` subcommands
2. **Retry up to 3 times** (exponential backoff: 0s → 2s → 4s)
3. **SDK/API (fallback)** — After 3 consecutive jdc failures

See [CLI Usage](references/cli-usage.md) for critical jdc behavioral notes.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "SSL certificate", "证书", "HTTPS", "TLS", "数字证书"
- CRUD operations on SSL certificates: upload, query, download, update, delete
- Certificate expiry checking / certificate lifecycle management
- Certificate rotation or renewal workflows
- Keywords: uploadCert, describeCerts, describeCert, downloadCert, deleteCerts, certId, certName, SSL, TLS

### SHOULD NOT Use This Skill When

- Domain **registration** → delegate to: `jdcloud-domain-ops` (when present)
- **DNS** record management → delegate to: `jdcloud-dns-ops`
- **CLB** HTTPS listener creation → delegate to: `jdcloud-clb-ops`
- **CDN** domain configuration → delegate to: `jdcloud-cdn-ops` (when present)
- **WAF** domain protection → delegate to: `jdcloud-waf-ops`
- **Monitoring/alarms** → delegate to: `jdcloud-cloudmonitor-ops`

### Delegation Rules

- For CLB HTTPS listener cert binding, coordinate with `jdcloud-clb-ops`
- For CDN domain cert binding, coordinate with `jdcloud-cdn-ops`
- For DNS validation records, coordinate with `jdcloud-dns-ops`

## Variable Convention (Agent-Readable)

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime | NEVER ask user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime | NEVER ask user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime | Use `cn-north-1` as default |
| `{{user.cert_id}}` | User-supplied certificate ID | Ask once; reuse |
| `{{user.cert_name}}` | User-supplied certificate name | Ask once; reuse |
| `{{user.domain_name}}` | User-supplied domain name | Ask once; reuse |
| `{{user.cert_file}}` | Path to certificate PEM file | Ask once; reuse |
| `{{user.key_file}}` | Path to private key PEM file | Ask once; reuse |
| `{{user.server_type}}` | Server type for download | Ask once; reuse |
| `{{user.alias_name}}` | Certificate alias name | Ask once; reuse; optional |
| `{{user.new_cert_name}}` | New certificate name for rename | Ask once; reuse |
| `{{output.cert_id}}` | From API/CLI response | Parse from `$.result.certId` |

> **Security Warning:** NEVER log, print, or expose `JDC_SECRET_KEY`, certificate private keys, or any secret material. Check existence only. When logging cert content, use SHA-256 fingerprint only.

## API and Response Conventions

- **OpenAPI is canonical**: Base path `https://ssl.jdcloud-api.com/v1`
- **Timestamps**: ISO 8601 with timezone
- See [API & SDK Usage](references/api-sdk-usage.md) for detailed schemas

### Response Field Table

| Operation | JSON Path | Type |
|-----------|-----------|------|
| Upload Cert | `$.result.certId` | string |
| Describe Certs | `$.result.certListDetails[*].certId` | array |
| Describe Certs | `$.result.certListDetails[*].domainName` | array |
| Describe Certs | `$.result.certListDetails[*].endDate` | array |
| Describe Cert | `$.result.certId` | string |
| Describe Cert | `$.result.domainName` | string |
| Describe Cert | `$.result.endDate` | string |
| Download Cert | `$.result.certInfo` | object |
| Delete Certs | `$.requestId` or `$.error` | string/object |

### Expected State Transitions

| Operation | Initial | Target | Poll Interval | Max Wait |
|-----------|---------|--------|---------------|----------|
| Upload Cert | — | `available` | 5s | 30s |
| Delete Cert | — | (removed from list) | 5s | 30s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, recommended) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for CLI parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.0.0 | 2026-06-10 | Initial version with jdc-first execution and SDK fallback. Covers upload, describe, download, update, delete. Includes Certificate Expiry Cruise flow with cross-service binding discovery (CLB + CDN). GCL recommended (max_iter=3). |

## Execution Flows (Agent-Readable)

All operations follow: **Pre-flight → Execute (jdc/SDK) → Validate → Recover**

### Sandbox Config (before any jdc command)

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = cn-north-1
endpoint = ssl.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### Operation: Upload Certificate

#### Pre-flight

| Check | Expected | On Failure |
|-------|----------|------------|
| CLI deps | `jdc --version` exit 0 | Retry 3x; fallback to SDK |
| Cert file | Valid PEM format, readable | HALT; fix path |
| Key file | Valid PEM format, readable | HALT; fix path |
| Cert expiry | `endDate` in future | Warn user |

#### Execution — CLI [Primary]

```bash
jdc --output json ssl upload-cert \
  --cert-name "{{user.cert_name}}" \
  --cert-file "{{user.cert_file}}" \
  --key-file "{{user.key_file}}" \
  --alias-name "{{user.alias_name|default:""}}"
```

#### Execution — SDK [Fallback]

```python
from jdcloud_sdk.services.ssl.client.SslClient import SslClient
from jdcloud_sdk.services.ssl.apis.UploadCertRequest import UploadCertRequest, UploadCertParameters

client = SslClient(credential)
with open("{{user.cert_file}}") as f: cert = f.read()
with open("{{user.key_file}}") as f: key = f.read()
params = UploadCertParameters(certName="{{user.cert_name}}", keyFile=key, certFile=cert)
resp = client.send(UploadCertRequest(parameters=params))
cert_id = resp.result["certId"]
```

#### Validation

1. Capture `{{output.cert_id}}` from `$.result.certId`
2. Verify via `describe-cert`

### Operation: Describe Certificates (List)

```bash
# List all certs
jdc --output json ssl describe-certs --page-number 1 --page-size 100

# Filter by domain
jdc --output json ssl describe-certs --domain-name "{{user.domain_name}}"
```

SDK: `DescribeCertsRequest(DescribeCertsParameters())`.

| Field | JSON Path |
|-------|-----------|
| Cert ID | `$.result.certListDetails[*].certId` |
| Domain | `$.result.certListDetails[*].domainName` |
| Issuer | `$.result.certListDetails[*].issuer` |
| Start Date | `$.result.certListDetails[*].startDate` |
| End Date | `$.result.certListDetails[*].endDate` |

### Operation: Describe Certificate (Detail)

```bash
jdc --output json ssl describe-cert --cert-id "{{user.cert_id}}"
```

SDK: `DescribeCertRequest(DescribeCertParameters(certId="..."))`.

### Operation: Download Certificate

> **[MFA enabled]** — Requires Multi-Factor Authentication.

```bash
jdc --output json ssl download-cert \
  --cert-id "{{user.cert_id}}" \
  --server-type "{{user.server_type}}"
```

Server types: `Nginx`, `Apache`, `Tomcat`, `IIS`, `Other`.

SDK: `DownloadCertRequest(DownloadCertParameters(certId="...", serverType="..."))`.

### Operation: Update Certificate Name

```bash
jdc --output json ssl update-cert-name \
  --cert-id "{{user.cert_id}}" \
  --cert-name "{{user.new_cert_name}}"
```

SDK: `UpdateCertNameRequest(UpdateCertNameParameters(certId="...", certName="..."))`.

### Operation: Update Certificate

> **[MFA enabled]** — Replaces cert and key content.

```bash
jdc --output json ssl update-cert \
  --cert-id "{{user.cert_id}}" \
  --cert-file "{{user.cert_file}}" \
  --key-file "{{user.key_file}}"
```

SDK: `UpdateCertRequest(UpdateCertParameters(certId="...", keyFile=key, certFile=cert))`.

### Operation: Delete Certificate

#### Safety Gate

- **MUST** obtain explicit confirmation
- **MUST** check if cert is bound to CLB listeners or CDN domains — warn user
- **MUST NOT** proceed without user assent
- **MUST** use required confirmation flags per [Quality Gate (GCL)](#quality-gate-gcl):
  - `confirm=DELETE` required for all delete operations
  - `confirm=DELETE_PROD` required for prod-tagged certificates

#### Execution (CLI) [Primary]

> **[MFA enabled]**

```bash
jdc --output json ssl delete-certs --cert-id "{{user.cert_id}}"
```

SDK: `DeleteCertsRequest(DeleteCertsParameters(certId="..."))`.

#### Validation

Verify cert no longer appears in `describe-certs` list.

#### Failure Recovery

| Error | Retries | Action |
|-------|---------|--------|
| `InvalidParameter` / 400 | 0-1 | Fix args |
| Throttling / 429 | 3 | Exponential backoff |
| `InternalError` / 5xx | 3 | Retry then HALT |

## Certificate Expiry Cruise (证书到期巡检)

> **Read-only flow.** No mutations. Cross-references CLB and CDN to discover which instances use each certificate.

### Flow Overview

```
[1] List all certificates (describe-certs)
        │
        ▼
[2] For each cert, check endDate
        │
        ├─ expired (endDate < now)         → CRITICAL
        ├─ expiring within 30 days          → WARNING
        ├─ expiring within 60 days          → INFO
        └─ valid (> 60 days)               → OK
        │
        ▼
[3] For expiring/expired certs, discover bindings:
        │
        ├─ Query CLB listeners (via jdcloud-clb-ops)
        │   → jdc --output json lb describe-listeners
        │   → For each HTTPS listener, check certificateId matches
        │
        └─ Query CDN domains (via jdcloud-cdn-ops)
            → jdc --output json cdn get-ssl-cert-list
            → Match certId to CDN domains
        │
        ▼
[4] Generate report
```

### Step 1: List All Certificates

```bash
jdc --output json ssl describe-certs --page-number 1 --page-size 100
```

Parse `$.result.certListDetails` for each cert's `certId`, `domainName`, `endDate`.

### Step 2: Classify by Expiry

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
for cert in certs:
    end_date = datetime.fromisoformat(cert["endDate"])
    days_left = (end_date - now).days
    if days_left < 0:
        status = "CRITICAL"  # expired
    elif days_left <= 30:
        status = "WARNING"   # expiring soon
    elif days_left <= 60:
        status = "INFO"      # approaching expiry
    else:
        status = "OK"
```

### Step 3: Discover Bindings

#### CLB Listener Binding Check

> **Note:** JD Cloud CLB listener detail may not expose `certificateId` in the API response.
> If cert binding cannot be determined via API, document this limitation in the report.

For each expiring/expired cert, check CLB HTTPS listeners:

```bash
# Step 1: List all CLBs
CLBS=$(jdc --output json lb describe-load-balancers --region-id "{{user.region}}" --page-number 1 --page-size 100)

# Step 2: For each CLB, list listeners and check for certificate binding
for lb_id in $(echo "$CLBS" | jq -r '.result.loadBalancers[].loadBalancerId'); do
  LISTENERS=$(jdc --output json lb describe-listeners --region-id "{{user.region}}" --load-balancer-id "$lb_id")
  # Check if any listener uses the cert (note: JD Cloud CLB API may not expose certId in listener response)
  echo "$LISTENERS" | jq -r --arg certId "{{user.cert_id}}" '.result.listeners[] | select(.certificateId == $certId) | {lbId: "'$lb_id'", listenerId: .listenerId, protocol: .protocol}'
done
```

#### CDN Domain Binding Check

> **Note:** CDN CLI support depends on `jdc cdn` availability.
> If `jdc cdn` commands fail, skip CDN binding discovery and note in the report:
> "CDN binding check skipped — CDN CLI not available or returned error."

```bash
# Attempt to query CDN domains (may not be available)
jdc --output json cdn get-domain-list 2>/dev/null || echo "CDN CLI not available"
```

### Step 4: Generate Report

Output format:

| Field | Source | Description |
|-------|--------|-------------|
| `certId` | SSL API | Certificate ID |
| `certName` | SSL API | Certificate name |
| `domainName` | SSL API | Primary domain |
| `endDate` | SSL API | Expiry date (ISO 8601) |
| `daysUntilExpiry` | Calculated | Days remaining (negative = expired) |
| `status` | Calculated | CRITICAL / WARNING / INFO / OK |
| `boundCLBInstances` | CLB API | List of CLB instance IDs using this cert |
| `boundCDNDomains` | CDN API | List of CDN domains using this cert |

**Example report:**

```
SSL Certificate Expiry Cruise Report — 2026-06-10
====================================================

CRITICAL (expired):
  cert-abc123 | example.com | 2026-05-01 | -40 days
    → Bound CLB: lb-xxx (HTTPS listener on port 443)
    → Bound CDN: cdn.example.com

WARNING (≤30 days):
  cert-def456 | api.example.com | 2026-06-25 | 15 days
    → Bound CLB: lb-yyy (HTTPS listener on port 443)

INFO (≤60 days):
  cert-ghi789 | www.example.com | 2026-07-20 | 40 days
    → No bindings found

OK (>60 days): 5 certificates
```

### Delegation for Remediation

After the cruise report is generated:

- **Renew certificate**: Upload new cert via this skill (`upload-cert` or `update-cert`)
- **Update CLB listener cert**: Delegate to `jdcloud-clb-ops`
- **Update CDN domain cert**: Delegate to `jdcloud-cdn-ops`
- **Set expiry alarm**: Delegate to `jdcloud-cloudmonitor-ops`

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
| `safety_confirm_required` | **true** for delete cert / update cert | delete cert breaks HTTPS for bound CLB/CDN; update cert replaces content |
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
   │   (recommended for cert-ops)    - CLI parameter existence
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
> **before** they reach the JD Cloud SSL API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for cert-ops):**

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` exists in `jdc ssl <operation>` | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads | Validate field nesting matches OpenAPI schema |

**Key Parameters to Validate:**

| Operation | Critical Parameters |
|---|---|
| `upload-cert` | `--cert-name`, `--cert-file`, `--key-file` |
| `describe-certs` | `--page-number`, `--page-size`, `--domain-name` |
| `describe-cert` | `--cert-id` |
| `download-cert` | `--cert-id`, `--server-type` |
| `update-cert-name` | `--cert-id`, `--cert-name` |
| `update-cert` | `--cert-id`, `--cert-file`, `--key-file` |
| `delete-certs` | `--cert-id` |

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
# 2. Filter patterns by current skill name (jdcloud-cert-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints
```

**This is a HINT, not a CONSTRAINT** — the Generator should use these patterns to avoid known mistakes, but is not required to follow them if the context differs.

**Failure Pattern Extraction:**

When a GCL iteration fails (SAFETY_FAIL, HALLUCINATION_ABORT, or rubric dimension < threshold), the Orchestrator SHOULD extract a structured failure pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter|runtime|cross_skill",
    "skill": "jdcloud-cert-ops",
    "command": "jdc ssl upload-cert ...",
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

- **`upload-cert`** — Cert + key must be valid PEM. Check expiry date; warn if already expired.
- **`delete-cert`** — **Breaks HTTPS** for all bound CLB listeners and CDN domains. Safety = 0 without `confirm=DELETE` → ABORT. For prod-tagged certs, `confirm=DELETE_PROD` required. Must check CLB/CDN bindings first and warn user.
- **`download-cert`** — Requires MFA. Server type must be valid (Nginx/Apache/Tomcat/IIS/Other).
- **`update-cert`** — Requires MFA. New cert must not be expired. Old cert content is replaced.
- **`certificate-expiry-cruise`** — Read-only. Must cross-reference CLB listeners and CDN domains. Report must include binding information for expiring/expired certs.

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

- **Least privilege**: IAM policies scoped to required SSL APIs only
- **Private key security**: Never log or store private keys in plaintext
- **Expiry monitoring**: Run certificate expiry cruise regularly (weekly recommended)
- **Rotation planning**: Begin renewal at least 30 days before expiry
- **Binding awareness**: Always check CLB/CDN bindings before deleting or updating certs
- **MFA**: Enable MFA for download and update operations

