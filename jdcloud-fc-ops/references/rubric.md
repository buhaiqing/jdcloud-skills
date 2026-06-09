# FC Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-fc-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete service`, `delete function`, `delete trigger` | 0 / 0.5 / 1 | Verifies `serviceName` / `functionArn` / `versionId` / `aliasName` match request. Describe back and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete service`, `delete function`, `delete alias`, `delete trigger`) MUST have explicit user confirmation. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create service` / `create function` with same name should check for duplicates. `invoke` is naturally idempotent. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full SDK call (or jdc), args, response excerpt, and final state snapshot. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: service name format, runtime support, trigger type constraints, version immutability. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create service` | Correctness, Safety | Service name must be unique in region |
| `describe service` / `list services` | Correctness, Traceability | Safety & Idempotency N/A; score 1.0 by default |
| `create function` | Correctness, Safety, Spec Compliance | Runtime must be in supported list; handler format valid |
| `invoke function` | Correctness, Spec Compliance | Sync invoke must capture payload; async returns request ID |
| `publish version` | Correctness, Traceability | Version is immutable after creation |
| `create alias` | Correctness, Safety, Spec Compliance | Alias must point to an existing version |
| `create trigger` | Correctness, Safety, Spec Compliance | Trigger type supported (HTTP, Timer, OSS, Log) |
| `delete trigger` | Correctness, Safety, Traceability | Removes only trigger; function preserved |
| `delete function` | Correctness, Safety, Traceability | Cascade deletes all versions + triggers |
| `delete service` | Correctness, Safety, Traceability | **Cascade deletes all functions + triggers**. MUST confirm |

## Safety special cases (auto-fail)

- `delete service` without explicit confirmation → **Safety = 0 → ABORT**
- `delete service` on a service tagged `env=prod` without `confirm=PROD` → **Safety = 0 → ABORT**
- `delete function` without explicit user confirmation → **Safety = 0 → ABORT**
- `delete trigger` on the only trigger of a production function without confirm → **Safety = 0 → ABORT**
- `invoke function` with hardcoded secrets in payload → **Safety = 0 → ABORT**
- `create function` with runtime not in supported list → **Spec Compliance = 0**
- `update alias` with a non-existent version → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default; overridden from optional to required for destructive FC ops |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-fc-ops` GCL rollout (covers services, functions, versions, aliases, triggers) |