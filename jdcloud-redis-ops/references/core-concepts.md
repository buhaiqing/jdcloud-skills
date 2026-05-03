# JD Cloud Redis Core Concepts

## What is JD Cloud Redis (分布式缓存)

JD Cloud Redis (分布式缓存/云缓存 Redis) is a high-performance, distributed cache service fully compatible with open-source Redis protocol. It provides elastic, scalable, and reliable caching with automatic failover, data backup, and online scaling capabilities. Built on JD Cloud's infrastructure, it delivers high throughput, low latency, and enterprise-grade reliability tested through JD's major promotional events.

## Instance Architecture Types

JD Cloud Redis supports three architecture types to meet different business requirements:

### 1. Standard Version (master-slave)

- **Architecture**: Single-shard master-slave replication
- **Use Cases**: Small-scale applications, development/testing, personal learning, small websites
- **Features**:
  - Memory capacity: 1GB - 32GB
  - High availability with master-slave hot standby
  - Automatic failover when master fails
  - Suitable for scenarios with moderate QPS requirements
- **Instance Type Code**: `master-slave`

### 2. Proxy Cluster Version (cluster)

- **Architecture**: Proxy-based distributed cluster with multiple shards behind proxy layer
- **Use Cases**: Mid-to-large scale internet applications, high-concurrency scenarios
- **Features**:
  - Memory capacity: 4GB - 4TB (up to 128 shards)
  - Proxy layer handles request routing and load balancing
  - Smooth scaling without service interruption
  - Supports 16-256 DBs
  - Suitable for scenarios requiring large capacity and high throughput
- **Instance Type Code**: `cluster`

### 3. Native Cluster Version (native-cluster)

- **Architecture**: Redis Cluster (open-source native cluster architecture)
- **Use Cases**: Large-scale applications requiring direct connection, ultra-low latency
- **Features**:
  - Memory capacity: 3GB - 2TB (up to 128 shards)
  - Direct client connection to Redis nodes (bypass proxy)
  - Lower latency, higher performance
  - Full Redis Cluster protocol compatibility
  - Optional SmartProxy for compatibility with non-cluster-aware clients
- **Instance Type Code**: `native-cluster`

## Redis Versions

JD Cloud Redis supports multiple versions:

| Version | Status | Features |
|---------|--------|----------|
| Redis 2.8 | Deprecated | No longer sold, existing instances maintained |
| Redis 4.0 | Available | Stable, widely used, supports Stream data type |
| Redis 5.0 | Available | Enhanced Stream, new data structures |
| Redis 6.2 | Available | Latest features, improved performance, ACL enhancements |

**Note**: Version cannot be changed after instance creation. To upgrade, create a new instance and migrate data.

## Core Components

### 1. Shards (分片)

- Basic unit of data storage in cluster architectures
- Each shard contains master and replica nodes
- Data is distributed across shards via hash slots
- More shards = higher total QPS capacity and bandwidth

### 2. Replicas (副本)

- Master node: handles read/write operations
- Slave/Replica node: replicates master data, provides read scaling and failover
- Default: 2 replicas (1 master + 1 slave) for high availability
- Single replica (1 master only) available for small instances (<1GB), but no HA guarantee

### 3. VPC and Subnet

- Redis instances must be created within a VPC
- Subnet must have sufficient IP addresses for instance nodes
- Internal network access for security and performance
- Optional public network access via specific configuration

### 4. Availability Zones

- Master and slave can be placed in different AZs for cross-AZ HA
- AzIdSpec defines AZ placement strategy:
  - `SpecifyByReplicaGroup`: Specify AZ for each replica group
  - `SpecifyByCluster`: Specify AZ range for entire cluster

## Instance Specifications

### Memory and Performance

Specifications are determined by:
- **Memory capacity**: Per-shard memory size
- **CPU cores**: Processing power per shard
- **Bandwidth**: Network throughput limit
- **Connection limit**: Maximum concurrent connections
- **QPS**: Queries per second capacity

### Common Spec Codes

Standard version examples:
- `redis.micro`: 1GB memory
- `redis.small`: 2GB memory
- `redis.medium`: 4GB memory
- `redis.large`: 8GB memory

Cluster version examples:
- `redis.cluster.g.micro`: Cluster, 1GB per shard
- `redis.cluster.g.small`: Cluster, 2GB per shard

Use `describeInstanceClass` or `describeSpecConfig` API to query available specs.

## Instance Lifecycle

### Instance States

| State | Description | Operable Actions |
|-------|-------------|------------------|
| Creating | Instance being provisioned | None (wait) |
| Running | Instance operational | Modify, backup, restart, delete |
| Modifying | Configuration change in progress | None (wait) |
| Error | Instance creation or operation failed | Delete, retry |
| Deleted | Instance terminated | None |

### State Transitions

```
Creating → Running ↔ Modifying
              ↓
           Error
              ↓
           Deleted
```

## Billing Models

### 1. Pay-As-You-Go (postpaid_by_duration)

- Billed by hour based on instance configuration
- Suitable for short-term testing, fluctuating workloads
- Can be released at any time
- Higher unit price compared to subscription

### 2. Subscription (prepaid_by_duration)

- Monthly or yearly subscription
- Suitable for long-term stable workloads
- More cost-effective (discounts for longer terms)
- Can purchase up to 3 years
- Cannot cancel at any time (committed period)

### Billing Items

- Instance specifications (memory, CPU, shard count)
- Storage (if applicable)
- Network bandwidth
- Backup storage (optional)

## High Availability and Disaster Recovery

### Automatic Failover

- Master-slave architecture ensures HA
- Automatic detection of master failure
- Slave promotes to master within seconds
- Service interruption minimized (<30s typically)

### Cross-AZ Deployment

- Deploy master and slave in different AZs
- Protect against AZ-level failures
- Same-region cross-AZ network is low-latency
- Recommended for production environments

### Data Persistence

- AOF (Append-Only File) persistence available
- RDB snapshots via backup feature
- Persistence can be enabled on slave nodes
- Backup retention configurable

## Security Features

### 1. VPC Isolation

- Instances run in user's VPC
- Network isolation from other tenants
- Access controlled by subnet and security groups

### 2. IP Whitelist

- Control which IPs can connect to Redis
- Modify via `modifyIpWhiteList` API
- Supports both VPC and public IPs

### 3. Password Authentication

- Redis password for client authentication
- Reset via `resetCacheInstancePassword` API
- IAM accounts with granular permissions (Redis 6.2+)

### 4. Command Restriction

- Disable dangerous commands (FLUSHALL, KEYS, etc.)
- Configure via `setDisableCommands` API
- Protect against accidental data loss

## Performance Optimization

### Hot Key and Big Key Analysis

- Identify frequently accessed keys (hot keys)
- Find oversized keys (big keys) affecting performance
- Use `createCacheAnalysis` and `createBigKeyAnalysis` APIs
- Regular analysis helps optimize data structure

### Slow Log Analysis

- Query slow operations via `describeSlowLog` API
- Identify performance bottlenecks
- Optimize slow commands or data structures

### Connection Pool Optimization

- Use connection pooling for high-concurrency clients
- Properly configure pool size based on instance connection limit
- Refer to best practices for JedisPool, Lettuce, etc.

## Data Migration

### Migration Tools

- **RDTS**: JD Cloud's dedicated migration tool for Redis
- **redis-cli**: For offline data import
- **Third-party tools**: Support for open-source migration tools

### Migration Strategies

- Online migration: Minimal downtime
- Offline migration: Full data export/import
- Verify data consistency after migration

## Monitoring and Alerts

### Key Metrics

- CPU utilization
- Memory usage
- Connection count
- QPS (queries per second)
- Network bandwidth
- Slow log count

### Alert Configuration

- Set thresholds via Cloud Monitor
- Multiple notification channels
- Proactive alerting for anomalies

## Common Use Cases

### 1. Session Cache

- Store user session data
- Fast retrieval for web applications
- Reduce database load

### 2. Data Cache

- Cache frequently queried data
- Reduce database query pressure
- Improve response time

### 3. Message Queue

- Lightweight message queue via Redis List
- Pub/Sub for event notification
- Not suitable for heavy messaging (use dedicated MQ)

### 4. Real-time Leaderboard

- Use Redis Sorted Set for rankings
- Real-time updates and queries
- Gaming, e-commerce scenarios

### 5. Inventory Management

- High-concurrency inventory updates
- Atomic operations prevent overselling
- E-commerce flash sales scenarios

## Related Services

- **VPC**: Network isolation and subnet management
- **Cloud Monitor**: Instance monitoring and alerts
- **Object Storage**: Backup data storage
- **Cloud Host**: Application servers connecting to Redis
- **DTS**: Data migration service

## Limits and Quotas

### Resource Limits

- Maximum shards: 128 (cluster versions)
- Maximum memory: 4TB (Proxy cluster), 2TB (Native cluster)
- Maximum DBs: 256 (depends on architecture)
- Maximum connection: depends on spec (up to 60,000)

### Quota Checks

- Use `describeUserQuota` API to check resource quotas
- Request quota increase if needed
- Regional quotas may vary