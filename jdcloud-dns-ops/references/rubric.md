# DNS Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric defined in
> `AGENTS.md` §3 for `jdcloud-dns-ops`.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|---|---|---|---|---|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `delete domain`, `delete resource record`, `batch set` | 0 / 0.5 / 1 | Verifies `domainId` / `recordId` / record type/value match the request. Read back via `describe-*` and compare. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete domain`, `delete resource record`, `batch set`) MUST have explicit user confirmation captured in trace. **Deleting a domain removes ALL records irreversibly.** |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create domain` may fail on duplicate name. `create resource record` is naturally idempotent at API level. `batch set` should snapshot first. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `describe-*` snapshot. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Conforms to `core-concepts.md`: valid record types, type-specific value formats, CNAME not at apex, MX has priority, TTL in valid range. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|---|---|---|
| `create domain` | Correctness, Safety, Spec Compliance | Pack ID must be valid (0/1/2); domain name must be valid FQDN |
| `describe domains` / `search rr` | Correctness, Traceability | Safety & Idempotency are N/A; score 1.0 by default |
| `delete domain` | Correctness, **Safety**, **Traceability** | **Irreversible** — all records deleted. Safety = 0 without `confirm=DELETE` → ABORT. For prod-tagged domains, `confirm=DELETE_PROD` required. Must include pre-delete snapshot of all records |
| `create resource record` | Correctness, Spec Compliance | Type-specific validation: A=IPv4, AAAA=IPv6, CNAME=FQDN, MX=priority+host, TXT=string, SRV=priority+weight+port+target. **CNAME at apex** (`hostRecord="@"`) → Spec Compliance = 0 → ABORT |
| `modify resource record` | Correctness, Spec Compliance | Same validation as create |
| `delete resource record` | Correctness, **Safety**, Traceability | Safety = 0 without `confirm=DELETE_RR` for production domains |
| `enable/disable resource record` | Correctness, **Safety** | Safety = 0 if disabling critical records (`www`, `@`, `mail`) on production domains without confirm |
| `batch set resource records` | Correctness, **Safety**, **Traceability** | Safety = 0 without `confirm=BATCH`. Must include pre-batch snapshot of existing records |

## Safety special cases (auto-fail)

- `delete domain` without `confirm=DELETE` in trace → **Safety = 0 → ABORT**
- `delete domain` on prod-tagged domain without `confirm=DELETE_PROD` → **Safety = 0 → ABORT**
- `batch set` without pre-snapshot of existing records → **Traceability = 0**
- CNAME at apex (`hostRecord="@"`, `type="CNAME"`) → **Spec Compliance = 0 → ABORT**
- MX record without priority field → **Correctness = 0**
- Any operation targeting a `domainId` not echoed back from a `describe-domains` lookup → **Correctness = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for `jdcloud-dns-ops` |
| Trace path | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | `AGENTS.md` §6 |
| Rubric version | `v1` | this file |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial rubric for `jdcloud-dns-ops` GCL rollout |
