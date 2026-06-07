# PostgreSQL RDS Field Mapping

> 京东云 PostgreSQL 实例与 MySQL 共享 `jdc rds describe-instances` API,通过 `engine` 字段区分。

**JD Cloud API**: `jdc rds describe-instances` (filter `engine=PostgreSQL`)

## Mapping Rules

与 `mysql.md` 几乎完全相同,关键差异点:

| 字段 | MySQL | PostgreSQL |
|------|-------|------------|
| `engine` | `MySQL` | `PostgreSQL` |
| `engineVersion` | `8.0` / `5.7` | `15` / `14` / `13` |
| `instanceClass` | `db.mysql.n2.medium` | `db.pg.n2.medium` |

完整字段列表参见 `mysql.md`,本文件仅标注 PostgreSQL 特有内容。

## Block Name

`{instance_name_slug}` (e.g. `prod_pg_01`)

## Stable Import ID

`rds:{region}:{instanceId}`(与 MySQL 共用 ID 空间)
