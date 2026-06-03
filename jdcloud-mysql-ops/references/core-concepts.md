# Core Concepts - JD Cloud RDS MySQL

## Overview

JD Cloud RDS MySQL is a fully managed relational database service that provides:
- High availability with automatic failover
- Automated backup and point-in-time recovery
- Elastic scaling of compute and storage
- Read replicas for high read throughput
- Security features including VPC isolation, IP whitelist, and SSL/TLS

## Key Concepts

### Instance
A MySQL database instance is the basic unit of RDS MySQL service. Each instance runs a single MySQL server.

### Engine Version
Supported MySQL versions: 5.7, 8.0

### Instance Class
Determines the computing power and memory capacity. Instance classes follow the naming convention:
- `rds.mysql.s1.small` - Small instance
- `rds.mysql.s1.medium` - Medium instance
- `rds.mysql.s2.large` - Large instance
- `rds.mysql.s2.xlarge` - Extra large instance

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