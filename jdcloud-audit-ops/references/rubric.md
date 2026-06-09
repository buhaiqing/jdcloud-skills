# Audit Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-audit-ops`. This skill is **read-only** —
> it queries the JD Cloud Audit Log API and never mutates it.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for event detail, time-range filter, principal filter | 0 / 0.5 / 1 | Verifies the time range, region, resource id, and event name filters match the user request. Read back via `describe-events` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | **Read-only by definition**. Safety = 0 if the response includes PII (access-key secret, password, plaintext) verbatim. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `describe-events` / `describe-event-detail` / `describe-trails` are naturally idempotent. Re-running the same query returns the same data. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full command (or REST/SDK call), args, exit code, raw response excerpt (≤ 2 KB), and `pageNumber`/`pageSize`/`totalCount` if paginated. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: time range within retention (90 days for trail; event detail per request), region valid, event name valid. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `describe-events` (list operation events) | Correctness, Traceability, Spec Compliance | Time range + region + filter MUST be explicit. Default time range = last 24h. Trace MUST include `pageNumber`/`pageSize`/`totalCount` |
| `describe-event-detail` (get single event details) | Correctness, Safety, Traceability | Event id MUST be explicit. Response MAY contain sensitive request parameters — **MUST mask** `requestParameters`/`responseElements` per Safety rule; unmasked sensitive data → Safety = 0 → ABORT |
| `describe-trails` (list audit trails) | Correctness, Traceability | All trails visible to the principal |

## Safety special cases (auto-fail)

- Any access-key secret, password, plaintext ciphertext, or PII appears
  verbatim in the response (or in the GCL trace) → **Safety = 0 → ABORT**
  (mask the field with `***` or SHA-256 prefix)
- Time range > 90 days → **Spec Compliance = 0 → ABORT** (retention limit)
- Event id referenced but not echoed back from `describe-events`
  → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for `jdcloud-audit-ops` (optional, read-only) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-audit-ops` GCL rollout (read-only audit log query; PII masking guard) |
