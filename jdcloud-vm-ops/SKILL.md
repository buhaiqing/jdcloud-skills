---
name: jdcloud-vm-ops
description: >-
  Manages JD Cloud Virtual Machine resources. Use when you need to deploy, 
  configure, troubleshoot, or monitor VM instances on JD Cloud.
  Includes CLI usage, SDK integration, and operational best practices.
---

# JD Cloud VM Operations Skill

## Overview
JD Cloud Virtual Machine (VM) is a core computing service that provides elastic, scalable, and secure cloud servers. This skill enables efficient operations, including automated deployment, real-time monitoring, and rapid troubleshooting of VM resources.

## Changelog

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0.0 | 2026-04-28 | 初始版本，包含基础运维指南和参考模板 |
| 1.0.1 | 2026-04-28 | 添加VM实例管理、网络配置、安全组操作指南 |

## Prerequisites
1. **Install JD Cloud CLI**:
   ```bash
   # Install JD Cloud CLI
   pip install jdcloud-cli
   jdc config init
   ```
2. **Configure Credentials**:
   Set environment variables for secure credential management:
   ```bash
   export JDC_ACCESS_KEY="your_access_key_here"
   export JDC_SECRET_KEY="your_secret_key_here"
   export JDC_REGION="cn-north-1"  # Default region
   ```
   Alternatively, configure via CLI interactive setup:
   ```bash
   jdc config init  # Will prompt for credentials securely
   ```

## Reference Directory
- [Core Concepts](references/core-concepts.md)
- [CLI Usage](references/cli-usage.md)
- [Troubleshooting Guide](references/troubleshooting.md)
- [Monitoring & Alerts](references/monitoring.md)
- [Integration (MCP/SDK)](references/integration.md)

## Operational Best Practices
- **High Availability**: Always deploy across multiple availability zones.
- **Security**: Apply least-privilege IAM policies and regularly update security groups.
- **Cost Optimization**: Utilize auto-scaling and reserved instances where applicable.
- **Backup Strategy**: Regularly create snapshots of critical VM instances.
- **Resource Tagging**: Tag VM resources for better organization and cost tracking.