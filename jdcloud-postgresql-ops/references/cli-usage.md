# CLI — JD Cloud RDS PostgreSQL (`jdc`)

## Install and config

- **Install:** See [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` INI file, NOT from environment variables.
- For sandbox environments, redirect `HOME` and pre-create config files (see generator SKILL.md "Critical jdc CLI Behavioral Notes").

## Conventions (agent execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json rds <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API).

## CLI vs API coverage gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| Create Instance | yes | `jdc rds create-instance` |
| Describe Instance | yes | `jdc rds describe-instance` |
| Describe Instances | yes | `jdc rds describe-instances` |
| Modify Instance Attribute | yes | `jdc rds modify-instance-attribute` |
| Delete Instance | yes | `jdc rds delete-instance` |
| Create Backup | yes | `jdc rds create-backup` |
| Restore Instance | yes | `jdc rds restore-instance` |
| Describe Slow Logs | yes | `jdc rds describe-slow-logs` — Query slow query summaries by time range (PostgreSQL only) |

## Command map

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Create Instance | `jdc --output json rds create-instance --region-id cn-north-1 --instance-name my-postgresql --instance-class rds.pg.s1.small --engine PostgreSQL --engine-version 14 --vpc-id vpc-xxx --subnet-id subnet-xxx --az-id cn-north-1a --storage-type local --storage-size 20 --username admin --password xxx` | `--output json` BEFORE subcommand |
| Describe Instance | `jdc --output json rds describe-instance --region-id cn-north-1 --instance-id rds-xxx` | Get instance details |
| List Instances | `jdc --output json rds describe-instances --region-id cn-north-1 --page-number 1 --page-size 100` | Pagination supported |
| Modify Instance | `jdc --output json rds modify-instance-attribute --region-id cn-north-1 --instance-id rds-xxx --instance-name new-name` | Modify attributes |
| Delete Instance | `jdc --output json rds delete-instance --region-id cn-north-1 --instance-id rds-xxx` | Irreversible operation |
| Create Backup | `jdc --output json rds create-backup --region-id cn-north-1 --instance-id rds-xxx` | Manual backup |
| Restore Instance | `jdc --output json rds restore-instance --region-id cn-north-1 --instance-id rds-xxx --backup-id backup-xxx` | Overwrites data |
| Describe Slow Logs | `jdc --output json rds describe-slow-logs --region-id cn-north-1 --instance-id rds-xxx --start-time "2026-06-01 00:00:00" --end-time "2026-06-03 23:59:59" --page-number 1 --page-size 50` | Query slow query summaries (PostgreSQL only) |

## Output JSON Paths

| Field | Path | Example |
|-------|------|---------|
| Instance ID | `$.result.instanceId` | `rds-abc123` |
| Instance Status | `$.result.instance.status` | `running` |
| Connection Domain | `$.result.instance.connectionDomain` | `postgresql-xxx.jdcloud.com` |
| Port | `$.result.instance.port` | `5432` |
| **Slow Logs** |
| Total Count | `$.result.totalCount` | `42` |
| SQL Pattern | `$.result.slowLogs[*].sql` | `SELECT * FROM large_table WHERE...` |
| Execution Count | `$.result.slowLogs[*].executionCount` | `15` |
| Avg Exec Time | `$.result.slowLogs[*].executionTimeAvg` | `1250` (ms) |
| Max Exec Time | `$.result.slowLogs[*].executionTimeMax` | `5234` (ms) |
| Rows Examined | `$.result.slowLogs[*].rowsExaminedSum` | `150000` |

## Describe Slow Logs Examples

### Basic query (default pagination)
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-abc123 \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59"
```

### With pagination (page 2, 50 items per page)
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-abc123 \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --page-number 2 \
  --page-size 50
```

### Filter by database account
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-abc123 \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --filters '[{"name":"account","operator":"eq","values":["postgres"]}]'
```

### Filter by SQL keyword
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-abc123 \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --filters '[{"name":"keyword","operator":"eq","values":["SELECT * FROM orders"]}]'
```

### Sort by execution time (descending) — find slowest queries
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-abc123 \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --sorts '[{"name":"executionTimeSum","direction":"DESC"}]' \
  --page-size 20
```

### Sort by rows examined (identify full table scans)
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-abc123 \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --sorts '[{"name":"rowsExaminedSum","direction":"DESC"}]' \
  --page-size 20
```

### Recent 24 hours with high execution count filter
```bash
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-abc123 \
  --start-time "$(date -v-1d '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -d '1 day ago' '+%Y-%m-%d %H:%M:%S')" \
  --end-time "$(date '+%Y-%m-%d %H:%M:%S')" \
  --sorts '[{"name":"executionCount","direction":"DESC"}]' \
  --page-size 100
```

## Sandbox Setup

```bash
# Set HOME to writable location
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc

cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = rds.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

printf "%s" "default" > /tmp/jdc-home/.jdc/current
```