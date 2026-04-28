# JD Cloud VM Troubleshooting Guide

## Common Issues Quick Reference

| Issue Type | Possible Cause | Solution |
|-----------|---------------|----------|
| Cannot SSH | Security group port 22 not open | Check and add security group rule |
| Instance launch fails | Insufficient resources or configuration error | Check quota and configuration parameters |
| Disk attachment fails | Device name conflict or format error | Check device name and filesystem |
| Network unreachable | Route table or ACL configuration error | Check VPC network configuration |
| Performance degradation | High resource utilization | Monitor and optimize resource configuration |

## Connectivity Issues

### 1. SSH Connection Failure

#### Symptoms
```bash
ssh: connect to host x.x.x.x port 22: Connection timed out
# or
ssh: connect to host x.x.x.x port 22: Connection refused
```

#### Troubleshooting Steps

**Step 1: Check Instance Status**
```bash
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0].status'
```
Expected output: `"running"`

**Step 2: Check Security Group Rules**
```bash
# Get the instance's network interface ID
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0].primaryNetworkInterface.networkInterfaceId'

# Check security group inbound rules
jdc vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  | jq '.result.securityGroup.rules[] | select(.direction == "ingress")'
```

Ensure the following rule exists:
- Protocol: TCP
- Port: 22
- Source: Your IP range

**Step 3: Check EIP Binding**
```bash
jdc vpc describe-elastic-ips \
  --region-id cn-north-1 \
  | jq '.result.elasticIps[] | select(.instanceId == "i-xxxxx")'
```

**Step 4: Test Network Connectivity**
```bash
# Test from local machine
ping <EIP address>
telnet <EIP address> 22

# Test from another instance in the same VPC
ssh -i ~/.ssh/your-key.pem centos@<private IP>
```

#### Solutions

**Solution 1: Add Security Group Rule**
```bash
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 22,
    "toPort": 22,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow SSH"
  }]'
```

**Solution 2: Use VNC Login (Emergency)**
1. Log in to the JD Cloud Console
2. Go to the VM instance details page
3. Click "Remote Connection" -> "VNC Login"
4. Log in with username and password

**Solution 3: Check Firewall Configuration**
After logging in via VNC, check the system firewall:
```bash
# CentOS/RHEL
sudo systemctl status firewalld
sudo firewall-cmd --list-all

# Ubuntu
sudo ufw status
```

### 2. RDP Connection Failure (Windows Instances)

#### Symptoms
Remote Desktop connection timeout or refused

#### Troubleshooting Steps

**Step 1: Check Security Group Rules**
Ensure port 3389 is open:
```bash
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 3389,
    "toPort": 3389,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow RDP"
  }]'
```

**Step 2: Check Windows Firewall**
Log in via VNC and verify Remote Desktop service is enabled:
```powershell
# PowerShell
Get-Service TermService
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
```

## Instance Launch Issues

### 1. Instance Creation Failed

#### Common Error Codes

| Error Code | Description | Solution |
|-----------|-------------|----------|
| `InvalidInstanceType` | Instance type does not exist or is not supported | Query available instance types |
| `InvalidImageId` | Invalid image ID | Check if the image ID is correct |
| `InsufficientResource` | Insufficient resources in the availability zone | Switch to another availability zone |
| `InvalidSubnetId` | Invalid subnet ID | Check if the subnet exists in the specified VPC |
| `QuotaExceeded` | Quota limit exceeded | Apply for a quota increase |

#### Troubleshooting Steps

**Step 1: Verify Instance Type**
```bash
jdc vm describe-instance-types \
  --region-id cn-north-1 \
  | jq '.result.instanceTypes[] | select(.instanceType == "g.n2.medium")'
```

**Step 2: Verify Image**
```bash
jdc vm describe-images \
  --region-id cn-north-1 \
  --image-ids '["img-xxxxx"]'
```

**Step 3: Verify Subnet**
```bash
jdc vpc describe-subnet \
  --region-id cn-north-1 \
  --subnet-id subnet-xxxxx
```

**Step 4: Check Quota**
```bash
jdc vm describe-quota \
  --region-id cn-north-1
```

#### Solutions

**Solution 1: Choose Another Availability Zone**
```bash
# Query availability zones
jdc vm describe-azs --region-id cn-north-1

# Create instance in another AZ
jdc vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1b" \
  ...
```

**Solution 2: Request Quota Increase**
Contact JD Cloud customer service or submit a ticket through the console to request a quota increase.

### 2. Instance Stops Automatically After Launch

#### Possible Causes
- System crash
- Out of Memory (OOM)
- Kernel panic

#### Troubleshooting Steps

**Step 1: View Instance Status History**
```bash
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0]'
```

**Step 2: Check System Logs via VNC**
1. Log in to the instance using VNC
2. Check system logs:
```bash
# Linux
dmesg | tail -50
journalctl -xe --no-pager | tail -100

# Check for OOM records
grep -i "out of memory" /var/log/messages
```

**Step 3: Check Resource Usage**
```bash
# Check memory usage
free -h

# Check CPU load
top -bn1 | head -20

# Check disk space
df -h
```

#### Solutions

**Solution 1: Upgrade Instance Specification**
```bash
jdc vm stop-instance --region-id cn-north-1 --instance-id i-xxxxx
jdc vm resize-instance --region-id cn-north-1 --instance-id i-xxxxx --instance-type "g.n2.large"
jdc vm start-instance --region-id cn-north-1 --instance-id i-xxxxx
```

**Solution 2: Optimize Application Configuration**
- Adjust application memory limits
- Optimize database configuration
- Clean up unnecessary processes and services

## Disk Issues

### 1. Disk Attachment Failed

#### Symptoms
```bash
Error attaching disk: Device or resource busy
# or
mount: wrong fs type, bad option, bad superblock
```

#### Troubleshooting Steps

**Step 1: Check Disk Status**
```bash
jdc disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]' \
  | jq '.result.disks[0] | {status, instanceId}'
```

**Step 2: Check Device Name Conflict**
```bash
# Check used devices inside the instance
lsblk
fdisk -l
```

**Step 3: Check Filesystem**
```bash
# Check filesystem type
file -s /dev/vdb

# If it's a new disk, create a filesystem
sudo mkfs.ext4 /dev/vdb
```

#### Solutions

**Solution 1: Use Correct Device Name**
```bash
# Detach and reattach with a different device name
jdc disk detach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx
jdc disk attach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx --device-name "/dev/vdc"
```

**Solution 2: Format New Disk**
```bash
# Create ext4 filesystem
sudo mkfs.ext4 /dev/vdb

# Create mount point
sudo mkdir /data

# Mount the disk
sudo mount /dev/vdb /data

# Configure auto-mount on boot
echo '/dev/vdb /data ext4 defaults 0 0' | sudo tee -a /etc/fstab
```

### 2. Disk Space Full

#### Symptoms
```bash
No space left on device
```

#### Troubleshooting Steps

**Step 1: Check Disk Usage**
```bash
df -h
du -sh /* | sort -rh | head -10
```

**Step 2: Find Large Files**
```bash
# Find files larger than 100MB
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null

# Find the 10 largest directories
du -ah / | sort -rh | head -10
```

**Step 3: Check Log Files**
```bash
# Check log file sizes
ls -lh /var/log/

# Clean up old logs
sudo journalctl --vacuum-time=7d
```

#### Solutions

**Solution 1: Clean Up Space**
```bash
# Clean package manager cache
sudo yum clean all  # CentOS
sudo apt-get clean  # Ubuntu

# Delete temporary files
sudo rm -rf /tmp/*

# Clean Docker resources (if used)
docker system prune -a
```

**Solution 2: Resize Disk**
```bash
# Resize disk via console or CLI
jdc disk resize-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --disk-size-gb 200

# Extend filesystem inside the OS
# For ext4
sudo growpart /dev/vda 1
sudo resize2fs /dev/vda1

# For xfs
sudo growpart /dev/vda 1
sudo xfs_growfs /
```

## Network Issues

### 1. Instance Cannot Access Internet

#### Troubleshooting Steps

**Step 1: Check Route Table**
```bash
# Inside the instance
ip route show
route -n

# Should have a default route pointing to the gateway
default via 192.168.1.1 dev eth0
```

**Step 2: Check DNS Configuration**
```bash
cat /etc/resolv.conf

# Test DNS resolution
nslookup www.jdcloud.com
dig www.jdcloud.com
```

**Step 3: Check NAT Gateway**
```bash
# If using NAT gateway, check configuration
jdc vpc describe-nat-gateways \
  --region-id cn-north-1 \
  --vpc-id vpc-xxxxx
```

**Step 4: Test Network Connectivity**
```bash
# Test internal network connectivity
ping 192.168.1.1

# Test external network connectivity
ping 8.8.8.8

# Trace route
traceroute www.jdcloud.com
```

#### Solutions

**Solution 1: Configure DNS**
```bash
# Edit DNS configuration
sudo vi /etc/resolv.conf

# Add JD Cloud DNS
nameserver 10.0.0.2
nameserver 8.8.8.8
```

**Solution 2: Configure NAT Gateway**
If the subnet has no public internet access, configure a NAT gateway:
```bash
jdc vpc create-nat-gateway \
  --region-id cn-north-1 \
  --vpc-id vpc-xxxxx \
  --nat-gateway-name "my-nat" \
  --spec "small"
```

### 2. Instances in VPC Cannot Communicate

#### Troubleshooting Steps

**Step 1: Check Security Group Rules**
```bash
# Ensure security group allows VPC internal communication
jdc vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  | jq '.result.securityGroup.rules[]'
```

**Step 2: Check Network ACLs**
```bash
jdc vpc describe-network-acls \
  --region-id cn-north-1 \
  --vpc-id vpc-xxxxx
```

**Step 3: Test Connectivity**
```bash
# Ping instance B from instance A
ping <Instance B's private IP>

# Test specific port using telnet
telnet <Instance B's private IP> 80
```

#### Solutions

**Solution 1: Add Security Group Rule for VPC Internal Communication**
```bash
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "-1",
    "fromPort": -1,
    "toPort": -1,
    "addressPrefix": "192.168.0.0/16",
    "description": "Allow VPC internal traffic"
  }]'
```

## Performance Issues

### 1. High CPU Usage

#### Troubleshooting Steps

**Step 1: View CPU Usage Details**
```bash
# Real-time monitoring
top

# View historical data
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type avg
```

**Step 2: Identify High CPU Processes**
```bash
# Sort by CPU usage
ps aux --sort=-%cpu | head -10

# View process tree
pstree -p
```

**Step 3: Analyze System Calls**
```bash
# Install sysstat
sudo yum install sysstat

# View detailed CPU usage
mpstat -P ALL 1 5
```

#### Solutions

**Solution 1: Optimize Application**
- Analyze and optimize high CPU-consuming code
- Adjust thread pool size
- Optimize algorithm complexity

**Solution 2: Upgrade Instance Specification**
```bash
jdc vm resize-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --instance-type "g.n2.xlarge"
```

### 2. High Memory Usage

#### Troubleshooting Steps

**Step 1: View Memory Usage**
```bash
free -h
cat /proc/meminfo
```

**Step 2: Identify Memory Leaks**
```bash
# Sort by memory usage
ps aux --sort=-%mem | head -10

# Monitor memory changes
watch -n 1 'free -h'
```

**Step 3: Check Swap Usage**
```bash
swapon --show
cat /proc/swaps
```

#### Solutions

**Solution 1: Clear Cache**
```bash
# Clean page cache
sudo sync
sudo echo 3 > /proc/sys/vm/drop_caches
```

**Solution 2: Restart Application**
```bash
# Restart memory-heavy services
sudo systemctl restart your-service
```

**Solution 3: Increase Memory**
```bash
jdc vm resize-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --instance-type "r.n2.large"  # Memory-optimized instance
```

### 3. Low Disk I/O Performance

#### Troubleshooting Steps

**Step 1: Monitor Disk I/O**
```bash
# Real-time I/O monitoring
iostat -x 1 5

# Check I/O wait
vmstat 1 10
```

**Step 2: Identify I/O Intensive Processes**
```bash
# Use iotop
sudo yum install iotop
sudo iotop
```

**Step 3: Check Disk Type**
```bash
jdc disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]' \
  | jq '.result.disks[0].diskType'
```

#### Solutions

**Solution 1: Upgrade to SSD Cloud Disk**
```bash
# Create a new SSD cloud disk
jdc disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --disk-type "ssd" \
  --disk-size-gb 100

# Migrate data and switch
```

**Solution 2: Optimize Application I/O**
- Use asynchronous I/O
- Add caching layers
- Batch writes instead of frequent small file writes

## Snapshot and Backup Issues

### 1. Snapshot Creation Failed

#### Possible Causes
- Disk is performing another operation
- Insufficient quota
- Abnormal disk status

#### Solutions

**Step 1: Check Disk Status**
```bash
jdc disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]' \
  | jq '.result.disks[0].status'
```

**Step 2: Retry Creating Snapshot**
```bash
jdc disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --snapshot-name "retry-snapshot"
```

### 2. Snapshot Restore Failed

#### Solutions

**Step 1: Verify Snapshot Integrity**
```bash
jdc disk describe-snapshots \
  --region-id cn-north-1 \
  --snapshot-ids '["snap-xxxxx"]' \
  | jq '.result.snapshots[0].status'
```

**Step 2: Check Target Availability Zone Resources**
```bash
jdc vm describe-azs --region-id cn-north-1
```

## Common Diagnostic Commands

### System Level
```bash
# System information
uname -a
cat /etc/os-release

# CPU information
lscpu
cat /proc/cpuinfo

# Memory information
free -h
cat /proc/meminfo

# Disk information
lsblk
fdisk -l
df -h

# Network information
ip addr show
ip route show
cat /etc/resolv.conf

# Process information
ps aux
top -bn1

# System load
uptime
w
```

### Log Viewing
```bash
# System logs
tail -f /var/log/messages      # CentOS
tail -f /var/log/syslog        # Ubuntu

# Kernel logs
dmesg | tail -50

# Authentication logs
tail -f /var/log/secure        # CentOS
tail -f /var/log/auth.log      # Ubuntu

# systemd logs
journalctl -xe --no-pager
journalctl -u your-service -f
```

### Network Diagnostics
```bash
# Connectivity test
ping -c 4 <target>
traceroute <target>

# Port test
telnet <host> <port>
nc -zv <host> <port>

# DNS test
nslookup <domain>
dig <domain>

# Network statistics
netstat -tuln
ss -tuln
```

## Getting Technical Support

### Self-Service
1. **JD Cloud Documentation**: https://docs.jdcloud.com
2. **API Documentation**: https://docs.jdcloud.com/cn/api
3. **CLI Documentation**: https://docs.jdcloud.com/cn/cli

### Contact Support
1. **Console Tickets**: Log in to JD Cloud Console to submit a ticket
2. **Customer Service Hotline**: 400-606-5500
3. **Online Chat**: Click the online chat button at the bottom right of the JD Cloud official website

### Information to Provide
When submitting a ticket, please provide the following information:
- Instance ID
- Time the issue occurred
- Screenshot of error message
- Troubleshooting steps already performed
- Relevant log snippets
