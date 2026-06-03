# CLI — MongoDB (`jdc`)

## Install and Config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` INI file, NOT from environment variables.
- For sandbox environments, redirect `HOME` and pre-create config files (see SKILL.md "Critical jdc CLI Behavioral Notes").

## Conventions (agent execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json <product> <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API).

## CLI vs API Coverage Gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| Create Instance | yes | `jdc mongodb create-instance` |
| Describe Instance | yes | `jdc mongodb describe-instance` |
| Describe Instances | yes | `jdc mongodb describe-instances` |
| Modify Instance | yes | `jdc mongodb modify-instance-attribute` |
| Delete Instance | yes | `jdc mongodb delete-instance` |
| Create Backup | yes | `jdc mongodb create-backup` |
| Describe Backups | yes | `jdc mongodb describe-backups` |
| Restore Instance | yes | `jdc mongodb restore-instance` |
| Reset Password | yes | `jdc mongodb reset-password` |
| Describe Regions | yes | `jdc mongodb describe-available-region` |
| Describe Specs | yes | `jdc mongodb describe-spec-config` |
| Create Account | partial | Check CLI help |
| Describe Accounts | partial | Check CLI help |

## Command Map

### Instance Management

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Create | `jdc --output json mongodb create-instance --region-id <region> --instance-name <name> ...` | `--output json` BEFORE subcommand |
| Describe | `jdc --output json mongodb describe-instance --region-id <region> --instance-id <id>` | Returns single instance details |
| List | `jdc --output json mongodb describe-instances --region-id <region> --page-number 1 --page-size 100` | Supports pagination |
| Modify | `jdc --output json mongodb modify-instance-attribute --region-id <region> --instance-id <id> --instance-name <new_name>` | Partial updates supported |
| Delete | `jdc --output json mongodb delete-instance --region-id <region> --instance-id <id>` | **Safety gate required** |

### Backup Management

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Create Backup | `jdc --output json mongodb create-backup --region-id <region> --instance-id <id>` | Manual backup |
| List Backups | `jdc --output json mongodb describe-backups --region-id <region> --instance-id <id>` | Includes auto and manual |
| Restore | `jdc --output json mongodb restore-instance --region-id <region> --instance-id <id> --backup-id <backup_id>` | **Safety gate required** |

### Account Management

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Reset Password | `jdc --output json mongodb reset-password --region-id <region> --instance-id <id> --account-name <username> --account-password <new_password>` | Requires instance to be running |

### Configuration & Metadata

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| Describe Regions | `jdc --output json mongodb describe-available-region` | List available regions |
| Describe Specs | `jdc --output json mongodb describe-spec-config --region-id <region>` | List available instance classes |

## JSON Output Examples

### Describe Instance Response

```json
{
  "requestId": "bp6g7h8j9k0l1m2n3o4p",
  "result": {
    "instance": {
      "instanceId": "mongo-abc123def",
      "instanceName": "my-mongodb",
      "instanceClass": "mongodb.s1.small",
      "engine": "MongoDB",
      "engineVersion": "4.4",
      "status": "running",
      "vpcId": "vpc-abc123",
      "subnetId": "subnet-def456",
      "azId": "cn-north-1a",
      "storageType": "local_ssd",
      "storageSize": 20,
      "connectionDomain": "mongo-abc123def.mongo.jdcloud.com",
      "port": 27017,
      "replicaSetName": "rs0",
      "createTime": "2026-06-03T10:00:00+08:00",
      "charge": {
        "chargeMode": "postpaid",
        "chargeStatus": "normal"
      }
    }
  }
}
```

### Describe Instances (List) Response

```json
{
  "requestId": "qr5s6t7u8v9w0x1y2z3a",
  "result": {
    "instances": [
      {
        "instanceId": "mongo-abc123def",
        "instanceName": "my-mongodb",
        "instanceClass": "mongodb.s1.small",
        "engineVersion": "4.4",
        "status": "running"
      }
    ],
    "totalCount": 1
  }
}
```

## Common CLI Patterns

### Paginated List

```bash
# Get all instances across pages
PAGE=1
while true; do
  RESULT=$(jdc --output json mongodb describe-instances \
    --region-id cn-north-1 \
    --page-number $PAGE \
    --page-size 100)
  
  # Process current page
  echo "$RESULT" | jq '.result.instances[]'
  
  # Check if we've got all results
  TOTAL=$(echo "$RESULT" | jq '.result.totalCount')
  SEEN=$((PAGE * 100))
  if [ "$SEEN" -ge "$TOTAL" ]; then
    break
  fi
  
  PAGE=$((PAGE + 1))
done
```

### Poll for Status

```bash
# Poll until instance is running
INSTANCE_ID="mongo-abc123def"
REGION="cn-north-1"

for i in {1..60}; do
  STATUS=$(jdc --output json mongodb describe-instance \
    --region-id "$REGION" \
    --instance-id "$INSTANCE_ID" | jq -r '.result.instance.status')
  
  echo "Attempt $i: status=$STATUS"
  
  if [ "$STATUS" = "running" ]; then
    echo "Instance is running!"
    break
  elif [ "$STATUS" = "error" ]; then
    echo "Instance creation failed!"
    exit 1
  fi
  
  sleep 10
done
```

## Troubleshooting CLI Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `unrecognized arguments: --output json` | Flag placed after subcommand | Move `--output json` BEFORE the product name |
| `PermissionError: [Errno 13]` | HOME not writable | `export HOME=/tmp/jdc-home` and create config |
| `Invalid credentials` | Config file missing or wrong | Verify `~/.jdc/config` and `~/.jdc/current` |
| `region not found` | Invalid region ID | Check `describe-available-region` output |
