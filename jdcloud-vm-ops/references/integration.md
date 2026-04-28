# JD Cloud VM Integration Guide

## 概述

本文档介绍如何将JD Cloud VM服务与其他工具和平台集成，包括SDK开发、MCP Server配置、Terraform自动化等。

## SDK集成

### Python SDK

#### 安装

```bash
pip install jdcloud_sdk
```

#### 初始化客户端

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.client import VmClient

# 使用环境变量管理凭证（推荐）
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# 创建VM客户端
client = VmClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

#### 查询实例列表

```python
from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import DescribeInstancesRequest

request = DescribeInstancesRequest({
    "regionId": "cn-north-1",
    "pageNumber": 1,
    "pageSize": 20
})

response = client.describeInstances(request)

if response.error is None:
    for instance in response.result.instances:
        print(f"Instance ID: {instance.instanceId}")
        print(f"Name: {instance.name}")
        print(f"Status: {instance.status}")
        print(f"Private IP: {instance.primaryNetworkInterface.privateIpAddress}")
        if instance.primaryNetworkInterface.elasticIp:
            print(f"Public IP: {instance.primaryNetworkInterface.elasticIp.publicIpAddress}")
        print("---")
else:
    print(f"Error: {response.error.message}")
```

#### 创建实例

```python
from jdcloud_sdk.services.vm.apis.CreateInstancesRequest import CreateInstancesRequest

request = CreateInstancesRequest({
    "regionId": "cn-north-1",
    "az": "cn-north-1a",
    "instanceType": "g.n2.medium",
    "imageId": "img-xxxxx",
    "name": "my-vm",
    "description": "Created via SDK",
    "primaryNetworkInterface": {
        "subnetId": "subnet-xxxxx",
        "securityGroupIds": ["sg-xxxxx"],
        "networkInterfaceName": "eth0"
    },
    "systemDisk": {
        "diskCategory": "local",
        "diskSizeGB": 40
    },
    "dataDisks": [
        {
            "diskCategory": "cloud_ssd",
            "diskSizeGB": 100,
            "deviceName": "/dev/vdb",
            "autoDelete": True
        }
    ],
    "keyNames": ["my-keypair"],
    "chargeMode": "postpaid_by_duration"
})

response = client.createInstances(request)

if response.error is None:
    print(f"Instances created: {response.result.instanceIds}")
else:
    print(f"Error: {response.error.message}")
```

#### 启动/停止实例

```python
from jdcloud_sdk.services.vm.apis.StartInstanceRequest import StartInstanceRequest
from jdcloud_sdk.services.vm.apis.StopInstanceRequest import StopInstanceRequest

# 启动实例
start_request = StartInstanceRequest({
    "regionId": "cn-north-1",
    "instanceId": "i-xxxxx"
})
start_response = client.startInstance(start_request)

# 停止实例
stop_request = StopInstanceRequest({
    "regionId": "cn-north-1",
    "instanceId": "i-xxxxx"
})
stop_response = client.stopInstance(stop_request)
```

#### 创建快照

```python
from jdcloud_sdk.services.disk.apis.CreateSnapshotRequest import CreateSnapshotRequest
from jdcloud_sdk.services.disk.client import DiskClient

# 创建Disk客户端
disk_client = DiskClient(credential, 'cn-north-1')

request = CreateSnapshotRequest({
    "regionId": "cn-north-1",
    "diskId": "vol-xxxxx",
    "snapshotName": "backup-snapshot",
    "description": "Automated backup"
})

response = disk_client.createSnapshot(request)

if response.error is None:
    print(f"Snapshot created: {response.result.snapshotId}")
else:
    print(f"Error: {response.error.message}")
```

#### 错误处理

```python
from jdcloud_sdk.core.exception import ClientException, ServerException

try:
    response = client.describeInstances(request)
    
    if response.error is not None:
        print(f"API Error: {response.error.code} - {response.error.message}")
        
except ClientException as e:
    print(f"Client error: {e.error_msg}")
    # 客户端错误，通常是参数错误或网络问题
    
except ServerException as e:
    print(f"Server error: {e.error_code} - {e.error_msg}")
    # 服务端错误，通常是京东云服务端问题
```

### Java SDK

#### Maven依赖

```xml
<dependency>
    <groupId>com.jdcloud.sdk</groupId>
    <artifactId>vm</artifactId>
    <version>1.0.0</version>
</dependency>
```

#### 初始化客户端

```java
import com.jdcloud.sdk.auth.CredentialsProvider;
import com.jdcloud.sdk.auth.EnvironmentVariablesCredentialsProvider;
import com.jdcloud.sdk.http.HttpRequestConfig;
import com.jdcloud.sdk.service.vm.client.VmClient;

// 使用环境变量获取凭证
CredentialsProvider credentialsProvider = new EnvironmentVariablesCredentialsProvider();

// 创建VM客户端
VmClient client = VmClient.builder()
    .credentialsProvider(credentialsProvider)
    .httpRequestConfig(new HttpRequestConfig.Builder().build())
    .build();
```

#### 查询实例

```java
import com.jdcloud.sdk.service.vm.model.DescribeInstancesRequest;
import com.jdcloud.sdk.service.vm.model.DescribeInstancesResponse;

DescribeInstancesRequest request = new DescribeInstancesRequest();
request.setRegionId("cn-north-1");
request.setPageNumber(1);
request.setPageSize(20);

DescribeInstancesResponse response = client.describeInstances(request);

if (response.getError() == null) {
    response.getResult().getInstances().forEach(instance -> {
        System.out.println("Instance ID: " + instance.getInstanceId());
        System.out.println("Status: " + instance.getStatus());
    });
} else {
    System.out.println("Error: " + response.getError().getMessage());
}
```

## MCP Server集成

### 什么是MCP Server

Model Context Protocol (MCP) Server是一种标准化的方式，让AI助手能够与外部系统交互。通过MCP Server，AI可以直接操作JD Cloud资源。

### 配置MCP Server

在您的MCP客户端配置文件中添加JD Cloud VM Server：

```json
{
  "mcpServers": {
    "jdcloud-vm": {
      "command": "uvx",
      "args": ["run", "--python", "3.10", "@jdcloud/vm-mcp"],
      "env": {
        "JDC_ACCESS_KEY": "{{env.JDC_ACCESS_KEY}}",
        "JDC_SECRET_KEY": "{{env.JDC_SECRET_KEY}}",
        "JDC_REGION": "{{env.JDC_REGION}}"
      }
    }
  }
}
```

> **注意**: 
> - MCP服务器使用Python 3.10+开发
> - 使用`uvx`命令启动
> - 环境变量应在shell配置文件或CI/CD系统中设置
> - **切勿**在配置文件中硬编码凭证

### 可用的MCP工具

配置完成后，AI助手可以使用以下工具：

#### 1. 查询实例

```
描述: 查询VM实例列表或详情
参数:
  - region_id: 区域ID (必填)
  - instance_ids: 实例ID列表 (可选)
  - filters: 过滤条件 (可选)
  
示例: 查询所有运行中的实例
```

#### 2. 创建实例

```
描述: 创建新的VM实例
参数:
  - region_id: 区域ID (必填)
  - az: 可用区 (必填)
  - instance_type: 实例规格 (必填)
  - image_id: 镜像ID (必填)
  - name: 实例名称 (必填)
  - subnet_id: 子网ID (必填)
  - security_group_ids: 安全组ID列表 (必填)
  - key_name: 密钥对名称 (可选)
  
示例: 创建一个通用型实例
```

#### 3. 启动/停止实例

```
描述: 启动或停止VM实例
参数:
  - region_id: 区域ID (必填)
  - instance_id: 实例ID (必填)
  - action: start 或 stop (必填)
  
示例: 停止指定实例
```

#### 4. 查询监控数据

```
描述: 查询实例的监控指标数据
参数:
  - region_id: 区域ID (必填)
  - instance_id: 实例ID (必填)
  - metric: 指标名称 (必填)
  - start_time: 开始时间 (可选)
  - end_time: 结束时间 (可选)
  
示例: 查询最近1小时的CPU使用率
```

#### 5. 创建快照

```
描述: 为云硬盘创建快照
参数:
  - region_id: 区域ID (必填)
  - disk_id: 云硬盘ID (必填)
  - snapshot_name: 快照名称 (必填)
  
示例: 为系统盘创建备份快照
```

### 使用示例场景

#### 场景1: 日常巡检

用户: "检查生产环境所有VM实例的状态和资源使用情况"

AI助手将:
1. 调用`list_instances`获取所有实例
2. 对每个实例调用`get_metrics`获取CPU、内存使用率
3. 汇总并展示结果

#### 场景2: 故障排查

用户: "实例i-xxxxx无法连接，帮我排查一下"

AI助手将:
1. 调用`describe_instance`检查实例状态
2. 调用`describe_security_group`检查安全组规则
3. 调用`describe_network_interface`检查网络配置
4. 提供排查建议

#### 场景3: 批量操作

用户: "晚上10点停止所有测试环境的实例"

AI助手将:
1. 调用`list_instances`过滤出测试环境实例
2. 对每个实例调用`stop_instance`
3. 确认操作完成

## Terraform集成

### 安装Terraform Provider

```bash
# 在terraform配置中声明provider
```

### Terraform配置示例

#### 主配置文件 (main.tf)

```hcl
terraform {
  required_providers {
    jdcloud = {
      source  = "jdcloud/jdcloud"
      version = "~> 1.0"
    }
  }
}

provider "jdcloud" {
  access_key = var.jdcloud_access_key
  secret_key = var.jdcloud_secret_key
  region     = var.jdcloud_region
}

variable "jdcloud_access_key" {
  type      = string
  sensitive = true
}

variable "jdcloud_secret_key" {
  type      = string
  sensitive = true
}

variable "jdcloud_region" {
  type    = string
  default = "cn-north-1"
}
```

#### 创建VM实例 (vm.tf)

```hcl
resource "jdcloud_vm_instance" "web_server" {
  count         = 3
  region_id     = "cn-north-1"
  az            = "cn-north-1a"
  instance_type = "g.n2.medium"
  image_id      = "img-xxxxx"
  name          = "web-server-${count.index + 1}"
  
  primary_network_interface {
    subnet_id          = jdcloud_vpc_subnet.main.id
    security_group_ids = [jdcloud_vpc_security_group.web.id]
  }
  
  system_disk {
    disk_category = "local"
    disk_size_gb  = 40
  }
  
  data_disks {
    disk_category = "cloud_ssd"
    disk_size_gb  = 100
    device_name   = "/dev/vdb"
  }
  
  key_name = jdcloud_vm_keypair.main.name
  
  charge_mode = "postpaid_by_duration"
  
  tags = {
    Environment = "production"
    Application = "web"
    ManagedBy   = "terraform"
  }
}

output "instance_ids" {
  value = jdcloud_vm_instance.web_server[*].id
}

output "private_ips" {
  value = jdcloud_vm_instance.web_server[*].primary_network_interface[0].private_ip_address
}
```

#### 网络配置 (network.tf)

```hcl
resource "jdcloud_vpc" "main" {
  region_id = "cn-north-1"
  vpc_name  = "production-vpc"
  cidr_block = "192.168.0.0/16"
}

resource "jdcloud_vpc_subnet" "main" {
  region_id  = "cn-north-1"
  vpc_id     = jdcloud_vpc.main.id
  subnet_name = "production-subnet"
  cidr_block = "192.168.1.0/24"
  az         = "cn-north-1a"
}

resource "jdcloud_vpc_security_group" "web" {
  region_id           = "cn-north-1"
  vpc_id              = jdcloud_vpc.main.id
  security_group_name = "web-sg"
  description         = "Security group for web servers"
}

resource "jdcloud_vpc_security_group_rule" "ssh" {
  region_id        = "cn-north-1"
  security_group_id = jdcloud_vpc_security_group.web.id
  direction        = "ingress"
  protocol         = "tcp"
  from_port        = 22
  to_port          = 22
  address_prefix   = "0.0.0.0/0"
  description      = "Allow SSH"
}

resource "jdcloud_vpc_security_group_rule" "http" {
  region_id        = "cn-north-1"
  security_group_id = jdcloud_vpc_security_group.web.id
  direction        = "ingress"
  protocol         = "tcp"
  from_port        = 80
  to_port          = 80
  address_prefix   = "0.0.0.0/0"
  description      = "Allow HTTP"
}

resource "jdcloud_vpc_security_group_rule" "https" {
  region_id        = "cn-north-1"
  security_group_id = jdcloud_vpc_security_group.web.id
  direction        = "ingress"
  protocol         = "tcp"
  from_port        = 443
  to_port          = 443
  address_prefix   = "0.0.0.0/0"
  description      = "Allow HTTPS"
}
```

#### 弹性公网IP (eip.tf)

```hcl
resource "jdcloud_vpc_elastic_ip" "web" {
  count          = 3
  region_id      = "cn-north-1"
  bandwidth_mbps = 10
  charge_mode    = "postpaid_by_duration"
}

resource "jdcloud_vpc_elastic_ip_association" "web" {
  count         = 3
  region_id     = "cn-north-1"
  elastic_ip_id = jdcloud_vpc_elastic_ip.web[count.index].id
  instance_id   = jdcloud_vm_instance.web_server[count.index].id
}
```

#### 云硬盘 (disk.tf)

```hcl
resource "jdcloud_disk" "data" {
  count       = 3
  region_id   = "cn-north-1"
  az          = "cn-north-1a"
  disk_type   = "ssd"
  disk_size_gb = 100
  disk_name   = "data-disk-${count.index + 1}"
  
  charge_mode = "postpaid_by_duration"
}

resource "jdcloud_disk_attachment" "data" {
  count      = 3
  region_id  = "cn-north-1"
  disk_id    = jdcloud_disk.data[count.index].id
  instance_id = jdcloud_vm_instance.web_server[count.index].id
  device_name = "/dev/vdb"
}
```

#### 快照策略 (snapshot.tf)

```hcl
resource "jdcloud_disk_snapshot_policy" "daily_backup" {
  region_id      = "cn-north-1"
  policy_name    = "daily-backup"
  enable         = true
  cron_expression = "0 2 * * *"  # 每天凌晨2点
  
  retention_days = 7
  
  disk_ids = jdcloud_disk.data[*].id
}
```

### 使用Terraform

```bash
# 初始化
terraform init

# 预览变更
terraform plan

# 应用变更
terraform apply

# 查看输出
terraform output

# 销毁资源
terraform destroy
```

## Ansible集成

### 安装JD Cloud Collection

```bash
ansible-galaxy collection install jdcloud.cloud
```

### Playbook示例

#### 创建VM实例

```yaml
---
- name: Create VM instances
  hosts: localhost
  gather_facts: no
  
  vars:
    jdcloud_access_key: "{{ lookup('env', 'JDC_ACCESS_KEY') }}"
    jdcloud_secret_key: "{{ lookup('env', 'JDC_SECRET_KEY') }}"
    jdcloud_region: "cn-north-1"
  
  tasks:
    - name: Create web server instances
      jdcloud.cloud.vm_instance:
        access_key: "{{ jdcloud_access_key }}"
        secret_key: "{{ jdcloud_secret_key }}"
        region_id: "{{ jdcloud_region }}"
        az: "cn-north-1a"
        instance_type: "g.n2.medium"
        image_id: "img-xxxxx"
        name: "web-server-{{ item }}"
        subnet_id: "subnet-xxxxx"
        security_group_ids:
          - "sg-xxxxx"
        key_name: "my-keypair"
        system_disk:
          disk_category: "local"
          disk_size_gb: 40
        data_disks:
          - disk_category: "cloud_ssd"
            disk_size_gb: 100
            device_name: "/dev/vdb"
        charge_mode: "postpaid_by_duration"
        state: present
      loop: "{{ range(1, 4) | list }}"
      register: instances
      
    - name: Display instance IDs
      debug:
        msg: "Created instances: {{ instances.results | map(attribute='instance_id') | list }}"
```

#### 配置实例

```yaml
---
- name: Configure VM instances
  hosts: all
  become: yes
  
  tasks:
    - name: Install nginx
      yum:
        name: nginx
        state: present
      
    - name: Start nginx service
      systemd:
        name: nginx
        state: started
        enabled: yes
      
    - name: Configure firewall
      firewalld:
        service: http
        permanent: yes
        state: enabled
      
    - name: Reload firewall
      firewalld:
        state: reloaded
```

## CI/CD集成

### GitHub Actions示例

```yaml
name: Deploy VM Infrastructure

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0
      
      - name: Terraform Init
        run: terraform init
        env:
          TF_VAR_jdcloud_access_key: ${{ secrets.JDC_ACCESS_KEY }}
          TF_VAR_jdcloud_secret_key: ${{ secrets.JDC_SECRET_KEY }}
      
      - name: Terraform Plan
        run: terraform plan -out=tfplan
        env:
          TF_VAR_jdcloud_access_key: ${{ secrets.JDC_ACCESS_KEY }}
          TF_VAR_jdcloud_secret_key: ${{ secrets.JDC_SECRET_KEY }}
      
      - name: Terraform Apply
        run: terraform apply tfplan
        env:
          TF_VAR_jdcloud_access_key: ${{ secrets.JDC_ACCESS_KEY }}
          TF_VAR_jdcloud_secret_key: ${{ secrets.JDC_SECRET_KEY }}
      
      - name: Verify Deployment
        run: |
          pip install jdcloud-cli
          export JDC_ACCESS_KEY=${{ secrets.JDC_ACCESS_KEY }}
          export JDC_SECRET_KEY=${{ secrets.JDC_SECRET_KEY }}
          
          # Check instance status
          jdc vm describe-instances \
            --region-id cn-north-1 \
            --filters '[{"name":"status","values":["running"]}]'
```

### Jenkins Pipeline示例

```groovy
pipeline {
    agent any
    
    environment {
        JDC_ACCESS_KEY = credentials('jdc-access-key')
        JDC_SECRET_KEY = credentials('jdc-secret-key')
    }
    
    stages {
        stage('Deploy Infrastructure') {
            steps {
                script {
                    sh '''
                        terraform init
                        terraform plan -out=tfplan
                        terraform apply tfplan
                    '''
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    sh '''
                        pip install jdcloud-cli
                        export JDC_ACCESS_KEY=$JDC_ACCESS_KEY
                        export JDC_SECRET_KEY=$JDC_SECRET_KEY
                        
                        jdc vm describe-instances \
                            --region-id cn-north-1 \
                            --page-number 1 \
                            --page-size 10
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed!'
        }
    }
}
```

## IAM角色和权限

### 最小权限原则

为不同的应用场景创建专用的IAM用户和角色，仅授予必要的权限。

### 常用权限策略

#### 只读权限

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vm:Describe*",
        "disk:Describe*",
        "monitor:Describe*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 运维权限

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vm:Describe*",
        "vm:Start*",
        "vm:Stop*",
        "vm:Reboot*",
        "disk:Describe*",
        "disk:CreateSnapshot",
        "disk:DeleteSnapshot",
        "monitor:Describe*",
        "monitor:CreateAlarm",
        "monitor:UpdateAlarm",
        "monitor:DeleteAlarm"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 管理员权限

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vm:*",
        "disk:*",
        "vpc:*",
        "monitor:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 使用STS临时凭证

对于短期任务，建议使用STS临时凭证而非长期Access Key：

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.sts.client import StsClient
from jdcloud_sdk.services.sts.apis.AssumeRoleRequest import AssumeRoleRequest

# 创建STS客户端
sts_client = StsClient(credential, 'cn-north-1')

# 请求临时凭证
request = AssumeRoleRequest({
    "roleArn": "acs:ram::123456789:role/OpsRole",
    "roleSessionName": "ops-session",
    "durationSeconds": 3600
})

response = sts_client.assumeRole(request)

if response.error is None:
    # 使用临时凭证
    temp_credential = Credential(
        response.result.credentials.accessKeyId,
        response.result.credentials.accessKeySecret,
        response.result.credentials.securityToken
    )
    
    vm_client = VmClient(temp_credential, 'cn-north-1')
else:
    print(f"Error: {response.error.message}")
```

## 最佳实践

### 1. 凭证管理

- ✅ 使用环境变量存储凭证
- ✅ 使用密钥管理服务（如AWS Secrets Manager、HashiCorp Vault）
- ✅ 定期轮换Access Key
- ❌ 不要在代码中硬编码凭证
- ❌ 不要将凭证提交到版本控制系统

### 2. 错误处理

- 实现重试机制处理临时错误
- 记录详细的错误日志
- 为用户提供清晰的错误信息
- 区分客户端错误和服务端错误

### 3. 资源标签

- 为所有资源添加标签便于管理
- 使用统一的标签规范
- 标签示例：Environment, Application, Owner, CostCenter

### 4. 幂等性

- 确保脚本和自动化流程具有幂等性
- 多次执行不会产生副作用
- 先检查资源是否存在再创建

### 5. 版本控制

- 对Infrastructure as Code文件进行版本控制
- 使用语义化版本号
- 在变更前进行代码审查

### 6. 测试

- 在测试环境验证自动化脚本
- 使用dry-run模式预览变更
- 编写单元测试和集成测试

## 相关资源

- [JD Cloud SDK文档](https://docs.jdcloud.com/cn/sdk/)
- [JD Cloud API文档](https://docs.jdcloud.com/cn/api/)
- [Terraform Provider文档](https://registry.terraform.io/providers/jdcloud/jdcloud/latest/docs)
- [Ansible Collection文档](https://galaxy.ansible.com/jdcloud/cloud)