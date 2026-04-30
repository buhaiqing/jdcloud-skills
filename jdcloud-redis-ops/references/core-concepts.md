# JD Cloud Redis Core Concepts

## What is JCS for Redis

JD Cloud Cache Redis (JCS for Redis) is a high-performance online caching service based on the Redis protocol. It provides:

- **Automatic Disaster Recovery**: Master-slave architecture with automatic failover
- **Data Backup**: Automated backup and point-in-time recovery
- **Online Scaling**: Seamless configuration changes without downtime
- **Instance Monitoring**: Real-time metrics and alerting
- **High Performance**: In-memory data store supporting millions of QPS

Redis is widely used for caching, session management, leaderboards, message queues, and real-time analytics.

## Core Components

### 1. Instance Architecture

#### Standalone (单节点)
- Single node deployment
- Suitable for development and testing
- No high availability guarantee
- Lower cost

#### Master-Slave (主从)
- Master node + one or more replica nodes
- Automatic failover if master fails
- Read/write splitting support
- Recommended for production workloads

#### Cluster (集群)
- Multiple shards with data partitioning
- Horizontal scaling support
- Higher throughput and capacity
- Suitable for large-scale production systems

### 2. Instance Specifications

JD Cloud Redis provides various instance classes:

| Spec Code | Memory | Max Connections | Bandwidth | Use Case |
|-----------|--------|-----------------|-----------|----------|
| redis.sw.1g | 1 GB | 10,000 | 96 Mbps | Small applications |
| redis.sw.2g | 2 GB | 10,000 | 96 Mbps | Medium applications |
| redis.sw.4g | 4 GB | 20,000 | 192 Mbps | Large applications |
| redis.sw.8g | 8 GB | 20,000 | 192 Mbps | High-traffic services |
| redis.sw.16g | 16 GB | 40,000 | 384 Mbps | Enterprise applications |
| redis.sw.32g | 32 GB | 40,000 | 384 Mbps | Large-scale caching |

> Note: Specifications may vary by region. Use `jdc redis describe-spec-config` to query available specs.

### 3. Redis Versions

| Version | Features | Status |
|---------|----------|--------|
| 4.0 | Basic Redis features, cluster support | Stable |
| 5.0 | Streams, enhanced modules | Stable, Recommended |
| 6.2 | ACL, client caching, string commands | Latest, Recommended |

### 4. Networking

#### VPC (Virtual Private Cloud)
- Redis instances are deployed in VPC
- Logically isolated network environment
- Customizable IP address range and subnets
- Low-latency internal network access

#### Connection Methods
- **Internal Endpoint**: Access from JD Cloud VMs in the same VPC (recommended)
- **Public Endpoint**: Access from internet (requires enabling, not recommended for production)
- **Domain Name**: Stable connection domain that remains unchanged during failover

### 5. Security

#### Whitelist (IP White List)
- Controls which IPs can access the Redis instance
- Supports CIDR notation (e.g., 192.168.1.0/24)
- Default: no whitelist (deny all)
- Best practice: only allow specific application server IPs

#### Password Authentication
- Required by default for all instances
- Supports complex passwords (letters + numbers + special characters)
- Can be reset without recreating instance
- Password changes disconnect existing clients

#### IAM Access Control
- Fine-grained permissions for Redis operations
- Supports RAM roles and policies
- Implement least-privilege principle

### 6. Data Persistence

#### RDB (Redis Database)
- Snapshot-based persistence
- Configurable save intervals
- Point-in-time recovery
- Used for backup and restore

#### AOF (Append Only File)
- Command log-based persistence
- Higher data durability
- Can be enabled/disabled online
- Larger file size than RDB

#### Backup Policy
- Automated daily backups
- Retention period: 7-732 days
- Manual backup on-demand
- Download backup files for offline analysis

## Instance Lifecycle

### State Transitions

```
Creating → Running ↔ Restarting
               ↓
           Changing (resizing)
               ↓
           Deleting → Deleted
```

### Main States

| State | Description | Operable Actions |
|-------|-------------|------------------|
| creating | Instance being provisioned | None |
| running | Instance running normally | Resize, backup, restart, delete, modify config |
| changing | Configuration change in progress | None |
| restarting | Instance restarting | None |
| deleted | Instance deleted | None |
| error | Instance in error state | Contact support |

## Billing Models

### By Payment Method

1. **Pay-As-You-Go (按配置计费)**
   - Billed hourly based on instance specifications
   - Suitable for short-term or variable workloads
   - Can be released at any time
   - Higher unit price

2. **Subscription (包年包月)**
   - Monthly or yearly billing
   - Suitable for long-term stable workloads
   - More cost-effective (up to 30% discount)
   - Cannot be canceled mid-term

### Billing Items

- Instance specifications (memory size)
- Architecture type (standalone, master-slave, cluster)
- Backup storage (if exceeds free quota)
- Public network bandwidth (if enabled)

## High Availability Architecture

### Master-Slave Replication
- Synchronous replication from master to slave
- Automatic failover within seconds
- No data loss during failover (with AOF enabled)
- Transparent to applications (stable domain name)

### Cluster Sharding
- Data distributed across multiple shards using hash slots
- Each shard has master-slave replication
- Horizontal scaling by adding shards
- Clients support cluster mode (JedisCluster, RedisCluster)

### Multi-AZ Deployment
- Deploy master and slave in different availability zones
- Protection against AZ-level failures
- Slightly higher latency due to cross-AZ replication
- Recommended for critical production workloads

## Performance Optimization

### 1. Avoid Big Keys
- Keys with large values (>10KB) or many elements (>10,000)
- Causes blocking operations and memory fragmentation
- Use `SCAN` instead of `KEYS *`
- Monitor with big key analysis feature

### 2. Avoid Hot Keys
- Keys accessed very frequently (>10,000 QPS)
- Causes single-node bottleneck
- Use local caching for hot keys
- Monitor with hot key analysis feature

### 3. Connection Pooling
- Use connection pools (JedisPool, Lettuce pool)
- Avoid creating new connections per request
- Configure pool size based on concurrency
- Typical pool size: 2-4x concurrent threads

### 4. Pipeline & Transactions
- Use pipeline for batch operations
- Reduce network round-trips
- MULTI/EXEC for atomic operations
- Avoid long transactions (blocking)

### 5. Memory Management
- Configure `maxmemory` appropriately
- Set eviction policy: `allkeys-lru` (recommended)
- Monitor memory usage regularly
- Avoid memory fragmentation

## Security Best Practices

1. **Enable Whitelist**: Only allow application server IPs
2. **Strong Password**: Use complex passwords, rotate regularly
3. **Disable Dangerous Commands**: FLUSHALL, FLUSHDB, KEYS, CONFIG
4. **Private Network Only**: Avoid public endpoints for production
5. **IAM Policies**: Implement least-privilege access control
6. **Encryption in Transit**: Use TLS for sensitive data (if supported)
7. **Audit Logs**: Monitor access patterns and anomalies

## Common Use Cases

### 1. Session Cache
- Store user session data
- Fast read/write with TTL
- Horizontal scaling support
- Example: web application sessions

### 2. Leaderboard / Ranking
- Sorted Sets for real-time rankings
- ZADD, ZRANGE, ZINCRBY commands
- Low latency updates
- Example: gaming leaderboards, content ranking

### 3. Message Queue
- List data structure (LPUSH, RPOP)
- Pub/Sub for event-driven architecture
- Streams for reliable messaging (Redis 5.0+)
- Example: notification system, task queue

### 4. Distributed Lock
- SET with NX and EX options
- Redlock algorithm for multi-node
- Prevent concurrent access
- Example: inventory management, order processing

### 5. Real-time Analytics
- Counters (INCR, INCRBY)
- HyperLogLog for unique visitors
- Bitmap for user behavior tracking
- Example: page views, active users

## Monitoring & Alerting

### Key Metrics
- **Memory Usage**: Current memory / max memory (%)
- **CPU Utilization**: Instance CPU usage (%)
- **Connections**: Current connected clients
- **QPS**: Queries per second
- **Hit Rate**: Cache hit ratio (%)
- **Replication Lag**: Master-slave replication delay (seconds)

### Recommended Alerts
| Metric | Threshold | Severity |
|--------|-----------|----------|
| Memory Usage | > 85% | Warning |
| Memory Usage | > 95% | Critical |
| CPU Utilization | > 80% | Warning |
| Connections | > 80% of max | Warning |
| Replication Lag | > 10s | Warning |
| Replication Lag | > 60s | Critical |

## Related Services

- **Cloud Monitor**: Monitor Redis metrics and set alerts
- **DTS (Data Transmission Service)**: Migrate data to/from Redis
- **VM (Cloud Host)**: Application servers accessing Redis
- **VPC**: Network isolation and security
- **CLB (Load Balancer)**: Distribute traffic across application servers
- **JCS for Memcached**: Alternative caching service for simple use cases
