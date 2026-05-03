# Monitoring JD Cloud Redis

## Key Metrics

JD Cloud Redis provides comprehensive monitoring metrics through JD Cloud Monitor (云监控). Metrics are available at multiple dimensions:

### Instance-Level Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| CPU utilization | `redis-instance` | % | CPU usage percentage |
| Memory usage | `redis-instance` | % | Memory usage percentage |
| Memory usage bytes | `redis-instance` | Bytes | Total memory bytes used |
| Connection count | `redis-instance` | Count | Active client connections |
| Max connection limit | `redis-instance` | Count | Maximum allowed connections |
| QPS | `redis-instance` | Count/s | Queries per second |
| Input bandwidth | `redis-instance` | Bytes/s | Network input bandwidth |
| Output bandwidth | `redis-instance` | Bytes/s | Network output bandwidth |
| Slow log count | `redis-instance` | Count | Number of slow operations |
| Key count | `redis-instance` | Count | Total number of keys |
| Expired key count | `redis-instance` | Count | Keys expired |
| Evicted key count | `redis-instance` | Count | Keys evicted due to memory limit |
| Hit rate | `redis-instance` | % | Cache hit rate percentage |

### Shard-Level Metrics (Cluster Versions)

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| Shard CPU | `redis-shard` | % | CPU usage per shard |
| Shard memory | `redis-shard` | % | Memory usage per shard |
| Shard QPS | `redis-shard` | Count/s | QPS per shard |
| Shard connection | `redis-shard` | Count | Connections per shard |

### Node-Level Metrics

| Metric Name | Namespace | Unit | Description |
|-------------|-----------|------|-------------|
| Node status | `redis-node` | Status | Master/Slave node status |
| Node replication lag | `redis-node` | Bytes | Replication lag between master and slave |
| Node sync status | `redis-node` | Status | Synchronization status |

## Metric Dimensions

Metrics can be queried at different dimensions:

- **Instance**: Overall instance metrics (most common)
- **Shard**: Per-shard metrics for cluster instances
- **Node**: Per-node metrics for detailed diagnostics

Dimension parameters:
- `regionId`: Region ID
- `cacheInstanceId`: Instance ID
- `shardId` (optional): Shard ID for shard-level metrics
- `nodeId` (optional): Node ID for node-level metrics

## Query Metrics via Cloud Monitor

Delegate metric queries to `jdcloud-cloudmonitor-ops` skill:

### CPU Utilization

```bash
# Use jdcloud-cloudmonitor-ops to query
# Metric: cpu_utilization
# Namespace: redis-instance
# Dimensions: cacheInstanceId
```

### Memory Usage

```bash
# Use jdcloud-cloudmonitor-ops to query
# Metric: memory_usage
# Namespace: redis-instance
# Dimensions: cacheInstanceId
```

### Connection Count

```bash
# Use jdcloud-cloudmonitor-ops to query
# Metric: connection_count
# Namespace: redis-instance
# Dimensions: cacheInstanceId
```

## Alert Configuration

Configure alerts through JD Cloud Monitor console or API. Recommended alert rules:

### Critical Alerts

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| CPU utilization | >80% | 5 min | Investigate slow logs, scale up |
| Memory usage | >90% | 5 min | Check for big keys, scale up |
| Connection count | >90% of max | 5 min | Scale up or optimize connection pooling |
| Node status | != running | 1 min | Immediate investigation |

### Warning Alerts

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| CPU utilization | >60% | 10 min | Monitor trend |
| Memory usage | >70% | 10 min | Plan scaling |
| Slow log count | >10/min | 5 min | Analyze slow commands |
| Evicted key count | >0 | 5 min | Memory pressure detected |

### Performance Alerts

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| Hit rate | <80% | 30 min | Review caching strategy |
| QPS drop | >30% decrease | 10 min | Check for issues |
| Latency increase | >50ms average | 5 min | Performance analysis |

## Alert Example (Structure)

Example alert configuration for memory usage:

```json
{
  "regionId": "cn-north-1",
  "alertName": "redis-memory-high",
  "metric": {
    "namespace": "redis-instance",
    "metricName": "memory_usage",
    "dimensions": [
      {
        "key": "cacheInstanceId",
        "value": "redis-abc123"
      }
    ]
  },
  "threshold": 90,
  "operator": ">=",
  "period": 300,
  "evaluationCount": 1,
  "notificationChannels": ["email", "sms"],
  "notificationTargets": ["admin@example.com"]
}
```

## Monitoring Best Practices

### 1. Regular Monitoring

- Check key metrics daily (CPU, memory, connections)
- Set up dashboard for Redis instances
- Review slow logs weekly
- Analyze hot keys periodically

### 2. Proactive Alerting

- Configure alerts for critical thresholds
- Use multiple notification channels
- Set escalation rules for critical alerts
- Test alert delivery regularly

### 3. Performance Analysis

- Run cache analysis monthly
- Identify hot keys and big keys
- Optimize data structures based on analysis
- Track performance trends

### 4. Capacity Planning

- Monitor growth trends in memory and QPS
- Plan scaling before hitting limits
- Consider seasonal traffic variations
- Review and adjust quotas proactively

## Monitoring Dashboard Recommendations

### Instance Overview Dashboard

Include:
- CPU utilization trend (24h, 7d)
- Memory usage trend (24h, 7d)
- Connection count vs. limit
- QPS trend
- Slow log count
- Hit rate percentage

### Performance Dashboard

Include:
- Slow log details (top 10 slow commands)
- Hot key analysis results
- Big key analysis results
- Shard-level metrics distribution
- Bandwidth usage

### Health Dashboard

Include:
- Instance status
- Node status
- Replication status
- Backup status
- Alert history

## Integration with Other Services

### Cloud Monitor (jdcloud-cloudmonitor-ops)

- Primary source for metrics and alerts
- Configure alert rules
- Query historical metrics
- Build custom dashboards

### Log Service

- Collect Redis logs for analysis
- Store slow logs for long-term analysis
- Build log-based alerts

### Auto Scaling

- Scale Redis instance based on metrics
- Note: Redis scaling is manual via API currently
- Can automate scaling workflows with metrics triggers

## Metric Access via API

### Describe Metric Data

Use Cloud Monitor API (delegate to `jdcloud-cloudmonitor-ops`):

```python
# Example: Query memory usage
# Delegate to jdcloud-cloudmonitor-ops skill
# API: describeMetricData
# Metric: memory_usage
# Namespace: redis-instance
```

### Describe Metric Statistics

```python
# Example: Query average CPU over last hour
# Delegate to jdcloud-cloudmonitor-ops skill
# API: describeMetricStatistics
```

## Slow Log Analysis

### Query Slow Log via Redis API

```bash
jdc redis describe-slow-log \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --start-time "2026-05-01T00:00:00Z" \
  --end-time "2026-05-03T00:00:00Z" \
  --page-number 1 \
  --page-size 100 \
  --output json
```

**Interpret Slow Log**:
- `command`: Slow command executed
- `key`: Key name involved
- `executionTime`: Execution time in microseconds
- `timestamp`: When command occurred

### Common Slow Operations

- KEYS pattern (use SCAN instead)
- HGETALL on large hashes
- LRANGE with large range
- Sorted set operations on large sets
- Multi-key operations without hash tag in cluster

## Cache Analysis

### Hot Key Analysis

```bash
jdc redis create-cache-analysis \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
```

Query results:
```bash
jdc redis describe-cache-analysis-result \
  --region-id "{{user.region}}" \
  --analysis-id "{{analysis_id}}" \
  --output json
```

### Big Key Analysis

```bash
jdc redis create-big-key-analysis \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
```

Query results:
```bash
jdc redis describe-big-key-detail \
  --region-id "{{user.region}}" \
  --analysis-id "{{analysis_id}}" \
  --output json
```

## Node Health Monitoring

### Query Cluster Info

```bash
jdc redis describe-cluster-info \
  --region-id "{{user.region}}" \
  --cache-instance-id "{{user.instance_id}}" \
  --output json
```

**Check**:
- Node roles (master/slave)
- Node connection status
- Replication lag
- Slot distribution

## Monitoring Checklist

### Daily Checks

- [ ] Instance status: All instances in `running` state
- [ ] CPU utilization: <80% for all instances
- [ ] Memory usage: <90% for all instances
- [ ] Connection count: Adequate headroom
- [ ] Slow log count: No unusual spikes

### Weekly Checks

- [ ] Slow log analysis: Review top slow operations
- [ ] Memory trend: Check 7-day trend
- [ ] Backup verification: Confirm backups succeeded
- [ ] Alert review: Check triggered alerts
- [ ] Connection trend: Check 7-day trend

### Monthly Checks

- [ ] Hot key analysis: Run and review results
- [ ] Big key analysis: Run and review results
- [ ] Capacity planning: Review 30-day trends
- [ ] Alert rules: Review and adjust thresholds
- [ ] Security review: Check IP whitelist and password rotation