# JD Cloud CLB Monitoring

## Key Metrics
JD Cloud CLB provides comprehensive monitoring metrics to track performance and health:

### Connection Metrics
- **ActiveConnections**: Current number of active connections
- **NewConnections**: Rate of new connections per second
- **TotalConnections**: Total number of connections over time
- **ConnectionSuccessRate**: Percentage of successful connections

### Traffic Metrics
- **BandwidthIn**: Incoming bandwidth usage (bits per second)
- **BandwidthOut**: Outgoing bandwidth usage (bits per second)
- **TotalTraffic**: Total data transferred
- **RequestCount**: Number of HTTP/HTTPS requests

### Performance Metrics
- **ResponseTime**: Average response time from backend servers
- **ServerResponseTime**: Time taken by backend servers to respond
- **ProcessingTime**: Total processing time including CLB overhead

### Health Metrics
- **HealthyServerCount**: Number of healthy backend servers
- **UnhealthyServerCount**: Number of unhealthy backend servers
- **HealthCheckSuccessRate**: Percentage of successful health checks

### Error Metrics
- **HTTP5xxErrorCount**: Number of 5xx errors from backend servers
- **HTTP4xxErrorCount**: Number of 4xx errors from clients
- **DroppedConnections**: Number of dropped connections

### SSL Certificate Metrics
- **CertificateExpirationDays**: Days until certificate expiration
- **SSLHandshakeFailures**: Number of failed SSL handshakes
- **SSLCipherSuiteUsage**: Distribution of cipher suites used
- **TLSVersionDistribution**: Distribution of TLS versions used

## Alert Configuration

### Basic Alert Rules
```json
{
  "metricName": "ActiveConnections",
  "threshold": 10000,
  "comparisonOperator": ">",
  "period": 300,
  "evaluationCount": 3,
  "alertAction": {
    "type": "notify",
    "contacts": ["admin@example.com"]
  }
}
```

### Recommended Alert Thresholds
| Metric | Warning Threshold | Critical Threshold | Period |
|--------|-------------------|-------------------|--------|
| ActiveConnections | 8000 | 10000 | 300s |
| BandwidthIn | 800Mbps | 950Mbps | 300s |
| BandwidthOut | 800Mbps | 950Mbps | 300s |
| ResponseTime | 1000ms | 3000ms | 300s |
| HTTP5xxErrorCount | 10 | 50 | 300s |
| UnhealthyServerCount | 1 | 2 | 300s |
| CertificateExpirationDays | 30 days | 7 days | 86400s (daily) |

## Monitoring Dashboard

### CLB Overview Dashboard
- CLB instance status
- Connection metrics over time
- Traffic patterns
- Error rates
- Backend server health

### Listener-Specific Dashboard
- Per-listener connection counts
- Listener traffic distribution
- Protocol-specific metrics
- SSL handshake performance

### Backend Server Group Dashboard
- Server health status
- Traffic distribution per server
- Server response times
- Load balancing effectiveness

## Custom Monitoring

### Query CLB Metrics via CLI
```bash
jdc clb describe-clb-metrics \
  --clb-id clb-xxxxx \
  --start-time "2026-04-28T00:00:00+08:00" \
  --end-time "2026-04-28T23:59:59+08:00" \
  --metric-name "ActiveConnections" \
  --period 300 \
  --region cn-north-1 \
  --output json
```

### Set Up CloudWatch Alarms
```bash
jdc monitor put-metric-alarm \
  --alarm-name "clb-high-connections" \
  --namespace "JDCloud/CLB" \
  --metric-name "ActiveConnections" \
  --statistic Average \
  --period 300 \
  --threshold 10000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions "arn:aws:sns:cn-north-1:123456789012:clb-alerts" \
  --region cn-north-1
```

## Best Practices
- Monitor connection counts to detect capacity issues early
- Set up alerts for backend server health degradation
- Track response times to identify performance bottlenecks
- Monitor error rates to detect application issues
- Review traffic patterns for capacity planning
- Use custom metrics for application-specific monitoring
- **Monitor certificate expiration** and set alerts at 30 and 7 days before expiry
- Implement automated certificate rotation where possible
- Regularly audit SSL policies to ensure compliance with security standards
- Monitor SSL handshake failures to detect client compatibility issues