# Tag Audit Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-tag-audit-ops`. This skill is **read-only for
> auditing**, but has a single mutating operation: **create DOPS ticket**
> for non-compliant resources.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for "non-compliant" classification, DOPS ticket payload | 0 / 0.5 / 1 | Verifies the tag-compliance rule (`{product, region, required_tag, required_value}`) matches the user request. Read back via `describe-instances` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Audit step is read-only. **DOPS ticket creation** is the only mutating op and requires explicit user confirmation. Safety = 0 if a DOPS ticket is created without `confirm=CREATE_DOPS_TICKET` in trace. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Re-running tag audit on the same `(product, region)` returns the same result. DOPS ticket creation MUST check for duplicate open tickets on the same resource first. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), the compliance rule applied, and the per-resource pass/fail decision. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: supported product list, supported region list, tag naming convention, value pattern. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `audit tag compliance` | Correctness, Traceability, Spec Compliance | Product + region + required tag + required value MUST be explicit. For each resource, classify pass/fail deterministically |
| `generate audit report` | Correctness, Traceability | Output: pass count, fail count, fail list with resource id + missing tag + actual value |
| `create DOPS ticket for non-compliant resources` | Correctness, **Safety**, Idempotency, Traceability | MUST check for duplicate open tickets on the same resource first. Safety = 0 without `confirm=CREATE_DOPS_TICKET` in trace. Each ticket MUST include: resource id, missing tag, actual value, suggested remediation, urgency level |

## Safety special cases (auto-fail)

- DOPS ticket created without `confirm=CREATE_DOPS_TICKET` in trace
  → **Safety = 0 → ABORT**
- DOPS ticket created for a resource that already has an open non-compliant
  ticket → **Idempotency = 0 → ABORT** (avoid duplicate tickets)
- Tag audit result missing the compliance rule applied → **Traceability = 0
  → ABORT**
- DOPS ticket payload missing resource id, missing tag, or urgency level
  → **Correctness = 0 → ABORT**
- Compliance rule references a product/region NOT in the
  `Supported Products` / `Supported Regions` list → **Spec Compliance = 0
  → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for `jdcloud-tag-audit-ops` (optional) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-tag-audit-ops` GCL rollout (read-only audit + DOPS ticket creation with idempotency check) |
