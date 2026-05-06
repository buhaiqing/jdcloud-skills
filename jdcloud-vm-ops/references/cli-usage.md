# JD Cloud VM CLI Usage Guide

## Prerequisites and Conventions

**CRITICAL: CLI credential handling differs from SDK:**
- The `jdc` CLI reads credentials **only** from `~/.jdc/config` INI file
- Environment variables `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` are **ignored** by the CLI
- For sandbox environments, redirect `HOME` and pre-create config (see SKILL.md "Critical jdc CLI Behavioral Notes")

**Conventions for Agent Execution:**
- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json vm <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag
- Credentials: CLI uses `~/.jdc/config` INI, SDK uses env vars `JDC_ACCESS_KEY`/`JDC_SECRET_KEY`

### Basic Setup

```bash
# Install CLI
pip install jdcloud_cli

# Initialize CLI credentials (interactive, or use the manual config approach below)
# For sandbox:
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = vm.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current

# Verify configuration
jdc --output json vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 1
```

## Instance Management

### Query Instances

```bash
# Query all instances
jdc --output json vm describe-instances \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query by instance ID
jdc --output json vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]'

# Filter by name
jdc --output json vm describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"instance-name","values":["my-vm"]}]'

# Query instances with a specific status
jdc --output json vm describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]'
```

### Create Instance

```bash
# Create a single instance
jdc --output json vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --instance-type "g.n2.medium" \
  --image-id "img-xxxxx" \
  --name "my-vm" \
  --description "My first VM" \
  --primary-network-interface '{
    "subnetId": "subnet-xxxxx",
    "securityGroupIds": ["sg-xxxxx"],
    "networkInterfaceName": "eth0"
  }' \
  --system-disk '{
    "diskCategory": "local",
    "diskSizeGB": 40
  }' \
  --data-disks '[{
    "diskCategory": "cloud_ssd",
    "diskSizeGB": 100,
    "deviceName": "/dev/vdb",
    "autoDelete": true
  }]' \
  --key-names '["my-keypair"]' \
  --charge-mode "postpaid_by_duration"

# Batch create instances
jdc --output json vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --instance-type "g.n2.medium" \
  --image-id "img-xxxxx" \
  --name-prefix "web-server" \
  --count 3 \
  --primary-network-interface '{
    "subnetId": "subnet-xxxxx",
    "securityGroupIds": ["sg-xxxxx"]
  }' \
  --system-disk '{"diskCategory": "local", "diskSizeGB": 40}' \
  --charge-mode "postpaid_by_duration"
```

### Start / Stop Instance

```bash
# Start instance
jdc --output json vm start-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx

# Stop instance (normal shutdown)
jdc --output json vm stop-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx

# Force stop instance
jdc --output json vm stop-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --force-stop true

# Reboot instance
jdc --output json vm reboot-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx
```

### Delete Instance

```bash
# Delete a single instance
jdc --output json vm delete-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx

# Delete instance and release associated resources
jdc --output json vm delete-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --delete-data-disks true \
  --delete-snapshot true
```

### Resize Instance

```bash
# Resize instance specification
jdc --output json vm resize-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --instance-type "g.n2.large"

# Note: Resizing requires the instance to be in stopped state
jdc --output json vm stop-instance --region-id cn-north-1 --instance-id i-xxxxx
jdc --output json vm resize-instance --region-id cn-north-1 --instance-id i-xxxxx --instance-type "g.n2.large"
jdc --output json vm start-instance --region-id cn-north-1 --instance-id i-xxxxx
```

## Image Management

### Query Images

```bash
# Query public images
jdc --output json vm describe-images \
  --region-id cn-north-1 \
  --owners official \
  --page-number 1 \
  --page-size 20

# Query custom images
jdc --output json vm describe-images \
  --region-id cn-north-1 \
  --owners self

# Query specific image details
jdc --output json vm describe-images \
  --region-id cn-north-1 \
  --image-ids '["img-xxxxx"]'
```

### Create Custom Image

```bash
# Create image from an instance
jdc --output json vm create-image \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --name "my-custom-image" \
  --description "Custom image from production server"

# Create image from a snapshot
jdc --output json vm create-image \
  --region-id cn-north-1 \
  --snapshot-id "snap-xxxxx" \
  --name "my-snapshot-image" \
  --description "Image created from snapshot"
```

### Delete Image

```bash
jdc --output json vm delete-image \
  --region-id cn-north-1 \
  --image-id img-xxxxx
```

## Cloud Disk Management

### Query Cloud Disks

```bash
# List cloud disks
jdc --output json disk describe-disks \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query a specific cloud disk
jdc --output json disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]'

# Query disks attached to a specific instance
jdc --output json disk describe-disks \
  --region-id cn-north-1 \
  --filters '[{"name":"instance-id","values":["i-xxxxx"]}]'
```

### Create Cloud Disk

```bash
# Create a cloud disk
jdc --output json disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --disk-type "ssd" \
  --disk-size-gb 100 \
  --disk-name "data-disk-1" \
  --description "Data disk for database" \
  --charge-mode "postpaid_by_duration"

# Create a cloud disk and attach it to an instance
jdc --output json disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --disk-type "ssd" \
  --disk-size-gb 100 \
  --disk-name "data-disk-1" \
  --instance-id "i-xxxxx" \
  --device-name "/dev/vdb" \
  --charge-mode "postpaid_by_duration"
```

### Attach / Detach Cloud Disk

```bash
# Attach cloud disk
jdc --output json disk attach-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --instance-id i-xxxxx \
  --device-name "/dev/vdb"

# Detach cloud disk
jdc --output json disk detach-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --instance-id i-xxxxx
```

### Resize Cloud Disk

```bash
# Resize cloud disk (can only increase, cannot decrease)
jdc --output json disk resize-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --disk-size-gb 200

# Note: After resizing, you need to extend the filesystem inside the operating system
```

### Delete Cloud Disk

```bash
# Delete cloud disk (must detach first)
jdc --output json disk detach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx
jdc --output json disk delete-disk --region-id cn-north-1 --disk-id vol-xxxxx
```

## Snapshot Management

### Create Snapshot

```bash
# Create a snapshot for a cloud disk
jdc --output json disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --snapshot-name "backup-2026-04-28" \
  --description "Daily backup snapshot"

# Create snapshots for all cloud disks of an instance
jdc --output json disk create-snapshots \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --snapshot-name-prefix "instance-backup"
```

### Query Snapshots

```bash
# List snapshots
jdc --output json disk describe-snapshots \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query a specific snapshot
jdc --output json disk describe-snapshots \
  --region-id cn-north-1 \
  --snapshot-ids '["snap-xxxxx"]'

# Query snapshots for a specific cloud disk
jdc --output json disk describe-snapshots \
  --region-id cn-north-1 \
  --filters '[{"name":"disk-id","values":["vol-xxxxx"]}]'
```

### Delete Snapshot

```bash
jdc --output json disk delete-snapshot \
  --region-id cn-north-1 \
  --snapshot-id snap-xxxxx
```

### Create Cloud Disk from Snapshot

```bash
jdc --output json disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --snapshot-id "snap-xxxxx" \
  --disk-name "restored-disk" \
  --charge-mode "postpaid_by_duration"
```

## Security Group Management

### Query Security Groups

```bash
# List security groups
jdc --output json vpc describe-security-groups \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query specific security group details
jdc --output json vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx
```

### Create Security Group

```bash
jdc --output json vpc create-security-group \
  --region-id cn-north-1 \
  --vpc-id "vpc-xxxxx" \
  --security-group-name "web-sg" \
  --description "Security group for web servers"
```

### Add Security Group Rules

```bash
# Add inbound rule - Allow HTTP access
jdc --output json vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 80,
    "toPort": 80,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow HTTP"
  }]'

# Add inbound rule - Allow SSH access (recommend restricting IP range)
jdc --output json vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 22,
    "toPort": 22,
    "addressPrefix": "192.168.1.0/24",
    "description": "Allow SSH from office"
  }]'

# Add inbound rule - Allow HTTPS access
jdc --output json vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 443,
    "toPort": 443,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow HTTPS"
  }]'

# Add outbound rule - Allow all outbound traffic
jdc --output json vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "egress",
    "protocol": "-1",
    "fromPort": -1,
    "toPort": -1,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow all outbound"
  }]'
```

### Delete Security Group Rules

```bash
jdc --output json vpc remove-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rule-ids '["rule-xxxxx"]'
```

### Assign Instance to Security Group

```bash
# Assign security group to network interface
jdc --output json vpc assign-security-group \
  --region-id cn-north-1 \
  --network-interface-id "eni-xxxxx" \
  --security-group-id sg-xxxxx
```

## Key Pair Management

### Create Key Pair

```bash
# Create a key pair (private key will be downloaded automatically)
jdc --output json vm create-keypair \
  --region-id cn-north-1 \
  --key-name "my-keypair" \
  --description "Key pair for production servers"
```

### Query Key Pairs

```bash
# List key pairs
jdc --output json vm describe-keypairs \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query a specific key pair
jdc --output json vm describe-keypairs \
  --region-id cn-north-1 \
  --key-names '["my-keypair"]'
```

### Import Public Key

```bash
# Import an existing public key
jdc --output json vm import-keypair \
  --region-id cn-north-1 \
  --key-name "existing-keypair" \
  --public-key "ssh-rsa AAAAB3NzaC1yc2E... user@host"
```

### Delete Key Pair

```bash
jdc --output json vm delete-keypair \
  --region-id cn-north-1 \
  --key-name "my-keypair"
```

## Elastic IP Management

### Apply for EIP

```bash
jdc --output json vpc create-elastic-ip \
  --region-id cn-north-1 \
  --bandwidth-mbps 10 \
  --charge-mode "postpaid_by_duration" \
  --description "EIP for web server"
```

### Query EIPs

```bash
# List EIPs
jdc --output json vpc describe-elastic-ips \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query a specific EIP
jdc --output json vpc describe-elastic-ips \
  --region-id cn-north-1 \
  --elastic-ip-ids '["eip-xxxxx"]'
```

### Associate / Disassociate EIP

```bash
# Associate EIP with instance
jdc --output json vpc associate-elastic-ip \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx \
  --instance-id i-xxxxx

# Disassociate EIP
jdc --output json vpc disassociate-elastic-ip \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx
```

### Modify Bandwidth

```bash
jdc --output json vpc modify-elastic-ip-bandwidth \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx \
  --bandwidth-mbps 20
```

### Release EIP

```bash
jdc --output json vpc delete-elastic-ip \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx
```

## Useful Command Combinations

### View Instance Details (including IP, status, etc.)

```bash
jdc --output json vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' | jq '.result.instances[0] | {
    instanceId: .instanceId,
    name: .name,
    status: .status,
    privateIp: .primaryNetworkInterface.privateIpAddress,
    publicIp: .primaryNetworkInterface.elasticIp.publicIpAddress,
    instanceType: .instanceType,
    az: .az
  }'
```

### Batch Stop Instances

```bash
# Get all running instance IDs and stop them
jdc --output json vm describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]' \
  | jq -r '.result.instances[].instanceId' \
  | while read instance_id; do
      echo "Stopping instance: $instance_id"
      jdc --output json vm stop-instance --region-id cn-north-1 --instance-id "$instance_id"
    done
```

### Clean Up Unused EIPs

```bash
# Find and release unbound EIPs
jdc --output json vpc describe-elastic-ips \
  --region-id cn-north-1 \
  | jq -r '.result.elasticIps[] | select(.instanceId == null) | .elasticIpId' \
  | while read eip_id; do
      echo "Releasing EIP: $eip_id"
      jdc --output json vpc delete-elastic-ip --region-id cn-north-1 --elastic-ip-id "$eip_id"
    done
```

### Monitor Instance Resource Usage

```bash
# Query CPU usage (last 1 hour)
jdc --output json monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type avg
```

## Common Issue Troubleshooting

### Instance Cannot Connect

```bash
# 1. Check instance status
jdc --output json vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# 2. Check security group rules
jdc --output json vpc describe-security-group --region-id cn-north-1 --security-group-id sg-xxxxx

# 3. Check network interface
jdc --output json vpc describe-network-interface --region-id cn-north-1 --network-interface-id eni-xxxxx
```

### Disk Space Full

```bash
# 1. View current disk information
jdc --output json disk describe-disks --region-id cn-north-1 --filters '[{"name":"instance-id","values":["i-xxxxx"]}]'

# 2. Resize disk
jdc --output json disk resize-disk --region-id cn-north-1 --disk-id vol-xxxxx --disk-size-gb 200
```

## Best Practice Tips

1. **Use Tags for Resource Management**: Add tags to resources for better management and cost analysis
2. **Regular Snapshot Creation**: Regularly back up important data, preferably using automated scripts
3. **Proper Security Group Configuration**: Follow the principle of least privilege, only open necessary ports
4. **Monitor Resource Usage**: Set up alert rules to detect anomalies in time
5. **Use Key Pairs for Login**: More secure than passwords, prevents brute force attacks
6. **Multi-AZ Deployment**: Improve application availability
7. **Clean Up Unused Resources**: Regularly check and release unused EIPs, disks, etc.

## CLI vs SDK Coverage Gap

| Operation | SDK Available | CLI Available | Notes |
|-----------|---------------|---------------|-------|
| Create Instance | Yes | Yes | Full coverage |
| Describe Instances | Yes | Yes | Full coverage |
| Start/Stop/Reboot Instance | Yes | Yes | Full coverage |
| Delete Instance | Yes | Yes | Full coverage |
| Resize Instance | Yes | Yes | Full coverage |
| Describe Instance Types | Yes | Yes | Full coverage |
| Describe Images | Yes | Yes | Full coverage |
| Create/Delete Image | Yes | Yes | Full coverage |
| Key Pair Operations | Yes | Yes | Full coverage |
| Disk Operations | Yes | Yes | Use `disk` subcommand |
| Snapshot Operations | Yes | Yes | Use `disk` subcommand |

> **Note**: VM and Disk operations are fully covered by both SDK and CLI. No SDK-only operations for this product.

## Path Preference (CLI vs SDK)

| Scenario | Recommended Path | Reason |
|----------|------------------|--------|
| Quick ad-hoc operations | CLI | Faster iteration, less code |
| Automation scripts / CI/CD | SDK | Better error handling, retry logic |
| Complex multi-step workflows | SDK | Easier state management, conditional logic |
| No Python runtime available | CLI | CLI is standalone tool |
| Resource querying with jq | CLI | Native JSON output + jq pipeline |
| Integration tests | SDK | Easier to mock/assert responses |

> **Default preference for agent execution**: Prefer **SDK** for complex workflows; prefer **CLI** for simple queries.
