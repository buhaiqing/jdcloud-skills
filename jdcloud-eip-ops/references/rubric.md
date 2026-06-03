# EIP Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-eip-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `release EIP`, `dissociate EIP`, `associate EIP` | 0 / 0.5 / 1 | Verifies `allocationId` / `eipId` / `instanceId` / `instanceType` match the user request. Read back via `describe-eip` and compare. For associate: verify `describe-eip` shows the target instance. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`release EIP`, `dissociate EIP` on a production-attached EIP) MUST have explicit user confirmation captured in trace. **Releasing an EIP can break production traffic** if the EIP is in DNS or a load balancer. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `allocate EIP` is naturally idempotent at the API level. `associate EIP` should check current association first. `dissociate EIP` is naturally idempotent (state-machine-guarded). |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-eip` snapshot showing `status` and `instanceType` / `instanceId`. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: bandwidth Mbps within quota, ISP (`bgp` / `single` / `dual`) valid, line type (`standard` / `bgp`) valid, AZ valid. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `allocate EIP` | Correctness, Safety, Spec Compliance | Bandwidth + ISP must be explicit; check quota first |
| `describe EIP` / `list EIPs` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `associate EIP` | Correctness, **Safety**, Spec Compliance | Target instance must be in `running` state (for VM) or `running` (for other instance types). EIP must be in `Available` state (not currently associated). Safety = 0 if EIP is in `InUse` state (already attached) without explicit opt-in |
| `dissociate EIP` | Correctness, **Safety**, Traceability | **Dissociating an EIP breaks production traffic** if the EIP is in DNS or a load balancer. Safety = 0 without `confirm=DISSOCIATE` → ABORT. Always `describe-eip` first to confirm the current binding |
| `release EIP` | Correctness, **Safety**, **Traceability** | **Releasing an EIP is irreversible** (the public IP is returned to the pool, and may be allocated to another tenant). Safety = 0 without `confirm=RELEASE` → ABORT. EIP MUST be in `Available` state (already dissociated) — if `InUse`, refuse and ask the user to dissociate first |

## Safety special cases (auto-fail)

- `release EIP` on an EIP in `InUse` state (still attached) → **Safety = 0
  → ABORT** (must dissociate first)
- `dissociate EIP` / `release EIP` on an EIP tagged `env=prod` without
  `confirm=*_PROD` in trace → **Safety = 0 → ABORT**
- `associate EIP` on an EIP already in `InUse` state without explicit
  opt-in → **Safety = 0 → ABORT** (force-rebind can drop the existing
  association without warning)
- `associate EIP` on a target instance not in `running` state → **Correctness = 0 → ABORT**
- Any operation targeting an `allocationId` that was not echoed back from a
  `describe-eip` lookup → **Correctness = 0 → ABORT**
- Bandwidth > quota for the region/ISP without explicit opt-in → **Spec Compliance = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-eip-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial rubric for `jdcloud-eip-ops` GCL rollout (covers allocate, associate, dissociate, release) |
