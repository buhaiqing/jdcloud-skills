# JD Cloud MongoDB Core Concepts

## What is JCS for MongoDB

JD Cloud MongoDB (JCS for MongoDB) is a high-performance NoSQL database service based on the globally popular MongoDB. It provides:

- **Automatic Disaster Recovery**: Built-in high availability architecture with automatic failover
- **Data Backup**: Automated backup and point-in-time recovery capabilities
- **Online Scaling**: Seamless specification changes without downtime
- **Instance Monitoring**: Real-time metrics and intelligent alerting
- **High Performance**: Document-oriented storage for flexible data models

MongoDB is widely used for content management, user data storage, IoT applications, real-time analytics, mobile backends, and catalog/inventory systems.

## Supported MongoDB Versions

| Version | Features | Status | Recommendation |
|---------|----------|--------|----------------|
| 3.6 | Basic features, transactions (multi-document), change events | Stable | Suitable for legacy applications |
| 4.0 | Enhanced transactions, retryable writes, improved performance | Stable | **Recommended** for new deployments |

> Note: JD Cloud MongoDB fully compatible with official MongoDB protocol. For MongoDB command reference, see [MongoDB Official Documentation](https://docs.mongodb.com/).

## Deployment Architectures

### 1. Replica Set (副本集)

**Architecture**: 3-node deployment with automatic failover

- **Primary Node**: Handles all write operations and reads (default)
- **Secondary Nodes**: Replicate data from primary, can serve read requests (read preference)
- **Hidden Node**: Optional, for backup/analytics, not visible to clients

**Benefits**:
- High availability with automatic failover (typically < 30 seconds)
- Data redundancy with 3 copies
- Read/write splitting for performance optimization
- Suitable for most production workloads

**Typical Use Cases**:
- E-commerce platforms
- Content management systems
- User profile storage
- Session management

### 2. Sharded Cluster (分片集群)

**Architecture**: Horizontal scaling with multiple shards

- **Mongos**: Query routers (2-32 nodes), distribute queries to appropriate shards
- **Shard**: Data partitions (2-32 shards), each shard is a 3-node replica set
- **Config Server**: Stores cluster metadata (3-node replica set)

**Benefits**:
- Horizontal scaling for massive data (TB+ scale)
- Higher throughput through parallel processing
- Transparent to applications (Mongos handles routing)
- Suitable for large-scale production systems

**Typical Use Cases**:
- Large-scale user systems (> 100M users)
- High-throughput logging systems
- Large product catalogs
- Time-series data storage

**Component Configuration**:
| Component | Min Nodes | Max Nodes | Recommended |
|-----------|-----------|-----------|-------------|
| Mongos | 2 | 32 | 2-3 for moderate load |
| Shard | 2 | 32 | 2-5 for most cases |
| Config Server | 3 (fixed) | 3 | Fixed at 3 |

### Architecture Comparison

| Aspect | Replica Set | Sharded Cluster |
|--------|-------------|-----------------|
| Max Data Size | Limited by single node (~TB) | Virtually unlimited (PB+) |
| Max Throughput | Limited by single primary | Scalable horizontally |
| Complexity | Simple | Moderate to complex |
| Cost | Lower | Higher |
| Suitable Scale | < 100M documents | > 100M documents |
| Use Case | Most applications | Large-scale systems |

## Instance Specifications

### Replica Set Specifications

| Spec Code | CPU | Memory | Max Connections | Storage Range | Use Case |
|-----------|-----|--------|-----------------|---------------|----------|
| mongodb.s.1.small | 1 vCPU | 2 GB | ~500 | 10-100 GB | Development, testing |
| mongodb.s.1.medium | 2 vCPU | 4 GB | ~1,000 | 10-500 GB | Small applications |
| mongodb.s.1.large | 4 vCPU | 8 GB | ~2,000 | 10-1000 GB | Medium applications |
| mongodb.s.2.large | 8 vCPU | 16 GB | ~4,000 | 10-2000 GB | Large applications |
| mongodb.s.2.xlarge | 16 vCPU | 32 GB | ~8,000 | 10-3000 GB | High-performance systems |
| mongodb.s.4.xlarge | 32 vCPU | 64 GB | ~16,000 | 10-5000 GB | Enterprise systems |

> Note: Specifications may vary by region. Use `jdc mongodb describe-flavors` to query available specs.

### Sharded Cluster Specifications

Each component (Mongos, Shard, Config Server) can be configured independently:

- **Mongos Specs**: CPU/Memory for query routing
- **Shard Specs**: CPU/Memory/Storage for data storage
- **Config Server Specs**: Fixed specs for metadata management

## Networking and Security

### VPC (Virtual Private Cloud)

- MongoDB instances deployed in user-defined VPC
- Network isolation from other tenants
- Low-latency internal network access
- Custom IP address ranges and subnets

### Connection Methods

- **Internal Endpoint**: Access from JD Cloud VMs in same VPC (recommended)
  - Connection string: `mongodb://user:pass@domain:port/database`
  - Domain remains stable during failover
- **Public Endpoint**: Access from internet (requires enabling)
  - Not recommended for production due to security risks
  - Higher latency than internal access

### IP Whitelist (白名单)

- Controls which IP addresses can access MongoDB
- Supports CIDR notation (e.g., 192.168.1.0/24)
- Default: no whitelist (all access blocked until configured)
- Best practice: Only allow application server IPs

### Password Authentication

- Required for all instances by default
- Supports complex passwords (letters + numbers + special characters)
- Can be reset without recreating instance
- Password changes disconnect existing clients

### IAM Access Control

- Fine-grained permissions for MongoDB operations
- Supports RAM roles and policies
- Implement least-privilege principle
- Separate read/write/admin permissions

## Data Persistence and Backup

### Storage Engine

- **WiredTiger**: Default and only supported storage engine
- Document-level concurrency control
- Compression support for storage efficiency
- Checkpoint-based persistence

### Backup Types

#### Automated Backup

- Daily full backups (default: 7-day retention)
- Backup files stored with 3-copy redundancy
- Configurable retention period (7-732 days)
- Backups stored in cloud object storage

#### Manual Backup

- On-demand backup creation
- Retention period configurable (up to 732 days)
- Suitable for pre-change snapshots
- Downloadable for offline analysis

#### Cross-Region Backup

- Backup synchronization across regions
- Disaster recovery preparation
- Create new instance from cross-region backup
- Additional storage costs apply

### Restore Options

- **Restore to Current Instance**: Replace current data with backup
- **Create New Instance from Backup**: Clone to new instance
- **Point-in-Time Recovery**: Restore to specific timestamp (if enabled)

## Instance Lifecycle

### State Transitions

```
Creating → Running ↔ Changing (resize/config)
              ↓
          Restoring
              ↓
          Restarting
              ↓
          Deleting → Deleted
```

### Main States

| State | Description | Available Actions |
|-------|-------------|-------------------|
| creating | Instance provisioning | None |
| running | Normal operation | Resize, backup, restart, modify, delete |
| changing | Spec/config modification | None |
| restoring | Data restoration | None |
| restarting | Service restart | None |
| deleted | Instance deleted | None |
| error | Error state | Contact support |

## High Availability Features

### Automatic Failover

- Primary failure → automatic election of new primary
- Failover time: typically < 30 seconds
- Client connections automatically redirected (via stable domain)
- Zero data loss with proper write concern

### Multi-AZ Deployment

- Nodes distributed across different availability zones
- Protection against AZ-level failures
- Cross-AZ replication for disaster recovery
- Slightly higher latency due to cross-AZ network

### Data Consistency

- **Strong Consistency**: Reads from primary (default)
- **Eventual Consistency**: Reads from secondaries (read preference)
- **Write Concern**: Configurable durability level (w1, w2, wmajority)
- **Read Preference**: primary, primaryPreferred, secondary, nearest

## Performance Optimization

### Index Strategy

- Create indexes for frequent queries
- Use compound indexes for multi-field queries
- Monitor index usage and remove unused indexes
- Avoid over-indexing (impacts write performance)

### Query Optimization

- Use covered queries (index-only)
- Avoid `$where` and JavaScript expressions
- Use projection to limit returned fields
- Batch operations with bulk write API

### Connection Pooling

- Use MongoDB drivers with connection pooling
- Configure pool size based on concurrency
- Typical pool size: 50-200 connections per application instance
- Monitor connection usage

### Memory Management

- WiredTiger cache size: ~50% of system memory (default)
- Working set should fit in cache for optimal performance
- Monitor cache hit rate
- Avoid document growth (update-in-place)

## Security Best Practices

1. **Enable IP Whitelist**: Only allow application server IPs
2. **Strong Password**: Use complex passwords, rotate regularly
3. **VPC Deployment**: Never use public endpoint for production
4. **Enable Auth**: Always run with authentication enabled (default)
5. **Least Privilege**: Create dedicated users per application with minimal permissions
6. **Audit Logging**: Monitor access patterns and anomalies
7. **TLS/SSL**: Enable encryption in transit for sensitive data
8. **Backup Encryption**: Ensure backup data is encrypted

## Common Use Cases

### 1. Content Management

- Flexible schema for diverse content types
- Rich query capabilities for content search
- Horizontal scaling for large catalogs
- Example: product catalogs, article repositories

### 2. User Profile Management

- Document model fits user profiles naturally
- Flexible schema evolution without migrations
- High read throughput for profile lookups
- Example: social platforms, e-commerce users

### 3. Real-Time Analytics

- Aggregation framework for complex analytics
- High write throughput for event ingestion
- Time-series data patterns
- Example: user behavior tracking, IoT metrics

### 4. Mobile Backend

- JSON-native document model (mobile-friendly)
- Offline sync patterns with change streams
- Geospatial queries for location-based features
- Example: mobile apps, location services

### 5. Session Store

- TTL indexes for automatic session expiration
- High read/write throughput
- Flexible session data structure
- Example: web application sessions

## Related Services

- **SmartDBA**: Database autonomous service for performance analysis
- **Cloud Monitor**: Instance monitoring and alerting
- **DTS (Data Transmission Service)**: Data migration and synchronization
- **VPC**: Network isolation and security
- **VM**: Application servers connecting to MongoDB
- **Object Storage**: Backup file storage