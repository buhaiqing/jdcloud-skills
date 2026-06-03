# CLI — JD Cloud RDS MySQL (`jdc`)

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

## Command map

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Create Instance | `jdc --output json rds create-instance --region-id cn-north-1 --instance-name my-mysql --instance-class rds.mysql.s1.small --engine MySQL --engine-version 8.0 --vpc-id vpc-xxx --subnet-id subnet-xxx --az-id cn-north-1a --storage-type local --storage-size 20 --username admin --password xxx` | `--output json` BEFORE subcommand |
| Describe Instance | `jdc --output json rds describe-instance --region-id cn-north-1 --instance-id rds-xxx` | Get instance details |
| List Instances | `jdc --output json rds describe-instances --region-id cn-north-1 --page-number 1 --page-size 100` | Pagination supported |
| Modify Instance | `jdc --output json rds modify-instance-attribute --region-id cn-north-1 --instance-id rds-xxx --instance-name new-name` | Modify attributes |
| Delete Instance | `jdc --output json rds delete-instance --region-id cn-north-1 --instance-id rds-xxx` | Irreversible operation |
| Create Backup | `jdc --output json rds create-backup --region-id cn-north-1 --instance-id rds-xxx` | Manual backup |
| Restore Instance | `jdc --output json rds restore-instance --region-id cn-north-1 --instance-id rds-xxx --backup-id backup-xxx` | Overwrites data |

## Output JSON Paths

| Field | Path | Example |
|-------|------|---------|
| Instance ID | `$.result.instanceId` | `rds-abc123` |
| Instance Status | `$.result.instance.status` | `running` |
| Connection Domain | `$.result.instance.connectionDomain` | `mysql-xxx.jdcloud.com` |
| Port | `$.result.instance.port` | `3306` |

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