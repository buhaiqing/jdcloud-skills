# Audit Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-audit-ops`. This skill is **read-only** —
> it queries the JD Cloud Audit Log API and never mutates it.

## Rubric version

`v2` — see `AGENTS.md` §11.

---

## 1. Core Dimensions (mandatory)

### 1.1 Correctness

**Definition:** The query parameters (time range, region, filters) and returned
events match the user's request.

| Score | Meaning | When to apply |
|:-----:|---------|---------------|
| **1** | Time range, region, and all filters match user request exactly; event count and pagination metadata present; for `describe-event-detail`, the returned event ID matches the requested ID | Default target for all operations |
| **0.5** | Query executed successfully but some filters were inferred rather than explicit (e.g., default time range used without user confirmation); pagination metadata incomplete | Acceptable for exploratory queries |
| **0** | Wrong region, wrong time range, missing required filters, or returned events don't match query criteria | Halt and request retry |

**Special requirement (describe-event-detail):**
Correctness MUST be **1.0** — the returned `eventId` MUST match the requested
`{{user.event_id}}`. A 0.5 here is treated as 0.

### 1.2 Safety

**Definition:** Read-only operation with no side effects; sensitive data properly
masked per Privacy Display Policy.

| Score | Meaning | When to apply |
|:-----:|---------|---------------|
| **1** | Query is read-only (Describe/List/Get); all sensitive fields in `requestParameters` / `responseElements` masked per `references/redaction.md`; no `JDC_SECRET_KEY` or credentials in trace | Default for all audit operations |
| **0** | Any access-key secret, password, plaintext ciphertext, or PII appears verbatim in the response or trace (unmasked); OR query attempts to mutate audit trail configuration | **ABORT — non-negotiable** |

**Per-operation Safety sub-rules for Audit Ops:**

| Operation | Sub-rule (Score 1 requires ALL of the following) |
|---|---|
| `describe-events` | (a) Time range ≤ 90 days (retention limit); (b) No mutation of trail configuration; (c) Sensitive fields in event details masked per redaction.md |
| `describe-event-detail` | (a) Event ID explicitly provided by user; (b) `requestParameters` / `responseElements` fully masked (password, secret, accessKey, privateKey → `***` or SHA-256); (c) Privacy Display Policy applied per mode (masked_default / full_internal / forensic_sealed) |
| `describe-trails` | (a) Read-only query; (b) No trail creation/deletion/modification attempted |

### 1.3 Idempotency

**Definition:** Retrying the same query returns the same data without side effects.

| Score | Meaning | When to apply |
|:-----:|---------|---------------|
| **1** | Query is naturally idempotent (Describe/List/Get); re-running returns same results | Default for all audit operations |
| **0.5** | Query executed but pagination state not captured (e.g., no `pageNumber`/`pageSize` in trace) | Acceptable for single-page results |
| **0** | Query has side effects (should not happen for read-only audit ops) | Reject; this indicates a bug |

**Idempotency notes for Audit Ops:**

- `describe-events` — naturally idempotent; same time range + filters → same results
- `describe-event-detail` — naturally idempotent; same event ID → same detail
- `describe-trails` — naturally idempotent; lists all trails visible to principal

### 1.4 Traceability

**Definition:** Output is auditable. The full command (or REST/SDK call), parameters,
raw response, and any error are captured in `./audit-results/gcl-trace-*.json`.

| Score | Meaning | When to apply |
|:-----:|---------|---------------|
| **1** | Trace contains: full REST/SDK call (with all parameters), exit code, raw JSON response (≤ 2 KB excerpt), pagination metadata (`pageNumber`/`pageSize`/`totalCount`), region, time range, and sanitized request | Required for all operations |
| **0.5** | Command + exit code present, but raw response truncated or pagination metadata missing | Acceptable for single-page results |
| **0** | Trace only contains a one-line summary with no command or response | Reject |

**Mandatory trace fields for Audit Ops:**

| Field | Required for | Notes |
|---|---|---|
| `iterations[].generator.command` | ALL | Full REST endpoint or SDK call |
| `iterations[].generator.args` | ALL | Map of parameter → value (sanitized) |
| `iterations[].generator.exit_code` | ALL | HTTP status code or SDK exit code |
| `iterations[].generator.result_excerpt` | ALL | First ≤ 2KB of raw JSON (sensitive fields masked) |
| `iterations[].generator.post_state` | ALL | `event_count`, `page_number`, `page_size`, `total_count`, `time_range`, `region` |
| `iterations[].critic.scores` | ALL | The 5+3 dimension map below |
| `iterations[].critic.suggestions` | ALL retries | ≤ 3 actionable items |
| `iterations[].decision` | ALL | `RETRY` / `PASS` / `ABORT_SAFETY` / `MAX_ITER` |

### 1.5 Spec Compliance

**Definition:** Conforms to `references/core-concepts.md` constraints (retention limits,
region validity, event name validity).

| Score | Meaning | When to apply |
|:-----:|---------|---------------|
| **1** | Time range within 90-day retention; region is valid JD Cloud region; event name (if provided) is a valid JD Cloud API operation; pagination parameters within limits (`pageSize` ≤ 100) | Default target |
| **0.5** | Time range or region OK, but some parameters were inferred without verification (e.g., assumed event name without checking API docs) | Reject for production; acceptable for dev |
| **0** | Time range > 90 days (retention violation), invalid region, or invalid event name | Halt and request retry |

---

## 2. Aliyun-Specific Extensions (per `AGENTS.md` §12.3)

### 2.1 Region Compliance

**Definition:** The query targets the region the user declared.

| Score | Meaning |
|:-----:|---------|
| **1** | `--region-id` or REST endpoint region matches `{{user.region}}` exactly |
| **0.5** | Region omitted but operation is region-agnostic (e.g., `describe-trails` for global trails) |
| **0** | Region differs from `{{user.region}}` (cross-region query without user consent) |

### 2.2 Credential Hygiene

**Definition:** `JDC_SECRET_KEY` (and any other secret) never appears in any log line,
command argument, or persisted trace.

| Score | Meaning |
|:-----:|---------|
| **1** | Trace was scanned; no `JDC_SECRET_KEY`, `JDC_ACCESS_KEY` (in plaintext), `BEGIN.*PRIVATE KEY`, or passwords present |
| **0** | Any of the above appears in the trace or stdout |

**Sanitization helper** (suggested, not mandatory):

```bash
# Before writing trace to disk
sed -E 's/(JDC_SECRET_KEY=)[^ ]+/\1<masked>/g' \
    -E 's/(JDC_ACCESS_KEY=)[^ ]+/\1<masked>/g' \
    -E 's/(Password=)"[^"]+"/\1<masked>/g'
```

### 2.3 Well-Architected (per `references/core-concepts.md`)

**Definition:** The operation does not violate a relevant Well-Architected pillar.
Apply only when the operation is WA-sensitive (security, compliance, or cost).

| Pillar | What to check | Score 1 requires |
|---|---|---|
| **安全 Security** | Sensitive data in `requestParameters` / `responseElements` properly masked; no credential leakage | See §1.2 Safety sub-rule; Privacy Display Policy applied |
| **稳定 Stability** | Query does not attempt to modify trail configuration (read-only) | No mutation operations attempted |
| **成本 Cost** | Query does not exceed retention limits (90 days); pagination used for large result sets to avoid timeout | Time range ≤ 90d; `pageSize` ≤ 100 |
| **效率 Efficiency** | Filters (`eventName`, `resourceType`, `username`) used to reduce query scope when result set is large | Filters applied when `totalCount` > 1000 |
| **性能 Performance** | Pagination used for large result sets; time range scoped to minimum necessary | `pageNumber`/`pageSize` in trace for paginated results |

---

## 2.4 Hallucination Detection (H Layer) — Optional for audit-ops

**Definition:** Pre-execution structural validity check catches LLM-generated REST/SDK calls with invalid parameters, wrong JSON structure, or time range violations **before** they reach the API.

| Score | Meaning | When to apply |
|:-----:|---------|---------------|
| **1** | All API parameters exist in spec; JSON structure matches OpenAPI schema; time range ≤ 90 days | Default target when H layer is enabled |
| **0.5** | Minor parameter naming issues (e.g., `startTime` vs `start_time`) that API tolerates; or time range slightly exceeds 90 days but API accepts | Acceptable for exploratory queries |
| **0** | Non-existent API parameters; malformed JSON payload; time range > 90 days causing API rejection | **HALLUCINATION_ABORT** after regeneration fails |

**Per-Check Scoring:**

| Check | Score 1 requires | Score 0 triggers |
|---|---|---|
| **API Parameter Existence** | All query parameters (`startTime`, `endTime`, `eventName`, `resourceType`, `username`, `pageNumber`, `pageSize`) exist in `references/api-sdk-usage.md` | Unrecognized parameter like `eventFilter` or `timeRange` |
| **JSON Structure Compliance** | `requestParameters` / `responseElements` field nesting matches OpenAPI schema (no flattening) | Flattened nested objects or wrong field types |
| **Time Range Validity** | `endTime - startTime ≤ 90 days` (retention limit) | Time range > 90 days causing `InvalidTimeRange` error |

**H Layer Termination:**

| Condition | Action |
|---|---|
| **H_PASS** (all checks score 1) | Continue to [1a] Execute |
| **H_FAIL → Regenerate** (any check < 1) | Inject hallucination report into G; max 1 regeneration attempt |
| **HALLUCINATION_ABORT** (regeneration still fails) | HALT — return unresolved hallucination report |

**Trace Integration:**

H result is embedded in GCL trace under `iterations[].hallucination_detector`:

```json
{
  "hallucination_detector": {
    "status": "PASS|FAIL",
    "checks": {
      "api_parameters": {
        "status": "PASS|FAIL",
        "total": 5,
        "recognized": 5,
        "unrecognized": []
      },
      "json_structure": {
        "status": "PASS|FAIL",
        "note": "no JSON payload in query"
      },
      "time_range": {
        "status": "PASS|FAIL",
        "delta_days": 30,
        "within_retention": true
      }
    },
    "report": "All checks passed"
  },
  "regenerated": false
}
```

**Anti-Patterns (H-specific):**

- ❌ H executes cloud API calls — H is an offline structural check; calling `jdc` or REST API from H risks side-effects
- ❌ H rewrites G's command — H must flag hallucinations, not mutate the command. Fixes come from G (re-generation)
- ❌ H checks skipped for time range validation — time range ≤ 90 days is MANDATORY for all audit queries

---

## 3. Termination Thresholds (inherited from `AGENTS.md` §12.5)

| Condition | Behavior |
|---|---|
| All scores ≥ threshold | **PASS** — return Generator's result |
| Safety = 0 | **ABORT** — never return partial output |
| Other dimension < threshold AND iter < `max_iter=5` | **RETRY** — inject Critic suggestions into Generator |
| Other dimension < threshold AND iter = `max_iter` | **MAX_ITER** — return best-so-far + unresolved rubric items |

Per-dimension thresholds (default, overridable per skill):

| Dimension | Threshold |
|---|---|
| Correctness | ≥ 0.5 (1.0 for `describe-event-detail`) |
| Safety | = 1 (absolute) |
| Idempotency | ≥ 0.5 |
| Traceability | ≥ 0.5 |
| Spec Compliance | ≥ 0.5 |
| Region Compliance | ≥ 0.5 |
| Credential Hygiene | = 1 (absolute) |
| Well-Architected | ≥ 0.5 (or N/A if op is not WA-sensitive) |

---

## 4. Worked Examples

### Example 1: `describe-events` PASS

Trace (abbreviated):

```json
{
  "iter": 1,
  "generator": {
    "command": "GET https://audit.jdcloud-api.com/v1/regions/cn-north-1/events?startTime=2026-06-17T00:00:00Z&endTime=2026-06-18T00:00:00Z&pageNumber=1&pageSize=50",
    "args": {"region": "cn-north-1", "startTime": "2026-06-17T00:00:00Z", "endTime": "2026-06-18T00:00:00Z", "pageNumber": 1, "pageSize": 50},
    "exit_code": 200,
    "result_excerpt": "{\"result\":{\"events\":[{\"eventId\":\"e-abc123\",\"eventTime\":\"2026-06-17T10:30:00Z\",\"eventName\":\"CreateInstance\",\"username\":\"admin\",\"resourceType\":\"vm\",\"resourceId\":\"i-xyz789\"}],\"totalCount\":1}}",
    "post_state": {"event_count": 1, "page_number": 1, "page_size": 50, "total_count": 1, "time_range": "2026-06-17T00:00:00Z/2026-06-18T00:00:00Z", "region": "cn-north-1"}
  },
  "critic": {
    "scores": {
      "correctness": 1, "safety": 1, "idempotency": 1,
      "traceability": 1, "spec_compliance": 1,
      "region_compliance": 1, "credential_hygiene": 1,
      "well_architected": 1
    },
    "suggestions": [],
    "blocking": false
  },
  "decision": "PASS"
}
```

### Example 2: `describe-event-detail` SAFETY_FAIL → ABORT

Trace (abbreviated):

```json
{
  "iter": 1,
  "generator": {
    "command": "GET https://audit.jdcloud-api.com/v1/regions/cn-north-1/events/e-abc123",
    "args": {"region": "cn-north-1", "eventId": "e-abc123"},
    "exit_code": 200,
    "result_excerpt": "{\"result\":{\"eventDetail\":{\"eventId\":\"e-abc123\",\"eventName\":\"CreateInstance\",\"username\":\"admin\",\"requestParameters\":{\"password\":\"MySecretPass123\",\"instanceType\":\"g.1xlarge\"}}}}",
    "post_state": {"event_count": 1, "region": "cn-north-1"}
  },
  "critic": {
    "scores": {
      "correctness": 1, "safety": 0, "idempotency": 1,
      "traceability": 1, "spec_compliance": 1,
      "region_compliance": 1, "credential_hygiene": 1,
      "well_architected": 0
    },
    "suggestions": ["BLOCKED: `requestParameters.password` contains plaintext secret. MUST mask to `***` per redaction.md before output."],
    "blocking": true
  },
  "decision": "ABORT_SAFETY"
}
```

### Example 3: `describe-events` retry for missing pagination metadata

Trace (abbreviated):

```json
{
  "iter": 1,
  "generator": {
    "command": "GET https://audit.jdcloud-api.com/v1/regions/cn-north-1/events?startTime=2026-06-17T00:00:00Z&endTime=2026-06-18T00:00:00Z",
    "exit_code": 200,
    "result_excerpt": "{\"result\":{\"events\":[...]}}"
  },
  "critic": {
    "scores": {
      "correctness": 0.5, "safety": 1, "idempotency": 0.5,
      "traceability": 0.5, "spec_compliance": 1
    },
    "suggestions": [
      "No `pageNumber`/`pageSize` parameters in query — pagination metadata missing",
      "Trace does not include `post_state.total_count` — cannot verify completeness"
    ],
    "blocking": true
  },
  "decision": "RETRY"
}
```

---

## 5. Anti-Patterns (banned — inherited from `AGENTS.md` §12.9)

- ❌ Critic scoring on vibes instead of this rubric → reject trace
- ❌ Critic seeing the original user request → reject trace
- ❌ Trace persisting `JDC_SECRET_KEY` unredacted → reject + sanitize
- ❌ Safety=0 returning best-effort output → ABORT, not a retry
- ❌ Loop running > `max_iter=5` → bug, not a feature
- ❌ Critic mutating cloud resources → banned; Critic is read-only
- ❌ Unmasked sensitive data in `requestParameters` / `responseElements` → Safety=0

---

## 6. Changelog

| Version | Date | Change |
|---|---|---|
| 2.0.0 | 2026-06-18 | **Complete GCL rollout**: Enhanced with 8 dimensions (5 core + 3 Aliyun-specific extensions); added per-operation Safety sub-rules; added worked examples; aligned with aliyun-skills GCL v1.9.0 pattern. |
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-audit-ops` GCL rollout (read-only audit log query; PII masking guard) |
