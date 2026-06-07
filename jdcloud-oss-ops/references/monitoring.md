# Monitoring — JD Cloud Object Storage Service (OSS)

## Key Metrics

OSS metrics are available through JD Cloud Monitor service. Use `jdcloud-cloudmonitor-ops` for metric queries and alarm rule configuration.

### Storage Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| oss_storage_bytes | jcs.oss | Bytes | Total storage usage |
| oss_object_count | jcs.oss | Count | Total number of objects |
| oss_bucket_count | jcs.oss | Count | Number of buckets |

### Request Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| oss_get_requests | jcs.oss | Count | GET request count |
| oss_put_requests | jcs.oss | Count | PUT request count |
| oss_head_requests | jcs.oss | Count | HEAD request count |
| oss_delete_requests | jcs.oss | Count | DELETE request count |
| oss_post_requests | jcs.oss | Count | POST request count |
| oss_list_requests | jcs.oss | Count | LIST request count |
| oss_total_requests | jcs.oss | Count | Total request count |

### Performance Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| oss_get_latency | jcs.oss | Milliseconds | GET request latency (average) |
| oss_put_latency | jcs.oss | Milliseconds | PUT request latency (average) |
| oss_get_bandwidth | jcs.oss | Bytes/Second | GET bandwidth |
| oss_put_bandwidth | jcs.oss | Bytes/Second | PUT bandwidth |
| oss_success_rate | jcs.oss | Percent | Request success rate |

### Error Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| oss_4xx_errors | jcs.oss | Count | Client error count (4xx) |
| oss_5xx_errors | jcs.oss | Count | Server error count (5xx) |
| oss_throttled_requests | jcs.oss | Count | Throttled request count |

### Traffic Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| oss_download_bytes | jcs.oss | Bytes | Data download volume |
| oss_upload_bytes | jcs.oss | Bytes | Data upload volume |

## Metric Dimensions

When querying metrics, use these dimensions:

| Dimension | Description | Example |
|-----------|-------------|---------|
| bucketName | Bucket name | my-test-bucket |
| storageClass | Storage class | Standard, InfrequentAccess, Archive |
| apiName | API operation name | GetObject, PutObject, ListBuckets |

## Alert Rules (Recommended)

### Critical Alerts

```json
{
  "alertName": "OSS-High-5xx-Rate",
  "metric": "oss_5xx_errors",
  "threshold": 10,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 2,
  "alarmActions": ["notify-oncall"]
}
```

```json
{
  "alertName": "OSS-Storage-Near-Limit",
  "metric": "oss_storage_bytes",
  "threshold": 9000000000000,
  "comparison": ">=",
  "period": 3600,
  "evaluationPeriods": 1,
  "alarmActions": ["notify-oncall"]
}
```

### Warning Alerts

```json
{
  "alertName": "OSS-High-Latency",
  "metric": "oss_get_latency",
  "threshold": 500,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 3,
  "alarmActions": ["notify-team"]
}
```

```json
{
  "alertName": "OSS-High-Throttle-Rate",
  "metric": "oss_throttled_requests",
  "threshold": 50,
  "comparison": ">=",
  "period": 300,
  "evaluationPeriods": 2,
  "alarmActions": ["notify-team"]
}
```

## Access Logging

OSS access logs can be enabled to track all requests to a bucket.

### Log Fields

| Field | Description | Example |
|-------|-------------|---------|
| bucket | Bucket name | my-test-bucket |
| requester | Access key of the requester | ak-xxx |
| requestId | Unique request ID | req-xxx |
| operation | API operation | GetObject |
| key | Object key | path/to/file.txt |
| httpStatus | HTTP status code | 200 |
| errorCode | Error code (if any) | NoSuchKey |
| bytesSent | Bytes sent | 1024 |
| objectSize | Object size | 1024 |
| totalTime | Total request time (ms) | 45 |
| turnAroundTime | Server processing time (ms) | 20 |
| storageClass | Storage class | Standard |

## Dashboard Recommendations

### Executive Dashboard

- Total storage usage (trend over time)
- Bucket count
- Request volume (by operation type)
- 4xx/5xx error rate

### Operational Dashboard

- Top 10 largest buckets by storage
- Request latency p50/p95/p99
- Data transfer volume (upload vs download)
- Throttled request count

### Cost Optimization Dashboard

- Storage by class (Standard vs IA vs Archive)
- Lifecycle transition savings estimate
- Inactive objects (no access in 90+ days)
- CRR data transfer costs

## Log Analysis Queries

### Find Most Active Buckets

```sql
SELECT bucket, COUNT(*) as request_count
FROM oss_access_logs
GROUP BY bucket
ORDER BY request_count DESC
LIMIT 10
```

### Find Error Patterns

```sql
SELECT error_code, COUNT(*) as error_count
FROM oss_access_logs
WHERE http_status >= 400
GROUP BY error_code
ORDER BY error_count DESC
```

### Find Slow Requests

```sql
SELECT operation, key, total_time
FROM oss_access_logs
WHERE total_time > 1000
ORDER BY total_time DESC
LIMIT 100
```

## Integration with CloudMonitor

For detailed metric queries and alarm configuration, see `jdcloud-cloudmonitor-ops` skill.

### Example: Query OSS Metrics

```python
# Using CloudMonitor SDK
from jdcloud_sdk.services.monitor.client.MonitorClient import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest, DescribeMetricDataParameters

client = MonitorClient(credential)

params = DescribeMetricDataParameters(
    regionId="cn-north-1",
    metric="oss_storage_bytes",
    serviceCode="jcs.oss",
    resourceId="my-test-bucket",
    startTime="2026-06-01T00:00:00Z",
    endTime="2026-06-07T23:59:59Z"
)
req = DescribeMetricDataRequest(parameters=params)
resp = client.send(req)
```