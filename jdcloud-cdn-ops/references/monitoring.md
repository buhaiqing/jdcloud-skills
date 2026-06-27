# JD Cloud CDN — Monitoring & Hit-Rate Analysis

This skill is read-only for monitoring; alarm creation is delegated to
`jdcloud-cloudmonitor-ops`. This file covers **what to query** and **how to
interpret**.

## 1. Metrics exposed by CDN

JD Cloud CDN exposes the following via `jdc cdn query-*`:

| Metric | Command | Use |
|--------|---------|-----|
| Bandwidth (bps) time series | `query-band` | Capacity planning, traffic shaping |
| Traffic (bytes) / request volume | `query-statistics-data` | Cost analysis, usage trend |
| Per-directory bandwidth | `query-dir-bandwidth` | Hot-spot identification |
| Per-URL top traffic | `query-statistics-top-url` | Cache rule tuning |
| Per-IP top traffic | `query-statistics-top-ip` | DDoS / abuse detection |
| DDoS attack events | `query-ddos-graph` | Attack response |
| Refresh / prefetch task status | `query-refresh-task` | Task ops |

For **alarm rules**, use Cloud Monitor metric namespace `CDN` (see §4).

## 2. Hit rate (命中率) — the WAF-PERF-048 metric

### Definition

```
hit_rate = 1 - (origin_bytes / total_bytes)
  where:
    total_bytes   = bytes served by edge (query-statistics-data)
    origin_bytes  = bytes pulled from origin (query-back-source-* or Cloud Monitor OriginTraffic)
```

### Compute pattern (recommended)

```bash
DOMAIN=cdn.example.com
START='2026-06-20T00:00:00Z'
END='2026-06-27T00:00:00Z'

TOTAL=$(jdc --output json cdn query-statistics-data \
  --domain $DOMAIN --start-time $START --end-time $END \
  | jq '[.result.data[].flow] | add')

# Note: no direct "origin bytes" API in jdc cdn. Use Cloud Monitor instead:
# jdcloud-cloudmonitor-ops GetMetricData with metric=OriginTraffic
```

### Threshold (WAF-PERF-048)

| Hit rate | Verdict | Action |
|----------|---------|--------|
| ≥ 90% | pass | No action |
| 70-90% | warn | Review cache rules (see §3) |
| < 70% | fail | Add cache rules, extend TTL, switch origin to OSS |

## 3. Improving low hit rate

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Hit rate < 70% on images | TTL too short | Increase to 30 days; use filename versioning |
| Hit rate drops after deploy | Cache invalidated by refresh | Pre-warm with `bat-create-prefetch-task` |
| Hit rate varies wildly per URL | Query string fragmentation | `set-ignore-query-string 1` |
| Hit rate low for `/api/*` | API responses shouldn't cache | Add priority=1 no-cache rule for `/api/*` |
| Hit rate 100% but latency high | Origin slow but cached | Investigate origin (vm-ops / oss-ops) |

## 4. Cloud Monitor metric namespace `CDN`

For alarm rules, use these metrics via `jdcloud-cloudmonitor-ops`:

| Metric | Unit | Notes |
|--------|------|-------|
| `CDN.TotalTraffic` | bytes | Total served |
| `CDN.OriginTraffic` | bytes | Bytes pulled from origin |
| `CDN.Bandwidth` | bps | Peak bandwidth |
| `CDN.RequestCount` | count | Total requests |
| `CDN.HitRate` | percent | (if namespace exposes it — else compute) |

### Alarm example

```
User: "CDN 命中率低于 80% 告警"
  → jdcloud-cloudmonitor-ops:
      namespace=CDN
      metric=OriginTraffic / TotalTraffic  (via expression)
      threshold=0.8 (OriginTraffic/TotalTraffic > 0.2 → alert)
      period=5min
      consecutive=3
```

This skill does **NOT** create alarms; it surfaces the metrics and thresholds
that alarm rules should use.

## 5. Refresh / prefetch monitoring

Refresh and prefetch tasks are async. To monitor:

```bash
# Submit
TASK_ID=$(jdc --output json cdn create-refresh-task \
  --domain cdn.example.com \
  --url-list '["https://cdn.example.com/a.html"]' \
  --task-type file | jq -r '.result.taskId')

# Poll
jdc --output json cdn query-refresh-task --task-id $TASK_ID

# Status: pending → processing → done | failed
# failed reasons: invalid url, domain stopped, quota exhausted
```

For batch monitoring (many in-flight tasks):

```bash
jdc --output json cdn query-refresh-task-by-ids \
  --task-ids '["task-1","task-2","task-3"]'
```

## 6. Anomaly detection

| Anomaly | Pattern | Tool |
|---------|---------|------|
| Bandwidth spike (10× normal) | DDoS or viral content | `query-ddos-graph` + `query-statistics-top-ip` |
| Origin traffic spike | Cache miss surge | Check `query-refresh-task` history (mass refresh?) |
| Hit rate sudden drop | Rule change or origin fail | Compare `query-band` before/after recent cache-rule changes |
| Domain 5xx surge | Origin unhealthy | Investigate origin (vm-ops / clb-ops health) |

## 7. Performance KPIs

| KPI | Healthy | Watch | Action |
|-----|---------|-------|--------|
| Hit rate | ≥ 90% | 70-90% | < 70% |
| Origin latency | < 100ms | 100-300ms | > 300ms |
| 5xx rate | < 0.1% | 0.1-1% | > 1% |
| Bandwidth utilization | < 70% of plan | 70-90% | > 90% |

## 8. Logs

```bash
jdc --output json cdn query-domain-log \
  --domain cdn.example.com \
  --start-time '2026-06-26T00:00:00Z' \
  --end-time   '2026-06-27T00:00:00Z'
```

Returns edge access logs (may be large — paginate via `--page-number` / `--page-size`).
For long-term log retention, configure CDN access logs to ship to
`jdcloud-logservice-ops` via the CDN console.

## 9. Out of scope

- **Live streaming** metrics — different metric namespace (`CDN.live.*`), different semantics (bandwidth-only, no hit rate)
- **PCDN / jbox** — separate product
- **Long-term stats archival** — CDN keeps ~90 days; for older data, export to log service or data warehouse