# JD Cloud VM Quick Reference

> This document provides the most commonly used VM operations commands for quick reference. For detailed usage, refer to the [CLI Usage Guide](references/cli-usage.md).

## Instance Lifecycle Quick Reference

### 1. Query Instances
```bash
# List all instances
jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 20

# Specify an instance
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# Filter by status
jdc vm describe-instances --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]'
```

### 2. Create → Start → Stop → Delete
```bash
# Create instance (minimal configuration)
jdc vm create-instances --region-id cn-north-1 --az "cn-north-1a" \
  --instance-type "g.n2.medium" --image-id "img-xxxxx" --name "my-vm" \
  --primary-network-interface '[{"subnetId":"subnet-xxxxx","securityGroupIds":["sg-xxxxx"]}]' \
  --system-disk '[{"diskCategory":"local","diskSizeGB":40}]' \
  --charge-mode "postpaid_by_duration"

# Start / Stop / Reboot
jdc vm start-instance   --region-id cn-north-1 --instance-id i-xxxxx
jdc vm stop-instance    --region-id cn-north-1 --instance-id i-xxxxx
jdc vm reboot-instance  --region-id cn-north-1 --instance-id i-xxxxx

# Delete (add --delete-data-disks to also delete data disks)
jdc vm delete-instance --region-id cn-north-1 --instance-id i-xxxxx
```

## Network Configuration Quick Reference

### Elastic IP (EIP)
```bash
# Apply → Associate → Disassociate → Release
jdc vpc create-elastic-ip --region-id cn-north-1 --bandwidth-mbps 10 --charge-mode "postpaid_by_duration"
jdc vpc associate-elastic-ip    --region-id cn-north-1 --elastic-ip-id eip-xxxxx --instance-id i-xxxxx
jdc vpc disassociate-elastic-ip --region-id cn-north-1 --elastic-ip-id eip-xxxxx
jdc vpc delete-elastic-ip       --region-id cn-north-1 --elastic-ip-id eip-xxxxx
```

### Security Group Rules
```bash
# Add inbound rules (⚠️ Restrict IP range in production)
jdc vpc add-security-group-rules --region-id cn-north-1 --security-group-id sg-xxxxx \
  --rules '[{"direction":"ingress","protocol":"tcp","fromPort":22,"toPort":22,"addressPrefix":"0.0.0.0/0"}]'

# Delete rules
jdc vpc remove-security-group-rules --region-id cn-north-1 \
  --security-group-id sg-xxxxx --rule-ids '["rule-xxxxx"]'
```

## Storage Management Quick Reference

### Cloud Disk
```bash
# Create → Attach → Detach → Resize → Delete
jdc disk create-disk --region-id cn-north-1 --az "cn-north-1a" \
  --disk-type "ssd" --disk-size-gb 100 --disk-name "data-disk" --charge-mode "postpaid_by_duration"
jdc disk attach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx --device-name "/dev/vdb"
jdc disk detach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx
jdc disk resize-disk --region-id cn-north-1 --disk-id vol-xxxxx --disk-size-gb 200
jdc disk delete-disk --region-id cn-north-1 --disk-id vol-xxxxx
```

### Snapshots
```bash
# Create → Query → Delete
jdc disk create-snapshot --region-id cn-north-1 --disk-id vol-xxxxx --snapshot-name "backup-$(date +%Y%m%d)"
jdc disk describe-snapshots --region-id cn-north-1 --page-number 1 --page-size 20
jdc disk delete-snapshot --region-id cn-north-1 --snapshot-id snap-xxxxx
```

## Monitoring & Alerting Quick Reference

### Query Monitoring Data
```bash
# Linux
jdc monitor describe-metric-data --region-id cn-north-1 \
  --metric "vm.cpu.util" --service-code vm --resource-id i-xxxxx \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --aggr-type avg

# macOS
jdc monitor describe-metric-data --region-id cn-north-1 \
  --metric "vm.cpu.util" --service-code vm --resource-id i-xxxxx \
  --start-time "$(date -u -v -1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --aggr-type avg
```

### Alert Rules
```bash
# Create → Query → Delete
jdc monitor create-alarm --region-id cn-north-1 --alarm-name "CPU-High" \
  --service-code vm --resource-id i-xxxxx --metric-name "vm.cpu.util" \
  --comparison-operator "gt" --threshold 90 --period 300 --evaluation-periods 2 \
  --contact-group-id 1 --notice-type "sms,email"
jdc monitor describe-alarms --region-id cn-north-1 --page-number 1 --page-size 20
jdc monitor delete-alarm --region-id cn-north-1 --alarm-id alarm-xxxxx
```

## Common Monitoring Metrics

| Metric | Code | Unit | Description |
|--------|------|------|-------------|
| CPU Usage | vm.cpu.util | % | Average CPU usage rate |
| Memory Usage | vm.memory.usage | % | Memory usage percentage |
| Disk Usage | vm.disk.usage | % | Disk space usage rate |
| Network Inbound | vm.network.in.bytes | KB/s | Inbound traffic |
| Network Outbound | vm.network.out.bytes | KB/s | Outbound traffic |
| TCP Connections | vm.tcp.connections | count | Current TCP connections |
| System Load (1m) | vm.load.1m | - | 1-minute average load |
| Disk IOPS Read | vm.disk.iops.read | count/s | Disk read IOPS |
| Disk IOPS Write | vm.disk.iops.write | count/s | Disk write IOPS |

## Instance Status Description

| Status | Description | Actionable |
|--------|-------------|------------|
| running | Running | Stop, reboot, delete |
| stopped | Stopped | Start, delete |
| starting | Starting | Wait |
| stopping | Stopping | Wait |
| resizing | Resizing | Wait |
| error | Error | Check logs, delete |

## Common Region IDs

| Region | ID | Availability Zones |
|--------|-----|--------------------|
| Beijing (North) | cn-north-1 | cn-north-1a, cn-north-1b, cn-north-1c |
| Shanghai (East) | cn-east-1 | cn-east-1a, cn-east-1b, cn-east-1c |
| Guangzhou (South) | cn-south-1 | cn-south-1a, cn-south-1b |

## Instance Specifications Quick Reference

| Spec | CPU | Memory | Use Case |
|------|-----|--------|----------|
| g.n2.medium | 1 core | 2GB | Test, development |
| g.n2.large | 2 cores | 4GB | Small applications |
| g.n2.xlarge | 4 cores | 8GB | Medium applications |
| g.n2.2xlarge | 8 cores | 16GB | Large applications |
| g.n2.4xlarge | 16 cores | 32GB | High-performance computing |

> Note: Specification naming convention `g.n2.xxx`, where g=General purpose, n2=Generation 2, xxx=Size

## Recommended Alert Thresholds

| Metric | Warning | Critical | Description |
|--------|---------|----------|-------------|
| CPU Usage | > 75% | > 90% | Sustained for 5 minutes |
| Memory Usage | > 80% | > 95% | Sustained for 5 minutes |
| Disk Usage | > 70% | > 85% | Sustained for 5 minutes |
| System Load (1m) | > CPU cores x 2 | > CPU cores x 4 | Sustained for 3 minutes |
| Disk IOPS Usage | > 70% | > 90% | Sustained for 5 minutes |

## Common Ports and Security Recommendations

| Service | Port | Protocol | Security Recommendation |
|---------|------|----------|------------------------|
| SSH | 22 | TCP | ⚠️ Restrict IP range, disable root login |
| HTTP | 80 | TCP | Use with HTTPS |
| HTTPS | 443 | TCP | Enable TLS 1.2+ |
| RDP (Windows) | 3389 | TCP | ⚠️ Restrict IP range, use VPN |
| MySQL | 3306 | TCP | ⚠️ Do not expose publicly, use internal network |
| Redis | 6379 | TCP | ⚠️ Do not expose publicly, enable authentication |

### Security Group Best Practices
```bash
# ❌ Not recommended: Open to all IPs
# --rules '[{"direction":"ingress","protocol":"tcp","fromPort":22,"toPort":22,"addressPrefix":"0.0.0.0/0"}]'

# ✅ Recommended: Restrict IP range
# --rules '[{"direction":"ingress","protocol":"tcp","fromPort":22,"toPort":22,"addressPrefix":"192.168.1.0/24"}]'
```

## Troubleshooting Quick Reference

### SSH Connection Failure
```bash
# 1. Check instance status
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# 2. Check security group rules (verify port 22 is open and your IP is allowed)
jdc vpc describe-security-group --region-id cn-north-1 --security-group-id sg-xxxxx

# 3. Check EIP binding
jdc vpc describe-elastic-ips --region-id cn-north-1

# 4. Test connectivity locally
ping <EIP>
telnet <EIP> 22
```

### Disk Space Full
```bash
# 1. Check disk usage (execute inside the instance)
df -h

# 2. Find large files
du -sh /* 2>/dev/null | sort -rh | head -10

# 3. Clean up logs (use with caution)
find /var/log -name "*.log" -mtime +7 -delete

# 4. Resize cloud disk
jdc disk resize-disk --region-id cn-north-1 --disk-id vol-xxxxx --disk-size-gb 200
# After resizing, you need to extend the filesystem inside the instance (refer to detailed documentation)
```

### Performance Issues
```bash
# Execute inside the instance
# CPU
top -bn1 | head -20

# Memory
free -h

# Disk I/O
iostat -x 1 5 2>/dev/null || echo "Install sysstat: yum install sysstat"

# Network connections
ss -tuln | head -20

# Process resource usage
ps aux --sort=-%cpu | head -10
```

## Code Examples

### Python SDK Quick Start
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.client import VmClient
from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import DescribeInstancesRequest

# Initialize
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = VmClient(credential, 'cn-north-1')

# Query instances
request = DescribeInstancesRequest({
    "regionId": "cn-north-1",
    "pageNumber": 1,
    "pageSize": 20
})
response = client.describeInstances(request)

if response.error is None:
    for instance in response.result.instances:
        print(f"{instance.instanceId}: {instance.status}")
```

> Full SDK examples refer to: [Integration Guide](references/integration.md)

### Terraform Quick Configuration
```hcl
resource "jdcloud_vm_instance" "web" {
  region_id     = "cn-north-1"
  az            = "cn-north-1a"
  instance_type = "g.n2.medium"
  image_id      = "img-xxxxx"
  name          = "web-server"
  
  primary_network_interface {
    subnet_id          = "subnet-xxxxx"
    security_group_ids = ["sg-xxxxx"]
  }
  
  system_disk {
    disk_category = "local"
    disk_size_gb  = 40
  }
}
```

## Useful Tips

### Batch Operations
```bash
# Batch stop all running instances
jdc vm describe-instances --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]' \
  | jq -r '.result.instances[].instanceId' \
  | while read id; do
      echo "Stopping $id..."
      jdc vm stop-instance --region-id cn-north-1 --instance-id "$id"
    done

# Batch tag instances
for id in i-xxx1 i-xxx2 i-xxx3; do
  jdc vm modify-instance-attribute --region-id cn-north-1 \
    --instance-id "$id" --name "web-server"
done
```

### JSON Formatted Output
```bash
# Pretty print output
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]' | jq

# Extract key information
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0] | {
    id: .instanceId,
    name: .name,
    status: .status,
    privateIp: .primaryNetworkInterface.privateIpAddress,
    publicIp: .primaryNetworkInterface.elasticIp.publicIpAddress
  }'

# List all instances in table format
jdc vm describe-instances --region-id cn-north-1 \
  | jq -r '.result.instances[] | "\(.instanceId)\t\(.name)\t\(.status)\t\(.primaryNetworkInterface.privateIpAddress)"' \
  | column -t -s $'\t'
```

## Resource Limits & Billing

### Resource Quotas

| Resource | Default Quota | Limit | Description |
|----------|---------------|-------|-------------|
| Instance Count | 20 | Can be increased | Per region |
| EIP Count | 20 | Can be increased | Per region |
| Security Group Rules | 100/group | 200 | Inbound + Outbound |
| Snapshot Count | 100 | Can be increased | Per region |
| Cloud Disk Count | 20 | Can be increased | Max 16 disks per instance |
| Custom Images | 10 | 50 | Per region |

### Billing Models

| Billing Method | Use Case | Features |
|----------------|----------|----------|
| Subscription | Long-running | Discounted price, prepaid |
| Pay-as-you-go | Short-term/Testing | Per-second billing, flexible |
| Spot | Batch processing | Low price, may be reclaimed |

### Billing Items
- **Instance**: CPU + Memory
- **Cloud Disk**: Capacity x Duration (SSD costs more than HDD)
- **EIP**: Bandwidth fee + IP occupancy fee
- **Snapshots**: Actual storage capacity x Duration
- **Traffic**: Outbound traffic billed (inbound free)

## Related Documents

| Document | Description |
|----------|-------------|
| [CLI Usage Guide](references/cli-usage.md) | Complete CLI command reference |
| [Core Concepts](references/core-concepts.md) | Core concepts explanation |
| [Troubleshooting](references/troubleshooting.md) | Detailed troubleshooting guide |
| [Monitoring](references/monitoring.md) | Monitoring & alert configuration |
| [Integration](references/integration.md) | SDK/MCP integration |
| [Official Docs](https://docs.jdcloud.com/cn/virtual-machines/) | JD Cloud official documentation |
| [API Docs](https://docs.jdcloud.com/cn/api/vm/) | API reference documentation |
| [Console](https://console.jdcloud.com) | JD Cloud Console |
