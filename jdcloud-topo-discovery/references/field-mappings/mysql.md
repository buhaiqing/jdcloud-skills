# RDS (MySQL) Field Mapping

**JD Cloud API**: `jdc rds describe-instances` → `jdcloud_rds_instance` (placeholder)

## Mapping Rules

| HCL Attribute | API JSON Path | Type | Required | Notes |
|---------------|---------------|------|----------|-------|
| `instance_name` | `instanceName` | string | ✅ | Block name derived from this |
| `engine` | `engine` | string | ✅ | `MySQL` / `PostgreSQL` / `MariaDB` / `SQLServer` |
| `engine_version` | `engineVersion` | string | ✅ | e.g. `8.0` |
| `instance_class` | `instanceClass` | string | ✅ | e.g. `db.mysql.n2.medium` |
| `instance_storage_gb` | `instanceStorageGB` | int | ❌ | Skipped if absent |
| `vpc_id` | `vpcId` | string | ✅ | Parent ref via VPC |
| `subnet_id` | `subnetId` | string | ✅ | Parent ref via Subnet |
| `az` | `az` | string | ✅ | e.g. `cn-north-1b` |
| `ha_mode` | `haMode` | string | ❌ | `StandardHA` / `FinanceHA` |
| `account_password` | N/A | string | ❌ | **NOT in describe response**; sensitive, masked to `var.mysql_password` if set in create |

> **京东云 RDS 特殊性**:
> - 京东云用 `engine` 字段区分 MySQL/PostgreSQL/SQL Server/MariaDB/MongoDB
> - `accountPassword` **不在 describe 响应中**(避免泄露),仅在 create 时接收
> - 主备/集群架构通过 `haMode` 字段标识

## Block Name

`{instance_name_slug}` (e.g. `prod_mysql_01`)

## Stable Import ID

`rds:{region}:{instanceId}`

## Multiple Engines

本 skill 用同一 `mysql` 资源类型表示 MySQL 实例,PostgreSQL 用 `postgresql`,以此类推。
SQL Server / MariaDB 也归入 `rds` 命名空间,需要进一步拆分时通过 `engine` 字段过滤。
