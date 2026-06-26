# Monitoring — JD Cloud Load Balancer (CLB)

> **ponytail: metric codes kept. Alarm rule CRUD → delegate to `jdcloud-cloudmonitor-ops`.**

## Key Metrics

| Metric Name | Unit | Description |
|-------------|------|-------------|
| `lb_bytes_in` | Bytes | Incoming traffic |
| `lb_bytes_out` | Bytes | Outgoing traffic |
| `lb_packets_in` | Count | Incoming packets |
| `lb_packets_out` | Count | Outgoing packets |
| `lb_active_connections` | Count | Current active connections |
| `lb_new_connections` | Count/s | New connections per second |
| `lb_request_count` | Count/s | Requests per second (HTTP/HTTPS) |
| `lb_latency` | ms | Response latency |
| `lb_healthy_host_count` | Count | Healthy backend servers |
| `lb_unhealthy_host_count` | Count | Unhealthy backend servers |
| `lb_health_check_failures` | Count | Health check failure count |
| `lb_http_4xx` | Count | HTTP 4xx errors |
| `lb_http_5xx` | Count | HTTP 5xx errors |
| `lb_drop_connections` | Count | Dropped connections |
| `lb_rejected_connections` | Count | Rejected connections (over limit) |

## Metric Dimensions

| Dimension | Example |
|-----------|---------|
| `loadBalancerId` | `lb-xxx` |
| `listenerId` | `listener-xxx` |
| `targetGroupId` | `tg-xxx` |

## Quick Query

```bash
jdc --output json monitor describe-metric-data \
  --region-id <region> --metric lb_active_connections \
  --service-code jcs.lb --resource-id lb-xxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --aggr-type avg
```

## Recommended Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Active Connections | > 80% of max | > 95% of max |
| 5xx Rate | > 1% for 5m | > 5% for 5m |
| Healthy Host % | < 50% | < 20% |
| Latency | > 500ms | > 1000ms |
| Rejected Connections | > 0 | > 10/min |

> For alarm rule CRUD, delegate to `jdcloud-cloudmonitor-ops`.