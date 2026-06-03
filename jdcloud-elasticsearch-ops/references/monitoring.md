# Monitoring JD Cloud Elasticsearch

## Key Metrics

### Cluster Health Metrics

| Metric Name | Description | Unit | Normal Range |
|-------------|-------------|------|--------------|
| `ClusterHealthStatus` | Overall cluster health | Enum | 0=green, 1=yellow, 2=red |
| `NumberOfNodes` | Number of nodes in cluster | Count | Expected node count |
| `NumberOfDataNodes` | Number of data nodes | Count | Expected data node count |
| `ActivePrimaryShards` | Number of active primary shards | Count | Varies by index |
| `ActiveShards` | Total active shards | Count | Varies by index |
| `RelocatingShards` | Shards being relocated | Count | 0 (brief spikes OK) |
| `InitializingShards` | Shards being initialized | Count | 0 (brief spikes OK) |
| `UnassignedShards` | Unassigned shards | Count | 0 (indicates problem) |

### Node Metrics

| Metric Name | Description | Unit | Alert Threshold |
|-------------|-------------|------|-----------------|
| `CPUUtilization` | CPU usage percentage | % | > 80% warning, > 90% critical |
| `MemoryUtilization` | Memory usage percentage | % | > 85% warning, > 95% critical |
| `JVMMemoryPressure` | JVM heap usage percentage | % | > 75% warning, > 85% critical |
| `JVMGCYoungCollectionCount` | Young GC count | Count/sec | > 10/sec |
| `JVMGCOldCollectionCount` | Old GC count | Count/sec | > 0 sustained |
| `DiskUsage` | Disk usage percentage | % | > 80% warning, > 90% critical |
| `DiskReadIOPS` | Disk read IOPS | Count | Baseline dependent |
| `DiskWriteIOPS` | Disk write IOPS | Count | Baseline dependent |
| `NetworkInRate` | Network inbound traffic | Bytes/sec | Baseline dependent |
| `NetworkOutRate` | Network outbound traffic | Bytes/sec | Baseline dependent |

### Index Metrics

| Metric Name | Description | Unit | Alert Threshold |
|-------------|-------------|------|-----------------|
| `IndexRate` | Documents indexed per second | Count/sec | Baseline dependent |
| `SearchRate` | Search requests per second | Count/sec | Baseline dependent |
| `SearchLatency` | Average search latency | ms | > 100ms warning |
| `IndexingLatency` | Average indexing latency | ms | > 50ms warning |
| `IndexSize` | Total index size | Bytes | Monitor growth |
| `DocumentCount` | Total document count | Count | Monitor growth |

### Query Performance Metrics

| Metric Name | Description | Unit | Alert Threshold |
|-------------|-------------|------|-----------------|
| `QueryTime` | Query execution time | ms | > 500ms warning |
| `FetchTime` | Fetch phase time | ms | > 200ms warning |
| `ScrollTime` | Scroll query time | ms | > 1000ms warning |

## Alert Example (Structure)

```json
{
  "metric": "CPUUtilization",
  "threshold": 80,
  "comparisonOperator": "GreaterThanOrEqualToThreshold",
  "period": 300,
  "evaluationPeriods": 2,
  "alarmActions": ["notify-on-call"],
  "dimensions": {
    "instanceId": "es-xxx"
  }
}
```

## Recommended Alert Rules

### Critical Alerts (Immediate Action Required)

| Alert Name | Metric | Condition | Action |
|------------|--------|-----------|--------|
| Cluster Health Red | `ClusterHealthStatus` | = 2 for 1 min | Page on-call |
| Node Down | `NumberOfNodes` | < expected | Page on-call |
| Disk Full | `DiskUsage` | > 90% for 2 min | Page on-call |
| JVM Heap Critical | `JVMMemoryPressure` | > 85% for 5 min | Page on-call |

### Warning Alerts (Investigation Required)

| Alert Name | Metric | Condition | Action |
|------------|--------|-----------|--------|
| Cluster Health Yellow | `ClusterHealthStatus` | = 1 for 5 min | Create ticket |
| High CPU | `CPUUtilization` | > 80% for 10 min | Create ticket |
| High Memory | `MemoryUtilization` | > 85% for 10 min | Create ticket |
| JVM Heap Warning | `JVMMemoryPressure` | > 75% for 10 min | Create ticket |
| Disk Warning | `DiskUsage` | > 80% for 10 min | Create ticket |
| High Search Latency | `SearchLatency` | > 100ms for 15 min | Create ticket |
| High Indexing Latency | `IndexingLatency` | > 50ms for 15 min | Create ticket |

### Info Alerts (Awareness)

| Alert Name | Metric | Condition | Action |
|------------|--------|-----------|--------|
| Unassigned Shards | `UnassignedShards` | > 0 for 30 min | Log/email |
| GC Pressure | `JVMGCYoungCollectionCount` | > 10/sec for 10 min | Log/email |

## Monitoring Integration

### CloudMonitor Integration

JD Cloud Elasticsearch integrates with CloudMonitor for metrics collection and alerting.

**Setup via CLI:**
```bash
# Create alarm rule
jdc --output json monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "es-cpu-high" \
  --metric "CPUUtilization" \
  --threshold 80 \
  --comparison-operator "gte" \
  --period 300 \
  --evaluation-periods 2 \
  --resource-type "es" \
  --resource-id "es-xxx"
```

**Setup via SDK:**
```python
from jdcloud_sdk.services.monitor.apis.CreateAlarmRequest import CreateAlarmRequest, CreateAlarmParameters

params = CreateAlarmParameters(
    regionId="cn-north-1",
    alarmName="es-cpu-high",
    metric="CPUUtilization",
    threshold=80,
    comparisonOperator="gte",
    period=300,
    evaluationPeriods=2,
    resourceType="es",
    resourceId="es-xxx"
)
req = CreateAlarmRequest(parameters=params)
resp = client.send(req)
```

### Custom Monitoring

**Query Metrics via API:**
```python
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import (
    DescribeMetricDataRequest, DescribeMetricDataParameters
)

params = DescribeMetricDataParameters(
    regionId="cn-north-1",
    metric="CPUUtilization",
    resourceType="es",
    resourceId="es-xxx",
    startTime="2026-06-01T00:00:00Z",
    endTime="2026-06-03T00:00:00Z"
)
req = DescribeMetricDataRequest(parameters=params)
resp = client.send(req)
```

## Dashboards

### Key Metrics Dashboard

Create a dashboard in CloudMonitor with the following widgets:

1. **Cluster Health Overview**
   - ClusterHealthStatus (gauge)
   - NumberOfNodes (count)
   - ActiveShards vs UnassignedShards

2. **Resource Utilization**
   - CPUUtilization (line chart, all nodes)
   - MemoryUtilization (line chart, all nodes)
   - JVMMemoryPressure (line chart, all nodes)
   - DiskUsage (line chart, all nodes)

3. **Performance Metrics**
   - SearchRate (line chart)
   - IndexRate (line chart)
   - SearchLatency (line chart)
   - IndexingLatency (line chart)

4. **Network & I/O**
   - NetworkInRate / NetworkOutRate
   - DiskReadIOPS / DiskWriteIOPS

## Troubleshooting with Metrics

### High CPU Usage

**Symptoms:**
- CPUUtilization > 80% sustained
- Increased search/indexing latency

**Investigation:**
1. Check SearchRate and IndexRate for traffic spikes
2. Review query patterns for expensive queries
3. Check for large aggregations or deep pagination

**Actions:**
1. Scale up to larger instance class
2. Add data nodes to distribute load
3. Optimize queries and mappings
4. Implement request caching

### High Memory Usage

**Symptoms:**
- JVMMemoryPressure > 75%
- Frequent GC (JVMGCYoungCollectionCount high)
- Search latency increases

**Investigation:**
1. Check field cache usage
2. Review aggregation queries
3. Check number of segments

**Actions:**
1. Force merge indices to reduce segments
2. Clear field data cache if needed
3. Scale up instance class with more memory
4. Optimize queries to use less memory

### Disk Space Issues

**Symptoms:**
- DiskUsage > 80%
- Indexing failures

**Investigation:**
1. Check IndexSize growth rate
2. Review retention policy
3. Check for unoptimized indices

**Actions:**
1. Delete old indices per retention policy
2. Force merge to reclaim space
3. Scale up disk size
4. Add more data nodes

### Unassigned Shards

**Symptoms:**
- UnassignedShards > 0
- Cluster health yellow/red

**Investigation:**
1. Check node status
2. Verify disk space on all nodes
3. Check for allocation rules

**Actions:**
1. Restart failed nodes
2. Free up disk space
3. Update shard allocation settings
4. Contact support if cannot resolve
