# SSL Certificate Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-cert-ops`.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete cert`, `update cert` | 0 / 0.5 / 1 | Verifies `certId` / `certName` / `domainName` match the request. Read back via `describe-cert` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete cert`, `update cert`) MUST have explicit user confirmation. **Deleting a cert breaks HTTPS for all bound services.** |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `upload cert` is naturally idempotent. `delete cert` is naturally idempotent (already-deleted returns error). |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB). **NEVER include private key content in trace.** |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: valid PEM format, server type valid, cert not expired on upload. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `upload cert` | Correctness, Safety, Spec Compliance | Cert + key must be valid PEM; warn if already expired |
| `describe certs` / `describe cert` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `download cert` | Correctness, Safety, Traceability | Requires MFA; server type must be valid |
| `update cert name` | Correctness | Low risk; rename only |
| `update cert` | Correctness, **Safety**, Traceability | Requires MFA; replaces cert content; new cert must not be expired |
| `delete cert` | Correctness, **Safety**, **Traceability** | **Deleting a cert breaks HTTPS** for all bound CLB listeners and CDN domains. Safety = 0 without `confirm=DELETE` → ABORT. For prod-tagged certs, `confirm=DELETE_PROD` required. Must check CLB/CDN bindings first |
| `certificate expiry cruise` | Correctness, Traceability | Read-only; must cross-reference CLB listeners and CDN domains; report must include binding info |

## Safety special cases (auto-fail)

- `delete cert` without `confirm=DELETE` in trace → **Safety = 0 → ABORT**
- `delete cert` on prod-tagged cert without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `delete cert` without checking CLB/CDN bindings → **Traceability = 0**
- `update cert` with expired new cert → **Spec Compliance = 0 → ABORT**
- Private key content in trace → **Safety = 0 → ABORT** (security violation)
- Any operation targeting a `certId` not echoed back from `describe-certs` → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-cert-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial rubric for `jdcloud-cert-ops` GCL rollout |
