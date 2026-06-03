# Core Concepts - JD Cloud RDS PostgreSQL

## Overview

JD Cloud RDS PostgreSQL is a fully managed relational database service that provides:
- High availability with automatic failover
- Automated backup and point-in-time recovery
- Elastic scaling of compute and storage
- Read replicas for high read throughput
- Security features including VPC isolation, IP whitelist, and SSL/TLS

## Key Concepts

### Instance
A PostgreSQL database instance is the basic unit of RDS PostgreSQL service. Each instance runs a single PostgreSQL server.

### Engine Version
Supported PostgreSQL versions: 10, 11, 12, 13, 14

### Instance Class
Determines the computing power and memory capacity. Instance classes follow the naming convention:
- `rds.pg.s1.small` - Small instance
- `rds.pg.s1.medium` - Medium instance
- `rds.pg.s2.large` - Large instance
- `rds.pg.s2.xlarge` - Extra large instance

### Storage Type
- `local` - Local SSD storage for high IOPS
- `cloud` - Cloud disk storage for cost optimization

### Availability Zone (AZ)
Physical data centers within a region. Multi-AZ deployment provides high availability.

### VPC and Subnet
VPC (Virtual Private Cloud) provides network isolation. Subnet is a subdivision of VPC.

## Architecture Options

### Single-AZ Deployment
- Single instance in one AZ
- Lower cost, suitable for development/testing

### Multi-AZ Deployment
- Primary instance + standby instance in different AZs
- Automatic failover in case of primary failure
- Suitable for production environments

### Read Replicas
- Up to 5 read replicas per primary instance
- Offload read traffic from primary
- Asynchronous replication