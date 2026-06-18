---
name: jdcloud-oss-ops
description: >-
  Use this skill for JD Cloud Object Storage Service (OSS) management — create
  and configure buckets, upload and download objects, manage ACL and lifecycle
  policies, generate presigned URLs, configure versioning and cross-region
  replication. Apply when the user mentions OSS, 对象存储, 存储桶, bucket,
  object storage, 文件存储, 静态网站托管, or asks about storing, retrieving,
  or managing data on JD Cloud OSS.
license: MIT
compatibility: >-
  Official JD Cloud Python SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud OSS endpoints. **OSS is NOT supported by the `jdc` CLI** —
  execution is SDK-only.
metadata:
  author: buhaiqing
  version: "1.1.0"
  last_updated: "2026-06-18"
  runtime: Harness AI Agent
  api_profile: "JD Cloud OSS API v1 - https://oss.jdcloud-api.com/v1"
  cli_applicability: sdk-only
  cli_version_locked: N/A
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    OSS is NOT exposed via `jdc` CLI. Confirmed via `jdc --help | grep -i oss`
    returning no output. The `jdc` CLI (`jdcloud_cli==1.2.12`) does not include
    an `oss` product group. All OSS operations MUST use the Python SDK
    (`jdcloud_sdk.services.oss.client.OssClient`) or direct HTTP API calls.
  gcl_classification: recommended
  gcl_max_iter: 3
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud Object Storage Service (OSS) Operations Skill

## Overview

JD Cloud Object Storage Service (OSS) is a scalable, durable, and secure cloud storage service. Data is stored as objects within buckets, distributed across multiple devices and facilities for high availability and durability. This skill is an **operational runbook** for agents: explicit scope, credential rules, pre-flight checks, **SDK-only execution** (OSS is NOT exposed via `jdc` CLI), response validation, and failure recovery. **Do not use the web console as the primary agent execution path** in `SKILL.md`.

### CLI applicability (repository policy)

- **`cli_applicability: sdk-only`:** The `jdc` CLI does NOT support OSS operations. The Agent MUST use the **Python SDK** (`jdcloud_sdk.services.oss.client.OssClient`) as the **sole execution path**. There is no `jdc` fallback. All OSS operations are performed via the OSS REST API at `oss.jdcloud-api.com`.

### Path Preference (SDK-only)

The Agent MUST follow this execution priority:

1. **Python SDK (sole path)** — Use `jdcloud_sdk.services.oss.client.OssClient` for all OSS operations.
2. **Retry up to 3 times** if SDK call fails (with exponential backoff: 0s → 2s → 4s).
3. **HTTP API (direct, after 3 SDK failures)** — Use direct HTTP calls to `https://oss.jdcloud-api.com/v1` as a last resort.

> **Important:** The `jdc` CLI (`jdcloud_cli==1.2.12`) does NOT include an `oss` product group. Do NOT attempt to run `jdc` commands for OSS operations. This is confirmed via `jdc --help | grep -i oss` returning no output.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User mentions "JD Cloud OSS" OR "对象存储" OR "存储桶" OR "bucket" OR "object storage"
- Task involves CRUD operations on buckets: create, list, describe, delete, configure ACL/lifecycle/versioning/replication
- Task involves object operations: upload, download, delete, list, copy, multipart upload, presigned URL
- Task keywords: createBucket, listBuckets, headBucket, deleteBucket, putBucketAcl, putBucketLifecycle, putObject, getObject, deleteObject, generatePresignedUrl
- User asks to store, retrieve, manage, archive, or backup data on JD Cloud OSS
- User asks about static website hosting on OSS
- User asks about cost optimization via lifecycle policies or storage class transitions

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops` (when present)
- Task is IAM / permission model only → delegate to: `jdcloud-iam-ops`
- Task is about VPC / subnet / security group → delegate to: `jdcloud-vpc-ops`
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops`
- Task is about CDN configuration for OSS origin → delegate to: `jdcloud-cdn-ops` (when present)
- Task is about KMS encryption key management → delegate to: `jdcloud-kms-ops`
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

### Delegation Rules

- If OSS bucket requires KMS encryption, delegate key creation/management to `jdcloud-kms-ops`.
- If user asks about OSS monitoring metrics or alarm rules, delegate metric query to `jdcloud-cloudmonitor-ops`.
- If user asks about IAM policies for OSS access control, delegate to `jdcloud-iam-ops`.
- Multi-product requests: handle each product with its skill; do not merge unrelated APIs into one ambiguous flow.

## Variable Convention (Agent-Readable)

Structured placeholders reduce injection ambiguity and unsafe prompts:

| Placeholder | Meaning | Agent Action |
|-------------|---------|--------------|
| `{{env.JDC_ACCESS_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_SECRET_KEY}}` | From runtime environment | NEVER ask the user; fail if unset |
| `{{env.JDC_REGION}}` | From runtime environment | Use `cn-north-1` as default if unset |
| `{{user.region}}` | User-supplied region | Ask once; reuse |
| `{{user.bucket_name}}` | User-supplied globally unique bucket name | Ask once; reuse |
| `{{user.object_key}}` | User-supplied object key (path) | Ask once; reuse |
| `{{user.bucket_acl}}` | User-supplied ACL (private/public-read/public-read-write) | Ask once; reuse |
| `{{output.bucket_name}}` | From last API JSON response | Parse from `$.result.bucketName` |
| `{{output.object_etag}}` | From last API JSON response | Parse from `$.result.objectETag` |
| `{{output.presigned_url}}` | From last API JSON response | Parse from `$.result.presignedUrl`; NEVER log fully |

> **`{{env.*}}` MUST NOT** be collected from the user. **`{{user.*}}`** MUST be collected interactively when missing.

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` (or any secret) in console output, debug messages, or logs. When verification is needed, check existence only (e.g., `if os.environ.get('JDC_SECRET_KEY')`) without printing the actual value. If logging credential status is required, use masked placeholders like `JDC_SECRET_KEY=<masked>` or `JDC_SECRET_KEY=***`. **NEVER** log full presigned URLs in trace output — they contain credential signatures. Log only the URL prefix (e.g., `presigned URL generated for object <key>`).

## API and Response Conventions (Agent-Readable)

- **OpenAPI is canonical** for path, query, body fields, enums, and response shapes. Base path: `https://oss.jdcloud-api.com/v1`
- **Errors:** Map SDK/HTTP errors to `code` / `status` / message fields per spec.
- **Timestamps:** ISO 8601 with timezone when the API returns strings (e.g. `2026-06-01T10:00:00+08:00`).
- **Idempotency:** Bucket creation with same name returns `BucketAlreadyExists`. Object PUT with same key overwrites existing object. Bucket deletion on non-empty bucket returns `BucketNotEmpty`.

### Example Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Bucket | `$.result.bucketName` | string | New bucket name |
| List Buckets | `$.result.buckets[*].bucketName` | array | All bucket names |
| Head Bucket | `$.result.objectCount` | integer | Number of objects in bucket |
| Head Bucket | `$.result.bucketAcl` | string | Current ACL (private/public-read/public-read-write) |
| Head Bucket | `$.result.versioning` | string | Versioning status (none/enabled/suspended) |
| Put Object | `$.result.objectETag` | string | ETag of uploaded object |
| List Objects | `$.result.objects[*].key` | array | All object keys |
| Gen. Presigned URL | `$.result.presignedUrl` | string | Temporary access URL (NEVER log fully) |

### Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Bucket | — | bucket exists | 5s | 60s |
| Delete Bucket | bucket exists | (404 on headBucket) | 5s | 120s |
| Put Object | — | object exists | 2s | 30s |
| Configure Lifecycle | — | rules applied | 5s | 30s |
| Set Versioning | — | versioning configured | 5s | 30s |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-06-18 | **GCL v2 rollout**: Enhanced Quality Gate with Phase 6 Hallucination Detection Layer (H, recommended) and Phase 7 Reflexion Integration. Added pre-execution structural validity check for SDK method parameters and JSON payloads. Integrated `docs/failure-patterns.md` for cross-session failure memory. Aligned with AGENTS.md GCL v2 specification (§10-11). |
| 1.0.0 | 2026-06-08 | Initial version: SDK-only execution path for OSS bucket CRUD, object CRUD, ACL, lifecycle, versioning, CRR, presigned URL; GCL rollout with rubric v1 and prompt templates; safety gates for destructive ops |

## Execution Flows (Agent-Readable)

Every operation: **Pre-flight → Execute (SDK) → Validate → Recover**. Do not skip phases.

**SDK-only strategy:** OSS is NOT supported by the `jdc` CLI. The Agent MUST use the Python SDK exclusively. If SDK calls fail after **3 retries** with exponential backoff, fall back to direct HTTP API calls.

### Prerequisites: SDK-only Setup

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk>=1.6.26
python -c "
import jdcloud_sdk
from jdcloud_sdk.services.oss.client.OssClient import OssClient
print('OSS SDK ready')
"
```

### SDK Client Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.oss.client.OssClient import OssClient

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = OssClient(credential, endpoint="oss.jdcloud-api.com")
```

### Operation: Create Bucket

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| SDK / deps | `import jdcloud_sdk.services.oss.client.OssClient` | No import error | HALT; install SDK |
| Credentials | Construct credential from env | Non-empty keys | HALT; user configures env |
| Bucket name uniqueness | `listBuckets` or `headBucket` | Name not taken | Suggest alternative |
| Bucket name validity | Validate per naming rules | 3-63 chars, lowercase, no IP | Fix name |
| Bucket quota | `listBuckets` count | < 100 buckets | HALT; quota exceeded |

#### Bucket Naming Rules

- Length: 3-63 characters
- Must be globally unique across all JD Cloud regions
- Can contain lowercase letters, numbers, and hyphens (-)
- Must start and end with a letter or number
- Cannot contain underscores, uppercase letters, or periods
- Cannot be formatted as an IP address (e.g., 192.168.0.1)
- Recommended pattern: `<project>-<environment>-<purpose>-<region-code>`

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.CreateBucketRequest import CreateBucketRequest, CreateBucketParameters

params = CreateBucketParameters(
    bucketName="{{user.bucket_name}}",
    regionId="{{user.region}}"
)
req = CreateBucketRequest(parameters=params)
resp = client.send(req)
bucket_name = resp.result["bucketName"]
```

#### Post-execution Validation

1. Capture `{{output.bucket_name}}` from `$.result.bucketName`.
2. Verify via `headBucket` call.
3. Report bucket name and location endpoint.

#### Failure Recovery

| Error pattern | Max retries | Backoff | Agent Action |
|---------------|-------------|---------|--------------|
| `InvalidBucketName` / 400 | 0–1 | — | Fix name per naming rules; retry once |
| `BucketAlreadyExists` / 409 | 0 | — | Suggest unique alternative name |
| `AccessDenied` / 403 | 0 | — | Check credentials and IAM policy |
| `InvalidArgument` / 400 | 0–1 | — | Fix region or params |
| Quota limit | 0 | — | HALT; max 100 buckets per account |
| `InternalError` / 5xx | 3 | 2s, 4s, 8s | Retry; HALT with requestId if persists |

### Operation: List Buckets

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.ListBucketsRequest import ListBucketsRequest, ListBucketsParameters

params = ListBucketsParameters()
req = ListBucketsRequest(parameters=params)
resp = client.send(req)
buckets = resp.result["buckets"]  # Array of bucket objects
```

### Operation: Head Bucket (Get Bucket Metadata)

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.HeadBucketRequest import HeadBucketRequest, HeadBucketParameters

params = HeadBucketParameters(bucketName="{{user.bucket_name}}")
req = HeadBucketRequest(parameters=params)
resp = client.send(req)
# Access fields: bucketName, regionId, bucketAcl, storageClass, objectCount, totalSizeBytes, creationDate, versioning
```

### Operation: Delete Bucket

#### Pre-flight (Safety Gate)

- **⚠️ IRREVERSIBLE** — ALL objects in the bucket will be permanently deleted.
- **MUST** verify bucket is empty via `headBucket` (check `objectCount == 0`).
- **MUST** obtain explicit confirmation: `confirm=DELETE_BUCKET`.
- For prod-tagged buckets (`env=prod`), additionally require `confirm=DELETE_BUCKET_PROD`.
- **MUST** capture pre-delete snapshot (bucket metadata with object count).

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.DeleteBucketRequest import DeleteBucketRequest, DeleteBucketParameters

# Pre-delete snapshot
head_params = HeadBucketParameters(bucketName="{{user.bucket_name}}")
head_req = HeadBucketRequest(parameters=head_params)
head_resp = client.send(head_req)
pre_snapshot = head_resp.result  # Save for trace

# Confirm deletion with user first
# Then execute
params = DeleteBucketParameters(bucketName="{{user.bucket_name}}")
req = DeleteBucketRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Verify deletion via `headBucket` (expect HTTP 404 / `NoSuchBucket`).

### Operation: Set Bucket ACL

#### Pre-flight (Safety Gate)

- **`public-read-write`** is a security risk — MUST obtain explicit opt-in confirmation.
- **`public-read`** on prod-tagged buckets requires warning + explicit opt-in.
- Always verify WAF-SEC-010 rules.

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.PutBucketAclRequest import PutBucketAclRequest, PutBucketAclParameters

params = PutBucketAclParameters(
    bucketName="{{user.bucket_name}}",
    bucketAcl="{{user.bucket_acl}}"  # "private" | "public-read" | "public-read-write"
)
req = PutBucketAclRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Verify ACL via `getBucketAcl` or `headBucket`.

| ACL Value | Production Safe | Confirmation Required |
|-----------|----------------|----------------------|
| `private` | ✅ Yes | None |
| `public-read` | ⚠️ With caution | Warning + opt-in on prod |
| `public-read-write` | ❌ No | Explicit opt-in (never on prod) |

### Operation: Configure Bucket Lifecycle

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.PutBucketLifecycleRequest import PutBucketLifecycleRequest, PutBucketLifecycleParameters

rules = [
    {
        "id": "{{user.rule_id}}",
        "status": "Enabled",
        "filter": {"prefix": "{{user.prefix}}"},
        "transitions": [
            {"days": {{user.transition_days_1}}, "storageClass": "{{user.storage_class_1}}"},
            {"days": {{user.transition_days_2}}, "storageClass": "{{user.storage_class_2}}"}
        ]
    }
]

params = PutBucketLifecycleParameters(
    bucketName="{{user.bucket_name}}",
    rules=rules
)
req = PutBucketLifecycleRequest(parameters=params)
resp = client.send(req)
```

#### Validation

- Verify transition days are ascending (e.g., 30 → 180, not 180 → 30).
- Validate storage class names: `Standard`, `InfrequentAccess`, `Archive`.
- Verify rule IDs are unique within the bucket.
- Recommend lifecycle rules if none exist (WAF-COST-009).

### Operation: Put Object (Upload)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Bucket exists | `headBucket` | Bucket found | HALT; create bucket first |
| Object size | Check content length | ≤ 5 TB | HALT; use multipart upload for > 5 GB |

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.PutObjectRequest import PutObjectRequest, PutObjectParameters

params = PutObjectParameters(
    bucketName="{{user.bucket_name}}",
    objectKey="{{user.object_key}}",
    contentLength={{user.content_length}},
    body={{user.body}}
)
req = PutObjectRequest(parameters=params)
resp = client.send(req)
etag = resp.result["objectETag"]
```

#### Post-execution Validation

1. Capture `{{output.object_etag}}` from `$.result.objectETag`.
2. Verify via `headObject`.
3. Report object key and ETag to user.

### Operation: Get Object (Download)

#### Pre-flight

- Verify object exists via `headObject`.

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.GetObjectRequest import GetObjectRequest, GetObjectParameters

params = GetObjectParameters(
    bucketName="{{user.bucket_name}}",
    objectKey="{{user.object_key}}"
)
req = GetObjectRequest(parameters=params)
resp = client.send(req)
# Response contains object data and metadata
```

### Operation: Delete Object

#### Pre-flight (Safety Gate)

- **⚠️ Irreversible** — object will be permanently deleted.
- **MUST** obtain explicit confirmation: `confirm=DELETE`.
- For versioned buckets, verify whether delete marker or permanent delete is intended.

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.DeleteObjectRequest import DeleteObjectRequest, DeleteObjectParameters

# Confirm deletion with user first
params = DeleteObjectParameters(
    bucketName="{{user.bucket_name}}",
    objectKey="{{user.object_key}}"
)
req = DeleteObjectRequest(parameters=params)
resp = client.send(req)
```

#### Post-execution Validation

Verify via `headObject` (expect `NoSuchKey`).

### Operation: Generate Presigned URL

#### Pre-flight (Safety Gate)

- Expiration MUST be 1–86400 seconds (1 second to 24 hours).
- **NEVER** log the full URL in trace output (contains credential signatures).

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.GeneratePresignedUrlRequest import GeneratePresignedUrlRequest, GeneratePresignedUrlParameters

params = GeneratePresignedUrlParameters(
    bucketName="{{user.bucket_name}}",
    objectKey="{{user.object_key}}",
    expirationSeconds={{user.expiration_seconds}}  # 1-86400
)
req = GeneratePresignedUrlRequest(parameters=params)
resp = client.send(req)
presigned_url = resp.result["presignedUrl"]
# Report: "Presigned URL generated for object <key> with <N>s expiry"
# Do NOT log the full URL
```

### Operation: Configure Bucket Versioning

#### Pre-flight (Safety Gate)

- Enabling versioning is **irreversible** — warn user about storage cost increase.
- Once enabled, can only be suspended, not disabled.

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.PutBucketVersioningRequest import PutBucketVersioningRequest, PutBucketVersioningParameters

params = PutBucketVersioningParameters(
    bucketName="{{user.bucket_name}}",
    status="{{user.versioning_status}}"  # "Enabled" or "Suspended"
)
req = PutBucketVersioningRequest(parameters=params)
resp = client.send(req)
```

### Operation: Configure Cross-Region Replication (CRR)

#### Pre-flight Checks

| Check | Method | Expected | On Failure |
|-------|--------|----------|------------|
| Source versioning | `getBucketVersioning` | Enabled | HALT; enable versioning first |
| Destination bucket exists | `headBucket` on dest | Bucket found | HALT; create destination first |
| Destination region | Verify region pair | Different region | HALT; CRR requires cross-region |
| Destination versioning | `getBucketVersioning` on dest | Enabled | HALT; enable versioning on dest |

#### Execution (SDK)

```python
from jdcloud_sdk.services.oss.apis.PutBucketReplicationRequest import PutBucketReplicationRequest, PutBucketReplicationParameters

params = PutBucketReplicationParameters(
    bucketName="{{user.bucket_name}}",
    # replication configuration object
)
req = PutBucketReplicationRequest(parameters=params)
resp = client.send(req)
```

## Quality Gate (GCL)

> This skill participates in the repository-wide **Generator-Critic-Loop**
> (GCL) defined in [`AGENTS.md` §Quality Gate](../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **recommended** (not mandatory) for all operations exposed by this skill.

### Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | Per `AGENTS.md` §8 default for `jdcloud-oss-ops` (recommended) |
| `rubric_version` | `v2` | see [rubric.md](references/rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **true** for `delete-bucket`, `delete-object`, `set-public-acl`, `set-public-read-acl-on-prod` | matches repository safety gate policy |
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
[1] Generator (G)            ──► SDK (sole path; no jdc for OSS)
   │                              generate SDK call (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (recommended for oss-ops)     - SDK method parameter existence
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
> **before** they reach the JD Cloud OSS API. This is a **pre-execution** gate placed between
> G's generation and actual API execution.

**Two-Category Check (for oss-ops):**

| Category | Check | Method |
|---|---|---|
| **SDK Method Parameter Existence** | Verify every parameter exists in SDK method signature | Compare against `references/api-sdk-usage.md` operation tables |
| **JSON Structure Compliance** | For JSON payloads (e.g., lifecycle rules, replication config) | Validate field nesting matches OpenAPI schema |

**Key Parameters to Validate:**

| Operation | Critical Parameters |
|---|---|
| `CreateBucket` | `bucketName`, `regionId` |
| `DeleteBucket` | `bucketName` |
| `PutBucketAcl` | `bucketName`, `bucketAcl` |
| `PutObject` | `bucketName`, `objectKey`, `contentLength`, `body` |
| `DeleteObject` | `bucketName`, `objectKey` |
| `GeneratePresignedUrl` | `bucketName`, `objectKey`, `expirationSeconds` |
| `PutBucketLifecycle` | `bucketName`, `rules` |
| `PutBucketVersioning` | `bucketName`, `status` |

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
# 2. Filter patterns by current skill name (jdcloud-oss-ops)
# 3. Inject top-3 relevant patterns into Generator context as prevention hints

# Example injection:
"Known failure patterns for this skill:
- InvalidBucketName: Bucket names must be 3-63 chars, lowercase, no IP format
- PresignedUrlExpiry: expirationSeconds must be 1-86400 (max 24 hours)
- PublicAclOnProd: public-read-write on prod buckets requires explicit opt-in"
```

### Artifacts

- Rubric (concrete scoring rules): [references/rubric.md](references/rubric.md)
- Prompt templates (G / C / O): [references/prompt-templates.md](references/prompt-templates.md)
- Failure patterns (cross-session memory): `docs/failure-patterns.md` (repository-wide)

### Integration with existing flows

The GCL **wraps** the SDK-only flow defined under `## Execution Flows` above. The Generator (G) IS the existing SDK executor. The Critic (C) is a read-only role with no SDK access. The Orchestrator (O) owns the loop and persists the GCL trace.

### Operation-specific behavior

- **`create-bucket`** — Critic verifies bucket name uniqueness check was performed (Idempotency = 1 required). Missing → Idempotency = 0.
- **`delete-bucket`** — Critic checks trace contains both pre-delete snapshot (`objectCount`) and post-delete 404. Missing either → Correctness = 0.
- **`delete-object`** — For versioned buckets, verify delete marker vs permanent delete intent in trace.
- **`set-bucket-acl` (public-read-write)** — Safety = 0 without explicit opt-in in trace. NEVER on prod → Safety = 0.
- **`set-bucket-acl` (public-read)** — On prod tag, Safety = 0 without warning + opt-in.
- **`generate-presigned-url`** — Expiration > 86400s → Safety = 0. Full URL logged in trace → Safety = 0 (credentials leak).
- **`put-bucket-versioning`** — Enabling versioning is irreversible; warn about storage cost. Missing warning → Spec Compliance = 0.5.

## Prerequisites

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

### Python Runtime (uv)

Both the JD Cloud Python SDK requires a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management:

```bash
# Install uv (system-wide, one-time per machine)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment (idempotent)
uv venv --python 3.10
source .venv/bin/activate

# Install SDK (no jdc for OSS)
uv pip install jdcloud_sdk>=1.6.26

# Verify
python -c "
import jdcloud_sdk
from jdcloud_sdk.services.oss.client.OssClient import OssClient
print(f'SDK Version: {jdcloud_sdk.__version__}')
print('OSS SDK ready')
"
```

### Configure Credentials (Environment Variables)

SDK reads credentials from environment variables:

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> Security: Never commit `.env` files to version control. Never log or print `JDC_SECRET_KEY`. Use `<masked>` for credential status logging.

## Reference Directory

- [Core Concepts](references/core-concepts.md)
- [API & SDK Usage](references/api-sdk-usage.md)
- [CLI Usage](references/cli-usage.md) (documents OSS as SDK-only; no `jdc` support)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration](references/integration.md)
- [Rubric (GCL)](references/rubric.md)
- [Prompt Templates (GCL)](references/prompt-templates.md)

## Operational Best Practices

- **Security:** Use `private` ACL for production buckets. Never use `public-read-write`. Use presigned URLs for temporary access.
- **Cost optimization:** Configure lifecycle policies to transition infrequently accessed data to IA or Archive storage classes.
- **Data protection:** Enable versioning to protect against accidental overwrites and deletions.
- **Disaster recovery:** Configure cross-region replication (CRR) for critical data.
- **Access control:** Use IAM policies for fine-grained access control instead of bucket ACL.
- **Encryption:** Enable server-side encryption (SSE-OSS or SSE-KMS) for sensitive data.
- **Performance:** Use CDN for frequently accessed content; use multipart upload for large objects (>5 GB).
- **Monitoring:** Set up CloudMonitor alarms for 5xx errors, storage limits, and latency thresholds.