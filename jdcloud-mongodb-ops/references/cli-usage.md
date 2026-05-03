# CLI — JD Cloud MongoDB (`jdc`)

## Installation and Configuration

### Install JD Cloud CLI

```bash
pip install jdcloud_cli
```

### Configure CLI

```bash
# Interactive configuration
jdc configure add \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --region-id cn-north-1

# Or use environment variables
export JDC_ACCESS_KEY=YOUR_ACCESS_KEY
export JDC_SECRET_KEY=YOUR_SECRET_KEY
export JDC_REGION=cn-north-1
```

### Verify Configuration

```bash
jdc mongodb describe-available-zones --region-id cn-north-1 --output json
```

## CLI Conventions for Agent Execution

### Mandatory Flags

- **`--output json`**: Machine-parseable output (REQUIRED for automation)
- **`--no-interactive`**: Prevent interactive prompts (when supported)

### Optional Flags

- **`--region-id`**: Override default region
- **`--help`**: Show command help

### Response Parsing

All responses follow this JSON structure:

```json
{
  "requestId": "string",
  "result": {
    // Operation-specific data
  },
  "error": null  // or error object on failure
}
```

## Command Reference

### Instance Lifecycle Commands

#### Create Replica Set Instance

```bash
jdc mongodb create-instance \
  --region-id cn-north-1 \
  --instance-name my-mongodb-prod \
  --instance-class mongodb.s.1.large \
  --engine-version 4.0 \
  --vpc-id vpc-xxxx \
  --subnet-id subnet-xxxx \
  --az-id cn-north-1a \
  --charge-mode postpaid_by_duration \
  --password MySecurePass123 \
  --output json \
  --no-interactive
```

**Response**:
```json
{
  "requestId": "bc7d7fxxxxxx",
  "result": {
    "instanceId": "mongodb-xxxx"
  }
}
```

**Parse instanceId**: `jq -r '.result.instanceId'`

#### Create Sharded Cluster Instance

```bash
jdc mongodb create-sharding-instance \
  --region-id cn-north-1 \
  --instance-name my-mongodb-cluster \
  --engine-version 4.0 \
  --vpc-id vpc-xxxx \
  --subnet-id subnet-xxxx \
  --mongos-spec mongodb.s.1.medium \
  --mongos-node-num 3 \
  --shard-spec mongodb.s.1.large \
  --shard-node-num 2 \
  --shard-storage 100 \
  --config-spec mongodb.s.1.small \
  --output json \
  --no-interactive
```

#### Describe Instances

```bash
# Single instance
jdc mongodb describe-instances \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json

# List all instances
jdc mongodb describe-instances \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20 \
  --output json
```

**Parse status**: `jq -r '.result.instance.status'`

#### Modify Instance Specification

```bash
jdc mongodb modify-instance-spec \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --instance-class mongodb.s.2.large \
  --output json \
  --no-interactive
```

#### Modify Instance Name

```bash
jdc mongodb modify-instance-name \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --instance-name new-name \
  --output json \
  --no-interactive
```

#### Restart Instance

```bash
jdc mongodb restart-instance \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json \
  --no-interactive
```

#### Delete Instance

```bash
jdc mongodb delete-instance \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json \
  --no-interactive
```

### Backup Commands

#### Create Manual Backup

```bash
jdc mongodb create-backup \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --backup-name pre-upgrade-snapshot \
  --output json \
  --no-interactive
```

**Response**:
```json
{
  "result": {
    "backupId": "backup-xxxx"
  }
}
```

#### List Backups

```bash
jdc mongodb describe-backups \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json
```

#### Get Backup Download URL

```bash
jdc mongodb backup-download-url \
  --region-id cn-north-1 \
  --backup-id backup-xxxx \
  --output json
```

#### Delete Backup

```bash
jdc mongodb delete-backup \
  --region-id cn-north-1 \
  --backup-id backup-xxxx \
  --output json \
  --no-interactive
```

#### Describe Backup Policy

```bash
jdc mongodb describe-backup-policy \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json
```

#### Modify Backup Policy

```bash
jdc mongodb modify-backup-policy \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --backup-period 7 \
  --backup-time "02:00" \
  --output json \
  --no-interactive
```

### Security Commands

#### Describe Whitelist

```bash
jdc mongodb describe-security-ips \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json
```

#### Modify Whitelist

```bash
jdc mongodb modify-security-ips \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --security-ips "192.168.1.0/24,10.0.0.100" \
  --output json \
  --no-interactive
```

### Metadata Commands

#### Query Available Zones

```bash
jdc mongodb describe-available-zones \
  --region-id cn-north-1 \
  --output json
```

#### Query Instance Specs

```bash
jdc mongodb describe-flavors \
  --region-id cn-north-1 \
  --output json
```

### Password Management

#### Reset Password

```bash
jdc mongodb reset-password \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --password NewSecurePass456 \
  --output json \
  --no-interactive
```

### Restore Commands

#### Restore Instance from Backup

```bash
jdc mongodb restore-instance \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --backup-id backup-xxxx \
  --output json \
  --no-interactive
```

## CLI vs API Coverage Gap

> **Coverage Status**: **Full Coverage** - JD Cloud CLI supports all MongoDB API operations documented in this skill.
> There are **no SDK-only operations** for this product.

| Operation | API Available | CLI Available | Notes |
|-----------|---------------|---------------|-------|
| Create replica set | ✓ | ✓ | Full coverage |
| Create sharded cluster | ✓ | ✓ | Full coverage |
| Describe instances | ✓ | ✓ | Full coverage |
| Modify spec | ✓ | ✓ | Full coverage |
| Modify name | ✓ | ✓ | Full coverage |
| Modify node spec | ✓ | ✓ | For sharded clusters |
| Restart instance | ✓ | ✓ | Full coverage |
| Restart node | ✓ | ✓ | For sharded clusters |
| Delete instance | ✓ | ✓ | Full coverage |
| Create backup | ✓ | ✓ | Full coverage |
| Describe backups | ✓ | ✓ | Full coverage |
| Delete backup | ✓ | ✓ | Full coverage |
| Backup download URL | ✓ | ✓ | Full coverage |
| Backup policy | ✓ | ✓ | Full coverage |
| Security whitelist | ✓ | ✓ | Full coverage |
| Reset password | ✓ | ✓ | Full coverage |
| Restore instance | ✓ | ✓ | Full coverage |
| Available zones | ✓ | ✓ | Full coverage |
| Instance specs | ✓ | ✓ | Full coverage |

> **Summary**: All 17 MongoDB operations are fully supported by both SDK and CLI. This is a **dual-path skill** with complete parity.

## Common Workflows

### Workflow 1: Create and Verify Instance

```bash
# 1. Create instance
INSTANCE_ID=$(jdc mongodb create-instance \
  --region-id cn-north-1 \
  --instance-name my-mongodb \
  --instance-class mongodb.s.1.large \
  --engine-version 4.0 \
  --vpc-id vpc-xxxx \
  --subnet-id subnet-xxxx \
  --az-id cn-north-1a \
  --output json | jq -r '.result.instanceId')

# 2. Poll until running (max 600s)
for i in $(seq 1 60); do
  STATUS=$(jdc mongodb describe-instances \
    --region-id cn-north-1 \
    --instance-id $INSTANCE_ID \
    --output json | jq -r '.result.instance.status')
  echo "Status: $STATUS"
  [ "$STATUS" = "running" ] && break
  sleep 10
done

# 3. Configure whitelist
jdc mongodb modify-security-ips \
  --region-id cn-north-1 \
  --instance-id $INSTANCE_ID \
  --security-ips "192.168.1.0/24" \
  --output json

# 4. Get connection info
jdc mongodb describe-instances \
  --region-id cn-north-1 \
  --instance-id $INSTANCE_ID \
  --output json | jq '.result.instance | {domain: .connectionDomain, port: .port}'
```

### Workflow 2: Backup and Restore

```bash
# 1. Create backup before change
BACKUP_ID=$(jdc mongodb create-backup \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --backup-name pre-change-backup \
  --output json | jq -r '.result.backupId')

# 2. Wait for backup completion
for i in $(seq 1 30); do
  STATUS=$(jdc mongodb describe-backups \
    --region-id cn-north-1 \
    --backup-id $BACKUP_ID \
    --output json | jq -r '.result.backupStatus')
  [ "$STATUS" = "completed" ] && break
  sleep 10
done

# 3. Make changes to instance...

# 4. If needed, restore from backup
jdc mongodb restore-instance \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --backup-id $BACKUP_ID \
  --output json
```

### Workflow 3: Resize Instance

```bash
# 1. Verify current status is running
CURRENT_STATUS=$(jdc mongodb describe-instances \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json | jq -r '.result.instance.status')

if [ "$CURRENT_STATUS" != "running" ]; then
  echo "Instance not in running state, cannot resize"
  exit 1
fi

# 2. Create pre-resize backup
jdc mongodb create-backup \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --backup-name pre-resize-backup \
  --output json

# 3. Resize instance
jdc mongodb modify-instance-spec \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --instance-class mongodb.s.2.large \
  --output json

# 4. Poll until running again (max 900s)
for i in $(seq 1 90); do
  STATUS=$(jdc mongodb describe-instances \
    --region-id cn-north-1 \
    --instance-id mongodb-xxxx \
    --output json | jq -r '.result.instance.status')
  [ "$STATUS" = "running" ] && break
  sleep 10
done

# 5. Verify new spec
jdc mongodb describe-instances \
  --region-id cn-north-1 \
  --instance-id mongodb-xxxx \
  --output json | jq '.result.instance.instanceClass'
```

## Error Handling

### Parse Error Messages

```bash
# Capture error if operation fails
RESPONSE=$(jdc mongodb create-instance ... --output json)

if echo "$RESPONSE" | jq -e '.error' > /dev/null; then
  ERROR_CODE=$(echo "$RESPONSE" | jq -r '.error.code')
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message')
  echo "Error: $ERROR_CODE - $ERROR_MSG"
fi
```

### Common Error Handling

| Error Code | Action |
|------------|--------|
| `InvalidParameter` | Check parameter format, fix and retry |
| `QuotaExceeded` | User needs to request quota increase |
| `InsufficientBalance` | User needs to top up account |
| `ResourceNotFound` | Verify instance ID exists |
| `ResourceAlreadyExists` | Use different instance name |

## Performance Tips

1. **Batch Queries**: Use pagination for large instance lists
2. **Parallel Commands**: Run independent queries in parallel (whitelist + backups)
3. **Cache Metadata**: Store region/spec info locally, refresh periodically
4. **Use Filters**: Filter by status, name to reduce result size
5. **Timeout Management**: Set appropriate timeouts for long operations

## Related Documentation

- [API & SDK Usage](api-sdk-usage.md)
- [Core Concepts](core-concepts.md)
- [Integration](integration.md)
- [Troubleshooting](troubleshooting.md)