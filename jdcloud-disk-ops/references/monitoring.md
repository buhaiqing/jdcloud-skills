# Monitoring JD Cloud Cloud Disk

## Key Metrics

JD Cloud Cloud Disk supports the following monitoring metrics via Cloud Monitor:

| Metric Name | Namespace | Description | Unit |
|-------------|-----------|-------------|------|
| `IOPSRead` | `jdcloud/disk` | Read IO operations per second | Count/s |
| `IOPSWrite` | `jdcloud/disk` | Write IO operations per second | Count/s |
| `IOPSTotal` | `jdcloud/disk` | Total IO operations per second (read + write) | Count/s |
| `ThroughputRead` | `jdcloud/disk` | Read throughput | Bytes/s |
| `ThroughputWrite` | `jdcloud/disk` | Write throughput | Bytes/s |
| `ThroughputTotal` | `jdcloud/disk` | Total throughput (read + write) | Bytes/s |
| `LatencyRead` | `jdcloud/disk` | Average read IO latency | ms |
| `LatencyWrite` | `jdcloud/disk` | Average write IO latency | ms |
| `LatencyTotal` | `jdcloud/disk` | Average total IO latency | ms |
| `DiskUsage` | `jdcloud/disk` | Disk used capacity | Bytes |
| `DiskUsagePercent` | `jdcloud/disk` | Disk usage percentage | % |
| `DiskSize` | `jdcloud/disk` | Total disk capacity | Bytes |
| `IOPSQueueDepth` | `jdcloud/disk` | IO queue depth (pending IO requests) | Count |
| `BurstIOPSCredits` | `jdcloud/disk` | Remaining burst IOPS credits (SSD disks) | Count |

## Alert Examples

### High Disk Usage Alert

```json
{
  "metric": "DiskUsagePercent",
  "namespace": "jdcloud/disk",
  "dimensions": {
    "diskId": "disk-xxx"
  },
  "threshold": 85,
  "period": 300,
  "comparisonOperator": ">=",
  "evaluationCount": 2,
  "alarmName": "Disk High Usage",
  "alarmDesc": "Disk usage exceeds 85%",
  "notifyType": ["SMS", "Email"],
  "contactGroups": ["ops-team"]
}
```

### High Latency Alert

```json
{
  "metric": "LatencyTotal",
  "namespace": "jdcloud/disk",
  "dimensions": {
    "diskId": "disk-xxx"
  },
  "threshold": 50,
  "period": 60,
  "comparisonOperator": ">",
  "evaluationCount": 5,
  "alarmName": "Disk High Latency",
  "alarmDesc": "Disk IO latency exceeds 50ms",
  "notifyType": ["SMS", "Email"],
  "contactGroups": ["ops-team"]
}
```

### IOPS Saturation Alert

```json
{
  "metric": "IOPSTotal",
  "namespace": "jdcloud/disk",
  "dimensions": {
    "diskId": "disk-xxx"
  },
  "threshold": 0.9,
  "period": 300,
  "comparisonOperator": ">=",
  "evaluationCount": 3,
  "alarmName": "Disk IOPS Saturation",
  "alarmDesc": "Disk IOPS usage reaches 90% of provisioned value",
  "notifyType": ["SMS", "Email", "Webhook"],
  "contactGroups": ["ops-team"]
}
```

## Monitoring Best Practices

1. **Set Usage Thresholds**: Configure tiered alerts for disk usage at 70%, 85%, and 95% to allow progressive response.
2. **Latency Baselines**: Establish normal latency per disk type (SSD vs. HDD) and alert on deviations.
3. **IOPS/Throughput Saturation**: Monitor IOPS and throughput utilization against provisioned values to detect performance ceilings.
4. **Queue Depth Watch**: High queue depth combined with high latency indicates IO bottlenecks requiring vertical or horizontal scaling.
5. **Burst Credit Tracking**: For SSD disks, monitor `BurstIOPSCredits` to anticipate performance degradation after credits are exhausted.
6. **Capacity Planning**: Use `DiskUsage` trend data to forecast capacity expansion needs before disks fill up.
7. **Multi-disk Aggregation**: Aggregate metrics at instance or application level for services spanning multiple disks.
8. **Integration with Alert Intelligence**: Use `jdcloud-alert-intelligence` for alert aggregation, deduplication, and noise suppression.

## Metric Collection

Metrics are collected automatically by JD Cloud Cloud Monitor at a default granularity (typically 60s for 7-day retention, 300s for 30-day retention). No additional agent installation is required.

### Accessing Metrics via Cloud Monitor API

```bash
# Example: Get total IOPS metrics for a cloud disk
jdc --output json cloudmonitor get-metric-data \
  --region-id cn-north-1 \
  --namespace jdcloud/disk \
  --metric-name IOPSTotal \
  --dimensions '[{"name":"diskId","value":"disk-xxx"}]' \
  --start-time "$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --period 60
```

```bash
# Example: Get disk usage percentage for capacity planning
jdc --output json cloudmonitor get-metric-data \
  --region-id cn-north-1 \
  --namespace jdcloud/disk \
  --metric-name DiskUsagePercent \
  --dimensions '[{"name":"diskId","value":"disk-xxx"}]' \
  --start-time "$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --period 300
```

```bash
# Example: Get disk latency metrics for performance analysis
jdc --output json cloudmonitor get-metric-data \
  --region-id cn-north-1 \
  --namespace jdcloud/disk \
  --metric-name LatencyTotal \
  --dimensions '[{"name":"diskId","value":"disk-xxx"}]' \
  --start-time "$(date -u -d '30 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --period 60
```

## Dashboard Recommendations

Create a Cloud Monitor dashboard with the following widgets:

1. **IOPS Overview**: Line chart showing read/write/total IOPS over time with provisioned value as reference line.
2. **Throughput Overview**: Line chart showing read/write/total throughput in MB/s.
3. **Latency Breakdown**: Line chart comparing read vs. write latency with p95/p99 percentile indicators.
4. **Disk Usage Distribution**: Stacked bar chart showing usage per disk or per instance.
5. **Top Disks by Usage**: Bar chart identifying disks with highest capacity utilization.
6. **Queue Depth Trend**: Area chart showing IO queue depth to detect sustained backlog.
7. **Burst Credits Remaining**: Gauge showing remaining burst credits for SSD disks.
8. **SLA Summary**: KPI widgets showing current latency percentile and IOPS saturation percentage.

## Alert Notification

Configure alerts to notify your operations team via:
- SMS (for critical P0/P1 alerts)
- Email (for P2/P3 alerts and daily digest)
- Webhook (for integration with incident management systems such as DingTalk, Feishu, or PagerDuty)
- JD Cloud Message Center (for unified notification history)
- Automated Runbook Trigger (invoke `jdcloud-disk-ops` runbooks such as `01-daily-health-check` or `02-capacity-planning` when thresholds are breached)