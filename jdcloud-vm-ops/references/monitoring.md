# JD Cloud VM Monitoring & Alerts Guide

## Monitoring Overview

JD Cloud Monitor provides comprehensive VM instance monitoring capabilities, including basic monitoring, OS monitoring, and custom monitoring. Through proper monitoring configuration and alert policies, potential issues can be detected and resolved in a timely manner.

## Core Monitoring Metrics

### 1. CPU-Related Metrics

| Metric Name | Metric Code | Unit | Description |
|------------|-------------|------|-------------|
| CPU Usage | vm.cpu.util | % | Average CPU usage rate |
| CPU Load (1 min) | vm.cpu.load1 | - | 1-minute system load |
| CPU Load (5 min) | vm.cpu.load5 | - | 5-minute system load |
| CPU Load (15 min) | vm.cpu.load15 | - | 15-minute system load |
| CPU Idle | vm.cpu.idle | % | CPU idle percentage |
| CPU User Mode | vm.cpu.user | % | User mode CPU usage |
| CPU System Mode | vm.cpu.system | % | System mode CPU usage |
| CPU I/O Wait | vm.cpu.iowait | % | CPU time waiting for I/O |

### 2. Memory-Related Metrics

| Metric Name | Metric Code | Unit | Description |
|------------|-------------|------|-------------|
| Memory Usage | vm.memory.util | % | Memory usage percentage |
| Used Memory | vm.memory.used | MB | Amount of used memory |
| Available Memory | vm.memory.available | MB | Amount of available memory |
| Cached Memory | vm.memory.cached | MB | Memory used for caching |
| Swap Usage | vm.swap.util | % | Swap partition usage rate |

### 3. Disk-Related Metrics

| Metric Name | Metric Code | Unit | Description |
|------------|-------------|------|-------------|
| Disk Usage | vm.disk.util | % | Disk space usage rate |
| Disk Read Rate | vm.disk.read.bytes | KB/s | Disk read speed |
| Disk Write Rate | vm.disk.write.bytes | KB/s | Disk write speed |
| Disk Read IOPS | vm.disk.read.iops | ops/s | Read operations per second |
| Disk Write IOPS | vm.disk.write.iops | ops/s | Write operations per second |
| Disk Read Latency | vm.disk.read.latency | ms | Average read operation latency |
| Disk Write Latency | vm.disk.write.latency | ms | Average write operation latency |

### 4. Network-Related Metrics

| Metric Name | Metric Code | Unit | Description |
|------------|-------------|------|-------------|
| Network Inbound | vm.network.in.bytes | KB/s | Inbound traffic rate |
| Network Outbound | vm.network.out.bytes | KB/s | Outbound traffic rate |
| Network Inbound Packets | vm.network.in.packets | packets/s | Inbound packet rate |
| Network Outbound Packets | vm.network.out.packets | packets/s | Outbound packet rate |
| TCP Connections | vm.tcp.connections | count | Current TCP connections |
| New TCP Connections | vm.tcp.new.connections | connections/s | New TCP connections per second |

### 5. System-Related Metrics

| Metric Name | Metric Code | Unit | Description |
|------------|-------------|------|-------------|
| System Uptime | vm.uptime | seconds | Running time since boot |
| Total Processes | vm.process.count | count | Number of running processes |
| Logged-in Users | vm.user.login | count | Number of currently logged-in users |

## Querying Monitoring Data

### CLI Method

#### Query Single Metric

```bash
# Query CPU usage (last 1 hour)
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type avg \
  --period 60
```

#### Query Multiple Metrics

```bash
# Query CPU and memory usage simultaneously
jdc monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxxxx \
  --metrics '["vm.cpu.util", "vm.memory.util", "vm.disk.util"]'
```

#### Query Historical Data

```bash
# Query CPU usage for the past 24 hours, aggregated by 5 minutes
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type avg \
  --period 300
```

#### Query Specific Time Range

```bash
# Query data for a specific time period
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time "2026-04-28T00:00:00Z" \
  --end-time "2026-04-28T23:59:59Z" \
  --aggr-type max
```

### SDK Method (Python)

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest
import os
from datetime import datetime, timedelta

# Initialize client
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = MonitorClient(credential, 'cn-north-1')

# Build request
request = DescribeMetricDataRequest({
    "regionId": "cn-north-1",
    "metric": "vm.cpu.util",
    "serviceCode": "vm",
    "resourceId": "i-xxxxx",
    "startTime": (datetime.utcnow() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "endTime": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    "aggrType": "avg",
    "period": 60
})

# Send request
response = client.describeMetricData(request)

# Process results
if response.error is None:
    for data in response.result.metricDatas:
        print(f"Time: {data.timestamp}, CPU Usage: {data.value}%")
else:
    print(f"Error: {response.error.message}")
```

## Alert Configuration

### Alert Levels

| Level | Description | Recommended Notification |
|-------|-------------|------------------------|
| Critical | Requires immediate action | SMS + Phone + Email |
| Warning | Requires attention | Email + IM notification |
| Info | General notification | Email |

### Common Alert Rules

#### 1. CPU Usage Alert

```bash
# CPU usage > 80% (Warning)
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-CPU-Warning" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 3 \
  --contact-group-id 1 \
  --notice-type "email" \
  --description "CPU usage exceeds 80%"

# CPU usage > 90% (Critical)
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
  --notice-type "sms,email" \
  --description "CPU usage exceeds 90%"
```

**Recommended Thresholds**:
- Warning: CPU > 70-80%
- Critical: CPU > 90%
- Statistic period: 5 minutes
- Consecutive times: 2-3

#### 2. Memory Usage Alert

```bash
# Memory usage > 85% (Warning)
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-Memory-Warning" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.memory.util" \
  --comparison-operator "gt" \
  --threshold 85 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "email" \
  --description "Memory usage exceeds 85%"

# Memory usage > 95% (Critical)
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-Memory-Critical" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.memory.util" \
  --comparison-operator "gt" \
  --threshold 95 \
  --period 300 \
  --evaluation-periods 1 \
  --contact-group-id 1 \
  --notice-type "sms,email" \
  --description "Memory usage exceeds 95%"
```

**Recommended Thresholds**:
- Warning: Memory > 80-85%
- Critical: Memory > 95%

#### 3. Disk Usage Alert

```bash
# Disk usage > 70% (Warning)
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-Disk-Warning" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.disk.util" \
  --comparison-operator "gt" \
  --threshold 70 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "email" \
  --description "Disk usage exceeds 70%"

# Disk usage > 85% (Critical)
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-Disk-Critical" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.disk.util" \
  --comparison-operator "gt" \
  --threshold 85 \
  --period 300 \
  --evaluation-periods 1 \
  --contact-group-id 1 \
  --notice-type "sms,email" \
  --description "Disk usage exceeds 85%"
```

**Recommended Thresholds**:
- Warning: Disk > 70%
- Critical: Disk > 85%

#### 4. System Load Alert

```bash
# High 1-minute load
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-HighLoad-Warning" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.cpu.load1" \
  --comparison-operator "gt" \
  --threshold 8 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "email" \
  --description "High system 1-minute load"
```

**Recommended Thresholds**:
- Warning: 1-min load > CPU cores x 2
- Critical: 1-min load > CPU cores x 4

#### 5. Network Bandwidth Alert

```bash
# High inbound bandwidth
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-NetworkIn-Warning" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.network.in.bytes" \
  --comparison-operator "gt" \
  --threshold 10240 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "email" \
  --description "Inbound bandwidth exceeds 10MB/s"
```

#### 6. TCP Connections Alert

```bash
# Too many TCP connections
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-TCPConnections-Warning" \
  --service-code vm \
  --resource-id i-xxxxx \
  --metric-name "vm.tcp.connections" \
  --comparison-operator "gt" \
  --threshold 10000 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "email" \
  --description "TCP connections exceed 10000"
```

### Managing Alert Rules

#### Query Alert Rules

```bash
# Query all alert rules
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query alert rules for a specific resource
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxxxx

# Query enabled alert rules
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --filters '[{"name":"enabled","values":["true"]}]'
```

#### Update Alert Rules

```bash
# Modify alert threshold
jdc monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --threshold 85

# Disable alert rule
jdc monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --enabled false

# Enable alert rule
jdc monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --enabled true
```

#### Delete Alert Rules

```bash
jdc monitor delete-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx
```

#### Query Alert History

```bash
# Query alert trigger history
jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --page-number 1 \
  --page-size 50
```

## Contact Group Management

### Create Contact Group

```bash
jdc monitor create-contact-group \
  --region-id cn-north-1 \
  --contact-group-name "Ops Team" \
  --description "Responsible for production environment operations" \
  --contacts '[{
    "name": "Zhang San",
    "phone": "138****8888",
    "email": "zhangsan@example.com"
  }, {
    "name": "Li Si",
    "phone": "139****9999",
    "email": "lisi@example.com"
  }]'
```

### Query Contact Groups

```bash
# Query all contact groups
jdc monitor describe-contact-groups \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# Query specific contact group
jdc monitor describe-contact-group \
  --region-id cn-north-1 \
  --contact-group-id 1
```

### Update Contact Group

```bash
jdc monitor update-contact-group \
  --region-id cn-north-1 \
  --contact-group-id 1 \
  --contacts '[{
    "name": "Wang Wu",
    "phone": "137****7777",
    "email": "wangwu@example.com"
  }]'
```

## Dashboard Configuration

### Create Custom Dashboard

You can create custom monitoring dashboards through the JD Cloud Console to display multiple metrics in one place.

#### Recommended Dashboard Layout

**1. Resource Overview Panel**
- CPU usage trend chart
- Memory usage trend chart
- Disk usage trend chart
- Network bandwidth trend chart

**2. Performance Details Panel**
- CPU load (1/5/15 minutes)
- Disk IOPS and latency
- TCP connections
- Process count

**3. Alert Status Panel**
- Currently triggered alerts list
- Alert level distribution
- Alert history trends

### Using Grafana Integration

If you need to display monitoring data using Grafana, you can configure a Prometheus data source or use the Grafana plugin provided by JD Cloud.

## Custom Monitoring

### Pushing Custom Metrics

For application-level monitoring, you can push custom monitoring data via the API.

#### Python Example

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.PutCustomMetricDataRequest import PutCustomMetricDataRequest
import os

# Initialize client
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = MonitorClient(credential, 'cn-north-1')

# Build custom metric data
request = PutCustomMetricDataRequest({
    "regionId": "cn-north-1",
    "namespace": "my-application",
    "metricDataList": [
        {
            "metricName": "order-count",
            "dimensions": [
                {"name": "region", "value": "cn-north-1"},
                {"name": "service", "value": "order-service"}
            ],
            "timestamp": "2026-04-28T12:00:00Z",
            "value": 1234,
            "type": 0,  # 0: raw value, 1: cumulative value
            "unit": "Count"
        },
        {
            "metricName": "api-latency",
            "dimensions": [
                {"name": "endpoint", "value": "/api/v1/orders"}
            ],
            "timestamp": "2026-04-28T12:00:00Z",
            "value": 45.2,
            "type": 0,
            "unit": "Milliseconds"
        }
    ]
})

# Push data
response = client.putCustomMetricData(request)
if response.error is None:
    print("Custom metrics pushed successfully")
else:
    print(f"Error: {response.error.message}")
```

#### Query Custom Metrics

```bash
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "order-count" \
  --namespace my-application \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type sum
```

## Monitoring Best Practices

### 1. Set Appropriate Alert Thresholds

- **Avoid Alert Fatigue**: Do not set overly sensitive thresholds
- **Tiered Alerts**: Use different notification methods based on severity
- **Consider Business Characteristics**: Different businesses may have different thresholds
- **Regular Adjustments**: Optimize thresholds based on historical data

### 2. Multi-Dimensional Monitoring

- **Infrastructure**: CPU, memory, disk, network
- **Application Metrics**: QPS, response time, error rate
- **Business Metrics**: Order volume, user count, transaction amount
- **Dependent Services**: Database, cache, message queue

### 3. Alert Convergence

- **Set Cooldown Periods**: Avoid repeated alerts within a short time
- **Alert Aggregation**: Merge related alerts into one notification
- **Suppression Rules**: Suppress unnecessary alerts during maintenance periods

### 4. Monitoring Coverage

- **Full Coverage**: Ensure all critical resources have monitoring
- **No Blind Spots**: Monitor not only the system level but also application and business levels
- **Automation**: Automatically add monitoring when new resources are created

### 5. Regular Checks

- **Verify Alerts**: Regularly test if alerts are working correctly
- **Clean Up Invalid Alerts**: Delete unnecessary alert rules
- **Update Contacts**: Ensure contact information is accurate

### 6. Documentation

- **Record Threshold Rationale**: Facilitate future optimization
- **Maintain Emergency Plans**: Develop handling procedures for different alerts
- **Share Experience**: Share monitoring and troubleshooting experience within the team

## Common Issues

### 1. Missing Monitoring Data

**Possible Causes**:
- Instance has been stopped or deleted
- Monitoring Agent not installed or abnormal
- Network issues causing data upload failure

**Solutions**:
```bash
# Check instance status
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# Check monitoring agent status (execute inside instance)
sudo systemctl status jcloud-monitor-agent
```

### 2. Alert Not Triggering

**Possible Causes**:
- Alert rule is disabled
- Threshold set incorrectly
- Contact group configuration error

**Solutions**:
```bash
# Check alert rule status
jdc monitor describe-alarms --region-id cn-north-1 --alarm-ids '["alarm-xxxxx"]'

# Check contact group
jdc monitor describe-contact-group --region-id cn-north-1 --contact-group-id 1
```

### 3. Too Many Alerts

**Solutions**:
- Adjust thresholds to avoid being too sensitive
- Increase statistic period and consecutive evaluation count
- Configure alert convergence and suppression rules
