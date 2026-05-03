# Monitoring JD Cloud MongoDB

## Monitoring Architecture

JD Cloud MongoDB provides comprehensive monitoring through:

1. **Built-in Monitoring**: Basic metrics collected automatically
2. **Cloud Monitor Service**: Centralized monitoring dashboard
3. **SmartDBA**: Advanced database performance analysis
4. **Custom Alerts**: User-defined alert rules

## Key Metrics

### Instance-Level Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| CPU Usage | `mongodb.cpu.usage` | % | CPU utilization across all nodes |
| Memory Usage | `mongodb.memory.usage` | % | Memory utilization |
| Disk Usage | `mongodb.disk.usage` | % | Disk space utilization |
| Connections | `mongodb.connections.current` | Count | Current active connections |
| Connection Usage | `mongodb.connections.usage` | % | Connection usage vs max connections |
| QPS (Query Per Second) | `mongodb.qps.total` | Count/s | Total queries per second |
| OPS (Operations Per Second) | `mongodb.ops.total` | Count/s | Total operations per second |

### Replica Set Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| Replica Lag | `mongodb.replication.lag` | Seconds | Replication delay between primary and secondary |
| Replica Status | `mongodb.replication.status` | Status | Health status of replica set |
| Oplog Size | `mongodb.oplog.size` | MB | Operation log size |
| Oplog Window | `mongodb.oplog.window` | Hours | Oplog time coverage |

### Storage Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| Data Size | `mongodb.data.size` | GB | Actual data size |
| Index Size | `mongodb.index.size` | GB | Index storage size |
| Storage Size | `mongodb.storage.size` | GB | Total storage used |
| Document Count | `mongodb.document.count` | Count | Total documents |

### Network Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| Network In | `mongodb.network.in` | KB/s | Network inbound traffic |
| Network Out | `mongodb.network.out` | KB/s | Network outbound traffic |
| Network Throughput | `mongodb.network.throughput` | KB/s | Total network traffic |

### Performance Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| Slow Query Count | `mongodb.slowquery.count` | Count | Number of slow queries |
| Average Query Time | `mongodb.query.time.avg` | ms | Average query execution time |
| Cache Hit Rate | `mongodb.cache.hitrate` | % | WiredTiger cache hit percentage |
| Lock Wait Time | `mongodb.lock.waittime` | ms | Time spent waiting for locks |

### Sharded Cluster Metrics (for sharding deployments)

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| Shard Balance Status | `mongodb.sharding.balance` | Status | Chunk balancer status |
| Chunk Count | `mongodb.sharding.chunks` | Count | Number of chunks per shard |
| Mongos Connections | `mongodb.mongos.connections` | Count | Connections per Mongos |

## Recommended Alerts

### Critical Alerts (Immediate Action)

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| CPU Usage | > 90% | 5 min | Scale up or optimize queries immediately |
| Memory Usage | > 95% | 5 min | Scale up or reduce working set |
| Disk Usage | > 90% | 5 min | Add storage or archive data immediately |
| Replica Lag | > 60s | 5 min | Check replication health, reduce write load |
| Connection Usage | > 95% | 5 min | Scale up or implement connection pooling |
| Instance Status | != running | 1 min | Check instance, contact support if error |

### Warning Alerts (Proactive Monitoring)

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| CPU Usage | > 80% | 15 min | Review queries, plan scaling |
| Memory Usage | > 85% | 15 min | Monitor working set, consider scaling |
| Disk Usage | > 80% | 15 min | Plan storage expansion or data cleanup |
| Replica Lag | > 10s | 15 min | Monitor replication, check network |
| Slow Query Count | > 10/min | 15 min | Analyze slow queries, optimize |
| Connection Usage | > 80% | 15 min | Monitor connections, plan pooling |
| Cache Hit Rate | < 90% | 15 min | Working set too large, consider scaling |

## Setting Up Alerts

### Via Cloud Monitor Console

1. **Access Cloud Monitor**: JD Cloud Console → Cloud Monitor
2. **Navigate to MongoDB**: Resource Monitoring → Database → MongoDB
3. **Select Instance**: Click instance ID to view metrics
4. **Create Alert Rule**: Click "Create Alert Rule"
5. **Configure Alert**:
   - Metric: Select from dropdown
   - Threshold: Set threshold value
   - Duration: Set evaluation period
   - Notification: Configure contact methods (SMS, email, webhook)

### Via CLI (if supported)

```bash
# Example: Create CPU alert (syntax may vary by region)
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --resource-id mongodb-xxxx \
  --metric mongodb.cpu.usage \
  --threshold 90 \
  --period 300 \
  --evaluation-count 1 \
  --alarm-name mongodb-cpu-high \
  --output json
```

## Monitoring Dashboard

### Key Panels to Create

1. **Resource Overview**
   - CPU, Memory, Disk usage (gauges)
   - Current connections vs max
   - Instance status indicator

2. **Performance Overview**
   - QPS and OPS trends (line chart)
   - Average query time trend
   - Slow query count trend

3. **Replica Set Health** (for replica deployments)
   - Replica lag trend
   - Node status matrix
   - Oplog window

4. **Storage Analysis**
   - Data size vs index size
   - Storage growth trend
   - Document count trend

5. **Network Traffic**
   - Inbound/outbound throughput
   - Traffic patterns over time

## SmartDBA Integration

### Features

- **Slow Query Analysis**: Identify and analyze slow queries
- **Performance Insights**: Visual query performance breakdown
- **Index Recommendations**: Suggest optimal indexes
- **Space Analysis**: Detailed storage usage breakdown
- **Session Analysis**: Connection and session diagnostics

### Access SmartDBA

1. **From Instance List**: Click "Performance" link
2. **Navigate to SmartDBA**: Automatic redirect to SmartDBA console
3. **Select Feature**: Choose analysis type (slow queries, space, etc.)

### Slow Query Analysis

**Metrics captured**:
- Query execution time
- Query pattern (normalized)
- Collection/database
- Execution count
- Average/max/min time

**Actions**:
- Identify top slow queries
- View query execution plan
- Get index recommendations
- Export slow query log

## Performance Tuning via Metrics

### CPU Optimization

**If CPU usage high (>80%)**:

1. **Check slow queries**: Use SmartDBA to identify slow queries
2. **Add indexes**: Create indexes for frequent queries
3. **Optimize queries**: Use projection, avoid `$where`
4. **Review write operations**: Batch writes, use bulk operations
5. **Scale up**: Increase CPU cores

### Memory Optimization

**If memory usage high (>85%)**:

1. **Check working set**: Verify active data fits in cache
2. **Add indexes**: Reduce document scanning
3. **Reduce document size**: Remove unused fields
4. **Scale up**: Increase memory allocation
5. **Configure WiredTiger cache**: Adjust cache size if needed

### Connection Optimization

**If connection usage high (>80%)**:

1. **Implement connection pooling**: Use MongoDB driver pools
2. **Review application connection logic**: Avoid creating new connections per request
3. **Set max pool size**: Configure appropriate pool size
4. **Scale up**: Increase max connections via spec upgrade
5. **Monitor connection leaks**: Check for unclosed connections

### Disk Optimization

**If disk usage high (>80%)**:

1. **Archive old data**: Implement TTL indexes
2. **Remove unused indexes**: Drop indexes not used
3. **Compact collections**: Run compact command (if supported)
4. **Scale up storage**: Increase storage allocation
5. **Review document structure**: Reduce document overhead

### Query Performance Optimization

**If slow queries increasing**:

1. **Analyze query patterns**: Use SmartDBA
2. **Create covering indexes**: Include all queried fields
3. **Use projection**: Return only needed fields
4. **Avoid expensive operations**: `$where`, large `$lookup`
5. **Batch operations**: Use bulk write for multiple ops

## Monitoring Best Practices

### 1. Baseline Metrics

- Establish baseline metrics during normal operation
- Compare current metrics against baseline
- Identify anomalies quickly

### 2. Trend Analysis

- Monitor trends over time (daily, weekly, monthly)
- Plan capacity based on growth trends
- Identify seasonal patterns

### 3. Alert Testing

- Test alert notifications regularly
- Verify alert thresholds are appropriate
- Tune thresholds based on experience

### 4. Comprehensive Coverage

- Monitor all critical instances
- Set up alerts for all critical metrics
- Review and update monitoring periodically

### 5. Integration with Incident Response

- Link alerts to incident response procedures
- Automate common remediation actions
- Escalate to support when needed

## Integration with jdcloud-cloudmonitor-ops

For advanced monitoring operations:

1. **Query Metrics Data**: Use Cloud Monitor APIs
2. **Create Custom Dashboards**: Build composite views
3. **Configure Advanced Alerts**: Set up multi-condition alerts
4. **Export Metrics**: Download historical data for analysis

**Delegation Rule**: For monitoring metrics queries, alert configuration, and dashboard management, delegate to `jdcloud-cloudmonitor-ops` skill.

## Related Documentation

- [Core Concepts](core-concepts.md)
- [Troubleshooting](troubleshooting.md)
- [API & SDK Usage](api-sdk-usage.md)
- [CLI Usage](cli-usage.md)