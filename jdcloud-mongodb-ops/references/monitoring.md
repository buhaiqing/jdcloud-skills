# Monitoring MongoDB

## Key Metrics

### Performance Metrics

| Metric | Namespace/Metric Name | Unit | Description |
|--------|----------------------|------|-------------|
| CPU Utilization | `mongodb_cpu_utilization` | % | CPU usage percentage |
| Memory Usage | `mongodb_memory_usage` | % | Memory usage percentage |
| Disk Usage | `mongodb_disk_usage` | % | Storage usage percentage |
| IOPS | `mongodb_iops` | count/s | Disk I/O operations per second |
| Connection Count | `mongodb_connections_current` | count | Current connections |
| Connection Usage | `mongodb_connections_usage` | % | Connection pool utilization |

### Throughput Metrics

| Metric | Namespace/Metric Name | Unit | Description |
|--------|----------------------|------|-------------|
| Operations/Second | `mongodb_opcounters` | count/s | Total operations per second |
| Query Rate | `mongodb_query_rate` | count/s | Queries per second |
| Insert Rate | `mongodb_insert_rate` | count/s | Inserts per second |
| Update Rate | `mongodb_update_rate` | count/s | Updates per second |
| Delete Rate | `mongodb_delete_rate` | count/s | Deletes per second |

### Latency Metrics

| Metric | Namespace/Metric Name | Unit | Description |
|--------|----------------------|------|-------------|
| Read Latency | `mongodb_read_latency` | ms | Average read latency |
| Write Latency | `mongodb_write_latency` | ms | Average write latency |
| Command Latency | `mongodb_command_latency` | ms | Average command latency |

### Replication Metrics (Replica Sets)

| Metric | Namespace/Metric Name | Unit | Description |
|--------|----------------------|------|-------------|
| Replication Lag | `mongodb_repl_lag` | seconds | Secondary lag behind primary |
| Oplog Window | `mongodb_oplog_window` | hours | Oplog retention window |

## CloudMonitor Integration

### Setting Up Alarms

```bash
# Example: Create CPU utilization alarm via CLI
jdc --output json monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "mongodb-high-cpu" \
  --metric-name "mongodb_cpu_utilization" \
  --namespace "JDCloud/MongoDB" \
  --dimensions '[{"instanceId":"mongo-xxx"}]' \
  --statistic "avg" \
  --threshold 80 \
  --comparison-operator "gte" \
  --period 300 \
  --evaluation-periods 2
```

### Recommended Alarm Thresholds

| Metric | Warning | Critical | Period |
|--------|---------|----------|--------|
| CPU Utilization | > 70% | > 85% | 5 min |
| Memory Usage | > 75% | > 90% | 5 min |
| Disk Usage | > 80% | > 90% | 5 min |
| Connection Usage | > 70% | > 85% | 5 min |
| Replication Lag | > 10s | > 60s | 1 min |

## Metric Collection via API

### Describe Metric Data

```python
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest, DescribeMetricDataParameters

params = DescribeMetricDataParameters(
    regionId="cn-north-1",
    metric="mongodb_cpu_utilization",
    serviceCode="mongodb",
    resourceId="mongo-abc123def",
    timeInterval="1h"
)
req = DescribeMetricDataRequest(parameters=params)
resp = client.send(req)
```

### Metric Data Points

```json
{
  "requestId": "abc123",
  "result": {
    "metricDatas": [
      {
        "timestamp": "2026-06-03T10:00:00Z",
        "value": 45.2
      },
      {
        "timestamp": "2026-06-03T10:05:00Z",
        "value": 52.1
      }
    ]
  }
}
```

## Slow Query Analysis

### Enabling Slow Query Log

Slow query logging is typically configured at instance creation or via modify operations:

```bash
# Via CLI - check if supported
jdc --output json mongodb modify-instance-attribute \
  --region-id cn-north-1 \
  --instance-id <instance-id> \
  # Add slow query threshold parameters if available
```

### Analyzing Slow Queries

Common slow query patterns:

| Pattern | Cause | Solution |
|---------|-------|----------|
| COLLSCAN | Collection scan - missing index | Add appropriate index |
| High docs examined/returned ratio | Inefficient query | Optimize query filter |
| Large sort operations | Sorting large result sets | Add sort index, limit results |
| Count with filter | Counting filtered documents | Consider estimatedDocumentCount |

## Performance Tuning Guide

### Index Optimization

```javascript
// Create index on frequently queried fields
db.collection.createIndex({ "field": 1 })

// Compound index for multi-field queries
db.collection.createIndex({ "field1": 1, "field2": -1 })

// Check index usage
db.collection.explain("executionStats").find({ "field": "value" })
```

### Connection Pool Tuning

| Instance Class | Max Connections | Recommended Pool Size |
|----------------|-----------------|----------------------|
| mongodb.s1.small | 500 | 50-100 |
| mongodb.s1.medium | 1000 | 100-200 |
| mongodb.s1.large | 2000 | 200-400 |
| mongodb.s1.xlarge | 4000 | 400-800 |

### Memory Optimization

```javascript
// Working set analysis
db.serverStatus().mem

// Check resident memory vs virtual memory
// Ensure working set fits in RAM
```

## Alerting Runbooks

### High CPU Alert

**Trigger**: CPU > 80% for 5 minutes

**Actions**:
1. Check current operations: `db.currentOp()`
2. Identify long-running queries
3. Consider vertical scaling if sustained
4. Check for missing indexes

### High Memory Alert

**Trigger**: Memory > 85% for 5 minutes

**Actions**:
1. Check working set size vs RAM
2. Review connection count
3. Consider vertical scaling
4. Optimize queries to reduce memory usage

### Disk Full Alert

**Trigger**: Disk usage > 90%

**Actions**:
1. Check data growth rate
2. Review and delete old data if possible
3. Expand storage or scale instance
4. Review backup retention policies

### Replication Lag Alert

**Trigger**: Secondary lag > 30 seconds

**Actions**:
1. Check secondary node status
2. Review network connectivity
3. Check secondary load (read queries)
4. Consider read preference tuning

## Dashboard Templates

### Key Metrics Dashboard

```json
{
  "dashboardName": "MongoDB Overview",
  "widgets": [
    {
      "title": "CPU & Memory",
      "metrics": ["mongodb_cpu_utilization", "mongodb_memory_usage"],
      "chartType": "line"
    },
    {
      "title": "Connections",
      "metrics": ["mongodb_connections_current"],
      "chartType": "line"
    },
    {
      "title": "Operations",
      "metrics": ["mongodb_opcounters"],
      "chartType": "bar"
    }
  ]
}
```

## Monitoring Best Practices

1. **Baseline**: Establish normal performance baselines
2. **Proactive**: Set alerts BEFORE issues become critical
3. **Correlation**: Monitor related metrics together
4. **Historical**: Keep historical data for trend analysis
5. **Testing**: Test alert mechanisms regularly
