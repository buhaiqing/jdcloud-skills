# JD Cloud VM Troubleshooting Guide

## 常见问题速查表

| 问题类型 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 无法SSH连接 | 安全组未开放22端口 | 检查并添加安全组规则 |
| 实例启动失败 | 资源不足或配置错误 | 检查配额和配置参数 |
| 磁盘挂载失败 | 设备名冲突或格式错误 | 检查设备名和文件系统 |
| 网络不通 | 路由表或ACL配置错误 | 检查VPC网络配置 |
| 性能下降 | 资源使用率过高 | 监控并优化资源配置 |

## 连接问题排查

### 1. SSH连接失败

#### 症状
```bash
ssh: connect to host x.x.x.x port 22: Connection timed out
# 或
ssh: connect to host x.x.x.x port 22: Connection refused
```

#### 排查步骤

**步骤1: 检查实例状态**
```bash
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0].status'
```
期望输出: `"running"`

**步骤2: 检查安全组规则**
```bash
# 获取实例的网络接口ID
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0].primaryNetworkInterface.networkInterfaceId'

# 检查安全组入站规则
jdc vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  | jq '.result.securityGroup.rules[] | select(.direction == "ingress")'
```

确保存在以下规则：
- 协议: TCP
- 端口: 22
- 源地址: 您的IP地址范围

**步骤3: 检查EIP绑定**
```bash
jdc vpc describe-elastic-ips \
  --region-id cn-north-1 \
  | jq '.result.elasticIps[] | select(.instanceId == "i-xxxxx")'
```

**步骤4: 测试网络连通性**
```bash
# 从本地测试
ping <EIP地址>
telnet <EIP地址> 22

# 从同VPC的其他实例测试
ssh -i ~/.ssh/your-key.pem centos@<内网IP>
```

#### 解决方案

**方案1: 添加安全组规则**
```bash
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 22,
    "toPort": 22,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow SSH"
  }]'
```

**方案2: 使用VNC登录（紧急情况下）**
1. 登录京东云控制台
2. 进入云主机详情页
3. 点击"远程连接" -> "VNC登录"
4. 使用用户名和密码登录

**方案3: 检查防火墙配置**
通过VNC登录后，检查系统防火墙：
```bash
# CentOS/RHEL
sudo systemctl status firewalld
sudo firewall-cmd --list-all

# Ubuntu
sudo ufw status
```

### 2. RDP连接失败（Windows实例）

#### 症状
远程桌面连接超时或被拒绝

#### 排查步骤

**步骤1: 检查安全组规则**
确保开放3389端口：
```bash
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "tcp",
    "fromPort": 3389,
    "toPort": 3389,
    "addressPrefix": "0.0.0.0/0",
    "description": "Allow RDP"
  }]'
```

**步骤2: 检查Windows防火墙**
通过VNC登录，确认远程桌面服务已启用：
```powershell
# PowerShell
Get-Service TermService
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
```

## 实例启动问题

### 1. 实例创建失败

#### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| `InvalidInstanceType` | 实例规格不存在或不支持 | 查询可用的实例规格列表 |
| `InvalidImageId` | 镜像ID无效 | 检查镜像ID是否正确 |
| `InsufficientResource` | 可用区资源不足 | 切换到其他可用区 |
| `InvalidSubnetId` | 子网ID无效 | 检查子网是否存在于指定VPC |
| `QuotaExceeded` | 超出配额限制 | 申请提升配额 |

#### 排查步骤

**步骤1: 验证实例规格**
```bash
jdc vm describe-instance-types \
  --region-id cn-north-1 \
  | jq '.result.instanceTypes[] | select(.instanceType == "g.n2.medium")'
```

**步骤2: 验证镜像**
```bash
jdc vm describe-images \
  --region-id cn-north-1 \
  --image-ids '["img-xxxxx"]'
```

**步骤3: 验证子网**
```bash
jdc vpc describe-subnet \
  --region-id cn-north-1 \
  --subnet-id subnet-xxxxx
```

**步骤4: 检查配额**
```bash
jdc vm describe-quota \
  --region-id cn-north-1
```

#### 解决方案

**方案1: 选择其他可用区**
```bash
# 查询可用区
jdc vm describe-azs --region-id cn-north-1

# 在另一个可用区创建实例
jdc vm create-instances \
  --region-id cn-north-1 \
  --az "cn-north-1b" \
  ...
```

**方案2: 申请提升配额**
联系京东云客服或通过控制台提交工单申请提升配额。

### 2. 实例启动后自动停止

#### 可能原因
- 系统崩溃
- 内存不足导致OOM
- 内核panic

#### 排查步骤

**步骤1: 查看实例状态历史**
```bash
jdc vm describe-instances \
  --region-id cn-north-1 \
  --instance-ids '["i-xxxxx"]' \
  | jq '.result.instances[0]'
```

**步骤2: 通过VNC查看系统日志**
1. 使用VNC登录实例
2. 查看系统日志：
```bash
# Linux
dmesg | tail -50
journalctl -xe --no-pager | tail -100

# 检查是否有OOM记录
grep -i "out of memory" /var/log/messages
```

**步骤3: 检查资源使用**
```bash
# 查看内存使用
free -h

# 查看CPU负载
top -bn1 | head -20

# 查看磁盘空间
df -h
```

#### 解决方案

**方案1: 升级实例规格**
```bash
jdc vm stop-instance --region-id cn-north-1 --instance-id i-xxxxx
jdc vm resize-instance --region-id cn-north-1 --instance-id i-xxxxx --instance-type "g.n2.large"
jdc vm start-instance --region-id cn-north-1 --instance-id i-xxxxx
```

**方案2: 优化应用配置**
- 调整应用程序内存限制
- 优化数据库配置
- 清理不必要的进程和服务

## 磁盘问题排查

### 1. 磁盘挂载失败

#### 症状
```bash
Error attaching disk: Device or resource busy
# 或
mount: wrong fs type, bad option, bad superblock
```

#### 排查步骤

**步骤1: 检查磁盘状态**
```bash
jdc disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]' \
  | jq '.result.disks[0] | {status, instanceId}'
```

**步骤2: 检查设备名是否冲突**
```bash
# 在实例内查看已使用的设备
lsblk
fdisk -l
```

**步骤3: 检查文件系统**
```bash
# 检查文件系统类型
file -s /dev/vdb

# 如果是新盘，需要创建文件系统
sudo mkfs.ext4 /dev/vdb
```

#### 解决方案

**方案1: 使用正确的设备名**
```bash
# 卸载后重新挂载，指定不同的设备名
jdc disk detach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx
jdc disk attach-disk --region-id cn-north-1 --disk-id vol-xxxxx --instance-id i-xxxxx --device-name "/dev/vdc"
```

**方案2: 格式化新磁盘**
```bash
# 创建ext4文件系统
sudo mkfs.ext4 /dev/vdb

# 创建挂载点
sudo mkdir /data

# 挂载磁盘
sudo mount /dev/vdb /data

# 设置开机自动挂载
echo '/dev/vdb /data ext4 defaults 0 0' | sudo tee -a /etc/fstab
```

### 2. 磁盘空间不足

#### 症状
```bash
No space left on device
```

#### 排查步骤

**步骤1: 查看磁盘使用情况**
```bash
df -h
du -sh /* | sort -rh | head -10
```

**步骤2: 查找大文件**
```bash
# 查找大于100MB的文件
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null

# 查找最大的10个目录
du -ah / | sort -rh | head -10
```

**步骤3: 检查日志文件**
```bash
# 查看日志文件大小
ls -lh /var/log/

# 清理旧日志
sudo journalctl --vacuum-time=7d
```

#### 解决方案

**方案1: 清理空间**
```bash
# 清理包管理器缓存
sudo yum clean all  # CentOS
sudo apt-get clean  # Ubuntu

# 删除临时文件
sudo rm -rf /tmp/*

# 清理Docker资源（如使用）
docker system prune -a
```

**方案2: 扩容磁盘**
```bash
# 在控制台或CLI扩容磁盘
jdc disk resize-disk \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --disk-size-gb 200

# 在操作系统内扩展文件系统
# 对于ext4
sudo growpart /dev/vda 1
sudo resize2fs /dev/vda1

# 对于xfs
sudo growpart /dev/vda 1
sudo xfs_growfs /
```

## 网络问题排查

### 1. 实例无法访问外网

#### 排查步骤

**步骤1: 检查路由表**
```bash
# 在实例内
ip route show
route -n

# 应该有默认路由指向网关
default via 192.168.1.1 dev eth0
```

**步骤2: 检查DNS配置**
```bash
cat /etc/resolv.conf

# 测试DNS解析
nslookup www.jdcloud.com
dig www.jdcloud.com
```

**步骤3: 检查NAT网关**
```bash
# 如果使用NAT网关，检查配置
jdc vpc describe-nat-gateways \
  --region-id cn-north-1 \
  --vpc-id vpc-xxxxx
```

**步骤4: 测试网络连通性**
```bash
# 测试内网连通性
ping 192.168.1.1

# 测试外网连通性
ping 8.8.8.8

# 跟踪路由
traceroute www.jdcloud.com
```

#### 解决方案

**方案1: 配置DNS**
```bash
# 编辑DNS配置
sudo vi /etc/resolv.conf

# 添加京东云DNS
nameserver 10.0.0.2
nameserver 8.8.8.8
```

**方案2: 配置NAT网关**
如果子网没有公网访问能力，需要配置NAT网关：
```bash
jdc vpc create-nat-gateway \
  --region-id cn-north-1 \
  --vpc-id vpc-xxxxx \
  --nat-gateway-name "my-nat" \
  --spec "small"
```

### 2. VPC内实例间无法通信

#### 排查步骤

**步骤1: 检查安全组规则**
```bash
# 确保安全组允许VPC内通信
jdc vpc describe-security-group \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  | jq '.result.securityGroup.rules[]'
```

**步骤2: 检查网络ACL**
```bash
jdc vpc describe-network-acls \
  --region-id cn-north-1 \
  --vpc-id vpc-xxxxx
```

**步骤3: 测试连通性**
```bash
# 从实例A ping 实例B
ping <实例B的内网IP>

# 使用telnet测试特定端口
telnet <实例B的内网IP> 80
```

#### 解决方案

**方案1: 添加安全组规则允许VPC内通信**
```bash
jdc vpc add-security-group-rules \
  --region-id cn-north-1 \
  --security-group-id sg-xxxxx \
  --rules '[{
    "direction": "ingress",
    "protocol": "-1",
    "fromPort": -1,
    "toPort": -1,
    "addressPrefix": "192.168.0.0/16",
    "description": "Allow VPC internal traffic"
  }]'
```

## 性能问题排查

### 1. CPU使用率过高

#### 排查步骤

**步骤1: 查看CPU使用详情**
```bash
# 实时监控
top

# 查看历史数据
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric "vm.cpu.util" \
  --service-code vm \
  --resource-id i-xxxxx \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --aggr-type avg
```

**步骤2: 识别高CPU进程**
```bash
# 按CPU使用率排序
ps aux --sort=-%cpu | head -10

# 查看进程树
pstree -p
```

**步骤3: 分析系统调用**
```bash
# 安装sysstat
sudo yum install sysstat

# 查看CPU详细使用情况
mpstat -P ALL 1 5
```

#### 解决方案

**方案1: 优化应用程序**
- 分析并优化高CPU消耗的代码
- 调整线程池大小
- 优化算法复杂度

**方案2: 升级实例规格**
```bash
jdc vm resize-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --instance-type "g.n2.xlarge"
```

### 2. 内存使用率过高

#### 排查步骤

**步骤1: 查看内存使用**
```bash
free -h
cat /proc/meminfo
```

**步骤2: 识别内存泄漏**
```bash
# 按内存使用排序
ps aux --sort=-%mem | head -10

# 监控内存变化
watch -n 1 'free -h'
```

**步骤3: 检查Swap使用**
```bash
swapon --show
cat /proc/swaps
```

#### 解决方案

**方案1: 释放缓存**
```bash
# 清理页面缓存
sudo sync
sudo echo 3 > /proc/sys/vm/drop_caches
```

**方案2: 重启应用**
```bash
# 重启占用内存过多的服务
sudo systemctl restart your-service
```

**方案3: 增加内存**
```bash
jdc vm resize-instance \
  --region-id cn-north-1 \
  --instance-id i-xxxxx \
  --instance-type "r.n2.large"  # 内存型实例
```

### 3. 磁盘I/O性能低

#### 排查步骤

**步骤1: 监控磁盘I/O**
```bash
# 实时I/O监控
iostat -x 1 5

# 查看I/O等待
vmstat 1 10
```

**步骤2: 识别I/O密集进程**
```bash
# 使用iotop
sudo yum install iotop
sudo iotop
```

**步骤3: 检查磁盘类型**
```bash
jdc disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]' \
  | jq '.result.disks[0].diskType'
```

#### 解决方案

**方案1: 升级到SSD云盘**
```bash
# 创建新的SSD云盘
jdc disk create-disk \
  --region-id cn-north-1 \
  --az "cn-north-1a" \
  --disk-type "ssd" \
  --disk-size-gb 100

# 迁移数据后切换
```

**方案2: 优化应用I/O**
- 使用异步I/O
- 增加缓存层
- 批量写入代替频繁小文件写入

## 快照和备份问题

### 1. 快照创建失败

#### 可能原因
- 磁盘正在执行其他操作
- 配额不足
- 磁盘状态异常

#### 解决方案

**步骤1: 检查磁盘状态**
```bash
jdc disk describe-disks \
  --region-id cn-north-1 \
  --disk-ids '["vol-xxxxx"]' \
  | jq '.result.disks[0].status'
```

**步骤2: 重试创建**
```bash
jdc disk create-snapshot \
  --region-id cn-north-1 \
  --disk-id vol-xxxxx \
  --snapshot-name "retry-snapshot"
```

### 2. 从快照恢复失败

#### 解决方案

**步骤1: 验证快照完整性**
```bash
jdc disk describe-snapshots \
  --region-id cn-north-1 \
  --snapshot-ids '["snap-xxxxx"]' \
  | jq '.result.snapshots[0].status'
```

**步骤2: 检查目标可用区资源**
```bash
jdc vm describe-azs --region-id cn-north-1
```

## 常用诊断命令汇总

### 系统层面
```bash
# 系统信息
uname -a
cat /etc/os-release

# CPU信息
lscpu
cat /proc/cpuinfo

# 内存信息
free -h
cat /proc/meminfo

# 磁盘信息
lsblk
fdisk -l
df -h

# 网络信息
ip addr show
ip route show
cat /etc/resolv.conf

# 进程信息
ps aux
top -bn1

# 系统负载
uptime
w
```

### 日志查看
```bash
# 系统日志
tail -f /var/log/messages      # CentOS
tail -f /var/log/syslog        # Ubuntu

# 内核日志
dmesg | tail -50

# 认证日志
tail -f /var/log/secure        # CentOS
tail -f /var/log/auth.log      # Ubuntu

# systemd日志
journalctl -xe --no-pager
journalctl -u your-service -f
```

### 网络诊断
```bash
# 连通性测试
ping -c 4 <target>
traceroute <target>

# 端口测试
telnet <host> <port>
nc -zv <host> <port>

# DNS测试
nslookup <domain>
dig <domain>

# 网络统计
netstat -tuln
ss -tuln
```

## 获取技术支持

### 自助服务
1. **京东云文档**: https://docs.jdcloud.com
2. **API文档**: https://docs.jdcloud.com/cn/api
3. **CLI文档**: https://docs.jdcloud.com/cn/cli

### 联系支持
1. **控制台工单**: 登录京东云控制台提交工单
2. **客服热线**: 400-606-5500
3. **在线客服**: 京东云官网右下角在线客服

### 提供信息清单
提交工单时请提供以下信息：
- 实例ID
- 问题发生时间
- 错误信息截图
- 已执行的排查步骤
- 相关日志片段