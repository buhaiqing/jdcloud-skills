# Core Concepts

## Overview

JD Cloud Tag Audit skill provides unified tag compliance checking across multiple JD Cloud products and regions.

## Key Concepts

### Tag Compliance

Tag compliance ensures that cloud resources have the required tags for proper resource management, cost tracking, and operational visibility.

### Required Tags

The skill checks for the following default required tags:
- **环境** (Environment): production, test, development, etc.
- **客户** (Customer): Customer name or identifier

### Product Support

| Product | Description |
|---------|-------------|
| Redis | Cloud Redis cache instances |
| VM | Virtual machine instances |
| RDS | Relational database instances (MySQL, PostgreSQL) |
| CLB | Cloud load balancers |
| EIP | Elastic IP addresses |

### Region Support

- cn-north-1 (华北-北京)
- cn-east-1 (华东-青岛)
- cn-east-2 (华东-上海)
- cn-south-1 (华南-广州)
- cn-south-2 (华南-深圳)

## Compliance Status

### Compliant
Resource has all required tags properly set.

### Non-Compliant
Resource is missing one or more required tags.

## Audit Workflow

1. **Pre-flight Check**: Verify credentials and available regions
2. **Multi-region Scan**: Scan all available regions
3. **Multi-product Audit**: Check each supported product
4. **Result Aggregation**: Collect non-compliant resources
5. **Report Generation**: Generate structured audit report
6. **Ticket Creation**: Optionally create DOPS tickets