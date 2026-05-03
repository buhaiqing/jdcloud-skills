# CLI Usage - JD Cloud Redis (`jdc`)

## Installation and Configuration

### Install JD Cloud CLI

```bash
pip install jdcloud_cli
```

### Configure CLI

Initialize configuration with credentials:

```bash
jdc configure add \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --region-id cn-north-1
```

Or set environment variables:

```bash
export JDC_ACCESS_KEY="YOUR_ACCESS_KEY"
export JDC_SECRET_KEY="YOUR_SECRET_KEY"
export JDC_REGION="cn-north-1"
```

### Verify Installation

```bash
jdc --version
# Expected output: version number, e.g., 0.7.2

jdc redis help
# Expected output: list of redis subcommands
```

**CLI Support Evidence**: The `jdc` CLI includes `redis` in its product list, confirmed via `jdc` help output showing: `{mps,cps,rds,jke,vpc,xdata,mongodb,configure,streambus,ipanti,baseanti,datastar,redis,nc,monitor,iam,disk,cr,streamcomputer,sop,clouddnsservice,vm,oss}`. Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction

## CLI Conventions for Agent Execution

### Output Format

- **ALWAYS** append `--output json` for machine-parseable output
- JSON output is required for automated workflows and response parsing
- Example: `jdc redis describe-cache-instance --output json`

### Non-Interactive Mode

- Append `--no-interactive` when supported to avoid prompts
- Required for automation and agent workflows
- Example: `jdc redis create-cache-instance ... --no-interactive`

### JSON Path Verification

- CLI JSON output may differ slightly from raw API response
- Verify exact JSON paths with real CLI invocations before documenting
- Use `jq` for JSON parsing in shell scripts
- Example: `jdc redis describe-cache-instance --output json | jq -r '.result.cacheInstance.status'`

## CLI vs API Coverage

| Operation | Available via `jdc` | CLI Subcommand | Notes |
|-----------|-------------------|----------------|-------|
| Create instance | ✅ | `create-cache-instance` | Full coverage |
| Describe instance | ✅ | `describe-cache-instance` | Full coverage |
| List instances | ✅ | `describe-cache-instances` | Full coverage |
| Modify instance attribute | ✅ | `modify-cache-instance-attribute` | Full coverage |
| Modify instance class | ✅ | `modify-cache-instance-class` | Full coverage |
| Delete instance | ✅ | `delete-cache-instance` | Full coverage |
| Create backup | ✅ | `create-backup` | Full coverage |
| Describe backups | ✅ | `describe-backups` | Full coverage |
| Restore instance | ✅ | `restore-instance` | Full coverage |
| Describe backup policy | ✅ | `describe-backup-policy` | Full coverage |
| Modify backup policy | ✅ | `modify-backup-policy` | Full coverage |
| Describe slow log | ✅ | `describe-slow-log` | Full coverage |
| Describe instance config | ✅ | `describe-instance-config` | Full coverage |
| Modify instance config | ✅ | `modify-instance-config` | Full coverage |
| Describe IP whitelist | ✅ | `describe-ip-white-list` | Full coverage |
| Modify IP whitelist | ✅ | `modify-ip-white-list` | Full coverage |
| Reset password | ✅ | `reset-cache-instance-password` | Full coverage |
| Describe cluster info | ✅ | `describe-cluster-info` | Full coverage |
| Describe client list | ✅ | `describe-client-list` | Full coverage |
| Create account | ✅ | `create-account` | Full coverage |
| Describe accounts | ✅ | `describe-accounts` | Full coverage |
| Delete account | ✅ | `delete-account` | Full coverage |
| Describe instance class | ✅ | `describe-instance-class` | Full coverage |
| Describe spec config | ✅ | `describe-spec-config` | Full coverage |
| Describe user quota | ✅ | `describe-user-quota` | Full coverage |

**Coverage Gap**: None - CLI covers all commonly used Redis operations. Some advanced analysis APIs may have limited CLI coverage; use SDK for those.

## CLI Command Reference

### Instance Management

#### Create Redis Instance

```bash
jdc redis create-cache-instance \
  --region-id "cn-north-1" \
  --cache-instance-name "my-redis-cluster" \
  --cache-instance-class "redis.cluster.g.small" \
  --vpc-id "vpc-abc123" \
  --subnet-id "subnet-def456" \
  --az-id-spec '{"azSpecifyType":"SpecifyByReplicaGroup","master":"cn-north-1a","slave":"cn-north-1b"}' \
  --cache-instance-type "cluster" \
  --redis-version "5.0" \
  --db-num 32 \
  --replica-number 2 \
  --charge '{"chargeMode":"postpaid_by_duration"}' \
  --output json \
  --no-interactive
```

**JSON Path for Instance ID**: `$.result.cacheInstanceId`

#### Describe Single Instance

```bash
jdc redis describe-cache-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json
```

**Key JSON Paths**:
- Instance ID: `$.result.cacheInstance.cacheInstanceId`
- Name: `$.result.cacheInstance.cacheInstanceName`
- Status: `$.result.cacheInstance.status`
- Connection: `$.result.cacheInstance.connectionDomain`
- Port: `$.result.cacheInstance.port`

#### List Instances

```bash
jdc redis describe-cache-instances \
  --region-id "cn-north-1" \
  --page-number 1 \
  --page-size 20 \
  --output json
```

**JSON Paths**:
- Instance list: `$.result.cacheInstances[*]`
- Total count: `$.result.totalCount`

#### Modify Instance Attribute

```bash
jdc redis modify-cache-instance-attribute \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --cache-instance-name "new-redis-name" \
  --output json \
  --no-interactive
```

#### Modify Instance Class (Scale Up/Down)

```bash
jdc redis modify-cache-instance-class \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --cache-instance-class "redis.cluster.g.medium" \
  --output json \
  --no-interactive
```

#### Delete Instance

```bash
# Safety gate: Must obtain explicit user confirmation first
jdc redis delete-cache-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json \
  --no-interactive
```

### Backup and Recovery

#### Create Manual Backup

```bash
jdc redis create-backup \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json \
  --no-interactive
```

**JSON Path**: `$.result.backupId`

#### List Backups

```bash
jdc redis describe-backups \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --page-number 1 \
  --page-size 20 \
  --output json
```

#### Restore from Backup

```bash
jdc redis restore-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --backup-id "backup-def456" \
  --output json \
  --no-interactive
```

#### Query Backup Policy

```bash
jdc redis describe-backup-policy \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json
```

#### Modify Backup Policy

```bash
jdc redis modify-backup-policy \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --backup-period '["Monday","Wednesday","Friday"]' \
  --backup-time "02:00-Z+8" \
  --output json \
  --no-interactive
```

### Configuration and Parameters

#### Describe Instance Config

```bash
jdc redis describe-instance-config \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json
```

#### Modify Instance Config

```bash
jdc redis modify-instance-config \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --config-parameter '[{"name":"maxmemory-policy","value":"volatile-lru"}]' \
  --output json \
  --no-interactive
```

### Network and Security

#### Describe IP Whitelist

```bash
jdc redis describe-ip-white-list \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json
```

#### Modify IP Whitelist

```bash
jdc redis modify-ip-white-list \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --ip-white-list '["192.168.1.0/24","10.0.0.100"]' \
  --output json \
  --no-interactive
```

#### Reset Password

```bash
jdc redis reset-cache-instance-password \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --password "NewSecurePassword123!" \
  --output json \
  --no-interactive
```

#### Describe Connected Clients

```bash
jdc redis describe-client-list \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json
```

### Performance Analysis

#### Query Slow Log

```bash
jdc redis describe-slow-log \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --start-time "2026-05-01T00:00:00Z" \
  --end-time "2026-05-03T00:00:00Z" \
  --page-number 1 \
  --page-size 100 \
  --output json
```

### Resource Queries

#### Describe Available Specs

```bash
jdc redis describe-instance-class \
  --region-id "cn-north-1" \
  --output json
```

#### Describe Spec Config (Recommended)

```bash
jdc redis describe-spec-config \
  --region-id "cn-north-1" \
  --output json
```

#### Query User Quota

```bash
jdc redis describe-user-quota \
  --region-id "cn-north-1" \
  --output json
```

## Shell Script Examples

### Poll for Instance Creation Completion

```bash
#!/bin/bash
REGION="cn-north-1"
INSTANCE_ID="redis-abc123"
MAX_WAIT=600  # seconds
POLL_INTERVAL=10

for i in $(seq 1 $((MAX_WAIT / POLL_INTERVAL))); do
  STATUS=$(jdc redis describe-cache-instance \
    --region-id "$REGION" \
    --cache-instance-id "$INSTANCE_ID" \
    --output json | jq -r '.result.cacheInstance.status')
  
  echo "[$i] Instance status: $STATUS"
  
  if [ "$STATUS" = "running" ]; then
    echo "✓ Instance is running"
    exit 0
  fi
  
  if [ "$STATUS" = "error" ] || [ "$STATUS" = "deleted" ]; then
    echo "✗ Instance creation failed: $STATUS"
    exit 1
  fi
  
  sleep $POLL_INTERVAL
done

echo "✗ Timeout waiting for instance to become running"
exit 1
```

### Batch List All Instances

```bash
#!/bin/bash
REGION="cn-north-1"
PAGE_SIZE=100

jdc redis describe-cache-instances \
  --region-id "$REGION" \
  --page-number 1 \
  --page-size $PAGE_SIZE \
  --output json | jq -r '.result.cacheInstances[] | [.cacheInstanceId, .cacheInstanceName, .status] | @tsv'
```

### Create and Verify Instance

```bash
#!/bin/bash
REGION="cn-north-1"
NAME="test-redis-cluster"
SPEC="redis.cluster.g.micro"

# Create instance
INSTANCE_ID=$(jdc redis create-cache-instance \
  --region-id "$REGION" \
  --cache-instance-name "$NAME" \
  --cache-instance-class "$SPEC" \
  --vpc-id "vpc-xxx" \
  --subnet-id "subnet-yyy" \
  --az-id-spec '{"azSpecifyType":"SpecifyByReplicaGroup","master":"cn-north-1a","slave":"cn-north-1b"}' \
  --cache-instance-type "cluster" \
  --redis-version "5.0" \
  --output json \
  --no-interactive | jq -r '.result.cacheInstanceId')

echo "Created instance: $INSTANCE_ID"

# Poll for completion
# ... (use polling script above)
```

## CLI Path Preference

When to use CLI vs SDK:

- **Prefer CLI** when:
  - Quick ad-hoc operations from terminal
  - No Python runtime available
  - Shell script automation
  - Simple single-operation tasks

- **Prefer SDK** when:
  - Complex multi-step workflows
  - Integration into Python applications
  - Need for programmatic error handling
  - Advanced analysis and data processing
  - CI/CD pipelines with Python tooling

## Troubleshooting CLI Issues

### Common CLI Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `configure not found` | CLI not configured | Run `jdc configure add` |
| `InvalidParameter` | Parameter format error | Check parameter syntax, use JSON for complex objects |
| `RegionId not found` | Invalid region | Use valid region: cn-north-1, cn-south-1, cn-east-2 |
| `Rate limit exceeded` | Too many requests | Slow down; CLI does not auto-retry rate limits |

### JSON Parameter Syntax

- Complex parameters (arrays, objects) must be JSON strings
- Use single quotes for shell, escape internal quotes
- Example: `--az-id-spec '{"master":"cn-north-1a","slave":"cn-north-1b"}'`
- Arrays: `--backup-period '["Monday","Wednesday"]'`

### Debugging CLI Output

```bash
# Enable debug mode
jdc redis describe-cache-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --output json \
  --debug
```