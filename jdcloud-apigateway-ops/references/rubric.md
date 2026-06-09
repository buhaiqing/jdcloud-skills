# API Gateway Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-apigateway-ops`. This file is the single source
> of truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete api group`, `delete api`, `deploy api` to prod | 0 / 0.5 / 1 | Verifies `apiGroupId` / `apiId` / `policyId` / `deploymentId` match request. Describe back and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete api group`, `delete api`, `undeploy api` from prod) MUST have explicit user confirmation. Deploy to prod requires confirmation. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create api group` / `create api` with same name should check for duplicates. Deploy to same stage is idempotent. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full SDK call, args, response excerpt, and final state snapshot. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: auth types valid, backend types valid, stage names supported, service timeout reasonable. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create api group` | Correctness, Safety | Group name must be unique in region |
| `describe api groups` / `describe apis` | Correctness, Traceability | Safety & Idempotency N/A; score 1.0 by default |
| `create api` | Correctness, Safety, Spec Compliance | Backend type must be supported; auth type valid |
| `deploy api` | Correctness, Safety, Spec Compliance | Stage must be valid; prod deploy requires confirm |
| `undeploy api` | Correctness, Safety | Undeploy from prod requires confirmation |
| `create throttling policy` | Correctness, Traceability | Rate limits must be positive integers |
| `bind throttling policy` | Correctness, Spec Compliance | API and stage must exist |
| `delete api` | Correctness, Safety, Traceability | Must not be deployed; cascade from stages |
| `delete api group` | Correctness, Safety, Traceability | **Cascade deletes all APIs**. MUST confirm |

## Safety special cases (auto-fail)

- `delete api group` without explicit confirmation → **Safety = 0 → ABORT**
- `delete api group` on a group tagged `env=prod` without `confirm=PROD` → **Safety = 0 → ABORT**
- `delete api` without explicit user confirmation → **Safety = 0 → ABORT**
- `delete api` on an API deployed to prod without confirm → **Safety = 0 → ABORT**
- `deploy api` to `prod` stage without explicit confirmation → **Safety = 0 → ABORT**
- `undeploy api` from `prod` stage without explicit confirmation → **Safety = 0 → ABORT**
- `create api` with `authType=no_auth` on a group tagged `env=prod` → **Spec Compliance = 0** (warn) |
- `create api` with unsupported backend type → **Spec Compliance = 0** |

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for API Gateway ops (recommended) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-apigateway-ops` GCL rollout (covers api groups, apis, deployments, throttling policies) |
