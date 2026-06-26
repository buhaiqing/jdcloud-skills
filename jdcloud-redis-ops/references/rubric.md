# Redis Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-redis-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v2` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete` / `restore` / `flushall` | 0 / 0.5 / 1 | Verifies `cacheInstanceId`, region, spec (memory MB / version), and vpc/subnet match the user request. Read back via `describe-cache-instance` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete-instance`, `restore-instance`, `modify-spec` with shrink, `flushdb`) MUST have explicit user confirmation captured in trace. Payloads MUST NOT include `force=true` without opt-in. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create-cache-instance` must use a stable `client-token`; `delete` and `restore` are already state-machine-guarded. Score 0 if no idempotency key on a `create` flow. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-cache-instance` snapshot. Score 1 only if all four present. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: cache version supported in the target region, memory MB matches a valid SKU, port 6379 (or user-specified), AZ valid. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create-cache-instance` | Correctness, Safety, **Idempotency** | Must set `client-token` (UUID v4 if user did not supply one) |
| `describe-cache-instance` / `list` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `modify-cache-instance` (config only) | Correctness, Safety | Hot-apply may cause brief reconnect — flag in trace |
| `modify-cache-instance` (spec upgrade) | Correctness, Safety, **Spec Compliance** | Downgrade is **forbidden** — Safety = 0 if shrinking without explicit opt-in |
| `delete-cache-instance` | Correctness, Safety, **Traceability** | Must include snapshot of pre-delete state (instance id + status) |
| `backup-cache-instance` | Correctness, Traceability | Backup id must be echoed back in trace |
| `restore-cache-instance` | Correctness, **Safety**, Spec Compliance | `baseId` (backup id) must be a real, recent backup owned by the same instance; Safety = 0 if restoring across instances without explicit confirm |
| `flushall` (via SDK low-level) | Correctness, Safety | Always Safety = 0 without `confirm=FLUSHALL` in trace → ABORT |

## Safety special cases (auto-fail)

- Delete / restore on an instance tagged `env=prod` **without** an explicit
  `confirm=DELETE` or `confirm=RESTORE` in the trace → **Safety = 0 → ABORT**
- Restore from a backup that belongs to a **different** instance without
  explicit cross-instance confirmation → **Safety = 0 → ABORT**
- Spec shrink (memory MB decreased) without explicit user opt-in → **Safety = 0 → ABORT**
- Any operation targeting a `cacheInstanceId` that was not echoed back from a
  `describe-cache-instance` lookup → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-redis-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v2` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-redis-ops` GCL rollout |
| 2.0.0 | 2026-06-27 | Bump to v2: align with SKILL.md rubric_version reference; add cross-skill delegation for cert-ops, dns-ops; fix --output json placement in monitoring.md and troubleshooting.md; fix CLI subcommand names in failure-patterns.md |
