# CLI Usage - JD Cloud Redis (`jdc`)

## Installation and Configuration

### Install JD Cloud CLI

```bash
pip install jdcloud_cli
```

### Configure CLI

**IMPORTANT**: The `jdc` CLI reads credentials exclusively from `~/.jdc/config` (INI format). Environment variables (`JDC_ACCESS_KEY`, `JDC_SECRET_KEY`) are NOT supported.

Initialize configuration with credentials using the interactive command:

```bash
jdc configure add \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --region-id cn-north-1
```

For sandboxed environments where `~` is not writable, manually create the config:

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = redis.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
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

- The `--output json` argument is a **top-level** argument (defined in `base_controller.py`), NOT a subcommand argument
- It MUST be placed **before** the subcommand, not after
- **CORRECT**: `jdc --output json redis describe-cache-instances`
- **WRONG**: `jdc redis describe-cache-instances --output json` (fails with `unrecognized arguments`)
- JSON output is the default and only output format

### Non-Interactive Mode

- The `--no-interactive` flag is **NOT supported** by jdc CLI. Do not use it.
- All jdc CLI commands are non-interactive by default when all required arguments are provided.

### Credential Configuration

- **CRITICAL**: `jdc` CLI does **NOT** read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` environment variables
- It reads credentials exclusively from `~/.jdc/config` (INI file)
- In sandboxed environments, set `HOME` to a writable path and pre-create the config:

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = redis.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### JSON Path Verification

- CLI output is always JSON (printed via `Printer.print_result()`)
- Output structure: `{"request_id": "...", "error": null, "result": {...}}`
- Verify exact JSON paths with real CLI invocations before documenting
- Use `jq` for JSON parsing in shell scripts

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
jdc --output json redis create-cache-instance \
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
  --charge '{"chargeMode":"postpaid_by_duration"}'
```

**JSON Path for Instance ID**: `$.result.cacheInstanceId`

#### Describe Single Instance

```bash
jdc --output json redis describe-cache-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```

**Key JSON Paths**:
- Instance ID: `$.result.cacheInstance.cacheInstanceId`
- Name: `$.result.cacheInstance.cacheInstanceName`
- Status: `$.result.cacheInstance.status`
- Connection: `$.result.cacheInstance.connectionDomain`
- Port: `$.result.cacheInstance.port`

#### List Instances

```bash
jdc --output json redis describe-cache-instances \
  --region-id "cn-north-1" \
  --page-number 1 \
  --page-size 20
```

**JSON Paths**:
- Instance list: `$.result.cacheInstances[*]`
- Total count: `$.result.totalCount`

#### Modify Instance Attribute

```bash
jdc --output json redis modify-cache-instance-attribute \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --cache-instance-name "new-redis-name"
```

#### Modify Instance Class (Scale Up/Down)

```bash
jdc --output json redis modify-cache-instance-class \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --cache-instance-class "redis.cluster.g.medium"
```

#### Delete Instance

```bash
# Safety gate: Must obtain explicit user confirmation first
jdc --output json redis delete-cache-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```

### Backup and Recovery

#### Create Manual Backup

```bash
jdc --output json redis create-backup \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```

**JSON Path**: `$.result.backupId`

#### List Backups

```bash
jdc --output json redis describe-backups \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --page-number 1 \
  --page-size 20
```

#### Restore from Backup

```bash
# Note: restore uses --base-id (not --backup-id)
jdc --output json redis restore-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --base-id "backup-def456"
```

#### Query Backup Policy

```bash
jdc --output json redis describe-backup-policy \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```

#### Modify Backup Policy

```bash
jdc --output json redis modify-backup-policy \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --backup-period '["Monday","Wednesday","Friday"]' \
  --backup-time "02:00-Z+8"
```

### Configuration and Parameters

#### Describe Instance Config

```bash
jdc --output json redis describe-instance-config \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```

#### Modify Instance Config

```bash
jdc --output json redis modify-instance-config \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --config-parameter '[{"name":"maxmemory-policy","value":"volatile-lru"}]'
```

### Network and Security

#### Describe IP Whitelist

```bash
jdc --output json redis describe-ip-white-list \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```

#### Modify IP Whitelist

```bash
jdc --output json redis modify-ip-white-list \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --ip-white-list '["192.168.1.0/24","10.0.0.100"]'
```

#### Reset Password

```bash
jdc --output json redis reset-cache-instance-password \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --password "NewSecurePassword123!"
```

#### Describe Connected Clients

```bash
jdc --output json redis describe-client-list \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```

### Performance Analysis

#### Query Slow Log

```bash
jdc --output json redis describe-slow-log \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123" \
  --start-time "2026-05-01T00:00:00Z" \
  --end-time "2026-05-03T00:00:00Z" \
  --page-number 1 \
  --page-size 100
```

### Resource Queries

#### Describe Available Specs

```bash
jdc --output json redis describe-instance-class \
  --region-id "cn-north-1"
```

#### Describe Spec Config (Recommended)

```bash
jdc --output json redis describe-spec-config \
  --region-id "cn-north-1"
```

#### Query User Quota

```bash
jdc --output json redis describe-user-quota \
  --region-id "cn-north-1"
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
  STATUS=$(jdc --output json redis describe-cache-instance \
    --region-id "$REGION" \
    --cache-instance-id "$INSTANCE_ID" | jq -r '.result.cacheInstance.status')
  
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

jdc --output json redis describe-cache-instances \
  --region-id "$REGION" \
  --page-number 1 \
  --page-size $PAGE_SIZE | jq -r '.result.cacheInstances[] | [.cacheInstanceId, .cacheInstanceName, .status] | @tsv'
```

### Create and Verify Instance

```bash
#!/bin/bash
REGION="cn-north-1"
NAME="test-redis-cluster"
SPEC="redis.cluster.g.micro"

# Create instance
INSTANCE_ID=$(jdc --output json redis create-cache-instance \
  --region-id "$REGION" \
  --cache-instance-name "$NAME" \
  --cache-instance-class "$SPEC" \
  --vpc-id "vpc-xxx" \
  --subnet-id "subnet-yyy" \
  --az-id-spec '{"azSpecifyType":"SpecifyByReplicaGroup","master":"cn-north-1a","slave":"cn-north-1b"}' \
  --cache-instance-type "cluster" \
  --redis-version "5.0" | jq -r '.result.cacheInstanceId')

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
| `configure not found` | CLI not configured | Run `jdc configure add` or manually create `~/.jdc/config` |
| `unrecognized arguments: --output json` | `--output` placed after subcommand | Move `--output json` to top-level: `jdc --output json redis ...` |
| `unrecognized arguments: --no-interactive` | `--no-interactive` not supported | Remove `--no-interactive` (all commands are non-interactive by default) |
| `PermissionError: [Errno 1] Operation not permitted: '/home/user/.jdc'` | Home directory not writable (sandbox) | Set `HOME=/tmp/jdc-home` and pre-create config files |
| `InvalidParameter` | Parameter format error | Check parameter syntax, use JSON for complex objects |
| `RegionId not found` | Invalid region | Use valid region: cn-north-1, cn-south-1, cn-east-2 |
| `Rate limit exceeded` | Too many requests | Slow down; CLI does not auto-retry rate limits |

### Credential Not Found

If `jdc` returns `Please use \`jdc configure add\` command to add cli configure first.`:

1. The CLI does NOT read `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` env vars
2. Check if `~/.jdc/config` exists and has correct INI format
3. For sandbox environments, export `HOME=/tmp/jdc-home` and pre-create the config
4. The `~/.jdc/current` file must contain exactly `default` (no trailing newline)

### JSON Parameter Syntax

- Complex parameters (arrays, objects) must be JSON strings
- Use single quotes for shell, escape internal quotes
- Example: `--az-id-spec '{"master":"cn-north-1a","slave":"cn-north-1b"}'`
- Arrays: `--backup-period '["Monday","Wednesday"]'`

### Debugging CLI Output

```bash
# Enable debug mode
jdc --debug --output json redis describe-cache-instance \
  --region-id "cn-north-1" \
  --cache-instance-id "redis-abc123"
```