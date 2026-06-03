# Monitoring JD Cloud EIP

## Key Metrics

JD Cloud EIP supports the following monitoring metrics via Cloud Monitor:

| Metric Name | Namespace | Description | Unit |
|-------------|-----------|-------------|------|
| `BandwidthIn` | `jdcloud/eip` | Inbound bandwidth usage | Mbps |
| `BandwidthOut` | `jdcloud/eip` | Outbound bandwidth usage | Mbps |
| `BytesIn` | `jdcloud/eip` | Inbound data transfer | Bytes |
| `BytesOut` | `jdcloud/eip` | Outbound data transfer | Bytes |
| `PacketsIn` | `jdcloud/eip` | Inbound packet count | Count |
| `PacketsOut` | `jdcloud/eip` | Outbound packet count | Count |
| `DropPacketsIn` | `jdcloud/eip` | Dropped inbound packets | Count |
| `DropPacketsOut` | `jdcloud/eip` | Dropped outbound packets | Count |

## Alert Examples

### High Bandwidth Usage Alert

```json
{
  "metric": "BandwidthOut",
  "namespace": "jdcloud/eip",
  "dimensions": {
    "addressId": "eip-xxx"
  },
  "threshold": 80,
  "period": 300,
  "comparisonOperator": ">=",
  "evaluationCount": 3,
  "alarmName": "EIP High Bandwidth Usage",
  "alarmDesc": "EIP bandwidth usage exceeds 80%",
  "notifyType": ["SMS", "Email"],
  "contactGroups": ["ops-team"]
}
```

### Packet Drop Alert

```json
{
  "metric": "DropPacketsOut",
  "namespace": "jdcloud/eip",
  "dimensions": {
    "addressId": "eip-xxx"
  },
  "threshold": 100,
  "period": 60,
  "comparisonOperator": ">",
  "evaluationCount": 1,
  "alarmName": "EIP Packet Drop",
  "alarmDesc": "EIP outbound packet drops detected",
  "notifyType": ["SMS", "Email"],
  "contactGroups": ["ops-team"]
}
```

## Monitoring Best Practices

1. **Set Baseline**: Establish normal bandwidth usage patterns for each EIP.
2. **Threshold Alerts**: Configure alerts for bandwidth thresholds (e.g., 80%, 90%, 95%).
3. **Packet Drop Monitoring**: Watch for unexpected packet drops indicating network issues.
4. **Trend Analysis**: Track bandwidth trends to anticipate capacity needs.
5. **Multi-region Monitoring**: Monitor EIPs across all regions where you have resources.
6. **Integration with Alert Intelligence**: Use `jdcloud-alert-intelligence` for alert aggregation and suppression.

## Metric Collection

Metrics are collected automatically by JD Cloud Cloud Monitor. No additional configuration is required for basic metric collection.

### Accessing Metrics via Cloud Monitor API

```bash
# Example: Get bandwidth metrics for EIP
jdc --output json cloudmonitor get-metric-data \
  --region-id cn-north-1 \
  --namespace jdcloud/eip \
  --metric-name BandwidthOut \
  --dimensions '[{"name":"addressId","value":"eip-xxx"}]' \
  --start-time "$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --period 60
```

## Dashboard Recommendations

Create a Cloud Monitor dashboard with the following widgets:

1. **Bandwidth Usage**: Line chart showing inbound/outbound bandwidth over time
2. **Top EIPs by Bandwidth**: Bar chart showing EIPs with highest usage
3. **Packet Drop Rate**: Gauge showing packet drop percentage
4. **EIP Status Summary**: Count of EIPs by state (available, in-use, error)
5. **Traffic Trend**: Area chart showing daily data transfer

## Alert Notification

Configure alerts to notify your operations team via:
- SMS
- Email
- Webhook (for integration with incident management systems)
- JD Cloud Message Center
