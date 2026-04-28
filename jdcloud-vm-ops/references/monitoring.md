# JD Cloud VM Monitoring & Alerts Guide

## 监控概述

京东云云监控（Cloud Monitor）提供全面的VM实例监控能力，包括基础监控、操作系统监控和自定义监控。通过合理的监控配置和告警策略，可以及时发现并解决潜在问题。

## 核心监控指标

### 1. CPU相关指标

| 指标名称 | 指标Code | 单位 | 说明 |
|---------|---------|------|------|
| CPU使用率 | vm.cpu.util | % | CPU平均使用率 |
| CPU负载(1分钟) | vm.cpu.load1 | - | 1分钟系统负载 |
| CPU负载(5分钟) | vm.cpu.load5 | - | 5分钟系统负载 |
| CPU负载(15分钟) | vm.cpu.load15 | - | 15分钟系统负载 |
| CPU空闲率 | vm.cpu.idle | % | CPU空闲百分比 |
| CPU用户态使用率 | vm.cpu.user | % | 用户态CPU使用率 |
| CPU系统态使用率 | vm.cpu.system | % | 系统态CPU使用率 |
| CPU等待I/O率 | vm.cpu.iowait | % | 等待I/O的CPU时间占比 |

### 2. 内存相关指标

| 指标名称 | 指标Code | 单位 | 说明 |
|---------|---------|------|------|
| 内存使用率 | vm.memory.util | % | 内存使用百分比 |
| 已用内存 | vm.memory.used | MB | 已使用的内存量 |
| 可用内存 | vm.memory.available | MB | 可用内存量 |
| 缓存内存 | vm.memory.cached | MB | 用于缓存的内存 |
| Swap使用率 | vm.swap.util | % | Swap分区使用率 |

### 3. 磁盘相关指标

| 指标名称 | 指标Code | 单位 | 说明 |
|---------|---------|------|------|
| 磁盘使用率 | vm.disk.util | % | 磁盘空间使用率 |
| 磁盘读取速率 | vm.disk.read.bytes | KB/s | 磁盘读取速度 |
| 磁盘写入速率 | vm.disk.write.bytes | KB/s | 磁盘写入速度 |
| 磁盘读取IOPS | vm.disk.read.iops | 次/秒 | 每秒读取次数 |
| 磁盘写入IOPS | vm.disk.write.iops | 次/秒 | 每秒写入次数 |
| 磁盘读取延迟 | vm.disk.read.latency | ms | 读取操作平均延迟 |
| 磁盘写入延迟 | vm.disk.write.latency | ms | 写入操作平均延迟 |

### 4. 网络相关指标

| 指标名称 | 指标Code | 单位 | 说明 |
|---------|---------|------|------|
| 网络流入带宽 | vm.network.in.bytes | KB/s | 入网流量速率 |
| 网络流出带宽 | vm.network.out.bytes | KB/s | 出网流量速率 |
| 网络流入数据包 | vm.network.in.packets | 个/秒 | 入网数据包速率 |
| 网络流出数据包 | vm.network.out.packets | 个/秒 | 出网数据包速率 |
| TCP连接数 | vm.tcp.connections | 个 | 当前TCP连接数 |
| TCP新建连接数 | vm.tcp.new.connections | 个/秒 | 每秒新建TCP连接数 |

### 5. 系统相关指标

| 指标名称 | 指标Code | 单位 | 说明 |
|---------|---------|------|------|
| 系统运行时间 | vm.uptime | 秒 | 系统启动后的运行时间 |
| 进程总数 | vm.process.count | 个 | 当前运行的进程数 |
| 登录用户数 | vm.user.login | 个 | 当前登录的用户数 |

## 查询监控数据

### CLI方式

#### 查询单个指标

```bash
# 查询CPU使用率（最近1小时）
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

#### 查询多个指标

```bash
# 同时查询CPU和内存使用率
jdc monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxxxx \
  --metrics '["vm.cpu.util", "vm.memory.util", "vm.disk.util"]'
```

#### 查询历史数据

```bash
# 查询过去24小时的CPU使用率，按5分钟聚合
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

#### 查询指定时间范围

```bash
# 查询特定时间段的数据
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time "2026-04-28T00:00:00Z" \
  --end-time "2026-04-28T23:59:59Z" \
  --aggr-type max
```

### SDK方式（Python）

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest
import os
from datetime import datetime, timedelta

# 初始化客户端
credential = Credential(
    os.environ.get('JDC_ACCESS_KEY'),
    os.environ.get('JDC_SECRET_KEY')
)
client = MonitorClient(credential, 'cn-north-1')

# 构建请求
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

# 发送请求
response = client.describeMetricData(request)

# 处理结果
if response.error is None:
    for data in response.result.metricDatas:
        print(f"Time: {data.timestamp}, CPU Usage: {data.value}%")
else:
    print(f"Error: {response.error.message}")
```

## 告警配置

### 告警级别

| 级别 | 说明 | 通知方式建议 |
|------|------|------------|
| 严重 (Critical) | 需要立即处理的问题 | 短信 + 电话 + 邮件 |
| 警告 (Warning) | 需要关注的问题 | 邮件 + IM通知 |
| 信息 (Info) | 一般性通知 | 邮件 |

### 常用告警规则

#### 1. CPU使用率告警

```bash
# CPU使用率 > 80% （警告）
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
  --description "CPU使用率超过80%"

# CPU使用率 > 90% （严重）
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
  --description "CPU使用率超过90%"
```

**建议阈值**：
- 警告级别：CPU > 70-80%
- 严重级别：CPU > 90%
- 统计周期：5分钟
- 连续次数：2-3次

#### 2. 内存使用率告警

```bash
# 内存使用率 > 85% （警告）
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
  --description "内存使用率超过85%"

# 内存使用率 > 95% （严重）
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
  --description "内存使用率超过95%"
```

**建议阈值**：
- 警告级别：内存 > 80-85%
- 严重级别：内存 > 95%

#### 3. 磁盘使用率告警

```bash
# 磁盘使用率 > 70% （警告）
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
  --description "磁盘使用率超过70%"

# 磁盘使用率 > 85% （严重）
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
  --description "磁盘使用率超过85%"
```

**建议阈值**：
- 警告级别：磁盘 > 70%
- 严重级别：磁盘 > 85%

#### 4. 系统负载告警

```bash
# 1分钟负载过高
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
  --description "系统1分钟负载过高"
```

**建议阈值**：
- 警告级别：1分钟负载 > CPU核数 × 2
- 严重级别：1分钟负载 > CPU核数 × 4

#### 5. 网络带宽告警

```bash
# 网络流入带宽过高
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
  --description "网络流入带宽超过10MB/s"
```

#### 6. TCP连接数告警

```bash
# TCP连接数过多
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
  --description "TCP连接数超过10000"
```

### 管理告警规则

#### 查询告警规则

```bash
# 查询所有告警规则
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 查询指定资源的告警规则
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxxxx

# 查询启用的告警规则
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --filters '[{"name":"enabled","values":["true"]}]'
```

#### 更新告警规则

```bash
# 修改告警阈值
jdc monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --threshold 85

# 禁用告警规则
jdc monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --enabled false

# 启用告警规则
jdc monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --enabled true
```

#### 删除告警规则

```bash
jdc monitor delete-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx
```

#### 查询告警历史

```bash
# 查询告警触发历史
jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxxxx \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --page-number 1 \
  --page-size 50
```

## 联系人组管理

### 创建联系人组

```bash
jdc monitor create-contact-group \
  --region-id cn-north-1 \
  --contact-group-name "运维团队" \
  --description "负责生产环境运维" \
  --contacts '[{
    "name": "张三",
    "phone": "138****8888",
    "email": "zhangsan@example.com"
  }, {
    "name": "李四",
    "phone": "139****9999",
    "email": "lisi@example.com"
  }]'
```

### 查询联系人组

```bash
# 查询所有联系人组
jdc monitor describe-contact-groups \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 查询指定联系人组
jdc monitor describe-contact-group \
  --region-id cn-north-1 \
  --contact-group-id 1
```

### 更新联系人组

```bash
jdc monitor update-contact-group \
  --region-id cn-north-1 \
  --contact-group-id 1 \
  --contacts '[{
    "name": "王五",
    "phone": "137****7777",
    "email": "wangwu@example.com"
  }]'
```

## Dashboard配置

### 创建自定义Dashboard

可以通过京东云控制台创建自定义监控面板，将多个指标集中展示。

#### 推荐的Dashboard布局

**1. 资源概览面板**
- CPU使用率趋势图
- 内存使用率趋势图
- 磁盘使用率趋势图
- 网络带宽趋势图

**2. 性能详情面板**
- CPU负载（1/5/15分钟）
- 磁盘IOPS和延迟
- TCP连接数
- 进程数

**3. 告警状态面板**
- 当前触发的告警列表
- 告警级别分布
- 告警历史趋势

### 使用Grafana集成

如果需要使用Grafana展示监控数据，可以配置Prometheus数据源或使用京东云提供的Grafana插件。

## 自定义监控

### 推送自定义指标

对于应用层面的监控指标，可以通过API推送自定义监控数据。

#### Python示例

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.PutCustomMetricDataRequest import PutCustomMetricDataRequest
import os

# 初始化客户端
credential = Credential(
    os.environ.get('JDC_ACCESS_KEY'),
    os.environ.get('JDC_SECRET_KEY')
)
client = MonitorClient(credential, 'cn-north-1')

# 构建自定义指标数据
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
            "type": 0,  # 0: 原始值, 1: 累加值
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

# 推送数据
response = client.putCustomMetricData(request)
if response.error is None:
    print("Custom metrics pushed successfully")
else:
    print(f"Error: {response.error.message}")
```

#### 查询自定义指标

```bash
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "order-count" \
  --namespace my-application \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type sum
```

## 监控最佳实践

### 1. 合理设置告警阈值

- **避免告警疲劳**: 不要设置过于敏感的阈值
- **分级告警**: 根据严重程度设置不同的通知方式
- **考虑业务特点**: 不同业务的阈值可能不同
- **定期调整**: 根据历史数据优化阈值

### 2. 多维度监控

- **基础资源**: CPU、内存、磁盘、网络
- **应用指标**: QPS、响应时间、错误率
- **业务指标**: 订单量、用户数、交易额
- **依赖服务**: 数据库、缓存、消息队列

### 3. 告警收敛

- **设置冷却时间**: 避免短时间内重复告警
- **告警聚合**: 将相关告警合并通知
- **抑制规则**: 在维护期间抑制非必要告警

### 4. 监控覆盖

- **全覆盖**: 确保所有关键资源都有监控
- **无死角**: 不仅监控系统层面，也要监控应用和业务层面
- **自动化**: 新资源创建时自动添加监控

### 5. 定期检查

- **验证告警**: 定期测试告警是否正常工作
- **清理无效告警**: 删除不再需要的告警规则
- **更新联系人**: 确保联系人信息准确

### 6. 文档化

- **记录阈值设定原因**: 便于后续优化
- **维护应急预案**: 针对不同告警制定处理流程
- **分享经验**: 团队内部分享监控和故障处理经验

## 常见问题

### 1. 监控数据缺失

**可能原因**：
- 实例已停止或删除
- 监控Agent未安装或异常
- 网络问题导致数据上报失败

**解决方案**：
```bash
# 检查实例状态
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# 检查监控Agent状态（需要在实例内执行）
sudo systemctl status jcloud-monitor-agent
```

### 2. 告警未触发

**可能原因**：
- 告警规则被禁用
- 阈值设置不合理
- 联系人组配置错误

**解决方案**：
```bash
# 检查告警规则状态
jdc monitor describe-alarms --region-id cn-north-1 --alarm-ids '["alarm-xxxxx"]'

# 检查联系人组
jdc monitor describe-contact-group --region-id cn-north-1 --contact-group-id 1
```

### 3. 收到过多告警

**解决方案**：
- 调整阈值，避免过于敏感
- 增加统计周期和连续次数
- 配置告警收敛和抑制规则