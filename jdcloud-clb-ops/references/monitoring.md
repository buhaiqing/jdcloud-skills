# Monitoring — JD Cloud Load Balancer (CLB)

## Key Metrics

CLB metrics are available through JD Cloud Monitor service. Use `jdcloud-cloudmonitor-ops` for metric queries.

### Performance Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| lb_bytes_in | jcs.lb | Bytes | Incoming traffic bytes |
| lb_bytes_out | jcs.lb | Bytes | Outgoing traffic bytes |
| lb_packets_in | jcs.lb | Count | Incoming packets |
| lb_packets_out | jcs.lb | Count | Outgoing packets |
| lb_active_connections | jcs.lb | Count | Current active connections |
| lb_new_connections | jcs.lb | Count/Second | New connections per second |
| lb_request_count | jcs.lb | Count/Second | Requests per second (HTTP/HTTPS) |
| lb_latency | jcs.lb | Milliseconds | Response latency |

### Health Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| lb_healthy_host_count | jcs.lb | Count | Number of healthy backend servers |
| lb_unhealthy_host_count | jcs.lb | Count | Number of unhealthy backend servers |
| lb_health_check_failures | jcs.lb | Count | Health check failure count |

### Error Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| lb_http_4xx | jcs.lb | Count | HTTP 4xx errors |
| lb_http_5xx | jcs.lb | Count | HTTP 5xx errors |
| lb_drop_connections | jcs.lb | Count | Dropped connections |
| lb_rejected_connections | jcs.lb | Count | Rejected connections (over limit) |

## Metric Dimensions

When querying metrics, use these dimensions:

| Dimension | Description | Example |
|-----------|-------------|---------|
| loadBalancerId | Load balancer ID | lb-xxx |
| listenerId | Listener ID | listener-xxx |
| targetGroupId | Target group ID | tg-xxx |

## Alert Rules (Recommended)

### Critical Alerts

```json
{
  "alertName": "CLB-High-5xx-Rate",
  "metric": "lb_http_5xx",
  "threshold": 10,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 2,
  "alarmActions": ["notify-oncall"]
}
```

```json
{
  "alertName": "CLB-No-Healthy-Targets",
  "metric": "lb_healthy_host_count",
  "threshold": 1,
  "comparison": "<",
  "period": 60,
  "evaluationPeriods": 1,
  "alarmActions": ["notify-oncall"]
}
```

### Warning Alerts

```json
{
  "alertName": "CLB-High-Latency",
  "metric": "lb_latency",
  "threshold": 1000,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 3,
  "alarmActions": ["notify-team"]
}
```

```json
{
  "alertName": "CLB-High-Connection-Count",
  "metric": "lb_active_connections",
  "threshold": 10000,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 2,
  "alarmActions": ["notify-team"]
}
```

## Access Logs

CLB access logs can be enabled for detailed request analysis:

### Log Format

```
timestamp client_ip:port lb_ip:port request_method request_url protocol status_code response_size response_time backend_ip:port
```

### Enabling Access Logs

Access logs are configured via API or console. Logs are delivered to JD Cloud Object Storage Service (OSS).

## Health Check Monitoring

### Monitoring Health Check Status

```bash
# CLI - Describe targets to see health status
jdc --output json lb describe-targets \
  --region-id <region> \
  --load-balancer-id <lb-id> \
  --target-group-id <tg-id>
```

### Health Check Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Healthy Host Count | > 50% of targets | 20-50% of targets | < 20% of targets |
| Health Check Failures | 0 | < 10% | >= 10% |

## Dashboard Recommendations

### Executive Dashboard

- Request count (QPS)
- Error rate (4xx + 5xx)
- Average latency
- Active connections

### Operational Dashboard

- Healthy vs unhealthy target count
- Bytes in/out
- New connections rate
- Top 10 URLs by request count

### Troubleshooting Dashboard

- Health check failure rate by target
- 5xx errors by backend
- Connection drops
- Rejected connections

## Log Analysis Queries

### Find Slow Requests

```sql
-- Requests with latency > 1 second
SELECT * FROM clb_access_logs 
WHERE response_time > 1000 
ORDER BY timestamp DESC 
LIMIT 100
```

### Find Error Patterns

```sql
-- 5xx errors by backend
SELECT backend_ip, status_code, COUNT(*) 
FROM clb_access_logs 
WHERE status_code >= 500 
GROUP BY backend_ip, status_code
```

### Traffic Distribution

```sql
-- Requests per backend
SELECT backend_ip, COUNT(*) as request_count 
FROM clb_access_logs 
GROUP BY backend_ip 
ORDER BY request_count DESC
```

## Integration with CloudMonitor

For detailed metric queries and alarm configuration, see `jdcloud-cloudmonitor-ops` skill.

### Example: Query CLB Metrics

```python
# Using CloudMonitor SDK
from jdcloud_sdk.services.monitor.client.MonitorClient import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest, DescribeMetricDataParameters

params = DescribeMetricDataParameters(
    regionId="cn-north-1",
    metric="lb_bytes_in",
    serviceCode="jcs.lb",
    resourceId="lb-xxx",
    startTime="2026-05-06T00:00:00Z",
    endTime="2026-05-06T23:59:59Z"
)
req = DescribeMetricDataRequest(parameters=params)
resp = client.send(req)
```
