# JD Cloud VM Quick Reference

> 本文档提供最常用的 VM 运维命令速查。详细用法请参考 [CLI Usage Guide](references/cli-usage.md)。

## 实例生命周期速查

### 1. 查询实例
```bash
# 列表查询
jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 20

# 指定实例
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# 按状态过滤
jdc vm describe-instances --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]'
```

### 2. 创建 → 启动 → 停止 → 删除
```bash
# 创建实例（最简配置）
jdc vm create-instances --region-id cn-north-1 --az "cn-north-1a" \
  --instance-type "g.n2.medium" --image-id "img-xxxxx" --name "my-vm" \
  --primary-network-interface '[{"subnetId":"subnet-xxxxx","securityGroupIds":["sg-xxxxx"]}]' \
  --system-disk '[{"diskCategory":"local","diskSizeGB":40}]' \
  --charge-mode "postpaid_by_duration"

# 启动/停止/重启
jdc vm start-instance   --region-id cn-north-1 --instance-id i-xxxxx
jdc vm stop-instance    --region-id cn-north-1 --instance-id i-xxxxx
jdc vm reboot-instance  --region-id cn-north-1 --instance-id i-xxxxx

# 删除（加 --delete-data-disks 同时删除数据盘）
jdc vm delete-instance --region-id cn-north-1 --instance-id i-xxxxx
```

## 网络配置速查

### 弹性公网IP (EIP)
```bash
# 申请 → 绑定 → 解绑 → 释放
jdc vpc create-elastic-ip --region-id cn-north-1 --bandwidth-mbps 10 --charge-mode "postpaid_by_duration"
jdc vpc associate-elastic-ip    --region-id cn-north-1 --elastic-ip-id eip-xxxxx --instance-id i-xxxxx
jdc vpc disassociate-elastic-ip --region-id cn-north-1 --elastic-ip-id eip-xxxxx
jdc vpc delete-elastic-ip       --region-id cn-north-1 --elastic-ip-id eip-xxxxx
```

### 安全组规则
```bash
# 添加入站规则（⚠️ 生产环境请限制IP范围）
jdc vpc add-security-group-rules --region-id cn-north-1 --security-group-id sg-xxxxx \
  --rules '[{"direction":"ingress","protocol":"tcp","fromPort":22,"toPort":22,"addressPrefix":"0.0.0.0/0"}]'

# 删除规则
jdc vpc remove-security-group-rules --region-id cn-north-1 \
  --security-group-id sg-xxxxx --rule-ids '["rule-xxxxx"]'
```

## 存储管理速查

### 云硬盘
```bash
# 创建 → 挂载 → 卸载 → 扩容 → 删除
jdc disk create-disk --region-id cn-north-1 --az "cn-north-1a" \
  --disk-type "ssd" --disk-size-gb 100 --disk-name "data-disk" --charge-mode "postpaid_by_duration"
jdc disk attach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx --device-name "/dev/vdb"
jdc disk detach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx
jdc disk resize-disk --region-id cn-north-1 --disk-id vol-xxxxx --disk-size-gb 200
jdc disk delete-disk --region-id cn-north-1 --disk-id vol-xxxxx
```

### 快照
```bash
# 创建 → 查询 → 删除
jdc disk create-snapshot --region-id cn-north-1 --disk-id vol-xxxxx --snapshot-name "backup-$(date +%Y%m%d)"
jdc disk describe-snapshots --region-id cn-north-1 --page-number 1 --page-size 20
jdc disk delete-snapshot --region-id cn-north-1 --snapshot-id snap-xxxxx
```

## 监控告警速查

### 查询监控数据
```bash
# Linux
jdc monitor describe-metric-data --region-id cn-north-1 \
  --metric "vm.cpu.util" --service-code vm --resource-id i-xxxxx \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --aggr-type avg

# macOS
jdc monitor describe-metric-data --region-id cn-north-1 \
  --metric "vm.cpu.util" --service-code vm --resource-id i-xxxxx \
  --start-time "$(date -u -v -1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --aggr-type avg
```

### 告警规则
```bash
# 创建 → 查询 → 删除
jdc monitor create-alarm --region-id cn-north-1 --alarm-name "CPU-High" \
  --service-code vm --resource-id i-xxxxx --metric-name "vm.cpu.util" \
  --comparison-operator "gt" --threshold 90 --period 300 --evaluation-periods 2 \
  --contact-group-id 1 --notice-type "sms,email"
jdc monitor describe-alarms --region-id cn-north-1 --page-number 1 --page-size 20
jdc monitor delete-alarm --region-id cn-north-1 --alarm-id alarm-xxxxx
```

## 常用监控指标

| 指标 | Code | 单位 | 说明 |
|------|------|------|------|
| CPU使用率 | vm.cpu.util | % | CPU平均使用率 |
| 内存使用率 | vm.memory.usage | % | 内存使用百分比 |
| 磁盘使用率 | vm.disk.usage | % | 磁盘空间使用率 |
| 网络流入带宽 | vm.network.in.bytes | KB/s | 入网流量 |
| 网络流出带宽 | vm.network.out.bytes | KB/s | 出网流量 |
| TCP连接数 | vm.tcp.connections | count | 当前TCP连接数 |
| 系统负载(1分钟) | vm.load.1m | - | 1分钟平均负载 |
| 磁盘IOPS读 | vm.disk.iops.read | count/s | 磁盘读IOPS |
| 磁盘IOPS写 | vm.disk.iops.write | count/s | 磁盘写IOPS |

## 实例状态说明

| 状态 | 说明 | 可操作 |
|------|------|--------|
| running | 运行中 | 停止、重启、删除 |
| stopped | 已停止 | 启动、删除 |
| starting | 启动中 | 等待 |
| stopping | 停止中 | 等待 |
| resizing | 变配中 | 等待 |
| error | 异常 | 查看日志、删除 |

## 常用Region ID

| Region | ID | 可用区 |
|--------|-----|--------|
| 华北-北京 | cn-north-1 | cn-north-1a, cn-north-1b, cn-north-1c |
| 华东-上海 | cn-east-1 | cn-east-1a, cn-east-1b, cn-east-1c |
| 华南-广州 | cn-south-1 | cn-south-1a, cn-south-1b |

## 实例规格速查

| 规格 | CPU | 内存 | 适用场景 |
|------|-----|------|----------|
| g.n2.medium | 1核 | 2GB | 测试、开发 |
| g.n2.large | 2核 | 4GB | 小型应用 |
| g.n2.xlarge | 4核 | 8GB | 中型应用 |
| g.n2.2xlarge | 8核 | 16GB | 大型应用 |
| g.n2.4xlarge | 16核 | 32GB | 高性能计算 |

> 注：规格命名规则 `g.n2.xxx` 中，g=通用型，n2=第二代，xxx=规格大小

## 推荐告警阈值

| 指标 | 警告 | 严重 | 说明 |
|------|------|------|------|
| CPU使用率 | > 75% | > 90% | 持续5分钟 |
| 内存使用率 | > 80% | > 95% | 持续5分钟 |
| 磁盘使用率 | > 70% | > 85% | 持续5分钟 |
| 系统负载(1分钟) | > CPU核数×2 | > CPU核数×4 | 持续3分钟 |
| 磁盘IOPS使用率 | > 70% | > 90% | 持续5分钟 |

## 常见端口与安全建议

| 服务 | 端口 | 协议 | 安全建议 |
|------|------|------|----------|
| SSH | 22 | TCP | ⚠️ 限制IP范围，禁用root登录 |
| HTTP | 80 | TCP | 配合HTTPS使用 |
| HTTPS | 443 | TCP | 启用TLS 1.2+ |
| RDP (Windows) | 3389 | TCP | ⚠️ 限制IP范围，使用VPN |
| MySQL | 3306 | TCP | ⚠️ 不对外开放，使用内网 |
| Redis | 6379 | TCP | ⚠️ 不对外开放，启用认证 |

### 安全组最佳实践
```bash
# ❌ 不推荐：开放所有IP
# --rules '[{"direction":"ingress","protocol":"tcp","fromPort":22,"toPort":22,"addressPrefix":"0.0.0.0/0"}]'

# ✅ 推荐：限制IP范围
# --rules '[{"direction":"ingress","protocol":"tcp","fromPort":22,"toPort":22,"addressPrefix":"192.168.1.0/24"}]'
```

## 故障排查速查

### SSH连接失败
```bash
# 1. 检查实例状态
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# 2. 检查安全组规则（确认22端口开放且IP允许）
jdc vpc describe-security-group --region-id cn-north-1 --security-group-id sg-xxxxx

# 3. 检查EIP绑定
jdc vpc describe-elastic-ips --region-id cn-north-1

# 4. 本地测试连通性
ping <EIP>
telnet <EIP> 22
```

### 磁盘空间不足
```bash
# 1. 查看磁盘使用情况（在实例内执行）
df -h

# 2. 查找大文件
du -sh /* 2>/dev/null | sort -rh | head -10

# 3. 清理日志（谨慎操作）
find /var/log -name "*.log" -mtime +7 -delete

# 4. 扩容云硬盘
jdc disk resize-disk --region-id cn-north-1 --disk-id vol-xxxxx --disk-size-gb 200
# 扩容后需在实例内执行文件系统扩容（参考详细文档）
```

### 性能问题排查
```bash
# 在实例内执行
# CPU
top -bn1 | head -20

# 内存
free -h

# 磁盘I/O
iostat -x 1 5 2>/dev/null || echo "安装sysstat: yum install sysstat"

# 网络连接
ss -tuln | head -20

# 进程资源占用
ps aux --sort=-%cpu | head -10
```

## 代码示例

### Python SDK 快速开始
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.client import VmClient
from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import DescribeInstancesRequest

# 初始化
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = VmClient(credential, 'cn-north-1')

# 查询实例
request = DescribeInstancesRequest({
    "regionId": "cn-north-1",
    "pageNumber": 1,
    "pageSize": 20
})
response = client.describeInstances(request)

if response.error is None:
    for instance in response.result.instances:
        print(f"{instance.instanceId}: {instance.status}")
```

> 完整SDK示例参考：[Integration Guide](references/integration.md)

### Terraform 快速配置
```hcl
resource "jdcloud_vm_instance" "web" {
  region_id     = "cn-north-1"
  az            = "cn-north-1a"
  instance_type = "g.n2.medium"
  image_id      = "img-xxxxx"
  name          = "web-server"
  
  primary_network_interface {
    subnet_id          = "subnet-xxxxx"
    security_group_ids = ["sg-xxxxx"]
  }
  
  system_disk {
    disk_category = "local"
    disk_size_gb  = 40
  }
}
```

## 实用技巧

### 批量操作
```bash
# 批量停止所有运行中的实例
jdc vm describe-instances --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]' \
  | jq -r '.result.instances[].instanceId' \
  | while read id; do
      echo "Stopping $id..."
      jdc vm stop-instance --region-id cn-north-1 --instance-id "$id"
    done

# 批量为实例打标签
for id in i-xxx1 i-xxx2 i-xxx3; do
  jdc vm modify-instance-attribute --region-id cn-north-1 \
    --instance-id "$id" --name "web-server"
done
```

### JSON格式化输出
```bash
# 美化输出
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]' | jq

# 提取关键信息
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0] | {
    id: .instanceId,
    name: .name,
    status: .status,
    privateIp: .primaryNetworkInterface.privateIpAddress,
    publicIp: .primaryNetworkInterface.elasticIp.publicIpAddress
  }'

# 列表展示所有实例
jdc vm describe-instances --region-id cn-north-1 \
  | jq -r '.result.instances[] | "\(.instanceId)\t\(.name)\t\(.status)\t\(.primaryNetworkInterface.privateIpAddress)"' \
  | column -t -s $'\t'
```

## 资源限制与计费

### 资源配额

| 资源 | 默认配额 | 上限 | 说明 |
|------|---------|------|------|
| 实例数量 | 20 | 可提升 | 按地域计算 |
| EIP数量 | 20 | 可提升 | 按地域计算 |
| 安全组规则 | 100/组 | 200 | 入站+出站 |
| 快照数量 | 100 | 可提升 | 每个地域 |
| 云硬盘数量 | 20 | 可提升 | 每实例最多挂载16块 |
| 自定义镜像 | 10 | 50 | 每个地域 |

### 计费模式

| 计费方式 | 适用场景 | 特点 |
|----------|----------|------|
| 包年包月 | 长期运行 | 价格优惠，需预付费 |
| 按量付费 | 短期/测试 | 按秒计费，灵活 |
| 抢占式 | 批处理任务 | 价格低，可能被回收 |

### 计费项说明
- **实例**: CPU + 内存费用
- **云硬盘**: 容量 × 时长（SSD单价高于HDD）
- **EIP**: 带宽费用 + IP占用费
- **快照**: 实际存储容量 × 时长
- **流量**: 出网流量计费（入站免费）

## 相关文档

| 文档 | 说明 |
|------|------|
| [CLI Usage Guide](references/cli-usage.md) | 完整CLI命令参考 |
| [Core Concepts](references/core-concepts.md) | 核心概念说明 |
| [Troubleshooting](references/troubleshooting.md) | 详细故障排查指南 |
| [Monitoring](references/monitoring.md) | 监控告警配置 |
| [Integration](references/integration.md) | SDK/MCP集成 |
| [官方文档](https://docs.jdcloud.com/cn/virtual-machines/) | 京东云官方文档 |
| [API文档](https://docs.jdcloud.com/cn/api/vm/) | API接口文档 |
| [控制台](https://console.jdcloud.com) | 京东云控制台 |