# 云监控集成指南

## MCP Server 配置

云监控 MCP Server 允许通过 MCP 协议与云监控服务交互。

### 配置示例

```json
{
  "mcpServers": {
    "jdcloud-monitor": {
      "command": "uvx",
      "args": [
        "run",
        "--python",
        "3.10",
        "@jdcloud/monitor-mcp"
      ],
      "env": {
        "JDC_ACCESS_KEY": "{{env.JDC_ACCESS_KEY}}",
        "JDC_SECRET_KEY": "{{env.JDC_SECRET_KEY}}",
        "JDC_REGION": "{{env.JDC_REGION}}"
      }
    }
  }
}
```

> **注意**：MCP servers 使用 Python 3.10+ 开发，通过 `uvx` 命令启动。环境变量必须在 Agent 运行时环境中设置。切勿在配置文件中硬编码凭证。`{{env.*}}` 占位符由 Agent harness 在运行时解析。

### 环境变量配置

Agent 运行时必须已配置以下环境变量：

```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

> Agent 不得向用户索取上述变量值。若未设置，引导用户通过 `jdc config init` 配置。

## SDK 集成

### Python SDK 集成

#### 安装 SDK

```bash
pip install jdcloud-sdk
```

#### SDK 初始化

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.services.monitor.client import MonitorClient

# 使用环境变量配置凭证（推荐）
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# 创建客户端
config = Config(timeout=30)
client = MonitorClient(config, credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

#### 查询监控服务列表

```python
from jdcloud_sdk.services.monitor.apis.DescribeServicesRequest import DescribeServicesRequest

request = DescribeServicesRequest({
    "regionId": "cn-north-1"
})

response = client.describeServices(request)
print(response.result)
```

#### 查询监控数据

```python
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest

request = DescribeMetricDataRequest({
    "regionId": "cn-north-1",
    "metric": "vm.cpu.util",
    "serviceCode": "vm",
    "resourceId": "i-xxx",
    "startTime": "2024-01-01T00:00:00Z",
    "endTime": "2024-01-01T23:59:59Z",
    "aggrType": "avg"
})

response = client.describeMetricData(request)
for data in response.result.metricDatas:
    print(f"Time: {data.timestamp}, Value: {data.value}")
```

#### 创建告警规则

```python
from jdcloud_sdk.services.monitor.apis.CreateAlarmRequest import CreateAlarmRequest

request = CreateAlarmRequest({
    "regionId": "cn-north-1",
    "alarmName": "HighCPUAlarm",
    "serviceCode": "vm",
    "resourceId": "i-xxx",
    "metricName": "vm.cpu.util",
    "comparisonOperator": "gt",
    "threshold": 80,
    "period": 300,
    "evaluationPeriods": 2,
    "contactGroupId": 1,
    "noticeType": "sms,email"
})

response = client.createAlarm(request)
print(f"Alarm created: {response.result.alarmId}")
```

#### 查询告警规则

```python
from jdcloud_sdk.services.monitor.apis.DescribeAlarmsRequest import DescribeAlarmsRequest

request = DescribeAlarmsRequest({
    "regionId": "cn-north-1",
    "serviceCode": "vm",
    "pageNumber": 1,
    "pageSize": 20
})

response = client.describeAlarms(request)
for alarm in response.result.alarms:
    print(f"Alarm: {alarm.alarmName}, Status: {alarm.status}")
```

#### 上报自定义监控数据

```python
from jdcloud_sdk.services.monitor.apis.PutMetricDataRequest import PutMetricDataRequest

request = PutMetricDataRequest({
    "regionId": "cn-north-1",
    "namespace": "custom-namespace",
    "metricName": "custom-metric",
    "value": 100,
    "dimensions": '{"instance":"app-01"}',
    "unit": "Count"
})

response = client.putMetricData(request)
print("Metric data uploaded successfully")
```

### Java SDK 集成

#### Maven 依赖

```xml
<dependency>
    <groupId>com.jdcloud.sdk</groupId>
    <artifactId>monitor</artifactId>
    <version>1.0.0</version>
</dependency>
```

#### SDK 初始化

```java
import com.jdcloud.sdk.JdcloudSdkException;
import com.jdcloud.sdk.client.CredentialProvider;
import com.jdcloud.sdk.client.JdcloudClient;
import com.jdcloud.sdk.service.monitor.client.MonitorClient;
import com.jdcloud.sdk.service.monitor.model.*;

public class MonitorExample {
    public static void main(String[] args) {
        // 配置凭证
        CredentialProvider credential = new CredentialProvider(
            System.getenv("JDC_ACCESS_KEY"),
            System.getenv("JDC_SECRET_KEY")
        );
        
        // 创建客户端
        MonitorClient client = MonitorClient.builder()
            .credentialsProvider(credential)
            .regionId("cn-north-1")
            .build();
    }
}
```

#### 查询监控数据

```java
DescribeMetricDataRequest request = new DescribeMetricDataRequest();
request.setRegionId("cn-north-1");
request.setMetric("vm.cpu.util");
request.setServiceCode("vm");
request.setResourceId("i-xxx");
request.setStartTime("2024-01-01T00:00:00Z");
request.setEndTime("2024-01-01T23:59:59Z");
request.setAggrType("avg");

DescribeMetricDataResponse response = client.describeMetricData(request);
for (MetricData data : response.getResult().getMetricDatas()) {
    System.out.println("Time: " + data.getTimestamp() + ", Value: " + data.getValue());
}
```

## OpenAPI 集成

### API 认证

云监控 API 使用京东云统一认证机制，需要在请求头中包含签名信息。

#### 签名算法

```python
import hmac
import hashlib
import base64
from datetime import datetime

def sign_request(access_key, secret_key, method, uri, headers, query_params):
    """生成请求签名"""
    # 1. 构建规范请求
    canonical_request = build_canonical_request(method, uri, headers, query_params)
    
    # 2. 构建待签名字符串
    string_to_sign = build_string_to_sign(canonical_request)
    
    # 3. 计算签名
    signature = hmac.new(
        secret_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # 4. Base64 编码
    return base64.b64encode(signature).decode('utf-8')
```

#### 请求示例

```bash
# 查询监控数据
curl -X GET \
  'https://open.jdcloud-api.com/v1/regions/cn-north-1/metrics/vm.cpu.util/data?serviceCode=vm&resourceId=i-xxx&startTime=2024-01-01T00:00:00Z&endTime=2024-01-01T23:59:59Z' \
  -H 'Content-Type: application/json' \
  -H 'x-jdcloud-date: 20240101T000000Z' \
  -H 'Authorization: JDCLOUD2-HMAC-SHA256 Credential=your_access_key/20240101/cn-north-1/monitor/jdcloud2_request, SignedHeaders=content-type;host;x-jdcloud-date, Signature=your_signature'
```

### API 端点

| 区域 | 端点 |
|------|------|
| 华北-北京(cn-north-1) | open.jdcloud-api.com |
| 华东-上海(cn-east-1) | open.jdcloud-api.com |
| 华南-广州(cn-south-1) | open.jdcloud-api.com |

## Prometheus 集成

云监控支持通过 Prometheus Remote Write 协议接收监控数据。

### 配置 Remote Write

```yaml
# prometheus.yml
remote_write:
  - url: "https://prometheus.jdcloud-api.com/api/v1/write"
    remote_timeout: 30s
    headers:
      X-JDC-Access-Key: "your_access_key"
    write_relabel_configs:
      - source_labels: [__name__]
        regex: 'custom_.*'
        action: keep
```

### 使用 Remote Read

```yaml
# prometheus.yml
remote_read:
  - url: "https://prometheus.jdcloud-api.com/api/v1/read"
    remote_timeout: 30s
    headers:
      X-JDC-Access-Key: "your_access_key"
```

## Grafana 集成

### 配置数据源

1. 安装京东云监控数据源插件
2. 配置数据源参数：

| 参数 | 值 |
|------|-----|
| Name | JD Cloud Monitor |
| Type | JD Cloud Monitor |
| Access Key | 您的 Access Key |
| Secret Key | 您的 Secret Key |
| Region | cn-north-1 |

### 导入 Dashboard

云监控提供预置的 Grafana Dashboard 模板，可从以下地址下载：
- 云主机 Dashboard: https://github.com/jdcloud/grafana-dashboards/vm.json
- RDS Dashboard: https://github.com/jdcloud/grafana-dashboards/rds.json
- 负载均衡 Dashboard: https://github.com/jdcloud/grafana-dashboards/lb.json

## Webhook 集成

### 告警回调配置

配置告警规则时指定回调 URL：

```bash
jdc monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "WebhookAlarm" \
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

#### 告警触发消息

```json
{
  "version": "1.0",
  "alarmId": "alarm-xxx",
  "alarmName": "HighCPUAlarm",
  "status": "ALARM",
  "level": "critical",
  "serviceCode": "vm",
  "resourceId": "i-xxx",
  "metricName": "vm.cpu.util",
  "metricValue": 95.2,
  "threshold": 90,
  "comparisonOperator": "gt",
  "triggerTime": "2024-01-01T12:00:00Z",
  "regionId": "cn-north-1",
  "duration": 600,
  "description": "CPU使用率超过阈值"
}
```

#### 告警恢复消息

```json
{
  "version": "1.0",
  "alarmId": "alarm-xxx",
  "alarmName": "HighCPUAlarm",
  "status": "OK",
  "level": "critical",
  "serviceCode": "vm",
  "resourceId": "i-xxx",
  "metricName": "vm.cpu.util",
  "metricValue": 45.2,
  "threshold": 90,
  "comparisonOperator": "gt",
  "triggerTime": "2024-01-01T12:30:00Z",
  "regionId": "cn-north-1",
  "duration": 0,
  "description": "CPU使用率已恢复正常"
}
```

### Webhook 处理示例 (Python)

```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # 验证签名（可选）
    if not verify_signature(request):
        return jsonify({"error": "Invalid signature"}), 401
    
    # 处理告警消息
    if data['status'] == 'ALARM':
        handle_alarm(data)
    elif data['status'] == 'OK':
        handle_recovery(data)
    
    return jsonify({"message": "OK"})

def handle_alarm(data):
    """处理告警"""
    print(f"告警触发: {data['alarmName']}")
    print(f"资源: {data['resourceId']}")
    print(f"当前值: {data['metricValue']}")
    
    # 发送通知到钉钉/企业微信/Slack
    send_notification(data)

def handle_recovery(data):
    """处理告警恢复"""
    print(f"告警恢复: {data['alarmName']}")
    print(f"资源: {data['resourceId']}")
    
    # 发送恢复通知
    send_recovery_notification(data)

def verify_signature(request):
    """验证请求签名"""
    # 实现签名验证逻辑
    return True

def send_notification(data):
    """发送通知"""
    # 实现通知发送逻辑
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Terraform 集成

### 配置 Provider

```hcl
provider "jdcloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = "cn-north-1"
}
```

### 创建告警规则

```hcl
resource "jdcloud_monitor_alarm" "high_cpu" {
  region_id           = "cn-north-1"
  alarm_name          = "HighCPUAlarm"
  service_code        = "vm"
  resource_id         = "i-xxx"
  metric_name         = "vm.cpu.util"
  comparison_operator = "gt"
  threshold           = 80
  period              = 300
  evaluation_periods  = 2
  contact_group_id    = 1
  notice_type         = "sms,email"
}
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Monitor Deployment

on:
  deployment:
    environments: [production]

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Setup JDCloud CLI
        run: |
          pip install jdcloud-cli
          jdc config init --access-key ${{ secrets.JDC_ACCESS_KEY }} --secret-key ${{ secrets.JDC_SECRET_KEY }} --region cn-north-1
      
      - name: Check Resource Status
        run: |
          jdc monitor last-downsample \
            --region-id cn-north-1 \
            --service-code vm \
            --resource-id ${{ secrets.VM_RESOURCE_ID }} \
            --metrics '["vm.cpu.util","vm.memory.util"]'
      
      - name: Create Temporary Alarm
        run: |
          jdc monitor create-alarm \
            --region-id cn-north-1 \
            --alarm-name "Deploy-Monitor-${{ github.run_id }}" \
            --service-code vm \
            --resource-id ${{ secrets.VM_RESOURCE_ID }} \
            --metric-name "vm.cpu.util" \
            --comparison-operator "gt" \
            --threshold 70 \
            --period 60 \
            --evaluation-periods 1 \
            --notice-type "callback" \
            --callback-url "${{ secrets.WEBHOOK_URL }}"
```

### Jenkins Pipeline 示例

```groovy
pipeline {
    agent any
    
    environment {
        JDC_ACCESS_KEY = credentials('jdc-access-key')
        JDC_SECRET_KEY = credentials('jdc-secret-key')
    }
    
    stages {
        stage('Monitor Check') {
            steps {
                script {
                    sh '''
                        pip install jdcloud-cli
                        export JDC_ACCESS_KEY=$JDC_ACCESS_KEY
                        export JDC_SECRET_KEY=$JDC_SECRET_KEY
                        
                        jdc monitor describe-metric-data \
                            --region-id cn-north-1 \
                            --metric vm.cpu.util \
                            --service-code vm \
                            --resource-id i-xxx \
                            --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
                            --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ)
                    '''
                }
            }
        }
    }
}
```

## 最佳实践

### 1. 凭证管理

- 使用环境变量或密钥管理服务存储凭证
- 定期轮换 Access Key
- 为不同环境使用不同的凭证

### 2. 错误处理

```python
from jdcloud_sdk.core.exception import ClientException
from jdcloud_sdk.core.exception import ServerException

try:
    response = client.describeMetricData(request)
except ClientException as e:
    print(f"Client error: {e.error_msg}")
except ServerException as e:
    print(f"Server error: {e.error_msg}")
```

### 3. 重试策略

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

@retry(max_attempts=3)
def get_metric_data(client, request):
    return client.describeMetricData(request)
```

### 4. 性能优化

- 使用批量 API 减少请求次数
- 合理设置查询时间范围
- 使用缓存避免重复查询
- 控制并发请求数量
