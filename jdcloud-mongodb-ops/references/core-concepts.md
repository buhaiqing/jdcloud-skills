# Core Concepts — MongoDB

## Product Overview

JD Cloud MongoDB is a fully managed document database service compatible with MongoDB protocol. It provides enterprise-grade reliability, security, and performance for modern applications.

### Key Features

| Feature | Description |
|---------|-------------|
| **Compatibility** | Fully compatible with MongoDB protocol (versions 4.0, 4.2, 4.4, 5.0, 6.0) |
| **High Availability** | Automatic failover with replica sets (3-node minimum) |
| **Elastic Scaling** | Vertical scaling (instance class) and horizontal scaling (add nodes) |
| **Backup & Recovery** | Automated backups with point-in-time recovery |
| **Security** | VPC isolation, IP whitelisting, SSL/TLS encryption |
| **Monitoring** | CloudMonitor integration for metrics and alarms |

## Architecture Patterns

### Replica Set

Default and recommended architecture for most workloads.

```
Primary Node  ←→  Secondary Node  ←→  Secondary Node
   (Write)           (Read)              (Read)
```

- **Minimum**: 3 nodes (1 primary + 2 secondaries)
- **Automatic failover**: If primary fails, a secondary is promoted
- **Read scaling**: Route read queries to secondaries

### Sharded Cluster

For very large datasets or high write throughput.

```
                    mongos (Query Router)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    Shard 1           Shard 2           Shard 3
  (Replica Set)    (Replica Set)    (Replica Set)
```

- **Components**: mongos routers, config servers, shard nodes
- **Use case**: Data > 2TB or write throughput > 10,000 ops/sec

## Instance Lifecycle States

| State | Description | Allowed Operations |
|-------|-------------|-------------------|
| `creating` | Instance is being provisioned | Describe only |
| `running` | Instance is active | All operations |
| `modifying` | Configuration change in progress | Describe only |
| `backing_up` | Backup in progress | Describe only |
| `restoring` | Restore in progress | Describe only |
| `deleting` | Instance is being deleted | Describe only |
| `deleted` | Instance has been deleted | None (404 on describe) |

## Storage Types

| Type | Use Case | Performance |
|------|----------|-------------|
| **Local SSD** | High-performance workloads | Highest IOPS, lowest latency |
| **Cloud Disk** | General purpose, cost-effective | Balanced performance |

## Instance Classes

Instance classes follow the pattern: `mongodb.{family}.{size}`

| Class | vCPU | Memory | Typical Use Case |
|-------|------|--------|------------------|
| mongodb.s1.small | 1 | 2 GB | Development, testing |
| mongodb.s1.medium | 2 | 4 GB | Small production |
| mongodb.s1.large | 4 | 8 GB | Medium production |
| mongodb.s1.xlarge | 8 | 16 GB | Large production |
| mongodb.s2.xlarge | 8 | 32 GB | Memory-intensive |
| mongodb.s2.2xlarge | 16 | 64 GB | High-performance |

## Connection String Format

### Replica Set Connection

```
mongodb://username:password@host1:27017,host2:27017,host3:27017/database?replicaSet=rs0
```

### Single Node Connection

```
mongodb://username:password@host:27017/database
```

## Security Model

### Network Security

1. **VPC Isolation**: Instances deployed in user's VPC
2. **Subnet**: Private subnet recommended
3. **Security Group**: Control inbound/outbound traffic
4. **IP Whitelist**: Restrict access by source IP

### Authentication

- **Database User**: Username/password per database
- **Role-Based Access**: Read-only, read-write, admin roles
- **SCRAM Authentication**: Default authentication mechanism

### Encryption

- **In-Transit**: SSL/TLS encryption for connections
- **At-Rest**: Disk encryption (automatic)

## Cross-Skill Dependencies

| Dependency | Skill | When Needed |
|------------|-------|-------------|
| VPC/Subnet | `jdcloud-vpc-ops` | Creating new instances |
| Security Groups | `jdcloud-vpc-ops` | Network access control |
| Monitoring | `jdcloud-cloudmonitor-ops` | Metrics and alarms |
| IAM | `jdcloud-iam-ops` | Access control policies |
