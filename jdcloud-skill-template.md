---
name: jdcloud-[product-name]-ops
description: >-
  Manages JD Cloud [Product Name] resources. Use when you need to deploy, 
  configure, troubleshoot, or monitor [Product Name] instances on JD Cloud.
  Includes CLI usage, SDK integration, and operational best practices.
---

# JD Cloud [Product Name] Operations Skill

## Overview
[Product Name] is a core service on JD Cloud that provides [brief description of functionality]. This skill enables efficient operations, including automated deployment, real-time monitoring, and rapid troubleshooting.


## Changelog

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0.0 | 2026-04-28 | 初始版本，包含基础运维指南和参考模板 |

## Prerequisites
1. **Install JD Cloud CLI**:
   ```bash
   # Example installation command
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
- **Security**: Apply least-privilege IAM policies.
- **Cost Optimization**: Utilize auto-scaling and reserved instances where applicable.


---

# Appendix: Reference File Templates

## references/troubleshooting.md Template
```markdown
# Troubleshooting [Product Name]

## Common Error Codes
| Error Code | Description | Solution |
|------------|-------------|----------|
| `InvalidParameter` | A required parameter is missing. | Check the CLI command syntax. |
| `InsufficientBalance` | Account balance is insufficient. | Top up your JD Cloud account. |

## Diagnostic Steps
1. **Check Resource Status**: `jdc [product] describe-[resource]s --[resource]-ids [ID]`
2. **View System Logs**: Access via JD Cloud Console -> VNC (for VM) or product-specific log service.
3. **Network Connectivity**: Use `ping` and `telnet` from a bastion host to verify network access.
```

## references/monitoring.md Template
```markdown
# Monitoring [Product Name]

## Key Metrics
- **CPU Utilization**: `namespace/jcs.vm/cpu_usage`
- **Memory Usage**: `namespace/jcs.vm/memory_usage`
- **Disk I/O**: `namespace/jcs.vm/disk_read_bytes`

## Alert Configuration Example
```json
{
  "metricName": "cpu_usage",
  "threshold": 80,
  "comparisonOperator": ">",
  "period": 300
}
```
```

## references/integration.md Template
```markdown
# Integration & Tooling

## MCP Server Configuration
```json
{
  "mcpServers": {
    "jdcloud-[product]": {
      "command": "uvx", 
      "args": ["run", "--python", "3.10", "@jdcloud/[product]-mcp"],
      "env": {
        "JDC_ACCESS_KEY": "${JDC_ACCESS_KEY}",
        "JDC_SECRET_KEY": "${JDC_SECRET_KEY}",
        "JDC_REGION": "${JDC_REGION:-cn-north-1}"
      }
    }
  }
}
```
> Note: MCP servers are developed with Python 3.10+ and launched using `uvx` command. Environment variables should be set in your shell profile or CI/CD system. Never hardcode credentials in configuration files.

## SDK Initialization (Python)
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.[product].client import [Product]Client

# Use environment variables for secure credential management
credential = Credential(
    os.environ.get('JDC_ACCESS_KEY'), 
    os.environ.get('JDC_SECRET_KEY')
)
client = [Product]Client(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```
```
