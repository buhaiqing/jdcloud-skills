# Cloud Monitor Integration Guide

> **⚠️ Security Warning:** **Never** print `JDC_SECRET_KEY` value in logs, console output, or debug information. When verifying credentials, only check existence. If status logging is needed, use a sanitized placeholder (e.g. `JDC_SECRET_KEY=<masked>`).

## SDK Version Locking

> **Recommended**: Use locked SDK versions to ensure reproducible environments. See [SDK Version Locking Guide](../../docs/SDK_VERSION_LOCKING.md).

### Recommended Versions

| Package | Version | Notes |
|---------|---------|-------|
| jdcloud_cli | 1.2.12 | Cloud Monitor CLI (supports full Monitor subcommands) |
| jdcloud_sdk | >=1.6.26 | SDK Fallback |

### Install Locked Versions

```bash
# Using uv (recommended)
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk>=1.6.26

# Or using pip
pip install jdcloud_cli==1.2.12 jdcloud_sdk>=1.6.26
```

### Verify Versions

```bash
jdc --version
python -c "import jdcloud_sdk; print(f'SDK version: {jdcloud_sdk.__version__}')"
```

### Version Compatibility

| SDK Version | CLI Version | Python | Monitor API | Status |
|-------------|-------------|--------|-------------|--------|
| >=1.6.26 | 1.2.12 | 3.10+ | Monitor API v1.0 | ✅ Tested |

## SDK Integration

### Python SDK Integration

#### Install SDK

```bash
pip install jdcloud_sdk
```

#### SDK Initialization

**Environment Variable Configuration:**

| Variable | Required | Description | Default |
|----------|----------|-------------|--------|
| `JDC_ACCESS_KEY` | Yes | JD Cloud Access Key | — |
| `JDC_SECRET_KEY` | Yes | JD Cloud Secret Key | — |
| `JDC_REGION` | No | Default region | `cn-north-1` |

**Method 1: `.env` File (Local Development)**
```ini
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```

**Method 2: Shell Environment Variables (Production)**
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.services.monitor.client import MonitorClient

# Configure credentials using environment variables (recommended)
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# Create client
config = Config(timeout=30)
client = MonitorClient(config, credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

**Method 3: CLI Configuration**
```bash
jdc config init
```

> **Priority**: Shell env > `.env` > CLI config > Defaults. Never commit `.env` to version control.

#### List Monitoring Services

```python
from jdcloud_sdk.services.monitor.apis.DescribeServicesRequest import DescribeServicesRequest

request = DescribeServicesRequest({
    "regionId": "cn-north-1"
})

response = client.describeServices(request)
print(response.result)
```

#### Query Metric Data

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

#### Create Alarm Rule

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

#### Query Alarm Rules

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

#### Report Custom Metric Data

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

## OpenAPI Integration

### API Authentication

Cloud Monitor API uses JD Cloud unified authentication mechanism, requiring signature information in the request headers.

#### Signature Algorithm

```python
import hmac
import hashlib
import base64
from datetime import datetime

def sign_request(access_key, secret_key, method, uri, headers, query_params):
    """Generate request signature"""
    # 1. Build canonical request
    canonical_request = build_canonical_request(method, uri, headers, query_params)
    
    # 2. Build string to sign
    string_to_sign = build_string_to_sign(canonical_request)
    
    # 3. Calculate signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # 4. Base64 encode
    return base64.b64encode(signature).decode('utf-8')
```

#### Request Example

```bash
# Query metric data
curl -X GET \
  'https://open.jdcloud-api.com/v1/regions/cn-north-1/metrics/vm.cpu.util/data?serviceCode=vm&resourceId=i-xxx&startTime=2024-01-01T00:00:00Z&endTime=2024-01-01T23:59:59Z' \
  -H 'Content-Type: application/json' \
  -H 'x-jdcloud-date: 20240101T000000Z' \
  -H 'Authorization: JDCLOUD2-HMAC-SHA256 Credential=your_access_key/20240101/cn-north-1/monitor/jdcloud2_request, SignedHeaders=content-type;host;x-jdcloud-date, Signature=your_signature'
```

### API Endpoints

| Region | Endpoint |
|------|------|
| North China-Beijing (cn-north-1) | open.jdcloud-api.com |
| East China-Shanghai (cn-east-1) | open.jdcloud-api.com |
| South China-Guangzhou (cn-south-1) | open.jdcloud-api.com |

## Prometheus Integration

Cloud Monitor supports receiving metric data via the Prometheus Remote Write protocol.

### Configure Remote Write

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

### Use Remote Read

```yaml
# prometheus.yml
remote_read:
  - url: "https://prometheus.jdcloud-api.com/api/v1/read"
    remote_timeout: 30s
    headers:
      X-JDC-Access-Key: "your_access_key"
```

## Grafana Integration

### Configure Data Source

1. Install the JD Cloud Monitor data source plugin
2. Configure data source parameters:

| Parameter | Value |
|------|-----|
| Name | JD Cloud Monitor |
| Type | JD Cloud Monitor |
| Access Key | Your Access Key |
| Secret Key | Your Secret Key |
| Region | cn-north-1 |

### Import Dashboard

Cloud Monitor provides pre-built Grafana Dashboard templates, available from the following addresses:
- VM Dashboard: https://github.com/jdcloud/grafana-dashboards/vm.json
- RDS Dashboard: https://github.com/jdcloud/grafana-dashboards/rds.json
- Load Balancer Dashboard: https://github.com/jdcloud/grafana-dashboards/lb.json

## Webhook Integration

### Alarm Callback Configuration

Specify a callback URL when configuring alarm rules:

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

### Callback Message Format

#### Alarm Trigger Message

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
  "description": "CPU usage exceeds threshold"
}
```

#### Alarm Recovery Message

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
  "description": "CPU usage has returned to normal"
}
```

### Webhook Processing Example (Python)

```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # Verify signature (optional)
    if not verify_signature(request):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process alarm message
    if data['status'] == 'ALARM':
        handle_alarm(data)
    elif data['status'] == 'OK':
        handle_recovery(data)
    
    return jsonify({"message": "OK"})

def handle_alarm(data):
    """Handle alarm"""
    print(f"Alarm triggered: {data['alarmName']}")
    print(f"Resource: {data['resourceId']}")
    print(f"Current value: {data['metricValue']}")
    
    # Send notification to DingTalk/WeCom/Slack
    send_notification(data)

def handle_recovery(data):
    """Handle alarm recovery"""
    print(f"Alarm recovered: {data['alarmName']}")
    print(f"Resource: {data['resourceId']}")
    
    # Send recovery notification
    send_recovery_notification(data)

def verify_signature(request):
    """Verify request signature"""
    # Implement signature verification logic
    return True

def send_notification(data):
    """Send notification"""
    # Implement notification sending logic
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Other Integration Methods

| Integration Method | Reference |
|---------|---------|
| Java SDK | [integration-java.md](integration-java.md) |
| Terraform & CI/CD (GitHub Actions / Jenkins) | [integration-iac.md](integration-iac.md) |

## Best Practices

### 1. Credential Management

- Store credentials using environment variables or key management services
- Rotate Access Key regularly
- Use different credentials for different environments

### 2. Error Handling

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

### 3. Retry Strategy

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

### 4. Performance Optimization

- Use batch APIs to reduce request count
- Set reasonable query time ranges
- Use caching to avoid duplicate queries
- Control concurrent request count