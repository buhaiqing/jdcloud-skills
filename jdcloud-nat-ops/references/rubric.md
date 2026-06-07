# NAT Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-nat-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete nat gateway`, `delete snat rule`, `delete dnat rule` | 0 / 0.5 / 1 | Verifies `natGatewayId` / `snatRuleId` / `dnatRuleId` / `vpcId` / `subnetId` match the user request. Read back via `describe-nat-gateway` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete nat gateway`, `delete snat rule`, `delete dnat rule`, `disassociate eip` last-EIP) MUST have explicit user confirmation. NAT deletion breaks ALL VPC internet connectivity. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create nat gateway` with the same name in same VPC should check for duplicates. `associate eip` is naturally idempotent. `delete` is state-machine-guarded. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-*` snapshot showing `state`, `elasticIpAddresses`, `snatRuleCount`, `dnatRuleCount`. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: VPC exists, EIPs exist in the same region, subnet belongs to the VPC, DNAT protocol is TCP/UDP, ports are 1-65535, SNAT subnet unique. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create nat gateway` | Correctness, Safety, Spec Compliance | VPC + EIP must be verified first; WAF-REL-010: warn if <2 EIPs |
| `describe nat gateway` / `list` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `create snat rule` | Correctness, Safety, Spec Compliance | Subnet must belong to the same VPC as NAT |
| `create dnat rule` | Correctness, Safety, Spec Compliance | Protocol must be TCP or UDP; private IP must be in VPC CIDR; port conflict check |
| `delete snat rule` | Correctness, **Safety**, Traceability | Breaks subnet internet access; Safety = 0 without explicit confirm |
| `delete dnat rule` | Correctness, **Safety**, Traceability | Breaks port forwarding; Safety = 0 without explicit confirm |
| `associate eip` | Correctness, Safety | WAF-REL-010: recommend ≥2 EIPs for production |
| `disassociate eip` | Correctness, **Safety**, Traceability | If disassociating last EIP, SNAT/DNAT fails; require `confirm=EIP_LAST` |
| `modify nat gateway` (name, desc) | Correctness, Safety | Non-destructive; standard checks |
| `delete nat gateway` | Correctness, **Safety**, **Traceability** | **Breaks ALL VPC internet connectivity**. MUST have `confirm=DELETE` in trace. Must include pre-delete snapshot of SNAT/DNAT rules + EIPs |

## Safety special cases (auto-fail)

- `delete nat gateway` without `confirm=DELETE` in trace → **Safety = 0 → ABORT**
- `delete nat gateway` on a NAT tagged `env=prod` without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `delete nat gateway` without pre-delete snapshot of SNAT rules + DNAT rules + EIPs → **Traceability = 0 → ABORT**
- `disassociate eip` removing the LAST EIP without `confirm=EIP_LAST` → **Safety = 0 → ABORT**
- `delete snat rule` without explicit user confirmation → **Safety = 0 → ABORT**
- `delete dnat rule` without explicit user confirmation → **Safety = 0 → ABORT**
- `create snat rule` using a subnet that already has a SNAT rule → **Spec Compliance = 0**
- `create dnat rule` with port conflict on the same EIP → **Spec Compliance = 0**
- Any operation targeting a `natGatewayId` that was not echoed back from a `describe-*` lookup → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **2** | `AGENTS.md` §8 default for `jdcloud-nat-ops` (required) |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-nat-ops` GCL rollout (covers NAT GW, SNAT rules, DNAT rules, EIP association) |