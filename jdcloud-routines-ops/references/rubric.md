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
| 5 | **Spec Compliance** | ≥ 0.5 | 0 / 0.5 / 1 | jdc-first with SDK fallback is followed per `cli-usage.md`. Python 3.10. No `--no-interactive`. `sys.path` insert matches AGENTS.md convention. **Resource inventory reports must follow `report-format.md` R1-R5 (see §Dimensions Detail below).** |

**Safety = 0 → ABORT immediately**, regardless of total score.

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `expiry_cruise.py` (default) | Correctness, **Safety** | Idempotency required for cron reuse |
| `expiry_cruise.py --customer X` (multi-tenant path) | Correctness, **Safety**, Spec Compliance | Cross-customer raw data MUST NOT leak across reports |
| Planned `billing_cruise.py` | Correctness, Safety, **Traceability** | Billing numbers must be reproducible; include `request_id` if available |
| Planned `inventory_cruise.py` | Correctness, **Traceability** | Snapshot stability matters more than execution safety |

## Dimensions Detail

### Dimension 5: Spec Compliance — Resource Inventory Report Sub-rules

For `inventory_cruise.py` (resource inventory reports) and all `jdcloud-routines-ops` customer-facing reports, the following sub-rules apply under **Spec Compliance**:

| Sub-rule | Weight | Criteria | Scoring |
|---|---|---|---|
| **R1: Dual-identifier (Name + ID)** | 0.30 | All subnets, VPCs, security groups, route tables must display both **Name** and **ID** (format: `Name / id`). Applies to §2 Network Architecture, §3 Business Workload, §5 Billing/Lifecycle, §7 Topology Diagram, §11 Appendix. | Full: All resources compliant. Partial (0.5): ≥80% compliant. Fail (0): <80% compliant or systematic omission. |
| **R2: Actionable list with instance ID** | 0.30 | Renewal/change/deletion lists must contain **specific instance IDs** per row (e.g., `i-9i22fdurlq`, `redis-jq8j5c6slnfd`). No aggregation like "12 VMs" without ID breakdown. Applies to §5.2 Expiry Lists, §8 Risk actionable items, §9 Cross-Skill Action Items. | Full: All actionable items have IDs. Partial (0.5): Some IDs missing but resource names present. Fail (0): Aggregation without IDs. |
| **R3: Attribution responsibility matrix** | 0.20 | Data inconsistency risks (e.g., name/vpc/tag mismatch) must distinguish **"cloud resource state"** vs **"Skill bug"**. `jdcloud-aiops-cruise` is read-only; skill mirrors cloud state without modification. Wording must reflect this. Applies to §4 Security Architecture, §8 Risk List. | Full: Proper attribution. Partial (0.5): Attribution ambiguous. Fail (0): Incorrectly attributes cloud state to skill bug. |
| **R4: Executor perspective** | 0.10 | Each section must answer: **"What will the reader do with this?"** If operating resources, provide directly usable IDs/API parameters. If informing, provide traceable identifiers. Avoid "secondary query" descriptions. Applies to §5 Checklist YAML, §9 Action Items. | Full: Directly executable. Partial (0.5): Needs minor lookup. Fail (0): Requires significant re-query. |
| **R5: Self-checklist signature** | 0.10 | Report must include self-checklist (see `report-format.md` §3) with signatures. | Full: Checklist present and signed. Partial (0.5): Checklist present but incomplete. Fail (0): No checklist. |

**Calculation**: `Spec Compliance = R1×0.30 + R2×0.30 + R3×0.20 + R4×0.10 + R5×0.10`

**Threshold**: ≥ 0.5 to pass. If R1 or R2 is 0, **max Spec Compliance = 0.5** regardless of other scores.

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