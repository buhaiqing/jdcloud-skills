# Monitoring JD Cloud RDS MySQL

## Key Metrics

JD Cloud CloudMonitor provides the following metrics for RDS MySQL instances:

| Metric | Namespace | Description | Unit |
|--------|-----------|-------------|------|
| CPUUtilization | rds | CPU usage percentage | % |
| MemoryUtilization | rds | Memory usage percentage | % |
| DiskUtilization | rds | Disk usage percentage | % |
| IOPSRead | rds | Read IOPS count | Count/s |
| IOPSWrite | rds | Write IOPS count | Count/s |
| NetworkIn | rds | Inbound network traffic | Bytes/s |
| NetworkOut | rds | Outbound network traffic | Bytes/s |
| Connections | rds | Active connections count | Count |
| SlowQueries | rds | Slow query count per minute | Count/min |
| AbortedConnections | rds | Aborted connections count | Count |

## Alert Examples

### High CPU Usage Alert

```json
{
  "metric": "CPUUtilization",
  "namespace": "rds",
  "dimensions": {
    "instanceId": "{{user.instance_id}}"
  },
  "threshold": 80,
  "comparisonOperator": ">=",
  "period": 300,
  "statistics": "Average",
  "evaluationCount": 3,
  "alarmName": "MySQL High CPU Alert"
}
```

### High Connection Count Alert

```json
{
  "metric": "Connections",
  "namespace": "rds",
  "dimensions": {
    "instanceId": "{{user.instance_id}}"
  },
  "threshold": 500,
  "comparisonOperator": ">=",
  "period": 60,
  "statistics": "Maximum",
  "evaluationCount": 1,
  "alarmName": "MySQL High Connection Alert"
}
```

### Slow Queries Alert

```json
{
  "metric": "SlowQueries",
  "namespace": "rds",
  "dimensions": {
    "instanceId": "{{user.instance_id}}"
  },
  "threshold": 10,
  "comparisonOperator": ">=",
  "period": 60,
  "statistics": "Sum",
  "evaluationCount": 5,
  "alarmName": "MySQL Slow Queries Alert"
}
```

## Monitoring Best Practices

1. **Set baseline:** Establish normal metric ranges for your workload
2. **Configure alerts:** Set appropriate thresholds for critical metrics
3. **Monitor trends:** Track metric changes over time
4. **Correlate metrics:** Look for relationships between CPU, IOPS, and connections
5. **Use dashboards:** Create custom dashboards in CloudMonitor
6. **Set up notifications:** Configure alert notifications via email/SMS/webhook

## Logs

### Slow Query Log
- Captures queries exceeding long_query_time (default 10 seconds)
- Useful for identifying performance bottlenecks

### Error Log
- Records database errors and warnings
- Useful for troubleshooting instance issues

### General Log
- Records all connections and queries
- Useful for auditing and debugging

## Tools

- **JD Cloud CloudMonitor:** Native monitoring service
- **MySQL Workbench:** GUI tool for database management
- **Prometheus + Grafana:** Custom monitoring stack