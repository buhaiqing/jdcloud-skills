# JD Cloud VM CLI Usage Guide

## 前置条件

确保已安装并配置好京东云CLI：

```bash
# 安装CLI
pip install jdcloud-cli

# 初始化配置
jdc config init

# 验证配置
jdc vm describe-instances --region-id cn-north-1 --page-number 1 --page-size 1
```

## 实例管理

### 查询实例列表

```bash
# 查询所有实例
jdc vm describe-instances \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 根据实例ID查询
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]'

# 根据名称过滤
jdc vm describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"instance-name","values":["my-vm"]}]'

# 查询指定状态的实例
jdc vm describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]'
```

### 创建实例

```bash
# 创建单个实例
jdc vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --instance-type "g.n2.medium" \
  --image-id "img-xxxxx" \
  --name "my-vm" \
  --description "My first VM" \
  --primary-network-interface '{
    "subnetId": "subnet-xxxxx",
    "securityGroupIds": ["sg-xxxxx"],
    "networkInterfaceName": "eth0"
  }' \
  --system-disk '{
    "diskCategory": "local",
    "diskSizeGB": 40
  }' \
  --data-disks '[{
    "diskCategory": "cloud_ssd",
    "diskSizeGB": 100,
    "deviceName": "/dev/vdb",
    "autoDelete": true
  }]' \
  --key-names '["my-keypair"]' \
  --charge-mode "postpaid_by_duration"

# 批量创建实例
jdc vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --instance-type "g.n2.medium" \
  --image-id "img-xxxxx" \
  --name-prefix "web-server" \
  --count 3 \
  --primary-network-interface '{
    "subnetId": "subnet-xxxxx",
    "securityGroupIds": ["sg-xxxxx"]
  }' \
  --system-disk '{"diskCategory": "local", "diskSizeGB": 40}' \
  --charge-mode "postpaid_by_duration"
```

### 启动/停止实例

```bash
# 启动实例
jdc vm start-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx

# 停止实例（正常关机）
jdc vm stop-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx

# 强制停止实例
jdc vm stop-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --force-stop true

# 重启实例
jdc vm reboot-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx
```

### 删除实例

```bash
# 删除单个实例
jdc vm delete-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx

# 删除实例并释放关联资源
jdc vm delete-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --delete-data-disks true \
  --delete-snapshot true
```

### 变更实例配置

```bash
# 变更实例规格
jdc vm resize-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --instance-type "g.n2.large"

# 注意：变配需要实例处于停止状态
jdc vm stop-instance --region-id cn-north-1 --instance-id i-xxxxx
jdc vm resize-instance --region-id cn-north-1 --instance-id i-xxxxx --instance-type "g.n2.large"
jdc vm start-instance --region-id cn-north-1 --instance-id i-xxxxx
```

## 镜像管理

### 查询镜像

```bash
# 查询公共镜像
jdc vm describe-images \
  --region-id cn-north-1 \
  --owners official \
  --page-number 1 \
  --page-size 20

# 查询自定义镜像
jdc vm describe-images \
  --region-id cn-north-1 \
  --owners self

# 查询指定镜像详情
jdc vm describe-images \
  --region-id cn-north-1 \
  --image-ids '["img-xxxxx"]'
```

### 创建自定义镜像

```bash
# 基于实例创建镜像
jdc vm create-image \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --name "my-custom-image" \
  --description "Custom image from production server"

# 基于快照创建镜像
jdc vm create-image \
  --region-id cn-north-1 \
  --snapshot-id "snap-xxxxx" \
  --name "my-snapshot-image" \
  --description "Image created from snapshot"
```

### 删除镜像

```bash
jdc vm delete-image \
  --region-id cn-north-1 \
  --image-id img-xxxxx
```

## 云硬盘管理

### 查询云硬盘

```bash
# 查询云硬盘列表
jdc disk describe-disks \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 查询指定云硬盘
jdc disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]'

# 查询挂载到指定实例的云硬盘
jdc disk describe-disks \
  --region-id cn-north-1 \
  --filters '[{"name":"instance-id","values":["i-xxxxx"]}]'
```

### 创建云硬盘

```bash
# 创建云硬盘
jdc disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --disk-type "ssd" \
  --disk-size-gb 100 \
  --disk-name "data-disk-1" \
  --description "Data disk for database" \
  --charge-mode "postpaid_by_duration"

# 创建云硬盘并挂载到实例
jdc disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --disk-type "ssd" \
  --disk-size-gb 100 \
  --disk-name "data-disk-1" \
  --instance-id "i-xxxxx" \
  --device-name "/dev/vdb" \
  --charge-mode "postpaid_by_duration"
```

### 挂载/卸载云硬盘

```bash
# 挂载云硬盘
jdc disk attach-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --instance-id i-xxxxx \
  --device-name "/dev/vdb"

# 卸载云硬盘
jdc disk detach-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --instance-id i-xxxxx
```

### 扩容云硬盘

```bash
# 扩容云硬盘（只能扩容，不能缩容）
jdc disk resize-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --disk-size-gb 200

# 注意：扩容后需要在操作系统内进行文件系统扩容
```

### 删除云硬盘

```bash
# 删除云硬盘（必须先卸载）
jdc disk detach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx
jdc disk delete-disk --region-id cn-north-1 --disk-id vol-xxxxx
```

## 快照管理

### 创建快照

```bash
# 为云硬盘创建快照
jdc disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --snapshot-name "backup-2026-04-28" \
  --description "Daily backup snapshot"

# 为实例的所有云硬盘创建快照
jdc disk create-snapshots \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --snapshot-name-prefix "instance-backup"
```

### 查询快照

```bash
# 查询快照列表
jdc disk describe-snapshots \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 查询指定快照
jdc disk describe-snapshots \
  --region-id cn-north-1 \
  --snapshot-ids '["snap-xxxxx"]'

# 查询指定云硬盘的快照
jdc disk describe-snapshots \
  --region-id cn-north-1 \
  --filters '[{"name":"disk-id","values":["vol-xxxxx"]}]'
```

### 删除快照

```bash
jdc disk delete-snapshot \
  --region-id cn-north-1 \
  --snapshot-id snap-xxxxx
```

### 基于快照创建云硬盘

```bash
jdc disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --snapshot-id "snap-xxxxx" \
  --disk-name "restored-disk" \
  --charge-mode "postpaid_by_duration"
```

## 安全组管理

### 查询安全组

```bash
# 查询安全组列表
jdc vpc describe-security-groups \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 查询指定安全组详情
jdc vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx
```

### 创建安全组

```bash
jdc vpc create-security-group \
  --region-id cn-north-1 \
  --vpc-id "vpc-xxxxx" \
  --security-group-name "web-sg" \
  --description "Security group for web servers"
```

### 添加安全组规则

```bash
# 添加入站规则 - 允许HTTP访问
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 80,
    "toPort": 80,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow HTTP"
  }]'

# 添加入站规则 - 允许SSH访问（建议限制IP范围）
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 22,
    "toPort": 22,
    "addressPrefix": "192.168.1.0/24",
    "description": "Allow SSH from office"
  }]'

# 添加入站规则 - 允许HTTPS访问
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 443,
    "toPort": 443,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow HTTPS"
  }]'

# 添加出站规则 - 允许所有出站流量
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "egress",
    "protocol": "-1",
    "fromPort": -1,
    "toPort": -1,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow all outbound"
  }]'
```

### 删除安全组规则

```bash
jdc vpc remove-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rule-ids '["rule-xxxxx"]'
```

### 将实例加入安全组

```bash
# 为网络接口分配安全组
jdc vpc assign-security-group \
  --region-id cn-north-1 \
  --network-interface-id "eni-xxxxx" \
  --security-group-id sg-xxxxx
```

## 密钥对管理

### 创建密钥对

```bash
# 创建密钥对（私钥会自动下载）
jdc vm create-keypair \
  --region-id cn-north-1 \
  --key-name "my-keypair" \
  --description "Key pair for production servers"
```

### 查询密钥对

```bash
# 查询密钥对列表
jdc vm describe-keypairs \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 查询指定密钥对
jdc vm describe-keypairs \
  --region-id cn-north-1 \
  --key-names '["my-keypair"]'
```

### 导入公钥

```bash
# 导入已有的公钥
jdc vm import-keypair \
  --region-id cn-north-1 \
  --key-name "existing-keypair" \
  --public-key "ssh-rsa AAAAB3NzaC1yc2E... user@host"
```

### 删除密钥对

```bash
jdc vm delete-keypair \
  --region-id cn-north-1 \
  --key-name "my-keypair"
```

## 弹性公网IP管理

### 申请EIP

```bash
jdc vpc create-elastic-ip \
  --region-id cn-north-1 \
  --bandwidth-mbps 10 \
  --charge-mode "postpaid_by_duration" \
  --description "EIP for web server"
```

### 查询EIP

```bash
# 查询EIP列表
jdc vpc describe-elastic-ips \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20

# 查询指定EIP
jdc vpc describe-elastic-ips \
  --region-id cn-north-1 \
  --elastic-ip-ids '["eip-xxxxx"]'
```

### 绑定/解绑EIP

```bash
# 绑定EIP到实例
jdc vpc associate-elastic-ip \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx \
  --instance-id i-xxxxx

# 解绑EIP
jdc vpc disassociate-elastic-ip \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx
```

### 调整带宽

```bash
jdc vpc modify-elastic-ip-bandwidth \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx \
  --bandwidth-mbps 20
```

### 释放EIP

```bash
jdc vpc delete-elastic-ip \
  --region-id cn-north-1 \
  --elastic-ip-id eip-xxxxx
```

## 实用命令组合

### 查看实例详细信息（包括IP、状态等）

```bash
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' | jq '.result.instances[0] | {
    instanceId: .instanceId,
    name: .name,
    status: .status,
    privateIp: .primaryNetworkInterface.privateIpAddress,
    publicIp: .primaryNetworkInterface.elasticIp.publicIpAddress,
    instanceType: .instanceType,
    az: .az
  }'
```

### 批量停止实例

```bash
# 获取所有运行中的实例ID并停止
jdc vm describe-instances \
  --region-id cn-north-1 \
  --filters '[{"name":"status","values":["running"]}]' \
  | jq -r '.result.instances[].instanceId' \
  | while read instance_id; do
      echo "Stopping instance: $instance_id"
      jdc vm stop-instance --region-id cn-north-1 --instance-id "$instance_id"
    done
```

### 清理未使用的EIP

```bash
# 查找未绑定的EIP并释放
jdc vpc describe-elastic-ips \
  --region-id cn-north-1 \
  | jq -r '.result.elasticIps[] | select(.instanceId == null) | .elasticIpId' \
  | while read eip_id; do
      echo "Releasing EIP: $eip_id"
      jdc vpc delete-elastic-ip --region-id cn-north-1 --elastic-ip-id "$eip_id"
    done
```

### 监控实例资源使用

```bash
# 查询实例CPU使用率（最近1小时）
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type avg
```

## 常见问题排查

### 实例无法连接

```bash
# 1. 检查实例状态
jdc vm describe-instances --region-id cn-north-1 --instance-ids '["i-xxxxx"]'

# 2. 检查安全组规则
jdc vpc describe-security-group --region-id cn-north-1 --security-group-id sg-xxxxx

# 3. 检查网络接口
jdc vpc describe-network-interface --region-id cn-north-1 --network-interface-id eni-xxxxx
```

### 磁盘空间不足

```bash
# 1. 查看当前磁盘信息
jdc disk describe-disks --region-id cn-north-1 --filters '[{"name":"instance-id","values":["i-xxxxx"]}]'

# 2. 扩容磁盘
jdc disk resize-disk --region-id cn-north-1 --disk-id vol-xxxxx --disk-size-gb 200
```

## 最佳实践提示

1. **使用标签管理资源**: 为实例、磁盘等资源添加标签，便于管理和成本分析
2. **定期创建快照**: 重要数据定期备份，建议使用自动化脚本
3. **合理配置安全组**: 遵循最小权限原则，仅开放必要端口
4. **监控资源使用**: 设置告警规则，及时发现异常
5. **使用密钥对登录**: 比密码更安全，避免暴力破解
6. **多可用区部署**: 提高应用可用性
7. **清理未使用资源**: 定期检查并释放未使用的EIP、磁盘等