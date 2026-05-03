# Monitoring JD Cloud Load Balancer

## Key Metrics

Load Balancer metrics are collected via JD Cloud Monitor service. Query metrics using the Cloud Monitor API or delegate to `jdcloud-cloudmonitor-ops`.

### Application Load Balancer (ALB) Metrics

| Metric | Namespace | Dimensions | Description |
|--------|-----------|------------|-------------|
| Active Connections | `alb` | `loadBalancerId` | Current active TCP connections |
| Connection Rate | `alb` | `loadBalancerId` | New connections per second |
| Request Count (HTTP) | `alb` | `loadBalancerId`, `listenerId` | HTTP requests per second |
| Response Time (HTTP) | `alb` | `loadBalancerId`, `listenerId` | Average HTTP response latency (ms) |
| Upstream Response Time | `alb` | `loadBalancerId` | Backend server response time |
| HTTP 2xx Rate | `alb` | `loadBalancerId` | 2xx response percentage |
| HTTP 4xx Rate | `alb` | `loadBalancerId` | 4xx response percentage |
| HTTP 5xx Rate | `alb` | `loadBalancerId` | 5xx response percentage |
| Traffic In | `alb` | `loadBalancerId` | Inbound traffic (bytes/sec) |
| Traffic Out | `alb` | `loadBalancerId` | Outbound traffic (bytes/sec) |
| Healthy Target Count | `alb` | `targetGroupId` | Number of healthy backends |
| Unhealthy Target Count | `alb` | `targetGroupId` | Number of unhealthy backends |

### Network Load Balancer (NLB) Metrics

| Metric | Namespace | Dimensions | Description |
|--------|-----------|------------|-------------|
| Active Connections | `nlb` | `loadBalancerId` | Current active connections |
| Connection Rate | `nlb` | `loadBalancerId` | New connections per second |
| Connection Drop Rate | `nlb` | `loadBalancerId` | Connections dropped per second |
| Traffic In | `nlb` | `loadBalancerId` | Inbound traffic (bytes/sec) |
| Traffic Out | `nlb` | `loadBalancerId` | Outbound traffic (bytes/sec) |
| Healthy Target Count | `nlb` | `targetGroupId` | Healthy backend count |
| Unhealthy Target Count | `nlb` | `targetGroupId` | Unhealthy backend count |
| Source IP Connection Count | `nlb` | `loadBalancerId` | Connections per source IP |

## Querying Metrics via SDK

### Example: Query ALB Active Connections

```python
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest

req = DescribeMetricDataRequest(
    namespace="alb",
    metric="activeConnections",
    dimensions=[{"loadBalancerId": "lb-abc"}],
    startTime="2026-05-01T00:00:00Z",
    endTime="2026-05-03T00:00:00Z",
    period="60"  # 60-second granularity
)

resp = monitor_client.describeMetricData(req)
for point in resp.result.metricData:
    print(f"Time: {point.timestamp}, Value: {point.value}")
```

### Example: Query HTTP 5xx Rate

```python
req = DescribeMetricDataRequest(
    namespace="alb",
    metric="http5xxRate",
    dimensions=[{"loadBalancerId": "lb-abc"}],
    startTime="2026-05-01T00:00:00Z",
    endTime="2026-05-03T00:00:00Z",
    period="300"  # 5-minute granularity
)

resp = monitor_client.describeMetricData(req)
```

## Alert Configuration

### Recommended Alert Rules

| Alert | Metric | Threshold | Period | Description |
|-------|--------|-----------|--------|-------------|
| High Error Rate | HTTP 5xx Rate | > 5% | 5 min | Backend errors exceeding threshold |
| Low Health Ratio | Healthy Target Count | < 50% of targets | 3 min | Insufficient healthy backends |
| High Latency | Response Time | > 1000ms | 5 min | Slow backend responses |
| Connection Surge | Connection Rate | > 10000/s | 1 min | Abnormal traffic spike |
| All Backends Unhealthy | Healthy Target Count | = 0 | 1 min | Complete backend failure |

### Alert Rule Structure (via Cloud Monitor)

```json
{
  "ruleName": "alb-high-error-rate",
  "namespace": "alb",
  "metric": "http5xxRate",
  "dimensions": [{"loadBalancerId": "lb-abc"}],
  "threshold": 5.0,
  "comparisonOperator": "greaterThan",
  "period": 300,
  "evaluationCount": 3,
  "notificationChannels": ["email", "sms"]
}
```

### Creating Alert Rule via SDK

Delegate alert creation to `jdcloud-cloudmonitor-ops` for full Cloud Monitor integration:

```
User: "Set up an alert for high 5xx error rate on my ALB"

Agent:
1. Use jdcloud-clb-ops to identify the LB ID.
2. Delegate to jdcloud-cloudmonitor-ops to create the alert rule with:
   - namespace: alb
   - metric: http5xxRate
   - threshold: 5%
   - period: 300s
```

## Dashboards

### Recommended Dashboard Panels

1. **LB Overview**: Active connections, connection rate, traffic (in/out)
2. **HTTP Performance**: Request rate, response time, error rates (2xx, 4xx, 5xx)
3. **Backend Health**: Healthy/unhealthy target counts, health check failures
4. **Traffic Analysis**: Geographic distribution, protocol breakdown
5. **Certificate Status**: SSL certificate expiration countdown

### Custom Dashboard Creation

Use JD Cloud Monitor console or delegate to `jdcloud-cloudmonitor-ops` for dashboard configuration.

## Health Check Integration

Load Balancer health check results are reflected in `healthyTargetCount` and `unhealthyTargetCount` metrics.

### Health Check Monitoring Pattern

1. **Poll describeTargetHealth** for real-time backend status.
2. **Monitor healthyTargetCount metric** for historical trends.
3. **Alert on unhealthyTargetCount > 0** to catch backend failures early.

```python
# Real-time health check via LB SDK
from jdcloud_sdk.services.alb.apis.DescribeTargetHealthRequest import DescribeTargetHealthRequest

req = DescribeTargetHealthRequest(
    regionId="cn-north-1",
    loadBalancerId="lb-abc"
)

resp = client.describeTargetHealth(req)
for target in resp.result.targets:
    status = target.healthStatus  # "healthy" / "unhealthy" / "initializing"
    print(f"Target {target.targetId}: {status}")
```

## Access Log Collection (ALB)

ALB supports access log collection via JD Cloud Log Service.

### Enabling Access Logs

1. Create log service topic (delegate to log service skill).
2. Configure ALB access log export via console or API.
3. Query logs via Log Service API for traffic analysis.

### Log Fields

| Field | Description |
|-------|-------------|
| timestamp | Request time |
| client_ip | Source IP address |
| listener_port | Listener port |
| protocol | HTTP / HTTPS |
| method | HTTP method |
| host | Request host header |
| path | Request path |
| status_code | Response status |
| response_time | Response latency (ms) |
| upstream_ip | Backend server IP |
| upstream_response_time | Backend latency |

## Monitoring Best Practices

1. **Set up alerts before production**: Configure health and error rate alerts immediately after LB creation.
2. **Monitor backend health separately**: Alert when any backend becomes unhealthy.
3. **Track certificate expiration**: Monitor SSL certificate validity days.
4. **Baseline performance**: Record normal connection rates and response times for anomaly detection.
5. **Cross-AZ monitoring**: Ensure traffic distribution across AZs is balanced.

## Integration with jdcloud-cloudmonitor-ops

For comprehensive monitoring configuration, delegate metric queries and alert creation to `jdcloud-cloudmonitor-ops`:

| Task | Delegation |
|------|------------|
| Query LB metrics | `jdcloud-cloudmonitor-ops` with namespace `alb` or `nlb` |
| Create alert rules | `jdcloud-cloudmonitor-ops` with LB dimension |
| Configure dashboards | `jdcloud-cloudmonitor-ops` dashboard skill |

## See Also

- [JD Cloud Monitor Documentation](https://docs.jdcloud.com/cn/cloudmonitor/)
- [ALB Access Log](https://docs.jdcloud.com/cn/application-load-balancer/configure-access-log)