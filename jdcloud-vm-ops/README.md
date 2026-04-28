# JD Cloud VM Operations Skill

## 概述

这是一个用于管理京东云云主机（VM）的运维Skill，提供了完整的实例管理、监控告警、故障排查和自动化集成能力。

## 功能特性

- ✅ **实例管理**: 创建、启动、停止、删除VM实例
- ✅ **存储管理**: 云硬盘挂载、快照备份、磁盘扩容
- ✅ **网络配置**: 安全组规则、弹性公网IP、VPC配置
- ✅ **监控告警**: CPU、内存、磁盘、网络等全方位监控
- ✅ **故障排查**: 常见问题诊断和解决方案
- ✅ **自动化集成**: SDK、MCP Server、Terraform、Ansible支持

## 目录结构

```
jdcloud-vm-ops/
├── SKILL.md                    # Skill主文件
├── references/
│   ├── core-concepts.md        # 核心概念说明
│   ├── cli-usage.md            # CLI使用指南
│   ├── troubleshooting.md      # 故障排查手册
│   ├── monitoring.md           # 监控告警配置
│   └── integration.md          # 集成开发指南
└── assets/
    └── example-config.yaml     # 配置文件示例
```

## 快速开始

### 1. 安装JD Cloud CLI

```bash
pip install jdcloud-cli
jdc config init
```

### 2. 配置凭证

Agent 运行时必须已配置以下环境变量：

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> Agent 不得向用户索取凭证值。若未设置，引导用户通过 `jdc config init` 配置。切勿将凭证硬编码在代码或配置文件中。

### 3. 查询实例列表

```bash
jdc vm describe-instances \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
```

## 主要文档

### 📚 [核心概念](references/core-concepts.md)
了解VM的核心组件、实例类型、生命周期、计费模式等基础知识。

### 💻 [CLI使用指南](references/cli-usage.md)
详细的命令行操作手册，包括实例管理、存储管理、网络配置等。

### 🔧 [故障排查](references/troubleshooting.md)
常见问题的诊断流程和解决方案，包括连接问题、性能问题、磁盘问题等。

### 📊 [监控告警](references/monitoring.md)
监控指标说明、告警规则配置、Dashboard设置等。

### 🔌 [集成开发](references/integration.md)
SDK使用、MCP Server配置、Terraform、Ansible等自动化工具集成。

## 常用场景

### 场景1: 创建Web服务器

```bash
# 创建实例
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

# 配置安全组允许HTTP/HTTPS
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

### 场景2: 配置监控告警

```bash
# CPU使用率告警
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

### 场景3: 创建备份快照

```bash
# 为系统盘创建快照
jdc disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --snapshot-name "backup-$(date +%Y%m%d)" \
  --description "Daily backup"
```

### 场景4: 排查连接问题

```bash
# 检查实例状态
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]'

# 检查安全组规则
jdc vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx

# 检查EIP绑定
jdc vpc describe-elastic-ips \
  --region-id cn-north-1 \
  | jq '.result.elasticIps[] | select(.instanceId == "i-xxxxx")'
```

## 最佳实践

### 1. 高可用部署
- 将实例分布在多个可用区
- 使用负载均衡分发流量
- 配置自动伸缩应对流量波动

### 2. 安全加固
- 使用密钥对而非密码登录
- 遵循最小权限原则配置安全组
- 定期更新系统和应用补丁
- 启用云监控和安全审计

### 3. 成本优化
- 长期运行的实例使用包年包月
- 临时任务使用按量付费或抢占式实例
- 定期清理未使用的资源（EIP、磁盘、快照）
- 使用标签进行成本分析

### 4. 备份策略
- 重要数据定期创建快照
- 跨地域复制关键快照
- 测试快照恢复流程
- 保留适当数量的历史快照

### 5. 监控告警
- 配置CPU、内存、磁盘、网络告警
- 设置合理的阈值避免告警疲劳
- 分级告警（警告/严重）使用不同通知方式
- 定期验证告警是否正常工作

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0.0 | 2026-04-28 | 初始版本，包含基础运维指南 |
| 1.0.1 | 2026-04-28 | 添加完整的CLI命令和故障排查指南 |

## 相关资源

- [京东云官方文档](https://docs.jdcloud.com)
- [VM产品文档](https://docs.jdcloud.com/cn/virtual-machines/)
- [API文档](https://docs.jdcloud.com/cn/api/vm/)
- [CLI文档](https://docs.jdcloud.com/cn/cli/)
- [SDK下载](https://github.com/jdcloud-api)

## 技术支持

如遇到问题，可以通过以下方式获取帮助：

1. **在线文档**: https://docs.jdcloud.com
2. **控制台工单**: 登录京东云控制台提交工单
3. **客服热线**: 400-606-5500
4. **在线客服**: 京东云官网右下角在线客服

## License

本项目遵循MIT License。