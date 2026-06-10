# Core Concepts — JD Cloud Billing

## Billing Dimensions

### 1. Account Balance

JD Cloud accounts maintain multiple balance types:

| Balance Type | Description | Usage Priority |
|--------------|-------------|----------------|
| **Total Amount** | Main account balance | Primary |
| **Available Amount** | Balance available for new purchases | Secondary |
| **Frozen Amount** | Temporarily frozen for pending transactions | — |

Queried via **Asset Service** (`DescribeAccountAmountRequest`).

### 2. Billing Types

| Type | Code | Description |
|------|------|-------------|
| **按配置 (Pay-As-You-Go)** | 1 | Pay by configuration |
| **按用量 (By Usage)** | 2 | Pay by actual usage |
| **包年包月 (PrePaid)** | 3 | Monthly/Yearly subscription |
| **按次 (Per-Action)** | 4 | Pay per action |

### 3. Product Categories

Billing aggregates costs by product category:

- **Compute**: VM, Kubernetes, Function Compute
- **Storage**: Cloud Disk, OSS
- **Database**: RDS, Redis, MongoDB, PostgreSQL
- **Network**: EIP, CLB, NAT, VPN
- **Security**: WAF, SSL Certificates
- **Other**: Various services

### 4. Voucher Types

| Voucher Type | Usage Scope | Validity |
|--------------|-------------|----------|
| **Instance Voucher** | Specific instance type | Time-limited |

Queried via **InstanceVoucher Service** (`DescribeInstanceVouchersRequest`).

## Billing Cycle

- **PrePaid**: Charged at purchase/renewal
- **PostPaid**: Charged hourly, settled daily/monthly
- **Invoice**: Generated monthly after settlement

## Cost Allocation Dimensions

When querying bills, you can group/filter by:

1. **Region** — Geographic region (cn-north-1, cn-south-1, etc.)
2. **Product** — Service type (vm, rds, redis, etc.)
3. **Resource ID** — Specific resource instance
4. **Tag** — User-defined resource tags
5. **Project** — JD Cloud project grouping

## Query Time Ranges

| Query Type | Max Range | Time Format |
|------------|-----------|-------------|
| Balance | Real-time | — |
| Consumption Summary | 1 month per query | `yyyy-MM-dd HH:mm:ss` |
| Bill Details | 1 month per query | `yyyy-MM-dd HH:mm:ss` |

> **Note**: Bill summary/detail queries do NOT support cross-month queries.
> Each query covers a single month period.
