# JD Cloud VM Integration Guide

## Overview

This document describes how to integrate JD Cloud VM services with other tools and platforms, including SDK development, MCP Server configuration, Terraform automation, and more.

## SDK Integration

### Python SDK

#### Installation

```bash
pip install jdcloud_sdk
```

#### Initialize Client

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.client import VmClient

# Use environment variables for credential management (recommended)
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# Create VM client
client = VmClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

#### Query Instances

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

#### Create Instance

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

#### Start / Stop Instance

```python
from jdcloud_sdk.services.vm.apis.StartInstanceRequest import StartInstanceRequest
from jdcloud_sdk.services.vm.apis.StopInstanceRequest import StopInstanceRequest

# Start instance
start_request = StartInstanceRequest({
    "regionId": "cn-north-1",
    "instanceId": "i-xxxxx"
})
start_response = client.startInstance(start_request)

# Stop instance
stop_request = StopInstanceRequest({
    "regionId": "cn-north-1",
    "instanceId": "i-xxxxx"
})
stop_response = client.stopInstance(stop_request)
```

#### Create Snapshot

```python
from jdcloud_sdk.services.disk.apis.CreateSnapshotRequest import CreateSnapshotRequest
from jdcloud_sdk.services.disk.client import DiskClient

# Create Disk client
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

#### Error Handling

```python
from jdcloud_sdk.core.exception import ClientException, ServerException

try:
    response = client.describeInstances(request)
    
    if response.error is not None:
        print(f"API Error: {response.error.code} - {response.error.message}")
        
except ClientException as e:
    print(f"Client error: {e.error_msg}")
    # Client error, usually parameter error or network issue
    
except ServerException as e:
    print(f"Server error: {e.error_code} - {e.error_msg}")
    # Server error, usually JD Cloud server-side issue
```

### Java SDK

#### Maven Dependencies

```xml
<dependency>
    <groupId>com.jdcloud.sdk</groupId>
    <artifactId>vm</artifactId>
    <version>1.0.0</version>
</dependency>
```

#### Initialize Client

```java
import com.jdcloud.sdk.auth.CredentialsProvider;
import com.jdcloud.sdk.auth.EnvironmentVariablesCredentialsProvider;
import com.jdcloud.sdk.http.HttpRequestConfig;
import com.jdcloud.sdk.service.vm.client.VmClient;

// Use environment variables to obtain credentials
CredentialsProvider credentialsProvider = new EnvironmentVariablesCredentialsProvider();

// Create VM client
VmClient client = VmClient.builder()
    .credentialsProvider(credentialsProvider)
    .httpRequestConfig(new HttpRequestConfig.Builder().build())
    .build();
```

#### Query Instances

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

## MCP Server Integration

### What is MCP Server

Model Context Protocol (MCP) Server is a standardized way for AI assistants to interact with external systems. Through MCP Server, AI can directly operate JD Cloud resources.

### Configure MCP Server

Add the JD Cloud VM Server to your MCP client configuration file:

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

> **Note**:
> - MCP Server is developed with Python 3.10+
> - Uses the `uvx` command to start
> - Environment variables should be set in shell configuration files or CI/CD systems
> - **Never** hardcode credentials in configuration files

### Available MCP Tools

Once configured, the AI assistant can use the following tools:

#### 1. Query Instance

```
Description: Query VM instance list or details
Parameters:
  - region_id: Region ID (required)
  - instance_ids: List of instance IDs (optional)
  - filters: Filter conditions (optional)
  
Example: Query all running instances
```

#### 2. Create Instance

```
Description: Create a new VM instance
Parameters:
  - region_id: Region ID (required)
  - az: Availability zone (required)
  - instance_type: Instance specification (required)
  - image_id: Image ID (required)
  - name: Instance name (required)
  - subnet_id: Subnet ID (required)
  - security_group_ids: Security group ID list (required)
  - key_name: Key pair name (optional)
  
Example: Create a general-purpose instance
```

#### 3. Start / Stop Instance

```
Description: Start or stop a VM instance
Parameters:
  - region_id: Region ID (required)
  - instance_id: Instance ID (required)
  - action: start or stop (required)
  
Example: Stop a specified instance
```

#### 4. Query Monitoring Data

```
Description: Query instance monitoring metric data
Parameters:
  - region_id: Region ID (required)
  - instance_id: Instance ID (required)
  - metric: Metric name (required)
  - start_time: Start time (optional)
  - end_time: End time (optional)
  
Example: Query CPU usage for the last 1 hour
```

#### 5. Create Snapshot

```
Description: Create a snapshot for a cloud disk
Parameters:
  - region_id: Region ID (required)
  - disk_id: Cloud disk ID (required)
  - snapshot_name: Snapshot name (required)
  
Example: Create a backup snapshot for the system disk
```

### Usage Example Scenarios

#### Scenario 1: Daily Inspection

User: "Check the status and resource usage of all VM instances in the production environment"

The AI assistant will:
1. Call `list_instances` to get all instances
2. Call `get_metrics` for each instance to get CPU and memory usage
3. Aggregate and display results

#### Scenario 2: Troubleshooting

User: "Instance i-xxxxx cannot connect, please help me diagnose"

The AI assistant will:
1. Call `describe_instance` to check instance status
2. Call `describe_security_group` to check security group rules
3. Call `describe_network_interface` to check network configuration
4. Provide diagnostic recommendations

#### Scenario 3: Batch Operations

User: "Stop all test environment instances at 10 PM"

The AI assistant will:
1. Call `list_instances` to filter test environment instances
2. Call `stop_instance` for each instance
3. Confirm the operation is complete

## Terraform Integration

### Install Terraform Provider

```bash
# Declare provider in terraform configuration
```

### Terraform Configuration Example

#### Main Configuration File (main.tf)

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

#### Create VM Instance (vm.tf)

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

#### Network Configuration (network.tf)

```hcl
resource "jdcloud_vpc" "main" {
  region_id  = "cn-north-1"
  vpc_name   = "production-vpc"
  cidr_block = "192.168.0.0/16"
}

resource "jdcloud_vpc_subnet" "main" {
  region_id   = "cn-north-1"
  vpc_id      = jdcloud_vpc.main.id
  subnet_name = "production-subnet"
  cidr_block  = "192.168.1.0/24"
  az          = "cn-north-1a"
}

resource "jdcloud_vpc_security_group" "web" {
  region_id           = "cn-north-1"
  vpc_id              = jdcloud_vpc.main.id
  security_group_name = "web-sg"
  description         = "Security group for web servers"
}

resource "jdcloud_vpc_security_group_rule" "ssh" {
  region_id         = "cn-north-1"
  security_group_id = jdcloud_vpc_security_group.web.id
  direction         = "ingress"
  protocol          = "tcp"
  from_port         = 22
  to_port           = 22
  address_prefix    = "0.0.0.0/0"
  description       = "Allow SSH"
}

resource "jdcloud_vpc_security_group_rule" "http" {
  region_id         = "cn-north-1"
  security_group_id = jdcloud_vpc_security_group.web.id
  direction         = "ingress"
  protocol          = "tcp"
  from_port         = 80
  to_port           = 80
  address_prefix    = "0.0.0.0/0"
  description       = "Allow HTTP"
}

resource "jdcloud_vpc_security_group_rule" "https" {
  region_id         = "cn-north-1"
  security_group_id = jdcloud_vpc_security_group.web.id
  direction         = "ingress"
  protocol          = "tcp"
  from_port         = 443
  to_port           = 443
  address_prefix    = "0.0.0.0/0"
  description       = "Allow HTTPS"
}
```

#### Elastic IP (eip.tf)

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

#### Cloud Disk (disk.tf)

```hcl
resource "jdcloud_disk" "data" {
  count        = 3
  region_id    = "cn-north-1"
  az           = "cn-north-1a"
  disk_type    = "ssd"
  disk_size_gb = 100
  disk_name    = "data-disk-${count.index + 1}"
  
  charge_mode = "postpaid_by_duration"
}

resource "jdcloud_disk_attachment" "data" {
  count       = 3
  region_id   = "cn-north-1"
  disk_id     = jdcloud_disk.data[count.index].id
  instance_id = jdcloud_vm_instance.web_server[count.index].id
  device_name = "/dev/vdb"
}
```

#### Snapshot Policy (snapshot.tf)

```hcl
resource "jdcloud_disk_snapshot_policy" "daily_backup" {
  region_id       = "cn-north-1"
  policy_name     = "daily-backup"
  enable          = true
  cron_expression = "0 2 * * *"  # Every day at 2 AM
  
  retention_days = 7
  
  disk_ids = jdcloud_disk.data[*].id
}
```

### Using Terraform

```bash
# Initialize
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply

# View output
terraform output

# Destroy resources
terraform destroy
```

## Ansible Integration

### Install JD Cloud Collection

```bash
ansible-galaxy collection install jdcloud.cloud
```

### Playbook Example

#### Create VM Instance

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

#### Configure Instance

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

## CI/CD Integration

### GitHub Actions Example

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

### Jenkins Pipeline Example

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

## IAM Roles and Permissions

### Principle of Least Privilege

Create dedicated IAM users and roles for different application scenarios, granting only the necessary permissions.

### Common Permission Policies

#### Read-Only Permissions

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

#### Operations Permissions

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

#### Admin Permissions

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

### Using STS Temporary Credentials

For short-term tasks, it is recommended to use STS temporary credentials instead of long-term Access Keys:

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.sts.client import StsClient
from jdcloud_sdk.services.sts.apis.AssumeRoleRequest import AssumeRoleRequest

# Create STS client
sts_client = StsClient(credential, 'cn-north-1')

# Request temporary credentials
request = AssumeRoleRequest({
    "roleArn": "acs:ram::123456789:role/OpsRole",
    "roleSessionName": "ops-session",
    "durationSeconds": 3600
})

response = sts_client.assumeRole(request)

if response.error is None:
    # Use temporary credentials
    temp_credential = Credential(
        response.result.credentials.accessKeyId,
        response.result.credentials.accessKeySecret,
        response.result.credentials.securityToken
    )
    
    vm_client = VmClient(temp_credential, 'cn-north-1')
else:
    print(f"Error: {response.error.message}")
```

## Best Practices

### 1. Credential Management

- ✅ Store credentials using environment variables
- ✅ Use key management services (e.g., AWS Secrets Manager, HashiCorp Vault)
- ✅ Rotate Access Keys regularly
- ❌ Do not hardcode credentials in code
- ❌ Do not commit credentials to version control

### 2. Error Handling

- Implement retry mechanisms to handle transient errors
- Log detailed error information
- Provide clear error messages to users
- Distinguish between client errors and server errors

### 3. Resource Tags

- Add tags to all resources for easier management
- Use a unified tag naming convention
- Examples: Environment, Application, Owner, CostCenter

### 4. Idempotency

- Ensure scripts and automation workflows are idempotent
- Multiple executions should not produce side effects
- Check if a resource exists before creating it

### 5. Version Control

- Version control Infrastructure as Code files
- Use semantic versioning
- Perform code reviews before changes

### 6. Testing

- Validate automation scripts in a test environment
- Use dry-run mode to preview changes
- Write unit tests and integration tests

## Related Resources

- [JD Cloud SDK Documentation](https://docs.jdcloud.com/cn/sdk/)
- [JD Cloud API Documentation](https://docs.jdcloud.com/cn/api/)
- [Terraform Provider Documentation](https://registry.terraform.io/providers/jdcloud/jdcloud/latest/docs)
- [Ansible Collection Documentation](https://galaxy.ansible.com/jdcloud/cloud)
