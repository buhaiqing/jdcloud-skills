---
name: jdcloud-cloudmonitor-ops
description: >-
  管理京东云云监控(CloudMonitor)资源。用于查询监控指标数据、创建和管理告警规则、
  查看告警历史、配置自定义监控等运维操作。支持40+云产品的监控数据查询和告警管理。
---

# 京东云云监控(CloudMonitor)运维 Skill

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0.0 | 2026-04-28 | 初始版本，包含云监控核心功能、告警配置和运维最佳实践 |

## 概述

京东云云监控(CloudMonitor)是对用户名下云资源进行监控和报警的服务，支持40余种云产品的监控，包括计算、网络、存储、数据库、中间件及大数据服务等。本 Skill 提供监控数据查询、告警规则管理、自定义监控等运维能力。

## 核心功能

- **监控数据查询**: 查询云资源的实时和历史监控指标数据
- **告警规则管理**: 创建、修改、启用/禁用、删除告警规则
- **告警历史查看**: 查询告警触发历史和通知记录
- **自定义监控**: 上报和查询自定义业务指标
- **Dashboard管理**: 监控面板和图表管理

## 前提条件

### 1. 安装京东云 CLI

京东云 CLI 支持多种安装方式：

**方式一：通过 pip 安装**

```bash
# 安装京东云 CLI
pip install jdcloud-cli

# 验证安装
jdc --version
```

**方式二：下载二进制文件**

```bash
# Linux/macOS
curl -fsSL https://github.com/jdcloud-api/jdcloud-cli/releases/latest/download/jdc-linux-amd64.tar.gz | tar -xz
sudo mv jdc /usr/local/bin/

# Windows
# 下载 https://github.com/jdcloud-api/jdcloud-cli/releases/latest/download/jdc-windows-amd64.zip
# 解压并添加到 PATH
```

### 2. 配置凭证

方式一：环境变量（推荐）
```bash
export JDC_ACCESS_KEY="your_access_key_here"
export JDC_SECRET_KEY="your_secret_key_here"
export JDC_REGION="cn-north-1"  # 默认区域
```

方式二：配置文件
```bash
# 创建配置文件目录
mkdir -p ~/.jdc

# 编辑配置文件
cat > ~/.jdc/config.json << EOF
{
  "access_key": "your_access_key_here",
  "secret_key": "your_secret_key_here",
  "region_id": "cn-north-1"
}
EOF
```

方式三：命令行参数
```bash
# 在每个命令中指定凭证
jdc monitor describe-alarms \
  --access-key your_access_key \
  --secret-key your_secret_key \
  --region-id cn-north-1
```

## 支持的云产品监控

| 类别 | 产品 |
|------|------|
| 计算 | 云主机 CVM、轻量云主机、原生容器、Kubernetes 集群、函数计算 |
| 网络 | 负载均衡、NAT 网关、弹性公网 IP、共享带宽包、专线服务 |
| 存储 | 云硬盘、对象存储、云文件服务 |
| 数据库 | RDS、MongoDB、Redis、Memcached、TiDB、ClickHouse |
| 中间件 | 消息队列 JCQ/RabbitMQ/Kafka/RocketMQ、Zookeeper |
| 其他 | CDN、Elasticsearch、DTS、堡垒机等 |

## 常用 CLI 命令

### 查询监控服务列表
```bash
jdc monitor describe-services --region-id cn-north-1
```

### 查询指定产品的监控项
```bash
jdc monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx
```

### 查询监控数据
```bash
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```

### 查询最新监控数据（降采样）
```bash
jdc monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metrics '["vm.cpu.util","vm.memory.util"]'
```

### 创建告警规则
```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "HighCPUAlarm" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

### 查询告警规则列表
```bash
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
```

### 启用/禁用告警规则
```bash
# 启用告警
jdc monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled true

# 禁用告警
jdc monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled false
```

### 查询告警历史
```bash
jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z"
```

### 上报自定义监控数据
```bash
jdc monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --value 100 \
  --dimensions '{"instance":"app-server-01"}'
```

### 查询自定义监控数据
```bash
jdc monitor describe-custom-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```

## Reference 目录

- [核心概念](references/core-concepts.md) - 云监控核心概念和术语
- [CLI 使用指南](references/cli-usage.md) - 详细的 CLI 命令说明
- [故障排查指南](references/troubleshooting.md) - 常见问题及解决方案
- [监控与告警](references/monitoring.md) - 监控指标和告警配置
- [集成指南](references/integration.md) - SDK 和 MCP 集成

## 运维最佳实践

### 1. 监控覆盖策略
- **核心资源**: 对生产环境所有云资源启用基础监控
- **关键指标**: CPU、内存、磁盘、网络四大黄金指标必配告警
- **业务指标**: 通过自定义监控上报业务关键指标

### 2. 告警规则配置
- **阈值设置**: 根据业务特点设置合理的告警阈值，避免告警风暴
- **通知策略**: 配置多渠道通知（短信+邮件+回调），设置通知周期避免重复打扰
- **分级告警**: 区分 P0/P1/P2 级别，配置不同的通知策略和响应时间

### 3. Dashboard 管理
- **业务视角**: 按业务系统组织监控面板
- **关键指标置顶**: 将最重要的指标放在面板顶部
- **模板变量**: 使用模板变量实现资源的快速切换

### 4. 成本优化
- **存储周期**: 根据数据重要性设置不同的数据存储周期
- **采集频率**: 非关键资源可适当降低监控数据采集频率

## 常用监控指标

### 云主机(VM)常用指标
| 指标名称 | 说明 | 单位 |
|---------|------|------|
| vm.cpu.util | CPU 使用率 | % |
| vm.memory.util | 内存使用率 | % |
| vm.disk.read | 磁盘读速率 | Bps |
| vm.disk.write | 磁盘写速率 | Bps |
| vm.network.in | 内网入速率 | bps |
| vm.network.out | 内网出速率 | bps |

### 云数据库 RDS 常用指标
| 指标名称 | 说明 | 单位 |
|---------|------|------|
| rds.cpu.util | CPU 使用率 | % |
| rds.memory.util | 内存使用率 | % |
| rds.connection.util | 连接数使用率 | % |
| rds.qps | 每秒查询数 | 次/秒 |
| rds.tps | 每秒事务数 | 次/秒 |

### 负载均衡常用指标
| 指标名称 | 说明 | 单位 |
|---------|------|------|
| lb.newconnection | 新建连接数 | 个/秒 |
| lb.activeconnection | 活跃连接数 | 个 |
| lb.traffic.in | 入流量 | bps |
| lb.traffic.out | 出流量 | bps |

## API 限制说明

| 限制项 | 说明 |
|--------|------|
| 查询频率 | 监控数据查询接口默认 QPS 限制为 100 |
| 数据保留 | 原始监控数据保留 15 天，聚合数据保留 30 天 |
| 告警规则 | 每个区域最多可创建 500 条告警规则 |
| 自定义指标 | 每个命名空间最多支持 1000 个自定义指标 |

## 相关链接

- [京东云云监控产品页](https://www.jdcloud.com/cn/products/monitoring)
- [云监控文档中心](https://docs.jdcloud.com/cn/monitoring/learning)
- [云监控 API 文档](https://docs.jdcloud.com/cn/monitoring/api/overview)


