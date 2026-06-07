# OSS Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-oss-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` -- see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | >= 0.5; **= 1.0 required** for `delete bucket`, `delete object`, `set public ACL` | 0 / 0.5 / 1 | Verifies `bucketName` / `objectKey` / `acl` match the user request. Read back via `headBucket` / `headObject` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete bucket`, `delete object`) MUST have explicit user confirmation. `public-read-write` ACL MUST be flagged and confirmed. |
| 3 | **Idempotency** | soft | >= 0.5 | 0 / 0.5 / 1 | `create bucket` with same name MUST return `BucketAlreadyExists`, not create duplicates. `putObject` overwrites same key. |
| 4 | **Traceability** | soft | >= 0.5 | 0 / 0.5 / 1 | Trace MUST contain: SDK call (method + params), exit code, raw response excerpt (<= 2 KB), and post-state snapshot. |
| 5 | **Spec Compliance** | soft | >= 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: bucket name rules, valid ACL values, lifecycle transition days and storage classes, versioning states. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create bucket` | Correctness, Safety, Spec Compliance | Bucket name must be globally unique; check name rules first |
| `list buckets` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `head bucket` / `describe bucket` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `delete bucket` | Correctness, **Safety**, **Traceability** | **Irreversible** -- ALL objects lost. Must have `confirm=DELETE_BUCKET`. Must include pre-delete snapshot of `objectCount`. |
| `set bucket ACL` | Correctness, Safety, Spec Compliance | `public-read-write` prohibited without explicit confirm. `public-read` requires warning. |
| `configure lifecycle` | Correctness, Safety, Spec Compliance | Rule ID unique; status Enabled/Disabled; transition days ascending; storage class valid |
| `put object` | Correctness, Traceability | Must verify target bucket exists; object ETag captured |
| `get object` | Correctness, Traceability | Must verify object exists first; output file path reported |
| `delete object` | Correctness, **Safety**, Traceability | `confirm=DELETE` required. For versioned buckets, verify delete marker vs permanent delete. |
| `generate presigned URL` | Correctness, Safety, Spec Compliance | Expiration 1-86400 seconds. URL MUST NOT be logged fully in trace. |
| `put bucket versioning` | Correctness, Safety | Enabling versioning is irreversible -- warn about storage cost increase |
| `put bucket replication` | Correctness, Safety, Spec Compliance | Source must have versioning enabled; destination must exist in different region |

## Safety special cases (auto-fail)

- `delete bucket` without `confirm=DELETE_BUCKET` in trace -> **Safety = 0 -> ABORT**
- `delete bucket` on bucket tagged `env=prod` without `confirm=DELETE_BUCKET_PROD` -> **Safety = 0 -> ABORT**
- `delete bucket` on non-empty bucket without warning -> **Safety = 0 -> ABORT**
- `delete object` without `confirm=DELETE` in trace -> **Safety = 0 -> ABORT**
- `set bucket ACL` to `public-read-write` without explicit opt-in -> **Safety = 0 -> ABORT**
- `set bucket ACL` to `public-read-write` on `env=prod` bucket -> **Safety = 0 -> ABORT**
- `set bucket ACL` to `public-read` on prod bucket without warning + opt-in -> **Safety = 0 -> ABORT**
- Any operation on `bucketName` not echoed from `listBuckets` / `headBucket` -> **Correctness = 0 -> ABORT**
- Presigned URL with expiration > 86400 seconds -> **Safety = 0 -> ABORT**
- Full presigned URL logged in trace -> **Safety = 0 -> ABORT** (credentials leak)

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-oss-ops` (recommended) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## WAF Rule Alignment

| WAF Rule | Rubric Dimension | Enforcement |
|----------|-----------------|-------------|
| WAF-SEC-010 (Bucket ACL) | Safety, Spec Compliance | `public-read-write` -> Safety = 0 without confirm; `public-read` on prod -> Safety = 0 without warning + confirm |
| WAF-COST-009 (Lifecycle) | Spec Compliance | Missing lifecycle policy is Spec Compliance = 0.5 (warning) |
| WAF-REL-009 (CRR) | Spec Compliance | Missing CRR on critical data is Spec Compliance = 0.5 (warning) |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-oss-ops` GCL rollout (covers bucket CRUD, object CRUD, ACL, lifecycle, versioning, CRR, presigned URL) |