# 云监控监控指标与告警配置

## 监控指标概述

云监控支持 40+ 种云产品的监控，涵盖计算、网络、存储、数据库、中间件等多个类别。

## 云主机(VM)监控指标

### CPU 监控

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| vm.cpu.util | CPU 使用率 | % | CPU 使用率百分比 |
| vm.cpu.idle | CPU 空闲率 | % | CPU 空闲百分比 |
| vm.cpu.system | 系统 CPU 使用率 | % | 内核态 CPU 使用率 |
| vm.cpu.user | 用户 CPU 使用率 | % | 用户态 CPU 使用率 |
| vm.cpu.iowait | IO 等待率 | % | CPU 等待 IO 的百分比 |
| vm.cpu.load1 | 1分钟平均负载 | - | 系统 1 分钟平均负载 |
| vm.cpu.load5 | 5分钟平均负载 | - | 系统 5 分钟平均负载 |
| vm.cpu.load15 | 15分钟平均负载 | - | 系统 15 分钟平均负载 |

### 内存监控

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| vm.memory.util | 内存使用率 | % | 内存使用百分比 |
| vm.memory.used | 已用内存 | MB | 已使用的内存大小 |
| vm.memory.free | 空闲内存 | MB | 空闲内存大小 |
| vm.memory.buffers | 缓冲区 | MB | 缓冲区大小 |
| vm.memory.cached | 缓存 | MB | 缓存大小 |
| vm.memory.swap.util | 交换分区使用率 | % | Swap 使用百分比 |
| vm.memory.swap.used | 已用交换分区 | MB | 已使用的 Swap 大小 |

### 磁盘监控

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| vm.disk.util | 磁盘使用率 | % | 磁盘空间使用百分比 |
| vm.disk.used | 已用磁盘空间 | GB | 已使用的磁盘空间 |
| vm.disk.free | 空闲磁盘空间 | GB | 空闲磁盘空间 |
| vm.disk.read | 磁盘读速率 | Bps | 磁盘每秒读取字节数 |
| vm.disk.write | 磁盘写速率 | Bps | 磁盘每秒写入字节数 |
| vm.disk.iops.read | 磁盘读 IOPS | 次/秒 | 每秒读操作次数 |
| vm.disk.iops.write | 磁盘写 IOPS | 次/秒 | 每秒写操作次数 |

### 网络监控

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| vm.network.in | 内网入速率 | bps | 内网每秒接收比特数 |
| vm.network.out | 内网出速率 | bps | 内网每秒发送比特数 |
| vm.network.packets.in | 内网入包量 | 个/秒 | 内网每秒接收包数 |
| vm.network.packets.out | 内网出包量 | 个/秒 | 内网每秒发送包数 |
| vm.network.drop.in | 内网入丢包率 | 个/秒 | 内网每秒丢弃的接收包数 |
| vm.network.drop.out | 内网出丢包率 | 个/秒 | 内网每秒丢弃的发送包数 |
| vm.tcp.connections | TCP 连接数 | 个 | 当前 TCP 连接总数 |

### 进程监控

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| vm.process.total | 总进程数 | 个 | 系统总进程数 |
| vm.process.running | 运行中进程数 | 个 | 正在运行的进程数 |
| vm.process.blocked | 阻塞进程数 | 个 | 阻塞的进程数 |

## 云数据库 RDS 监控指标

### MySQL 监控

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| rds.cpu.util | CPU 使用率 | % | CPU 使用率 |
| rds.memory.util | 内存使用率 | % | 内存使用率 |
| rds.storage.util | 存储空间使用率 | % | 存储空间使用率 |
| rds.connection.util | 连接数使用率 | % | 连接数使用率 |
| rds.connections.active | 活跃连接数 | 个 | 当前活跃连接数 |
| rds.connections.total | 总连接数 | 个 | 当前总连接数 |
| rds.qps | QPS | 次/秒 | 每秒查询数 |
| rds.tps | TPS | 次/秒 | 每秒事务数 |
| rds.innodb.read | InnoDB 读取次数 | 次/秒 | InnoDB 每秒读取次数 |
| rds.innodb.write | InnoDB 写入次数 | 次/秒 | InnoDB 每秒写入次数 |
| rds.slow.queries | 慢查询数 | 个/分钟 | 每分钟慢查询数量 |
| rds.replication.lag | 主从延迟 | 秒 | 主从复制延迟时间 |

## 负载均衡监控指标

### 传统负载均衡(LB)

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| lb.newconnection | 新建连接数 | 个/秒 | 每秒新建连接数 |
| lb.activeconnection | 活跃连接数 | 个 | 当前活跃连接数 |
| lb.inactiveconnection | 非活跃连接数 | 个 | 当前非活跃连接数 |
| lb.traffic.in | 入流量 | bps | 每秒入流量 |
| lb.traffic.out | 出流量 | bps | 每秒出流量 |
| lb.packets.in | 入包量 | 个/秒 | 每秒入包数 |
| lb.packets.out | 出包量 | 个/秒 | 每秒出包数 |
| lb.httpcode.2xx | 2xx 状态码 | 个/秒 | 每秒 2xx 响应数 |
| lb.httpcode.4xx | 4xx 状态码 | 个/秒 | 每秒 4xx 响应数 |
| lb.httpcode.5xx | 5xx 状态码 | 个/秒 | 每秒 5xx 响应数 |
| lb.latency | 平均延迟 | ms | 平均响应延迟 |
| lb.qps | QPS | 次/秒 | 每秒请求数 |

## 对象存储(OSS)监控指标

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| oss.storage.util | 存储容量使用率 | % | 存储空间使用率 |
| oss.storage.used | 已用存储容量 | GB | 已使用的存储容量 |
| oss.request.get | GET 请求数 | 次 | GET 请求次数 |
| oss.request.put | PUT 请求数 | 次 | PUT 请求次数 |
| oss.request.delete | DELETE 请求数 | 次 | DELETE 请求次数 |
| oss.traffic.in | 流入流量 | B | 流入流量 |
| oss.traffic.out | 流出流量 | B | 流出流量 |
| oss.httpcode.2xx | 2xx 状态码 | 次 | 2xx 响应次数 |
| oss.httpcode.4xx | 4xx 状态码 | 次 | 4xx 响应次数 |
| oss.httpcode.5xx | 5xx 状态码 | 次 | 5xx 响应次数 |

## 弹性公网 IP(EIP)监控指标

| 指标名称 | 显示名称 | 单位 | 说明 |
|---------|---------|------|------|
| eip.traffic.in | 入流量 | bps | 每秒入流量 |
| eip.traffic.out | 出流量 | bps | 每秒出流量 |
| eip.packets.in | 入包量 | 个/秒 | 每秒入包数 |
| eip.packets.out | 出包量 | 个/秒 | 每秒出包数 |
| eip.bandwidth.util | 带宽使用率 | % | 带宽使用率 |

## 告警配置最佳实践

### 云主机告警配置示例

#### CPU 使用率告警

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

**建议阈值**：
- 警告级别：CPU > 70%
- 严重级别：CPU > 90%

#### 内存使用率告警

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

**建议阈值**：
- 警告级别：内存 > 80%
- 严重级别：内存 > 95%

#### 磁盘使用率告警

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

**建议阈值**：
- 警告级别：磁盘 > 70%
- 严重级别：磁盘 > 85%

#### 系统负载告警

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

**建议阈值**：
- 警告级别：1分钟负载 > CPU 核数 * 2
- 严重级别：1分钟负载 > CPU 核数 * 4

### RDS 告警配置示例

#### CPU 使用率告警

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

**建议阈值**：
- 警告级别：CPU > 60%
- 严重级别：CPU > 80%

#### 连接数使用率告警

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

**建议阈值**：
- 警告级别：连接数 > 70%
- 严重级别：连接数 > 85%

#### 慢查询告警

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

### 负载均衡告警配置示例

#### 活跃连接数告警

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

#### 5xx 错误率告警

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

**建议阈值**：
- 警告级别：5xx > 5 次/秒
- 严重级别：5xx > 10 次/秒

#### 延迟告警

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

**建议阈值**：
- 警告级别：延迟 > 200ms
- 严重级别：延迟 > 500ms

## 告警模板使用

### 创建自定义告警模板

```bash
# 使用默认模板复制
jdc monitor copy-alarm-template \
  --region-id cn-north-1 \
  --template-id default-vm \
  --template-name "My-VM-Template"
```

### 应用告警模板

```bash
# 将模板应用到资源
jdc monitor apply-alarm-template \
  --region-id cn-north-1 \
  --template-id template-xxx \
  --resource-ids '["i-xxx1","i-xxx2"]'
```

## 告警回调配置

### 创建带回调的告警规则

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

### 回调消息格式

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

## 监控数据查询示例

### 查询云主机最近1小时 CPU 数据

```bash
# 计算时间
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

### 批量查询多台云主机最新指标

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

## 监控数据保留策略

| 数据类型 | 保留期限 | 说明 |
|---------|---------|------|
| 原始数据 | 15 天 | 按采集周期存储的原始数据 |
| 1小时聚合 | 30 天 | 按小时聚合的数据 |
| 1天聚合 | 180 天 | 按天聚合的数据 |

## 监控采集周期

| 产品 | 默认采集周期 | 最小周期 |
|------|-------------|---------|
| 云主机 | 60 秒 | 10 秒 |
| RDS | 60 秒 | 60 秒 |
| 负载均衡 | 60 秒 | 60 秒 |
| 对象存储 | 300 秒 | 300 秒 |
| 自定义监控 | 60 秒 | 10 秒 |
