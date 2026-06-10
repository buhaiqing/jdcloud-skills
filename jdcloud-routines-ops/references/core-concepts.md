# Core Concepts — `jdcloud-routines-ops`

> Static / periodic JD Cloud operations scenarios — expiry cruise, billing analysis,
> resource inventory. Contrast with `jdcloud-aiops-cruise` (dynamic / event-driven
> cruise) — see the **Responsibility Boundary** section in `SKILL.md`.

## 1. What is `jdcloud-routines-ops`

`jdcloud-routines-ops` is the **routine operations** skill for JD Cloud. It collects
**time-invariant, periodically-executed** operational tasks that recur on a schedule
(weekly, monthly, per-billing-cycle) and do **not** depend on real-time signals.

Two product surfaces today:

| Surface | Type | Status | Script |
|---|---|---|---|
| **资源到期巡检** (Expiry Cruise) | Periodic / preventive | ✅ Available | `scripts/expiry_cruise.py` |
| **资源账单分析** (Billing Analysis) | Periodic / per-cycle | 🔜 Planned | — |
| **资源盘点报告** (Resource Inventory) | Periodic / weekly-monthly | 🔜 Planned | — |

The core design principle: **read-only, schedule-driven, snapshot output**. Every
scenario produces a JSON report + a console summary that is safe to drop into a
ticket, an email, or a Feishu notification.

## 2. Expiry Cruise — Domain Model

### 2.1 Charge model basics

JD Cloud resources have a billing `charge` block with these standard fields:

| Field | Type | Meaning |
|---|---|---|
| `chargeMode` | string | `prepaid_by_duration` (subscription) or `postpaid_by_duration` (pay-as-you-go) |
| `chargeStatus` | string | `Normal`, `Expired`, `Overdue` |
| `chargeStartTime` | ISO-8601 | Subscription start |
| `chargeExpiredTime` | ISO-8601 | Subscription end — **this is what expiry_cruise reads** |
| `chargeAutoRenew` | bool | Auto-renewal flag |

`expiry_cruise.py` only reads `charge.chargeExpiredTime`. Pay-as-you-go resources
typically have no expiry and are filtered out (days_left = -1, skipped).

### 2.2 `days_left` semantics

```python
days_left = (chargeExpiredTime.date() - today).days
```

| `days_left` | Bucket | Severity |
|---|---|---|
| `< 0` | Already expired | (filtered out of report) |
| `0–3` | Critical | 🔴 |
| `4–7` | High | 🟡 |
| `8–warning_days` | Warning | 🟢 |
| `> warning_days` | OK | (filtered out of report) |
| `None` / parse fail | Unknown | (filtered out, logged) |

`warning_days` defaults to **14**, configurable via `--warning-days`.

### 2.3 Customer tag convention

Resources are grouped by the `客户` tag. The current convention:

| Tag key | Tag value example | Meaning |
|---|---|---|
| `客户` | `烟台振华` | The customer this resource is billed to / owned by |
| `环境` | `prod` / `staging` / `dev` | Environment tier |
| `项目` | `core-erp` | Sub-project within the customer |

`expiry_cruise.py` reads only `客户` today. `--customer <name>` is a filter, not a
selector — when omitted, **all resources across all customer tags are scanned**.

> ⚠️ Customer-tag driven scans can become **multi-tenant**. Always keep raw
> resource payloads out of any non-customer-specific path. See `safety-gates.md`
> (planned) for cross-tenant handling.

### 2.4 Resource coverage matrix

| Resource | CLI command | JSON list path | Expiry field |
|---|---|---|---|
| VM | `vm describe-instances` | `$.result.instances[]` | `charge.chargeExpiredTime` |
| Redis | `redis describe-cache-instances` | `$.result.cacheInstances[]` | `charge.chargeExpiredTime` |
| EIP | `vpc describe-eips` | `$.result.eips[]` | `charge.chargeExpiredTime` |
| Disk | `disk describe-disks` | `$.result.disks[]` | `charge.chargeExpiredTime` |
| RDS | `rds describe-instances` | `$.result.dbInstances[]` | `charge.chargeExpiredTime` |
| CLB | `lb describe-load-balancers` | `$.result.loadBalancers[]` | `charge.chargeExpiredTime` |
| MongoDB | `mongodb describe-instances` | `$.result.mongodbInstances[]` | `charge.chargeExpiredTime` |
| Elasticsearch | SDK OpenAPI | `$.result.instances[]` | `charge.chargeExpiredTime` |
| SSL 证书 (global) | `ssl describe-certs` | `$.result.certListDetails[]` | `endTime` |

> SSL certificates are **global** resources — they are queried once outside the
> region loop.

## 3. Billing Analysis — Domain Model (planned)

> 🔜 Will use the `bill` OpenAPI. Pluggable time window (current month, last month,
> last quarter, YTD). Aggregation dimensions: customer, region, product, instance-id.
>
> Sketch:
>
> ```python
> {
>   "period": "2026-05",
>   "by_customer":  [{"customer": "烟台振华", "amount_cny": 12345.67}, ...],
>   "by_product":   [{"product": "VM",     "amount_cny": 5432.10}, ...],
>   "by_region":    [{"region": "cn-north-1", "amount_cny": 8000.00}, ...],
> }
> ```

## 4. Resource Inventory — Domain Model (planned)

> 🔜 Will join `describe-*` across products, deduplicate by `(customer, instance_id)`,
> and emit a Markdown table grouped by customer → region → product.
>
> Output target: customer-facing weekly digest, suitable for attaching to a
> service-review meeting.

## 5. Responsibility Boundary — Routines vs AIOps

> ⚠️ **Read this section before choosing which skill to invoke.**

| Aspect | `jdcloud-routines-ops` | `jdcloud-aiops-cruise` |
|---|---|---|
| **Cadence** | Scheduled (cron, weekly, monthly) | Event-driven / on-demand |
| **Trigger** | Calendar / tick / SLA window | Alert / ticket / human request |
| **Time horizon** | Days → months ahead | Real-time → minutes back |
| **Output shape** | Snapshot report | Streaming diagnosis + root-cause candidates |
| **Examples** | "Resources expiring in 14d", "May billing summary", "weekly resource digest" | "CLB has 5xx spike", "VM CPU 100% since 14:02", "MySQL slow query burst" |
| **Mutation** | ❌ None | ❌ None (read-only) |
| **Where to delegate** | Find what needs action | Diagnose why and how to fix |

**Decision rule of thumb**:

- "Did this happen / is this happening now?" → **`jdcloud-aiops-cruise`**
- "Will this happen / what's due soon?" → **`jdcloud-routines-ops`**

A single resource may appear in both — e.g. an expiring VM (routines-ops) may also
need a real-time health check (aiops-cruise) before renewal.

## 6. Design Invariants

These MUST hold across every script in `scripts/`:

1. **Read-only**: zero mutation calls (no `delete-*`, `stop-*`, `reboot-*`,
   `modify-*`).
2. **Idempotent**: re-running yields the same JSON shape and report schema. No
   side effects beyond writing the report file.
3. **No secret leakage**: credentials are read from `~/.jdc/config` (CLI) or
   `JDC_*` env vars (SDK). Never print `JDC_SECRET_KEY`. See
   `references/integration.md` §"Credential Loading Chain".
4. **jdc-first with SDK fallback**: try `jdc --output json …` first; only after
   3 consecutive failures, fall back to `jdcloud_sdk`. See `references/cli-usage.md`.
5. **sys.path compliance**: scripts in `scripts/` (or subdirs) MUST insert the
   `scripts/` directory (one level above) into `sys.path` before importing `lib`.
   This mirrors the AGENTS.md convention for AIOps scripts.
6. **Exit code semantics**:
   - `0` — at least one expiring resource found (or scenario succeeded with
     findings)
   - `1` — no findings (clean) **or** execution error (unparseable JSON, missing
     credential, region unreachable)
   - Other non-zero — fatal infrastructure failure (do not catch silently)

## 7. Region Coverage

See `references/regions.md` for the canonical region list, AZs, and the list of
products whose expiry info is NOT yet exposed via `jdc` CLI (Kubernetes, WAF, OSS,
some RDS engines). Coverage gaps fall back to `jdcloud_sdk` OpenAPI per the
jdc-first-with-SDK-fallback policy.

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial core-concepts for `jdcloud-routines-ops` (1.1.0 batch) |