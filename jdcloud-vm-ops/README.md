---
name: jdcloud-vm-ops
version: 1.0.1
description: Manage JD Cloud Virtual Machine resources, including instance management, monitoring, troubleshooting, and automation integration.
---

# JD Cloud VM Operations Skill

## Overview

Operational Skill for managing JD Cloud VM resources, providing instance management, monitoring & alerting, troubleshooting, and automation integration.

## Core Features

- ✅ Instance Management: Create, start, stop, delete
- ✅ Storage Management: Cloud disk, snapshots, disk expansion
- ✅ Network Configuration: Security groups, EIP, VPC
- ✅ Monitoring & Alerting: CPU, memory, disk, network
- ✅ Troubleshooting: Common issue diagnosis
- ✅ Automation: SDK, MCP Server, Terraform, Ansible

## Directory Structure

```
jdcloud-vm-ops/
├── SKILL.md
├── references/
│   ├── core-concepts.md
│   ├── cli-usage.md
│   ├── troubleshooting.md
│   ├── monitoring.md
│   └── integration.md
└── assets/example-config.yaml
```

## Trigger & Scope

### SHOULD Use

- Create, start, stop, reboot, delete VM instances
- Manage cloud disks and snapshots (create, attach, expand, delete)
- Configure security group rules and EIP
- Query instance status and monitoring metrics
- Troubleshoot: connectivity, performance, disk issues

### SHOULD NOT Use

- Cross-product operations (delegate to jdcloud-vpc-ops + jdcloud-vm-ops + jdcloud-cloudmonitor-ops)
- Batch automation (use Terraform/Ansible)
- Advanced network config (use jdcloud-vpc-ops)
- Alert rule management (use jdcloud-cloudmonitor-ops)

## Quick Start

### 1. Install CLI

```bash
pip install jdcloud_cli
jdc config init
```

### 2. Configure Credentials

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> Agent MUST NOT ask user for credentials. If not set, guide user to configure via `jdc config init`. Never hardcode credentials.

### 3. Query Instances

```bash
jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 20
```

## Main Documents

- [Core Concepts](references/core-concepts.md) - Instance types, lifecycle, billing
- [CLI Usage](references/cli-usage.md) - Instance, storage, network management
- [Troubleshooting](references/troubleshooting.md) - Connectivity, performance, disk issues
- [Monitoring](references/monitoring.md) - Metrics, alerts, dashboards
- [Integration](references/integration.md) - SDK, MCP Server, Terraform

## Common Scenarios

### Scenario 1: Create Web Server

```bash
jdc vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --instance-type "g.n2.medium" \
  --image-id "img-xxxxx" \
  --name "web-server" \
  --primary-network-interface '{"subnetId": "subnet-xxxxx", "securityGroupIds": ["sg-xxxxx"]}' \
  --system-disk '{"diskCategory": "local", "diskSizeGB": 40}' \
  --charge-mode "postpaid_by_duration"

# Configure security group
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{"direction": "ingress", "protocol": "tcp", "fromPort": 80, "toPort": 80, "addressPrefix": "0.0.0.0/0"}]'
```

### Scenario 2: Configure Monitoring Alert

```bash
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

### Scenario 3: Create Snapshot Backup

```bash
jdc disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --snapshot-name "backup-$(date +%Y%m%d)" \
  --description "Daily backup"
```

### Scenario 4: Troubleshoot Connectivity

```bash
# Check instance status
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# Check security group
jdc vpc describe-security-group --region-id cn-north-1 --security-group-id sg-xxxxx

# Check EIP binding
jdc vpc describe-elastic-ips --region-id cn-north-1 | jq '.result.elasticIps[] | select(.instanceId == "i-xxxxx")'
```

## Best Practices

### 1. High Availability
- Distribute across AZs
- Use load balancer
- Configure auto-scaling

### 2. Security
- Use key pairs, not passwords
- Least privilege for security groups
- Regular patch updates
- Enable monitoring & auditing

### 3. Cost Optimization
- Subscription for long-running
- Pay-as-you-go for temporary
- Clean up unused resources
- Use tags for cost analysis

### 4. Backup Strategy
- Regular snapshots for critical data
- Cross-region replication
- Test recovery process
- Retain appropriate history

### 5. Monitoring
- Configure CPU/memory/disk/network alerts
- Reasonable thresholds
- Different notification for levels
- Regular verification

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-28 | Initial version |
| 1.0.1 | 2026-04-28 | Added CLI commands and troubleshooting |

## Related Resources

- [Official Docs](https://docs.jdcloud.com)
- [VM Product](https://docs.jdcloud.com/cn/virtual-machines/)
- [API Docs](https://docs.jdcloud.com/cn/api/vm/)
- [CLI Docs](https://docs.jdcloud.com/cn/cli/)
- [SDK](https://github.com/jdcloud-api)
