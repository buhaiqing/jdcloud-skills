# GCL Rubric — jdcloud-vpn-ops

> This rubric instance applies to the Generator-Critic-Loop (GCL) for
> `jdcloud-vpn-ops`. See [`AGENTS.md` §Quality Gate](../../AGENTS.md)
> for the global GCL specification.

## Dimensions

| Dimension | Meaning | Scale | Threshold |
|-----------|---------|-------|-----------|
| **Correctness** | Resource id / state / config actually matches the request | 0 / 0.5 / 1 | ≥ 0.5 |
| **Safety** | Destructive op (`delete`) was confirmed or guarded | 0 / 1 | = 1 |
| **Idempotency** | Retrying the same call will not cause duplicate side-effects | 0 / 0.5 / 1 | ≥ 0.5 |
| **Traceability** | Output is auditable: command, params, raw response, errors all captured | 0 / 0.5 / 1 | ≥ 0.5 |
| **Spec Compliance** | Conforms to the skill's `core-concepts.md` constraints | 0 / 0.5 / 1 | ≥ 0.5 |

## Scoring Rules

### Correctness

- **1.0**: Resource ID exists, state matches expected transition, all parameters persisted correctly.
- **0.5**: Resource created but minor config drift (e.g., description mismatch, optional field not set).
- **0.0**: Wrong resource type, wrong region, creation failed silently, or state never reached target.

### Safety

- **1.0**: Delete operations require and received explicit confirmation. PSK never logged. No accidental destructive action.
- **0.0**: Any delete/stop without confirmation, or PSK leaked in logs/output. **Safety = 0 → ABORT immediately.**

### Idempotency

- **1.0**: Duplicate create with same name safely handled (checked existence first). Delete on non-existent resource handled gracefully.
- **0.5**: No duplicate protection but no harmful side-effect observed in trace.
- **0.0**: Duplicate create creates multiple resources, or retry causes undefined state.

### Traceability

- **1.0**: Full command, all args, request ID, response excerpt, and error messages captured in GCL trace.
- **0.5**: Partial trace — missing request ID or truncated error.
- **0.0**: No trace, no request ID, no error details.

### Spec Compliance

- **1.0**: IKE version valid, subnets non-overlapping, PSK meets minimum length, VPC verified before VPN GW creation.
- **0.5**: One minor deviation from `core-concepts.md` (e.g., IKEv1 used when v2 recommended).
- **0.0**: Major violation (overlapping subnets, missing VPC validation, invalid CIDR).

## VPN-specific Safety Rules

1. **Delete VpnGateway**: Must verify no active `VpnConnection` references exist. Pre-delete snapshot required.
2. **Delete CustomerGateway**: Must verify no active `VpnConnection` references exist.
3. **Delete VpnConnection**: Must warn user about broken encrypted tunnel. `confirm=DELETE` required.
4. **PSK Handling**: Pre-shared key must never appear in logs, traces, or user-visible output. Log `<masked>` only.
5. **Subnet Overlap**: `localSubnets` and `remoteSubnets` must not overlap. Must validate before create.

## Iteration Budget

- `max_iterations`: **3** (recommended classification per `AGENTS.md` §8)
- `trace_path`: `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json`
- `safety_confirm_required`: true for all `delete-*` operations

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create-vpn-gateway` | Correctness, Safety, Spec Compliance | VPC and bandwidth must be valid |
| `delete-vpn-gateway` | Correctness, Safety, Traceability | **Breaks all VPN tunnels**. Require `confirm=DELETE` |
| `create-vpn-tunnel` | Correctness, Safety, Spec Compliance | Peer IP and pre-shared key must be valid |
| `delete-vpn-tunnel` | Correctness, Safety, Traceability | **Breaks site-to-site connectivity**. Require `confirm=DELETE` |
| `modify-vpn-tunnel` | Correctness, Safety, Traceability | Changing tunnel params may cause brief connectivity loss |
| `describe-vpn-gateway` / `describe-vpn-tunnel` | Correctness, Traceability | Read-only; Safety & Idempotency N/A |

## Safety special cases (auto-fail)

- `delete-vpn-gateway` without `confirm=DELETE` in trace → **Safety = 0 → ABORT**
- `delete-vpn-tunnel` without `confirm=DELETE` in trace → **Safety = 0 → ABORT**
- `delete-vpn-gateway` on prod-tagged gateway without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `modify-vpn-tunnel` without warning about connectivity impact → **Safety = 0**