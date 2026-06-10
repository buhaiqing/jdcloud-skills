# Monitoring — `jdcloud-routines-ops`

> `jdcloud-routines-ops` is a **read-only** operations skill — it does **not**
> write Cloud Monitor alarm rules and does **not** subscribe to event streams.
> It produces **point-in-time** JSON reports.
>
> "Monitoring" here means: how the routine skill **consumes** monitor data when
> it expands beyond pure expiry, plus how its own outputs can be **fed into**
> Cloud Monitor as a downstream signal.

## 1. What this skill consumes (read-only)

For 1.1.0 the only data source is the `charge.chargeExpiredTime` field on each
resource. No metric query is performed by the cruise script itself.

Planned consumption (1.2.0+):

| Scenario | Metric / Field | Source |
|---|---|---|
| Billing analysis | `bill.summary` | `bill.describeBillSummaryByInstance` (SDK) |
| Resource inventory | `instance.count`, `cpu.utilization`, `memory.usage` | Cloud Monitor |
| Renewal readiness | `instance.health`, `clb.backend.healthy.host_count` | Cloud Monitor + `jdcloud-aiops-cruise` |

When these metrics are pulled, the call MUST be delegated to
`jdcloud-cloudmonitor-ops` per the cross-skill delegation rules. This skill
should never call Cloud Monitor OpenAPI directly.

## 2. What this skill produces (write-side)

A typical expiry report (`outputs/expiry/expiry-report-YYYYMMDD-HHMMSS.json`)
has this shape:

```json
{
  "report_time": "2026-06-10T06:30:00+08:00",
  "warning_days": 14,
  "regions_checked": ["cn-north-1", "cn-south-1", "cn-east-1", "cn-east-2", "ap-southeast-1"],
  "types_checked":   ["vm", "redis", "eip", "disk", "rds", "clb", "mongodb", "elasticsearch", "ssl"],
  "customer_filter": "烟台振华",
  "summary": {
    "total_expiring": 12,
    "by_type":   {"VM": 3, "RDS-MySQL": 2, "Redis": 1, "SSL证书": 6},
    "by_region": {"cn-north-1": 8, "cn-south-1": 4},
    "urgent_7days": 2
  },
  "details": [
    {
      "type": "VM",
      "name": "prod-web-01",
      "id":   "i-abc123",
      "region": "cn-north-1",
      "region_cn": "华北 (北京)",
      "expired":    "2026-06-15",
      "days_left":  5,
      "customer":   "烟台振华",
      "instance_type": "g.n6.large"
    }
  ]
}
```

## 3. Downstream consumption — Cloud Monitor alarms

A common pattern is: **run the cruise from cron, parse the JSON, raise a Cloud
Monitor event when urgent resources appear.** This is implemented as a thin
glue script in `scripts/notify_urgent.py` (planned).

Recommended alarm mapping:

| `urgent_7days` count | Severity | Suggested alarm action |
|---|---|---|
| `0` | OK | No-op |
| `1–3` | Warning | Notify ops channel |
| `4–10` | Critical | Notify ops + customer-success channel |
| `> 10` | Disaster | Page on-call |

The alarm rule itself MUST be created via `jdcloud-cloudmonitor-ops`, never
inline in this skill.

## 4. Logging / observability of the skill itself

When `expiry_cruise.py` runs, it emits:

- Console summary (colored by severity)
- JSON report file
- stdout/stderr captured by the cron runner

For 1.1.0 there is **no structured log file**. Tracked for 1.2.0.

## 5. Self-monitoring — when the skill itself fails

| Symptom | Likely cause | Action |
|---|---|---|
| Empty `details` for a type | (a) nothing expiring, (b) pagination cap hit, (c) CLI failure silently swallowed | Check `~/.jdcloud-routines-ops/outputs/expiry/*.json`; if `total_expiring == 0` but the type was queried, re-run with `--warning-days 60` to verify pagination |
| `days_left < 0` for all entries | `chargeExpiredTime` parse error — possibly region mismatch | Check `JDC_REGION` env / `~/.jdc/config` `region_id` |
| Script returns `1` immediately | Credential missing | Verify `~/.jdc/config` exists (see `cli-usage.md` §1.2) |
| Elasticsearch returns `[]` silently | SDK call failed; error swallowed | Re-run with `JDCS_DEBUG=1` (planned flag) |

## 6. Integration with `jdcloud-aiops-cruise`

| Trigger | Hand off to | Notes |
|---|---|---|
| Cruise finds an expiring `prod` resource | `jdcloud-aiops-cruise` | Run a pre-expiry health check to decide renew vs replace |
| Cruise finds a chronic overdue resource | `jdcloud-alert-intelligence` | Aggregate into suppression rule |
| Cruise finds an expiring resource with no `客户` tag | (no handoff) | Flag in report under `untagged_count` (planned 1.2.0) |

## 7. References

- `references/core-concepts.md` — design invariants
- `references/cli-usage.md` — exit code semantics
- `references/integration.md` — credential chain
- `references/troubleshooting.md` — failure-mode catalogue

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial monitoring doc for `jdcloud-routines-ops` (1.1.0 batch) |