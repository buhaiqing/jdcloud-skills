# JD Cloud VM Operations Skill

## Overview

This is an operational Skill for managing JD Cloud Virtual Machine (VM) resources, providing comprehensive capabilities including instance management, monitoring & alerting, troubleshooting, and automation integration.

## Features

- ✅ **Instance Management**: Create, start, stop, delete VM instances
- ✅ **Storage Management**: Cloud disk attachment, snapshot backup, disk expansion
- ✅ **Network Configuration**: Security group rules, Elastic IP, VPC configuration
- ✅ **Monitoring & Alerting**: Comprehensive monitoring for CPU, memory, disk, network
- ✅ **Troubleshooting**: Common issue diagnosis and solutions
- ✅ **Automation Integration**: SDK, MCP Server, Terraform, Ansible support

## Directory Structure

```
jdcloud-vm-ops/
├── SKILL.md                    # Skill main file
├── references/
│   ├── core-concepts.md        # Core concepts
│   ├── cli-usage.md            # CLI usage guide
│   ├── troubleshooting.md      # Troubleshooting guide
│   ├── monitoring.md           # Monitoring & alerts
│   └── integration.md          # Integration guide
└── assets/
    └── example-config.yaml     # Example configuration
```

## Quick Start

### 1. Install JD Cloud CLI

```bash
pip install jdcloud_cli
jdc config init
```

### 2. Configure Credentials

The Agent runtime MUST have the following environment variables configured:

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> The Agent MUST NOT ask the user for credential values. If not set, guide the user to configure via `jdc config init`. Never hardcode credentials in code or configuration files.

### 3. Query Instance List

```bash
jdc vm describe-instances \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
```

## Main Documents

### 📚 [Core Concepts](references/core-concepts.md)
Understand the core components, instance types, lifecycle, billing models, and more.

### 💻 [CLI Usage Guide](references/cli-usage.md)
Detailed command-line operations manual, including instance management, storage management, network configuration, etc.

### 🔧 [Troubleshooting](references/troubleshooting.md)
Diagnosis processes and solutions for common issues, including connectivity, performance, disk problems, etc.

### 📊 [Monitoring & Alerts](references/monitoring.md)
Monitoring metrics description, alert rule configuration, Dashboard setup, etc.

### 🔌 [Integration](references/integration.md)
SDK usage, MCP Server configuration, Terraform, Ansible, and other automation tool integration.

## Common Scenarios

### Scenario 1: Create a Web Server

```bash
# Create an instance
jdc vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --instance-type "g.n2.medium" \
  --image-id "img-xxxxx" \
  --name "web-server" \
  --primary-network-interface '{
    "subnetId": "subnet-xxxxx",
    "securityGroupIds": ["sg-xxxxx"]
  }' \
  --system-disk '{"diskCategory": "local", "diskSizeGB": 40}' \
  --charge-mode "postpaid_by_duration"

# Configure security group to allow HTTP/HTTPS
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 80,
    "toPort": 80,
    "addressPrefix": "0.0.0.0/0"
  }]'
```

### Scenario 2: Configure Monitoring Alerts

```bash
# CPU usage alert
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-CPU-Critical" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 90 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

### Scenario 3: Create Backup Snapshots

```bash
# Create a snapshot for the system disk
jdc disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --snapshot-name "backup-$(date +%Y%m%d)" \
  --description "Daily backup"
```

### Scenario 4: Troubleshoot Connectivity Issues

```bash
# Check instance status
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]'

# Check security group rules
jdc vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx

# Check EIP binding
jdc vpc describe-elastic-ips \
  --region-id cn-north-1 \
  | jq '.result.elasticIps[] | select(.instanceId == "i-xxxxx")'
```

## Best Practices

### 1. High Availability Deployment
- Distribute instances across multiple availability zones
- Use load balancer for traffic distribution
- Configure auto-scaling to handle traffic fluctuations

### 2. Security Hardening
- Use key pairs instead of passwords for login
- Follow the principle of least privilege when configuring security groups
- Regularly update system and application patches
- Enable cloud monitoring and security auditing

### 3. Cost Optimization
- Use subscription billing for long-running instances
- Use pay-as-you-go or spot instances for temporary tasks
- Regularly clean up unused resources (EIPs, disks, snapshots)
- Use tags for cost analysis

### 4. Backup Strategy
- Regularly create snapshots for critical data
- Replicate critical snapshots across regions
- Test snapshot recovery processes
- Retain an appropriate number of historical snapshots

### 5. Monitoring & Alerts
- Configure CPU, memory, disk, and network alerts
- Set reasonable thresholds to avoid alert fatigue
- Use different notification methods for different alert levels (warning/critical)
- Regularly verify that alerts are working correctly

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-28 | Initial version, includes basic operational guide |
| 1.0.1 | 2026-04-28 | Added complete CLI commands and troubleshooting guide |

## Related Resources

- [JD Cloud Official Documentation](https://docs.jdcloud.com)
- [VM Product Documentation](https://docs.jdcloud.com/cn/virtual-machines/)
- [API Documentation](https://docs.jdcloud.com/cn/api/vm/)
- [CLI Documentation](https://docs.jdcloud.com/cn/cli/)
- [SDK Downloads](https://github.com/jdcloud-api)

## Technical Support

If you encounter issues, you can get help through the following channels:

1. **Online Documentation**: https://docs.jdcloud.com
2. **Console Tickets**: Log in to JD Cloud Console to submit a ticket
3. **Customer Service Hotline**: 400-606-5500
4. **Online Chat**: Click the online chat button at the bottom right of the JD Cloud official website

## License

This project is licensed under the MIT License.
