# JD Cloud Redis CLI Usage

## CLI Command Structure

All Redis CLI commands follow this pattern:
```bash
jdc redis <action>-<resource> [parameters] --output json --no-interactive
```

## Instance Management

### List All Instances

List all Redis instances in a region:

```bash
jdc redis describe-cache-instances \
  --region-id cn-north-1 \
  --output json
```

**Filter by status:**
```bash
jdc redis describe-cache-instances \
  --region-id cn-north-1 \
  --status "running" \
  --output json
```

**Pagination:**
```bash
jdc redis describe-cache-instances \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20 \
  --output json
```

### Describe Single Instance

Get detailed information about a specific instance:

```bash
jdc redis describe-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

**Key fields in response:**
- `instanceId`: Instance ID
- `cacheInstanceName`: Instance name
- `status`: Current status (creating, running, changing, deleted)
- `instanceClass`: Instance specification
- `redisVersion`: Redis version (4.0, 5.0, 6.2)
- `capacityMB`: Memory size in MB
- `connectionDomain`: Connection domain name
- `connectionPort`: Connection port (default: 6379)
- `vpcId`: VPC ID
- `subnetId`: Subnet ID

### Create Instance

Create a new Redis instance:

```bash
jdc redis create-cache-instance \
  --region-id cn-north-1 \
  --az-id "cn-north-1a" \
  --cache-instance-name "my-redis-prod" \
  --instance-class "redis.sw.4g" \
  --vpc-id "vpc-abc123" \
  --subnet-id "subnet-def456" \
  --password "MyStr0ng!Pass#2026" \
  --redis-version "6.2" \
  --charge-mode "postpaid_by_duration" \
  --output json \
  --no-interactive
```

**Required parameters:**
- `--region-id`: Region ID
- `--az-id`: Availability zone ID
- `--cache-instance-name`: Instance name
- `--instance-class`: Instance specification
- `--vpc-id`: VPC ID
- `--subnet-id`: Subnet ID
- `--password`: Password (8-32 chars, letters + numbers + special chars)

**Optional parameters:**
- `--redis-version`: Redis version (default: latest)
- `--charge-mode`: Billing mode (postpaid_by_duration, prepaid)
- `--node-count`: Number of nodes (for cluster architecture)

### Delete Instance

Delete a Redis instance (IRREVERSIBLE):

```bash
jdc redis delete-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json \
  --no-interactive
```

> ⚠️ **WARNING**: This operation cannot be undone. All data will be lost. Create a backup first if needed.

### Resize Instance (Change Specification)

Change instance specification (scale up/down):

```bash
jdc redis modify-cache-instance-class \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --instance-class "redis.sw.8g" \
  --output json \
  --no-interactive
```

**Notes:**
- Instance must be in `running` status
- May cause brief connection interruption (usually < 30 seconds)
- Use connection retry logic in applications
- Can only scale to compatible specifications

### Modify Instance Attributes

Update instance name or other attributes:

```bash
jdc redis modify-cache-instance-attribute \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --cache-instance-name "my-redis-prod-updated" \
  --output json \
  --no-interactive
```

### Reset Password

Reset instance password:

```bash
jdc redis reset-cache-instance-password \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --new-password "NewStr0ng!Pass#2026" \
  --output json \
  --no-interactive
```

> ⚠️ **WARNING**: All existing connections will be disconnected. Update application configuration with new password.

## Backup & Recovery

### Create Backup

Create a manual backup:

```bash
jdc redis create-backup \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --backup-name "manual-backup-2026-04-30" \
  --output json \
  --no-interactive
```

### Describe Backups

List all backups for an instance:

```bash
jdc redis describe-backups \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

**Response fields:**
- `backupId`: Backup ID
- `backupName`: Backup name
- `status`: Backup status (success, failed, running)
- `backupSizeMB`: Backup file size
- `createTime`: Backup creation time

### Restore Instance from Backup

Restore instance from a backup:

```bash
jdc redis restore-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --backup-id backup-xyz789 \
  --output json \
  --no-interactive
```

> ⚠️ **WARNING**: This will overwrite current instance data. Create a backup first if needed.

### Describe Backup Policy

View backup policy configuration:

```bash
jdc redis describe-backup-policy \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

### Modify Backup Policy

Update backup policy:

```bash
jdc redis modify-backup-policy \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --backup-period "1,3,5" \
  --backup-time "02:00-03:00" \
  --backup-retention 30 \
  --output json \
  --no-interactive
```

**Parameters:**
- `--backup-period`: Days of week (1=Monday, 7=Sunday), comma-separated
- `--backup-time`: Backup time window (HH:MM-HH:MM)
- `--backup-retention`: Retention period in days (7-732)

## Network & Security

### Describe IP Whitelist

View current IP whitelist:

```bash
jdc redis describe-ip-white-list \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

### Modify IP Whitelist

Update IP whitelist:

```bash
jdc redis modify-ip-white-list \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --ip-white-list '["192.168.1.0/24", "10.0.0.100", "172.16.0.0/16"]' \
  --output json \
  --no-interactive
```

**Notes:**
- Supports single IPs and CIDR notation
- Maximum 500 entries
- Empty list means deny all access

### Describe Client List

View connected clients:

```bash
jdc redis describe-client-list \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

### Describe Client IP Details

View detailed client IP statistics:

```bash
jdc redis describe-client-ip-detail \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

## Configuration Management

### Describe Instance Config

View current configuration parameters:

```bash
jdc redis describe-instance-config \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

**Common parameters:**
- `maxmemory-policy`: Eviction policy (noeviction, allkeys-lru, volatile-lru, etc.)
- `timeout`: Connection timeout (seconds)
- `tcp-keepalive`: TCP keepalive interval
- `appendonly`: AOF persistence enabled (yes/no)
- `appendfsync`: AOF sync policy (always, everysec, no)

### Modify Instance Config

Update configuration parameters:

```bash
jdc redis modify-instance-config \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --instance-config '[{"parameterName":"maxmemory-policy","parameterValue":"allkeys-lru"}]' \
  --output json \
  --no-interactive
```

> Note: Some parameters require instance restart to take effect.

### Describe Config History

View configuration change history:

```bash
jdc redis describe-instance-config \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

## Performance Analysis

### Describe Slow Log

View slow query logs:

```bash
jdc redis describe-slow-log \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --start-time "2026-04-30T00:00:00+08:00" \
  --end-time "2026-04-30T23:59:59+08:00" \
  --output json
```

### Create Cache Analysis

Start cache analysis (big keys, hot keys):

```bash
jdc redis create-cache-analysis \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json \
  --no-interactive
```

### Describe Cache Analysis List

View analysis task list:

```bash
jdc redis describe-cache-analysis-list \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

### Describe Cache Analysis Result

Get analysis results:

```bash
jdc redis describe-cache-analysis-result \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --analysis-id analysis-abc123 \
  --output json
```

### Big Key Analysis

#### Create Big Key Analysis
```bash
jdc redis create-big-key-analysis \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json \
  --no-interactive
```

#### Describe Big Key List
```bash
jdc redis describe-big-key-list \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

#### Describe Big Key Detail
```bash
jdc redis describe-big-key-detail \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --key-name "my:big:key" \
  --output json
```

## Account Management

### Describe Accounts

List all accounts:

```bash
jdc redis describe-accounts \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

### Create Account

Create a new account:

```bash
jdc redis create-account \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --account-name "app-user" \
  --account-password "AppStr0ng!Pass#2026" \
  --account-privilege "read" \
  --output json \
  --no-interactive
```

**Privilege levels:**
- `read`: Read-only access
- `write`: Read-write access
- `role`: Custom role-based access

### Modify Account

Update account password or privileges:

```bash
jdc redis modify-account \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --account-name "app-user" \
  --account-password "NewStr0ng!Pass#2026" \
  --output json \
  --no-interactive
```

### Delete Account

Delete an account:

```bash
jdc redis delete-account \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --account-name "app-user" \
  --output json \
  --no-interactive
```

## Command Management

### Get Disabled Commands

View currently disabled commands:

```bash
jdc redis get-disable-commands \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json
```

### Set Disabled Commands

Disable dangerous commands:

```bash
jdc redis set-disable-commands \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --disabled-commands '["FLUSHALL", "FLUSHDB", "KEYS", "CONFIG"]' \
  --output json \
  --no-interactive
```

**Recommended disabled commands for production:**
- `FLUSHALL`: Flush all databases
- `FLUSHDB`: Flush current database
- `KEYS`: Pattern matching (use SCAN instead)
- `CONFIG`: Runtime configuration
- `SHUTDOWN`: Shutdown server
- `DEBUG`: Debug commands

## Quota & Specifications

### Describe User Quota

Check instance quota:

```bash
jdc redis describe-user-quota \
  --region-id cn-north-1 \
  --output json
```

### Describe Spec Config

View available instance specifications:

```bash
jdc redis describe-spec-config \
  --region-id cn-north-1 \
  --output json
```

### Describe Available Region

List available regions:

```bash
jdc redis describe-available-region \
  --output json
```

### Describe Available Resource

Check resource availability in AZ:

```bash
jdc redis describe-available-resource \
  --region-id cn-north-1 \
  --az-id "cn-north-1a" \
  --instance-class "redis.sw.4g" \
  --output json
```

## Common Operations Examples

### Example 1: Create Production Redis Instance

```bash
# Step 1: Check available specs
jdc redis describe-spec-config --region-id cn-north-1 --output json

# Step 2: Create instance
jdc redis create-cache-instance \
  --region-id cn-north-1 \
  --az-id "cn-north-1a" \
  --cache-instance-name "prod-cache-01" \
  --instance-class "redis.sw.8g" \
  --vpc-id "vpc-abc123" \
  --subnet-id "subnet-def456" \
  --password "Pr0d!R3dis#2026" \
  --redis-version "6.2" \
  --charge-mode "postpaid_by_duration" \
  --output json

# Step 3: Wait for instance to be ready (poll every 10s)
# Step 4: Configure whitelist
jdc redis modify-ip-white-list \
  --region-id cn-north-1 \
  --cache-instance-id <instance-id-from-step-2> \
  --ip-white-list '["10.0.1.0/24", "10.0.2.0/24"]' \
  --output json

# Step 5: Disable dangerous commands
jdc redis set-disable-commands \
  --region-id cn-north-1 \
  --cache-instance-id <instance-id> \
  --disabled-commands '["FLUSHALL", "FLUSHDB", "KEYS", "CONFIG"]' \
  --output json
```

### Example 2: Daily Backup and Monitoring

```bash
# Create manual backup
jdc redis create-backup \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --backup-name "daily-backup-$(date +%Y-%m-%d)" \
  --output json

# Check backup status
jdc redis describe-backups \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json

# View slow logs
jdc redis describe-slow-log \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --start-time "$(date -d '1 hour ago' -Iseconds)" \
  --end-time "$(date -Iseconds)" \
  --output json
```

### Example 3: Resize Instance (Scale Up)

```bash
# Step 1: Check current status
jdc redis describe-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json

# Step 2: Verify target spec is available
jdc redis describe-available-resource \
  --region-id cn-north-1 \
  --az-id "cn-north-1a" \
  --instance-class "redis.sw.16g" \
  --output json

# Step 3: Resize instance
jdc redis modify-cache-instance-class \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --instance-class "redis.sw.16g" \
  --output json

# Step 4: Poll until status returns to "running"
# Step 5: Verify new spec applied
jdc redis describe-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json | jq '.result.cacheInstance.instanceClass'
```

## Troubleshooting Commands

### Check Instance Status
```bash
jdc redis describe-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json | jq '.result.cacheInstance.status'
```

### Check Connection Info
```bash
jdc redis describe-cache-instance \
  --region-id cn-north-1 \
  --cache-instance-id jcs-redis-abc123 \
  --output json | jq '{
    domain: .result.cacheInstance.connectionDomain,
    port: .result.cacheInstance.connectionPort
  }'
```

### List All Running Instances
```bash
jdc redis describe-cache-instances \
  --region-id cn-north-1 \
  --status "running" \
  --output json | jq '.result.cacheInstances[] | {id: .instanceId, name: .cacheInstanceName}'
```
