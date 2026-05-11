---
name: jdcloud-cloudmonitor-quickstart
description: JD Cloud CloudMonitor Quick Start Tutorial
---

> **[中文版本](QUICK_START.md)** | **English Version**

# JD Cloud CloudMonitor Quick Start

## Table of Contents

1. [Overview](#overview)
2. [Environment Setup](#environment-setup)
3. [Core Concepts Overview](#core-concepts-overview)
4. [Prompt Tutorial](#prompt-tutorial)
5. [Appendix: CLI Command Reference](#appendix-cli-command-reference)
6. [Troubleshooting](#troubleshooting)

---

> **[中文版本](QUICK_START.md)** | **English Version**

---

## Overview

This tutorial will guide you from zero to using **JD Cloud CloudMonitor Operations Skill**. Through this tutorial, you will learn:

- Configure CloudMonitor environment using `.env` file
- Query monitoring metrics and create alarm rules through **natural language prompts**
- View alarm history and upload custom monitoring data
- (Advanced) Use CLI commands and Python SDK for advanced operations

> 💡 **Usage**: Send any **prompt from the tutorial below** to AI Agent for execution. No need to memorize CLI commands.

**Estimated Learning Time**: 10-15 minutes

---

## Environment Setup

### 1. Install JD Cloud CLI

**Recommended: Using uv (idempotent and reproducible)**

```bash
# Install uv (one-time system setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create isolated environment and install (idempotent, can be re-run)
uv venv --python 3.10
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install jdcloud_cli

# Verify installation
jdc --version
```

**Alternative: Using pip**

```bash
pip install jdcloud_cli
jdc --version
```

### 2. Configure Credentials

Credential configuration supports three methods, ordered by priority: **Shell environment variables > `.env` file > Interactive configuration**

**Method 1: `.env` file (Recommended for local development)**

Agent Runtime automatically loads `.env` file in project root directory, no manual loading needed.

```bash
# 1. Create .env file (project root)
cat > .env << 'EOF'
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
EOF

# 2. Ensure .gitignore contains .env (prevent committing to version control)
echo ".env" >> .gitignore

# 3. Verify file permissions (owner read/write only)
chmod 600 .env
```

> ⚠️ **Security Warning**: Never commit `.env` file to code repository! `.env` contains sensitive credential information, must be excluded in `.gitignore`.

> **🔒 Credential Masking Standard**: **NEVER** log, print, or expose `JDC_SECRET_KEY` value in logs, console output, or debug messages. When verifying credentials, only check existence (e.g., `[ -n "$JDC_SECRET_KEY" ]`). If logging credential status is needed, use masked placeholders like `JDC_SECRET_KEY=<masked>`.

**Method 2: Shell environment variables (Higher priority, can override `.env`)**

When both `.env` file and Shell environment variables exist, Shell environment variables take precedence:

```bash
export JDC_ACCESS_KEY="your_access_key_here"
export JDC_SECRET_KEY="your_secret_key_here"
export JDC_REGION="cn-north-1"
```

> 💡 **Use Case**: Production environments recommended to use Shell environment variables or secret management services, avoid credential file leakage.

**Method 3: Interactive configuration**

```bash
jdc config init
# Follow prompts to input Access Key, Secret Key, and default region
```

**Credential Priority Explanation**:

| Priority | Configuration Method | Description |
|----------|---------------------|-------------|
| 1 | Shell environment variables | Highest priority, overrides other configurations |
| 2 | `.env` file | Agent Runtime auto-loads |
| 3 | `jdc config` | CLI local configuration |

### 3. Verify Configuration

```bash
# Verify CLI configuration is correct
jdc monitor describe-services --region-id cn-north-1 --output json

# Expected output: Returns service list JSON
```

### 4. Install Python SDK (Optional, for complex automation)

**Using uv (Recommended)**

```bash
# Ensure uv environment is activated
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install jdcloud_sdk
```

**Using pip**

```bash
pip install jdcloud_sdk
```

---

### 5. Quick Verification of .env Configuration (Optional)

Create `verify_config.py` script to verify credentials:

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.core.exception import ClientException, ServerException

# SECURITY: NEVER print the actual secret_key value
access_key = os.environ.get('JDC_ACCESS_KEY')
secret_key = os.environ.get('JDC_SECRET_KEY')
region = os.environ.get('JDC_REGION', 'cn-north-1')

if not access_key or not secret_key:
    print("Error: Please configure JDC_ACCESS_KEY and JDC_SECRET_KEY")
    print("Method 1: Create .env file → Agent Runtime auto-loads")
    print("Method 2: source .env && python verify_config.py")
    exit(1)

credential = Credential(access_key, secret_key)
config = Config(timeout=30)
client = MonitorClient(config, credential, region)

try:
    result = client.describe_services()
    print(f"✅ Configuration successful! Region {region}, Service count: {len(result.result)}")
except ClientException as e:
    print(f"❌ Client error ({e.status}): {e.message}")
except ServerException as e:
    print(f"❌ Server error ({e.status}): {e.message}")
except Exception as e:
    print(f"❌ Unknown error: {e}")
```

Run verification:

```bash
# 1. Ensure .env file exists (don't print content to avoid credential leakage)
test -f .env && echo ".env file exists" || echo ".env file does not exist"

# 2. Method A: Load .env then run (manual scenario)
source .env && python verify_config.py

# 3. Method B: Agent Runtime auto-loads .env, just run directly
python verify_config.py
```

> **⚠️ Security Warning**: Never use `cat .env` or similar commands to print credential file content, this leaks sensitive information to console history.

> 💡 **Tip**: For most CLI commands, use `jdc <command> --help` to view all available parameters.

---

## Core Concepts Overview

Before starting operations, you need to understand these core concepts:

| Concept | Description | Example |
|---------|-------------|---------|
| **Service** | Monitorable cloud products | vm (VM), rds (Database), disk (Disk) |
| **Metric** | Specific monitoring metrics | vm.cpu.util (CPU usage), vm.memory.util (Memory usage) |
| **ResourceId** | Resource identifier being monitored | i-xxxxxxxx, disk-xxxxxxxx |
| **Alarm** | Monitoring condition + notification rules | Send SMS when CPU > 90% |
| **Period** | Data aggregation time window | 60 seconds, 300 seconds |

### Common Service Codes

| Service Code | Cloud Product |
|--------------|---------------|
| vm | Virtual Machine |
| rds | Cloud Database MySQL |
| disk | Cloud Disk |
| lb / nlb / alb | Load Balancer |
| redis | Distributed Cache |
| elasticsearch | Cloud Search |

### Common Monitoring Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| vm.cpu.util | CPU Usage | % |
| vm.memory.util | Memory Usage | % |
| vm.disk.util | Disk Usage | % |
| vm.network.in | Network Inbound Traffic | bps |
| vm.network.out | Network Outbound Traffic | bps |
| rds.cpu.util | RDS CPU Usage | % |
| rds.connection.util | RDS Connection Usage | % |

---

## Prompt Tutorial

Following prompts can be sent directly to AI Agent for execution. **No need to memorize CLI commands, just speak naturally**.

### Basic Operations

#### Query Monitoring Data

```
Query CPU and memory usage data for JD Cloud cn-north-1 region VM instance i-xxxxxxxx over the last 24 hours
```

> Supports multi-instance batch query, specify time range, specify aggregation method (avg / max / min).

#### Query Available Metrics

```
Query all available monitoring metrics for JD Cloud cn-north-1 region VM i-xxxxxxxx, output in table format
```

#### Query Latest Monitoring Snapshot

```
Query latest CPU, memory, disk, and network monitoring data for JD Cloud cn-north-1 region VM i-xxxxxxxx
```

#### Create Alarm Rule

```
Create alarm rule for JD Cloud cn-north-1 region VM i-xxxxxxxx:
- Alarm name: Production-CPU-Alarm
- Metric: CPU Usage
- Threshold: 80%
- Statistical period: 5 minutes
- Trigger after 2 consecutive periods exceeding threshold
- Notification method: SMS + Email
```

> Supports disk alarm, memory alarm, etc., just replace metric name and threshold.

#### View Alarm Details

```
View detailed information for JD Cloud alarm rule alarm-xxxxxxxx, including current status, trigger conditions, and notification settings
```

#### View Alarm History

```
Query all triggered alarms in JD Cloud cn-north-1 region over the past 7 days, count resources with most alarms
```

#### Delete Alarm Rule

```
Delete JD Cloud alarm rule alarm-xxxxxxxx, execute immediately after confirmation
```

#### Upload Custom Monitoring Data

```
Configure custom monitoring for order service:
1. Upload order count metric to JD Cloud Monitor (namespace custom.business, metric name order.count)
2. Create alarm: Order count < 100/minute for 5 minutes triggers notification
3. Query last 1 hour order volume data
```

---

### Comprehensive Scenarios

#### Scenario A: VM Daily Inspection

```
Perform monitoring inspection on all VMs in JD Cloud cn-north-1 region, query CPU, memory, disk usage for each instance,
find instances with resource usage over 80%, and provide optimization recommendations
```

**Expected Output**: Resource usage table, abnormal resource list, optimization recommendations

#### Scenario B: Database Performance Analysis

```
Analyze performance of JD Cloud cn-north-1 region RDS instance rds-xxxxxxxx:
1. Query CPU, memory, connection count, disk usage over last 24 hours
2. Find performance bottlenecks
3. Provide optimization recommendations
```

**Expected Output**: Performance metric trends, bottleneck analysis, optimization recommendations

#### Scenario C: Batch Alarm Rule Configuration

```
Create CPU alarms for all VMs tagged env=prod in JD Cloud cn-north-1 region:
- CPU usage > 80% for 5 minutes triggers alarm
- Notification method: SMS
- Alarm name format: Production-CPU-{instance_id}
```

---

## Appendix: CLI Command Reference

> Below are underlying CLI commands, for reference when manual execution or debugging is needed. Daily use recommended to directly use **Prompt Tutorial** above.

### Query Monitoring Service List

```bash
jdc monitor describe-services --region-id cn-north-1 --output json
```

### Query Available Metrics

```bash
jdc monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxxxxxxx \
  --output json
```

### Query Monitoring Data

```bash
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxxxxxxx \
  --start-time "2025-07-01T00:00:00+08:00" \
  --end-time "2025-07-01T12:00:00+08:00" \
  --aggr-type avg \
  --output json
```

### Create Alarm Rule

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-CPU-High-Alarm" \
  --service-code vm \
  --resource-id i-xxxxxxxx \
  --metric-name vm.cpu.util \
  --comparison-operator gt \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email" \
  --output json \
  --no-interactive
```

### View Alarms

```bash
# Query alarm list
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --service-code vm \
  --output json

# View alarm details
jdc monitor describe-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxxxxx \
  --output json
```

### View Alarm History

```bash
jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxxxxx \
  --start-time "2025-06-25T00:00:00+08:00" \
  --end-time "2025-07-01T23:59:59+08:00" \
  --output json
```

### Upload Custom Monitoring Data

```bash
jdc monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace "custom.business" \
  --metric-name "order.count" \
  --value 100 \
  --dimensions '{"service":"order-api"}' \
  --unit Count \
  --output json
```

---

## Troubleshooting

### Problem 1: CLI Command Returns Empty Results

**Possible Causes**:
- Resource ID does not exist
- No data in time range
- Query parameter error

**Troubleshooting Steps**:
```bash
# 1. Verify resource exists
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxxxxx"]' --output json

# 2. Verify metric name is correct
jdc monitor describe-metrics --region-id cn-north-1 --service-code vm --resource-id i-xxxxxxxx --output json
```

---

### Problem 2: Alarm Not Triggered

**Possible Causes**:
- Monitoring data not uploaded
- Threshold setting unreasonable
- Alarm disabled

**Troubleshooting Steps**:
```bash
# 1. Check alarm status
jdc monitor describe-alarm --region-id cn-north-1 --alarm-id alarm-xxxxxxxx --output json

# 2. Check if alarm is enabled
# 3. Verify monitoring data exists
```

---

### Problem 3: Credential Verification Failed

**Possible Causes**:
- `.env` file not created or path incorrect
- Shell environment variables not set
- Access Key / Secret Key incorrect
- Insufficient credential permissions

**Troubleshooting Steps**:
```bash
# 1. Check .env file exists (don't print content to avoid credential leakage)
test -f .env && echo ".env file exists" || echo ".env file does not exist"

# 2. Check environment variables exist (don't print actual values to avoid leakage)
# SECURITY: NEVER print the actual secret key value
if [ -n "$JDC_ACCESS_KEY" ] && [ -n "$JDC_SECRET_KEY" ]; then
    echo "Environment variables set (JDC_SECRET_KEY=<masked>)"
else
    echo "Error: JDC_ACCESS_KEY or JDC_SECRET_KEY not set"
fi

# 3. Verify .env file format is correct (no quotes allowed)
# Correct format: JDC_ACCESS_KEY=your_key_here
# Wrong format: JDC_ACCESS_KEY="your_key_here"  ❌

# 4. If using interactive configuration, reconfigure
jdc config init
```

> **⚠️ Security Warning**: Never use `cat .env` or `echo $JDC_SECRET_KEY` to print credential content, this leaks sensitive information to console history. Only check existence.

**Common `.env` File Errors**:

| Error | Description | Correct Format |
|-------|-------------|----------------|
| Quotes | Value wrapped in quotes | `JDC_ACCESS_KEY=xxx` |
| Spaces | Spaces around equals sign | `JDC_ACCESS_KEY=xxx` |
| Comments | Comments at line end | `JDC_ACCESS_KEY=xxx  # comment` |

---

### Problem 4: Permission Denied Error (403)

**Possible Causes**:
- Current credential lacks permission to access specified resource
- IAM policy not correctly configured

**Troubleshooting Steps**:
```bash
# 1. Check error message
jdc monitor describe-alarms --region-id cn-north-1 --service-code vm --output json

# 2. Verify credential permissions
# Login to JD Cloud Console → IAM → Check key permission policy
```

---

### Problem 5: Request Rate Limit (429)

**Possible Causes**:
- API call rate exceeds quota limit
- Too many requests in short time

**Troubleshooting Steps**:
```bash
# 1. Reduce request frequency, avoid large volume calls in short time
# 2. Use caching to reduce repeated queries
# 3. Contact customer service to apply for quota increase
```

---

### Problem 6: Network Connection Timeout

**Possible Causes**:
- Network unstable or firewall blocking
- JD Cloud service unavailable

**Troubleshooting Steps**:
```bash
# 1. Check network connection
ping jdcloud.com

# 2. Check proxy settings (if using proxy)
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 3. Retry operation
jdc monitor describe-services --region-id cn-north-1 --output json
```

---

## Advanced Learning

- [Core Concepts Details](jdcloud-cloudmonitor-ops/references/core-concepts.md) - Deep understanding of CloudMonitor features
- [CLI Usage Guide](jdcloud-cloudmonitor-ops/references/cli-usage.md) - Complete CLI command reference
- [API & SDK Reference](jdcloud-cloudmonitor-ops/references/api-sdk-usage.md) - SDK methods and API field descriptions
- [Monitoring Best Practices](jdcloud-cloudmonitor-ops/references/monitoring.md) - Monitoring configuration best practices
- [Troubleshooting Guide](jdcloud-cloudmonitor-ops/references/troubleshooting.md) - Common problem solutions

---

## Related Resources

- [JD Cloud Monitor Official Documentation](https://docs.jdcloud.com/cn/monitoring/)
- [JD Cloud CLI Documentation](https://docs.jdcloud.com/cn/cli/)
- [JD Cloud SDK GitHub](https://github.com/jdcloud-api)