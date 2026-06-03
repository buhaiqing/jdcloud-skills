# Core Concepts - JD Cloud Elasticsearch

## Service Overview

JD Cloud Elasticsearch (云搜索Elasticsearch) is a fully managed, distributed search and analytics engine service based on the open-source Elasticsearch project. It provides:

- **Full-text search**: Powerful text search capabilities with relevance scoring
- **Real-time analytics**: Aggregations and metrics for data analysis
- **Log analytics**: Centralized logging solution with Kibana visualization
- **Application monitoring**: APM (Application Performance Monitoring) capabilities
- **Security features**: VPC isolation, IP whitelisting, encryption at rest and in transit

## Key Concepts

### Instance
An Elasticsearch instance represents a complete ES cluster deployment, including data nodes, master nodes, and optional Kibana node.

### Node Types

| Node Type | Description | Recommended Count |
|-----------|-------------|-------------------|
| **Data Node** | Stores data and executes CRUD and search operations | Minimum 2 for HA, 3+ recommended |
| **Master Node** | Manages cluster-wide operations and metadata | 3 (mandatory for production) |
| **Kibana Node** | Provides Kibana visualization interface | 0 or 1 |

### Instance Class
Instance classes define the compute and memory resources for the cluster. Example classes:
- `es.n1.small` - Entry level
- `es.n1.medium` - Medium workload
- `es.n1.large` - Large workload
- `es.n1.xlarge` - Extra large workload

### Storage

| Storage Type | Use Case | Performance |
|--------------|----------|-------------|
| `cloud_ssd` | General purpose | Balanced IOPS |
| `cloud_efficiency` | Cost-effective | Lower IOPS |
| `local_ssd` | High performance | Highest IOPS |

### Versions
Supported Elasticsearch versions vary by region. Common versions:
- 6.8.x
- 7.10.x
- 7.17.x
- 8.x (latest)

### VPC and Networking
- Elasticsearch instances must be deployed in a VPC
- Subnet must have sufficient available IP addresses
- Security groups can be used for access control
- Supports private network access and public network access (optional)

### Snapshots and Backups
- Automated daily snapshots to OSS (Object Storage Service)
- Manual snapshots for point-in-time recovery
- Cross-region snapshot replication (optional)

### Monitoring
- CloudMonitor integration for cluster metrics
- Key metrics: cluster health, node status, index stats, query latency
- Alarm rules for critical thresholds

## Architecture Patterns

### Single-Zone Deployment
- All nodes in one availability zone
- Lower cost, simpler setup
- Not recommended for production

### Multi-Zone Deployment
- Nodes distributed across multiple AZs
- Higher availability
- Recommended for production workloads

### Access Patterns
1. **Private Network**: Access via VPC from applications
2. **Public Network**: Access from internet (requires IP whitelist)
3. **Kibana Access**: Web-based UI for data visualization

## Limits and Quotas

| Resource | Default Limit | Notes |
|----------|---------------|-------|
| Instances per region | 10 | Can be increased via ticket |
| Max data nodes | 50 | Per instance |
| Max storage per node | 16 TB | Depends on instance class |
| Max indices | 10,000 | Per cluster |
| Max shards per node | 1,000 | Recommended limit |

## Security Considerations

1. **Network Isolation**: Use VPC and security groups
2. **Access Control**: Enable authentication (X-Pack Security)
3. **Encryption**: Enable SSL/TLS for data in transit
4. **Audit Logging**: Enable audit logs for compliance
5. **IP Whitelist**: Restrict public access to known IPs
