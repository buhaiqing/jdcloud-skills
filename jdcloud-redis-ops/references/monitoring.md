# Monitoring JD Cloud Redis

## Overview

JD Cloud Redis provides comprehensive monitoring metrics through Cloud Monitor service. This guide covers key metrics, alert configuration, and monitoring best practices.

## Key Metrics

### 1. Memory Metrics

#### Memory Usage (内存使用率)
- **Metric Name**: `memory_usage`
- **Unit**: Percentage (%)
- **Description**: Current memory usage as percentage of max memory
- **Recommended Threshold**: 
  - Warning: > 85%
  - Critical: > 95%
- **Namespace**: `jcs_for_redis`

**Query via CLI:**
```bash
jdc monitor get-metric-data \
  --namespace jcs_for_redis \
  --metric-name memory_usage \
  --dimensions '[{"name":"instanceId","value":"jcs-redis-abc123"}]' \
  --start-time "2026-04-30T00:00:00+08:00" \
  --end-time "2026-04-30T23:59:59+08:00" \
  --period 300 \
  --output json
```

#### Used Memory (已用内存)
- **Metric Name**: `used_memory`
- **Unit**: MB
- **Description**: Actual memory used by Redis
- **Note**: Should be significantly lower than capacity

#### Memory Fragmentation Ratio (内存碎片率)
- **Metric Name**: `mem_fragmentation_ratio`
- **Unit**: Ratio
- **Description**: Ratio of actual memory to allocated memory
- **Recommended Threshold**: 
  - Warning: > 1.5
  - Critical: > 2.0
- **Note**: High ratio indicates memory fragmentation, consider restart

### 2. CPU Metrics

#### CPU Utilization (CPU使用率)
- **Metric Name**: `cpu_usage`
- **Unit**: Percentage (%)
- **Description**: Instance CPU usage
- **Recommended Threshold**: 
  - Warning: > 70%
  - Critical: > 85%
- **Note**: Single-threaded Redis, high CPU indicates blocking operations

### 3. Connection Metrics

#### Connected Clients (连接数)
- **Metric Name**: `connected_clients`
- **Unit**: Count
- **Description**: Number of connected clients
- **Recommended Threshold**: 
  - Warning: > 80% of max connections
  - Critical: > 95% of max connections
- **Max connections by spec**:
  - redis.sw.1g/2g: 10,000
  - redis.sw.4g/8g: 20,000
  - redis.sw.16g/32g: 40,000

#### New Connections Per Second (新建连接数)
- **Metric Name**: `new_connections`
- **Unit**: Count/second
- **Description**: Rate of new connections
- **Note**: High rate may indicate connection pool issues

### 4. Throughput Metrics

#### QPS (Queries Per Second)
- **Metric Name**: `qps`
- **Unit**: Count/second
- **Description**: Number of commands executed per second
- **Note**: Varies by workload, establish baseline

#### Network Inbound (网络入流量)
- **Metric Name**: `network_in`
- **Unit**: Bytes/second
- **Description**: Incoming network traffic

#### Network Outbound (网络出流量)
- **Metric Name**: `network_out`
- **Unit**: Bytes/second
- **Description**: Outgoing network traffic

### 5. Cache Performance Metrics

#### Cache Hit Rate (缓存命中率)
- **Metric Name**: `keyspace_hit_rate`
- **Unit**: Percentage (%)
- **Description**: Ratio of successful key lookups
- **Formula**: `keyspace_hits / (keyspace_hits + keyspace_misses) * 100`
- **Recommended Threshold**: 
  - Warning: < 80%
  - Critical: < 60%
- **Note**: Low hit rate indicates poor cache utilization

#### Keyspace Hits (命中次数)
- **Metric Name**: `keyspace_hits`
- **Unit**: Count
- **Description**: Number of successful key lookups

#### Keyspace Misses (未命中次数)
- **Metric Name**: `keyspace_misses`
- **Unit**: Count
- **Description**: Number of failed key lookups

### 6. Key Statistics

#### Total Keys (Key总数)
- **Metric Name**: `total_keys`
- **Unit**: Count
- **Description**: Total number of keys in database
- **Note**: Monitor for unexpected growth

#### Expiring Keys (过期Key数)
- **Metric Name**: `expiring_keys`
- **Unit**: Count
- **Description**: Number of keys with TTL set

### 7. Replication Metrics (Master-Slave/Cluster)

#### Replication Lag (主从延迟)
- **Metric Name**: `replication_lag`
- **Unit**: Seconds
- **Description**: Replication delay between master and slave
- **Recommended Threshold**: 
  - Warning: > 10 seconds
  - Critical: > 60 seconds
- **Note**: High lag increases data loss risk during failover

#### Replication Status (复制状态)
- **Metric Name**: `replication_status`
- **Unit**: Status (0=normal, 1=abnormal)
- **Description**: Master-slave replication health
- **Recommended Threshold**: Any non-zero value triggers alert

### 8. Persistence Metrics

#### AOF Rewrite Status (AOF重写状态)
- **Metric Name**: `aof_rewrite_in_progress`
- **Unit**: Boolean (0/1)
- **Description**: Whether AOF rewrite is in progress

#### Last Save Status (上次保存状态)
- **Metric Name**: `rdb_last_save_status`
- **Unit**: Status (0=success, 1=failed)
- **Description**: Status of last RDB save operation

## Alert Configuration

### Create Alert Rule via CLI

#### Example 1: Memory Usage Alert

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "redis-memory-usage-high" \
  --description "Alert when Redis memory usage exceeds 85%" \
  --resource-type "jcs_for_redis" \
  --resource-ids '["jcs-redis-abc123"]' \
  --metric-name "memory_usage" \
  --namespace "jcs_for_redis" \
  --statistics "Average" \
  --period 300 \
  --comparison-operator "GreaterThanThreshold" \
  --threshold 85 \
  --evaluation-count 3 \
  --contact-groups '["ops-team"]' \
  --alarm-actions '["arn:jdcloud:cms:::action/sms", "arn:jdcloud:cms:::action/email"]' \
  --output json
```

#### Example 2: CPU Usage Alert

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "redis-cpu-usage-high" \
  --description "Alert when Redis CPU usage exceeds 80%" \
  --resource-type "jcs_for_redis" \
  --resource-ids '["jcs-redis-abc123"]' \
  --metric-name "cpu_usage" \
  --namespace "jcs_for_redis" \
  --statistics "Average" \
  --period 300 \
  --comparison-operator "GreaterThanThreshold" \
  --threshold 80 \
  --evaluation-count 3 \
  --contact-groups '["ops-team"]' \
  --output json
```

#### Example 3: Connection Count Alert

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "redis-connections-high" \
  --description "Alert when connections exceed 80% of max" \
  --resource-type "jcs_for_redis" \
  --resource-ids '["jcs-redis-abc123"]' \
  --metric-name "connected_clients" \
  --namespace "jcs_for_redis" \
  --statistics "Average" \
  --period 300 \
  --comparison-operator "GreaterThanThreshold" \
  --threshold 16000 \
  --evaluation-count 2 \
  --contact-groups '["ops-team"]' \
  --output json
```

#### Example 4: Replication Lag Alert

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "redis-replication-lag" \
  --description "Alert when replication lag exceeds 10 seconds" \
  --resource-type "jcs_for_redis" \
  --resource-ids '["jcs-redis-abc123"]' \
  --metric-name "replication_lag" \
  --namespace "jcs_for_redis" \
  --statistics "Average" \
  --period 60 \
  --comparison-operator "GreaterThanThreshold" \
  --threshold 10 \
  --evaluation-count 3 \
  --contact-groups '["ops-team"]' \
  --output json
```

#### Example 5: Cache Hit Rate Alert

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "redis-cache-hit-rate-low" \
  --description "Alert when cache hit rate drops below 80%" \
  --resource-type "jcs_for_redis" \
  --resource-ids '["jcs-redis-abc123"]' \
  --metric-name "keyspace_hit_rate" \
  --namespace "jcs_for_redis" \
  --statistics "Average" \
  --period 300 \
  --comparison-operator "LessThanThreshold" \
  --threshold 80 \
  --evaluation-count 3 \
  --contact-groups '["ops-team"]' \
  --output json
```

### Alert Configuration Best Practices

#### Recommended Alerts for Production

| Metric | Threshold | Severity | Evaluation Count | Period |
|--------|-----------|----------|------------------|--------|
| Memory Usage | > 85% | Warning | 3 | 300s |
| Memory Usage | > 95% | Critical | 2 | 60s |
| CPU Usage | > 70% | Warning | 3 | 300s |
| CPU Usage | > 85% | Critical | 2 | 60s |
| Connections | > 80% of max | Warning | 2 | 300s |
| Replication Lag | > 10s | Warning | 3 | 60s |
| Replication Lag | > 60s | Critical | 2 | 60s |
| Cache Hit Rate | < 80% | Warning | 3 | 300s |
| Cache Hit Rate | < 60% | Critical | 2 | 300s |

#### Notification Channels

- **SMS**: Critical alerts (immediate response required)
- **Email**: Warning alerts (review within business hours)
- **Webhook**: Integration with incident management systems
- **Phone**: Critical production outages

## Monitoring Dashboard

### Create Custom Dashboard

```bash
jdc monitor create-dashboard \
  --region-id cn-north-1 \
  --dashboard-name "redis-production-overview" \
  --description "Production Redis instance monitoring" \
  --widgets '[
    {
      "title": "Memory Usage",
      "metric": "memory_usage",
      "namespace": "jcs_for_redis",
      "dimensions": [{"name": "instanceId", "value": "jcs-redis-abc123"}],
      "chartType": "line",
      "period": 300
    },
    {
      "title": "CPU Usage",
      "metric": "cpu_usage",
      "namespace": "jcs_for_redis",
      "dimensions": [{"name": "instanceId", "value": "jcs-redis-abc123"}],
      "chartType": "line",
      "period": 300
    },
    {
      "title": "Connections",
      "metric": "connected_clients",
      "namespace": "jcs_for_redis",
      "dimensions": [{"name": "instanceId", "value": "jcs-redis-abc123"}],
      "chartType": "line",
      "period": 300
    },
    {
      "title": "QPS",
      "metric": "qps",
      "namespace": "jcs_for_redis",
      "dimensions": [{"name": "instanceId", "value": "jcs-redis-abc123"}],
      "chartType": "line",
      "period": 60
    },
    {
      "title": "Cache Hit Rate",
      "metric": "keyspace_hit_rate",
      "namespace": "jcs_for_redis",
      "dimensions": [{"name": "instanceId", "value": "jcs-redis-abc123"}],
      "chartType": "line",
      "period": 300
    }
  ]' \
  --output json
```

## Monitoring Scripts

### Script 1: Check Redis Health

```bash
#!/bin/bash

INSTANCE_ID="jcs-redis-abc123"
REGION="cn-north-1"

echo "=== Redis Instance Health Check ==="
echo "Instance: $INSTANCE_ID"
echo "Region: $REGION"
echo ""

# Get instance status
STATUS=$(jdc redis describe-cache-instance \
  --region-id $REGION \
  --cache-instance-id $INSTANCE_ID \
  --output json | jq -r '.result.cacheInstance.status')

echo "Status: $STATUS"

if [ "$STATUS" != "running" ]; then
  echo "⚠️  WARNING: Instance is not in running state!"
  exit 1
fi

# Get memory usage
MEMORY_USAGE=$(jdc redis describe-cache-instance \
  --region-id $REGION \
  --cache-instance-id $INSTANCE_ID \
  --output json | jq -r '.result.cacheInstance.usedMemoryMB')

MEMORY_TOTAL=$(jdc redis describe-cache-instance \
  --region-id $REGION \
  --cache-instance-id $INSTANCE_ID \
  --output json | jq -r '.result.cacheInstance.capacityMB')

MEMORY_PERCENT=$((MEMORY_USAGE * 100 / MEMORY_TOTAL))

echo "Memory: ${MEMORY_USAGE}MB / ${MEMORY_TOTAL}MB (${MEMORY_PERCENT}%)"

if [ $MEMORY_PERCENT -gt 90 ]; then
  echo "⚠️  WARNING: Memory usage is high!"
fi

# Get connection info
DOMAIN=$(jdc redis describe-cache-instance \
  --region-id $REGION \
  --cache-instance-id $INSTANCE_ID \
  --output json | jq -r '.result.cacheInstance.connectionDomain')

PORT=$(jdc redis describe-cache-instance \
  --region-id $REGION \
  --cache-instance-id $INSTANCE_ID \
  --output json | jq -r '.result.cacheInstance.connectionPort')

echo "Endpoint: $DOMAIN:$PORT"

echo ""
echo "✅ Health check completed"
```

### Script 2: Monitor Key Metrics

```bash
#!/bin/bash

INSTANCE_ID="jcs-redis-abc123"
REGION="cn-north-1"
END_TIME=$(date -Iseconds)
START_TIME=$(date -d '1 hour ago' -Iseconds)

echo "=== Redis Metrics (Last 1 Hour) ==="
echo ""

# Memory usage
echo "--- Memory Usage ---"
jdc monitor get-metric-data \
  --namespace jcs_for_redis \
  --metric-name memory_usage \
  --dimensions "[{\"name\":\"instanceId\",\"value\":\"$INSTANCE_ID\"}]" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 300 \
  --output json | jq '.datapoints[-3:] | .[] | {timestamp: .timestamp, value: .value}'

echo ""

# CPU usage
echo "--- CPU Usage ---"
jdc monitor get-metric-data \
  --namespace jcs_for_redis \
  --metric-name cpu_usage \
  --dimensions "[{\"name\":\"instanceId\",\"value\":\"$INSTANCE_ID\"}]" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 300 \
  --output json | jq '.datapoints[-3:] | .[] | {timestamp: .timestamp, value: .value}'

echo ""

# Connections
echo "--- Connections ---"
jdc monitor get-metric-data \
  --namespace jcs_for_redis \
  --metric-name connected_clients \
  --dimensions "[{\"name\":\"instanceId\",\"value\":\"$INSTANCE_ID\"}]" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 300 \
  --output json | jq '.datapoints[-3:] | .[] | {timestamp: .timestamp, value: .value}'
```

## Monitoring Best Practices

### 1. Establish Baselines
- Monitor metrics for 1-2 weeks to establish normal patterns
- Document typical QPS, memory usage, connection counts
- Identify peak hours and seasonal patterns

### 2. Set Meaningful Thresholds
- Base thresholds on baselines, not arbitrary values
- Use percentile-based thresholds (P95, P99)
- Adjust thresholds as workload changes

### 3. Reduce Alert Fatigue
- Only alert on actionable issues
- Use different severity levels
- Implement alert grouping and deduplication
- Regular review and tuning of alert rules

### 4. Monitor Trends
- Track metric trends over time (days, weeks, months)
- Plan capacity based on growth trends
- Set up trend-based alerts (e.g., memory growing 5% daily)

### 5. Correlate Metrics
- Monitor multiple metrics together
- Correlate Redis metrics with application metrics
- Use dashboards for holistic view

### 6. Automate Responses
- Auto-scale based on metrics (if supported)
- Auto-restart on certain error conditions
- Auto-create tickets for critical alerts

## Integration with External Tools

### Grafana Integration

```json
{
  "datasource": "JD Cloud Monitor",
  "queries": [
    {
      "metric": "memory_usage",
      "namespace": "jcs_for_redis",
      "dimensions": {
        "instanceId": "jcs-redis-abc123"
      },
      "period": "300s"
    }
  ]
}
```

### Prometheus Integration

Use JD Cloud Monitor exporter to expose metrics to Prometheus:

```yaml
scrape_configs:
  - job_name: 'jdcloud-redis'
    scrape_interval: 60s
    static_configs:
      - targets: ['jdcloud-exporter:9090']
        labels:
          instance_id: 'jcs-redis-abc123'
```

## Incident Response Playbook

### Playbook 1: Memory Usage Critical

**Trigger**: Memory usage > 95%

**Steps:**
1. Check current memory usage and trends
2. Identify top keys by memory usage
3. Check for big keys or memory leaks
4. If temporary spike: monitor closely
5. If sustained: 
   - Delete unnecessary keys
   - Optimize data structures
   - Scale up instance
6. Verify memory usage returns to normal

### Playbook 2: High CPU Usage

**Trigger**: CPU usage > 85%

**Steps:**
1. Check slow logs for blocking commands
2. Identify high-frequency commands
3. Check for hot keys
4. Optimize application code:
   - Replace blocking commands
   - Use pipeline
   - Add local caching
5. If needed, scale up instance

### Playbook 3: Connection Exhaustion

**Trigger**: Connections > 95% of max

**Steps:**
1. Check connected clients
2. Identify clients with excessive connections
3. Check for connection leaks in application
4. Optimize connection pool settings
5. If needed, scale up instance or add read replicas

## Related Documentation

- [JD Cloud Cloud Monitor](https://docs.jdcloud.com/cn/cloudmonitor)
- [Redis Monitoring Metrics](https://docs.jdcloud.com/cn/jcs-for-redis/metrics)
- [Alert Configuration Guide](https://docs.jdcloud.com/cn/cloudmonitor/create-alarm)
