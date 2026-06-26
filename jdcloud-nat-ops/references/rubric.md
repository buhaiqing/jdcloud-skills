# NAT Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-nat-ops`. This file is the single source of
> truth for what the Critic scores against.

## Rubric version

`v2` — see `AGENTS.md` §11.

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
| Rubric version | `v2` | this file |

## §2.1 Critic Test & Regression Assessment

Per `AGENTS.md` §2.1, the Critic MUST evaluate two acceptance dimensions on every critique iteration:

| Assessment | What to check | On failure |
|---|---|---|
| **Test accuracy** | Does existing tests correctly exercise and assert behaviors touched by this change? Would these tests fail if this change introduced a bug? | `blocking=true`; concrete test fixes/additions in `suggestions`; RETRY |
| **Regression gate** | Is targeted regression required? Pick the **smallest accurate suite** for the change and adjacent risk — not blanket coverage | If required: name suite(s) and rationale; require green runs in trace/summary. If waived: document zero-behavioral-delta rationale |

**Banned**: padding test count, chasing coverage %, PASSing on green suites that do not assert the changed behavior.

### Per-operation regression guidance

| Operation | Test accuracy check | Regression gate default |
|---|---|---|
| `delete-nat` | Must have `pre_delete_snapshot` in post_state; describe-NAT call must precede delete | **Required**: `describe-nat-gateway` must appear in trace before delete |
| `delete-snat` / `delete-dnat` | Safety confirm echoed in trace; SNAT/DNAT count decrements after delete | **Required**: describe-NAT showing count change |
| `disassociate-eip` (last) | `confirm=EIP_LAST` present in trace; EIP removed from post_state | **Required**: describe-NAT showing EIP removed |
| `create-nat` / `create-snat` / `create-dnat` | NAT ID / rule ID present in post_state; state == `available` | **Required**: describe-NAT after create |
| `describe-nat` / `list-nats` | Read-only: no mutation, no side-effects | **Waived**: zero-behavioral-delta |
| `modify-nat` | Name/description reflected in post_state | **Required**: describe-NAT after modify |

## Changelog

| Version | Date | Change |
|---|---|---|
| 2.0.0 | 2026-06-27 | Aligned with prompt-templates.md v2.0.0: added §2.1 test_assessment dimensions, updated rubric version to v2 |
| 1.0.0 | 2026-06-08 | Initial rubric for `jdcloud-nat-ops` GCL rollout (covers NAT GW, SNAT rules, DNAT rules, EIP association) |