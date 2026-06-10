# Rubric — `jdcloud-routines-ops`

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-routines-ops`. This skill is **optional GCL**
> (read-only by construction), so the rubric is lighter than for destructive
> ops skills.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Scope: optional GCL

This skill is invoked from cron / weekly / monthly schedules. The output is a
JSON report + console summary. There are **no destructive operations**.

Therefore the GCL loop is **optional** and the threshold for mandatory
Critic invocation is:

- **Routine cron run** (no user watching): GCL skipped, output goes straight to
  the report directory.
- **On-demand operator run** (user invoked from chat / ticket): GCL recommended.
- **Pre-renewal decision run** (will feed a renewal ticket): GCL **required**.

`max_iterations = 3` (per AGENTS.md §8 default for `jdcloud-routines-ops`).

## Dimensions

| # | Dimension | Threshold | Scale | Notes |
|---|---|---|---|---|
| 1 | **Correctness** | ≥ 0.5 | 0 / 0.5 / 1 | Cruise output matches a manual `describe-*` spot check on ≥ 80% of resources. `days_left` math is correct (sampled against a known-future date). |
| 2 | **Safety** | = 1 | 0 / 1 | Read-only — no mutation calls. No secret leakage. Customer tag used as filter, not as a permission bypass. |
| 3 | **Idempotency** | ≥ 0.5 | 0 / 0.5 / 1 | Re-running the same command yields the same JSON shape, the same exit code (modulo timestamp / `days_left`), and the same `summary` after bucketing. |
| 4 | **Traceability** | ≥ 0.5 | 0 / 0.5 / 1 | Output report contains: `report_time`, `warning_days`, `regions_checked`, `types_checked`, `customer_filter`, `summary`, `details[]`. Exit code matches the convention in `core-concepts.md` §6. |
| 5 | **Spec Compliance** | ≥ 0.5 | 0 / 0.5 / 1 | jdc-first with SDK fallback is followed per `cli-usage.md`. Python 3.10. No `--no-interactive`. `sys.path` insert matches AGENTS.md convention. |

**Safety = 0 → ABORT immediately**, regardless of total score.

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `expiry_cruise.py` (default) | Correctness, **Safety** | Idempotency required for cron reuse |
| `expiry_cruise.py --customer X` (multi-tenant path) | Correctness, **Safety**, Spec Compliance | Cross-customer raw data MUST NOT leak across reports |
| Planned `billing_cruise.py` | Correctness, Safety, **Traceability** | Billing numbers must be reproducible; include `request_id` if available |
| Planned `inventory_cruise.py` | Correctness, **Traceability** | Snapshot stability matters more than execution safety |

## Safety special cases (auto-fail)

- Any `subprocess` invocation with `secret_key` in the env list → **Safety = 0 → ABORT**
- Any console output containing `JDC_SECRET_KEY` value → **Safety = 0 → ABORT**
- Report file written outside `~/.jdcloud-routines-ops/outputs/` or the
  `--output-dir` target → **Safety = 0 → ABORT**
- Report containing resources from a different `客户` than the `--customer`
  filter (i.e. filter did not apply) → **Safety = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-routines-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial rubric for `jdcloud-routines-ops` GCL rollout (1.1.0 batch) |