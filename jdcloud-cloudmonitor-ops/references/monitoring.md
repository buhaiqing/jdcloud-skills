# Cloud Monitor Metrics and Alarm Configuration

## Metric Overview

Cloud Monitor supports 40+ cloud product monitoring, covering compute, network, storage, database, middleware, and other categories.

## Virtual Machine (VM) Monitoring Metrics

### CPU Monitoring

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| vm.cpu.util | CPU Usage | % | CPU usage percentage |
| vm.cpu.idle | CPU Idle | % | CPU idle percentage |
| vm.cpu.system | System CPU Usage | % | Kernel-mode CPU usage |
| vm.cpu.user | User CPU Usage | % | User-mode CPU usage |
| vm.cpu.iowait | I/O Wait | % | CPU I/O wait percentage |
| vm.cpu.load1 | 1-min Load Average | - | System 1-minute average load |
| vm.cpu.load5 | 5-min Load Average | - | System 5-minute average load |
| vm.cpu.load15 | 15-min Load Average | - | System 15-minute average load |

### Memory Monitoring

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| vm.memory.util | Memory Usage | % | Memory usage percentage |
| vm.memory.used | Used Memory | MB | Used memory size |
| vm.memory.free | Free Memory | MB | Free memory size |
| vm.memory.buffers | Buffers | MB | Buffer size |
| vm.memory.cached | Cached | MB | Cache size |
| vm.memory.swap.util | Swap Usage | % | Swap usage percentage |
| vm.memory.swap.used | Used Swap | MB | Used swap size |

### Disk Monitoring

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| vm.disk.util | Disk Usage | % | Disk space usage percentage |
| vm.disk.used | Used Disk Space | GB | Used disk space |
| vm.disk.free | Free Disk Space | GB | Free disk space |
| vm.disk.read | Disk Read Rate | Bps | Disk bytes read per second |
| vm.disk.write | Disk Write Rate | Bps | Disk bytes written per second |
| vm.disk.iops.read | Disk Read IOPS | ops/s | Read operations per second |
| vm.disk.iops.write | Disk Write IOPS | ops/s | Write operations per second |

### Network Monitoring

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| vm.network.in | Internal Inbound Rate | bps | Internal network bits received per second |
| vm.network.out | Internal Outbound Rate | bps | Internal network bits sent per second |
| vm.network.packets.in | Internal Inbound Packets | packets/s | Internal network packets received per second |
| vm.network.packets.out | Internal Outbound Packets | packets/s | Internal network packets sent per second |
| vm.network.drop.in | Internal Inbound Drop Rate | packets/s | Internal network received packets dropped per second |
| vm.network.drop.out | Internal Outbound Drop Rate | packets/s | Internal network sent packets dropped per second |
| vm.tcp.connections | TCP Connections | count | Current total TCP connections |

### Process Monitoring

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| vm.process.total | Total Processes | count | Total system processes |
| vm.process.running | Running Processes | count | Currently running processes |
| vm.process.blocked | Blocked Processes | count | Blocked processes |

## RDS Monitoring Metrics

### MySQL Monitoring

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| rds.cpu.util | CPU Usage | % | CPU usage |
| rds.memory.util | Memory Usage | % | Memory usage |
| rds.storage.util | Storage Usage | % | Storage usage |
| rds.connection.util | Connection Usage | % | Connection usage |
| rds.connections.active | Active Connections | count | Current active connections |
| rds.connections.total | Total Connections | count | Current total connections |
| rds.qps | QPS | ops/s | Queries per second |
| rds.tps | TPS | ops/s | Transactions per second |
| rds.innodb.read | InnoDB Reads | ops/s | InnoDB reads per second |
| rds.innodb.write | InnoDB Writes | ops/s | InnoDB writes per second |
| rds.slow.queries | Slow Queries | queries/min | Slow queries per minute |
| rds.replication.lag | Replication Lag | seconds | Master-slave replication delay |

## Load Balancer Monitoring Metrics

### Traditional Load Balancer (LB)

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| lb.newconnection | New Connections | conn/s | New connections per second |
| lb.activeconnection | Active Connections | count | Current active connections |
| lb.inactiveconnection | Inactive Connections | count | Current inactive connections |
| lb.traffic.in | Inbound Traffic | bps | Inbound traffic per second |
| lb.traffic.out | Outbound Traffic | bps | Outbound traffic per second |
| lb.packets.in | Inbound Packets | packets/s | Inbound packets per second |
| lb.packets.out | Outbound Packets | packets/s | Outbound packets per second |
| lb.httpcode.2xx | 2xx Status Codes | ops/s | 2xx responses per second |
| lb.httpcode.4xx | 4xx Status Codes | ops/s | 4xx responses per second |
| lb.httpcode.5xx | 5xx Status Codes | ops/s | 5xx responses per second |
| lb.latency | Average Latency | ms | Average response latency |
| lb.qps | QPS | ops/s | Requests per second |

## Object Storage (OSS) Monitoring Metrics

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| oss.storage.util | Storage Usage | % | Storage usage |
| oss.storage.used | Used Storage | GB | Used storage capacity |
| oss.request.get | GET Requests | count | GET request count |
| oss.request.put | PUT Requests | count | PUT request count |
| oss.request.delete | DELETE Requests | count | DELETE request count |
| oss.traffic.in | Inbound Traffic | B | Inbound traffic |
| oss.traffic.out | Outbound Traffic | B | Outbound traffic |
| oss.httpcode.2xx | 2xx Status Codes | count | 2xx response count |
| oss.httpcode.4xx | 4xx Status Codes | count | 4xx response count |
| oss.httpcode.5xx | 5xx Status Codes | count | 5xx response count |

## Elastic IP (EIP) Monitoring Metrics

| Metric Name | Display Name | Unit | Description |
|---------|---------|------|------|
| eip.traffic.in | Inbound Traffic | bps | Inbound traffic per second |
| eip.traffic.out | Outbound Traffic | bps | Outbound traffic per second |
| eip.packets.in | Inbound Packets | packets/s | Inbound packets per second |
| eip.packets.out | Outbound Packets | packets/s | Outbound packets per second |
| eip.bandwidth.util | Bandwidth Usage | % | Bandwidth usage |

## Alarm Configuration Best Practices

### VM Alarm Configuration Examples

#### CPU Usage Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-HighCPU-Critical" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 90 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

**Recommended Thresholds**:
- Warning Level: CPU > 70%
- Critical Level: CPU > 90%

#### Memory Usage Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-HighMemory-Warning" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.memory.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 1 \
  --contact-group-id 1 \
  --notice-type "email"
```

**Recommended Thresholds**:
- Warning Level: Memory > 80%
- Critical Level: Memory > 95%

#### Disk Usage Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-HighDisk-Critical" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.disk.util" \
  --comparison-operator "gt" \
  --threshold 85 \
  --period 300 \
  --evaluation-periods 1 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

**Recommended Thresholds**:
- Warning Level: Disk > 70%
- Critical Level: Disk > 85%

#### System Load Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-HighLoad-Warning" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.cpu.load1" \
  --comparison-operator "gt" \
  --threshold 4 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "email"
```

**Recommended Thresholds**:
- Warning Level: 1-min Load > CPU Cores * 2
- Critical Level: 1-min Load > CPU Cores * 4

### RDS Alarm Configuration Examples

#### CPU Usage Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "RDS-HighCPU-Critical" \
  --service-code rds \
  --resource-id rds-xxx \
  --metric-name "rds.cpu.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

**Recommended Thresholds**:
- Warning Level: CPU > 60%
- Critical Level: CPU > 80%

#### Connection Usage Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "RDS-HighConnection-Critical" \
  --service-code rds \
  --resource-id rds-xxx \
  --metric-name "rds.connection.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 1 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

**Recommended Thresholds**:
- Warning Level: Connections > 70%
- Critical Level: Connections > 85%

#### Slow Query Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "RDS-SlowQuery-Warning" \
  --service-code rds \
  --resource-id rds-xxx \
  --metric-name "rds.slow.queries" \
  --comparison-operator "gt" \
  --threshold 10 \
  --period 300 \
  --evaluation-periods 1 \
  --contact-group-id 1 \
  --notice-type "email"
```

### Load Balancer Alarm Configuration Examples

#### Active Connections Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "LB-HighConnections-Critical" \
  --service-code lb \
  --resource-id lb-xxx \
  --metric-name "lb.activeconnection" \
  --comparison-operator "gt" \
  --threshold 10000 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

#### 5xx Error Rate Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "LB-High5xxError-Critical" \
  --service-code lb \
  --resource-id lb-xxx \
  --metric-name "lb.httpcode.5xx" \
  --comparison-operator "gt" \
  --threshold 10 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

**Recommended Thresholds**:
- Warning Level: 5xx > 5 ops/s
- Critical Level: 5xx > 10 ops/s

#### Latency Alarm

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "LB-HighLatency-Warning" \
  --service-code lb \
  --resource-id lb-xxx \
  --metric-name "lb.latency" \
  --comparison-operator "gt" \
  --threshold 500 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "email"
```

**Recommended Thresholds**:
- Warning Level: Latency > 200ms
- Critical Level: Latency > 500ms

## Using Alarm Templates

### Create Custom Alarm Template

```bash
# Copy from default template
jdc monitor copy-alarm-template \
  --region-id cn-north-1 \
  --template-id default-vm \
  --template-name "My-VM-Template"
```

### Apply Alarm Template

```bash
# Apply template to resources
jdc monitor apply-alarm-template \
  --region-id cn-north-1 \
  --template-id template-xxx \
  --resource-ids '["i-xxx1","i-xxx2"]'
```

## Alarm Callback Configuration

### Create Alarm Rule with Callback

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "VM-Callback-Alarm" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 90 \
  --period 300 \
  --evaluation-periods 2 \
  --notice-type "callback" \
  --callback-url "https://your-domain.com/webhook"
```

### Callback Message Format

```json
{
  "alarmId": "alarm-xxx",
  "alarmName": "VM-Callback-Alarm",
  "status": "ALARM",
  "serviceCode": "vm",
  "resourceId": "i-xxx",
  "metricName": "vm.cpu.util",
  "value": 95.2,
  "triggerTime": "2024-01-01T12:00:00Z",
  "regionId": "cn-north-1"
}
```

## Monitoring Data Query Examples

### Query Last 1-Hour VM CPU Data

```bash
# Calculate time range
start_time=$(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ")
end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "$start_time" \
  --end-time "$end_time" \
  --aggr-type avg \
  --period 300
```

### Batch Query Latest Metrics for Multiple VMs

```bash
#!/bin/bash

vm_ids=("i-xxx1" "i-xxx2" "i-xxx3")
metrics='["vm.cpu.util","vm.memory.util"]'

for vm_id in "${vm_ids[@]}"; do
  echo "=== $vm_id ==="
  jdc monitor last-downsample \
    --region-id cn-north-1 \
    --service-code vm \
    --resource-id $vm_id \
    --metrics "$metrics" \
    --output table
done
```

## Monitoring Data Retention Policy

| Data Type | Retention Period | Description |
|---------|---------|------|
| Raw Data | 15 days | Raw data stored at collection interval |
| 1-hour Aggregate | 30 days | Hourly aggregated data |
| 1-day Aggregate | 180 days | Daily aggregated data |

## Monitoring Collection Interval

| Product | Default Collection Interval | Minimum Interval |
|------|-------------|---------|
| VM | 60 seconds | 10 seconds |
| RDS | 60 seconds | 60 seconds |
| Load Balancer | 60 seconds | 60 seconds |
| Object Storage | 300 seconds | 300 seconds |
| Custom Monitoring | 60 seconds | 10 seconds |

## Operations Best Practices

### Monitoring Coverage Strategy
- **Core Resources**: Enable basic monitoring for all production cloud resources
- **Key Metrics**: CPU, memory, disk, network — the four golden signals — must have alarms configured
- **Business Metrics**: Report business-critical metrics via custom monitoring

### Alarm Rule Configuration
- **Threshold Settings**: Set reasonable alarm thresholds based on business characteristics to avoid alarm storms
- **Notification Strategy**: Configure multi-channel notifications (SMS + Email + Callback), set notification cycles to avoid redundant interruptions
- **Graded Alarming**: Distinguish P0/P1/P2 levels with different notification strategies and response times

### Dashboard Management
- **Business Perspective**: Organize monitoring panels by business system
- **Key Metrics on Top**: Place the most important metrics at the top of the panel
- **Template Variables**: Use template variables for quick resource switching

### Cost Optimization
- **Storage Periods**: Set different data retention periods based on data importance
- **Collection Frequency**: Reduce monitoring data collection frequency for non-critical resources

### API Limits
| Limit Item | Description |
|--------|------|
| Query Frequency | Monitoring data query API default QPS limit is 100 |
| Data Retention | Raw monitoring data retained for 15 days, aggregated data retained for 30 days |
| Alarm Rules | Up to 500 alarm rules per region |
| Custom Metrics | Up to 1000 custom metrics per namespace |

### Related Links
- [JD Cloud Monitoring Product Page](https://www.jdcloud.com/cn/products/monitoring)
- [Cloud Monitor Documentation](https://docs.jdcloud.com/cn/monitoring/learning)
- [Cloud Monitor API Documentation](https://docs.jdcloud.com/cn/monitoring/api/overview)
- [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)