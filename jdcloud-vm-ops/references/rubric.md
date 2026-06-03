# VM Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-vm-ops`. This file is the single source of truth
> for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete` / `stop` / `terminate` | 0 / 0.5 / 1 | Verifies resource id, state, region, instance-type match the user request. Read back via `describe-instances` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete` / `stop` / `reboot` of prod) MUST have an explicit user confirmation captured in trace. Payloads MUST include `force=false` unless user opted in. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create` with same `name` must use `client-token`; `delete` / `stop` already idempotent. Score 0 if no idempotency key on a `create` flow. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-instances` snapshot. Score 1 only if all four present. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: correct `instanceTypeFamily` for the region, AZ is a valid code, EIP is in `Available` state before attach. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create-instance` | Correctness, Safety, **Idempotency** | Must use `client-token` |
| `start-instance` | Correctness | Idempotency is N/A (state machine guards it) |
| `stop-instance` | Correctness, **Safety** | Safety = 0 if state was already `stopped` and no confirmation |
| `reboot-instance` | Correctness, **Safety** | Same as stop |
| `delete-instance` | Correctness, Safety, **Traceability** | Must include snapshot of pre-delete state |
| `resize-instance` | Correctness, Safety | Pre-check: must be `stopped` |
| `attach-disk` / `detach-disk` | Correctness, Safety | Hot-detach needs `force=true` and user opt-in |
| `associate-eip` | Correctness, Spec Compliance | EIP must be `Available` |
| cloud assistant `run-command` | Correctness, Safety, Traceability | All output MUST be captured |

## Safety special cases (auto-fail)

- Delete operation on a VM tagged `env=prod` **without** an explicit `confirm=DELETE` in the trace → **Safety = 0 → ABORT**
- Stop / reboot on more than 5 VMs in a single call **without** an explicit batch confirmation → **Safety = 0 → ABORT**
- Any operation targeting an instance id that was not echoed back from a `describe-instances` lookup → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-vm-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-vm-ops` GCL pilot |
