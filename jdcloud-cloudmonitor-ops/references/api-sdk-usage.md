# API & SDK — CloudMonitor

## OpenAPI Specification

- **API Docs**: https://docs.jdcloud.com/cn/monitoring/api/overview
- **Service Code**: `monitor`
- **Base Path**: `monitor.jdcloud-api.com`
- **API Version**: v1

## SDK Operation Mapping

| Target | API operationId | SDK Method (Python) |
|--------|-----------------|---------------------|
| Query service list | `describeServices` | `client.describeServices(request)` |
| Query metrics | `describeMetrics` | `client.describeMetrics(request)` |
| Query metric data | `describeMetricData` | `client.describeMetricData(request)` |
| Query latest data | `lastDownsample` | `client.lastDownsample(request)` |
| Create alarm rule | `createAlarm` | `client.createAlarm(request)` |
| Query alarm list | `describeAlarms` | `client.describeAlarms(request)` |
| Query alarm details | `describeAlarm` | `client.describeAlarm(request)` |
| Update alarm rule | `updateAlarm` | `client.updateAlarm(request)` |
| Enable/disable alarm | `enableAlarm` | `client.enableAlarm(request)` |
| Delete alarm rule | `deleteAlarms` | `client.deleteAlarms(request)` |
| Query alarm history | `describeAlarmHistory` | `client.describeAlarmHistory(request)` |
| Query alarm contacts | `describeAlarmContacts` | `client.describeAlarmContacts(request)` |
| Push custom metric data | `putMetricData` | `client.putMetricData(request)` |
| Query custom metric data | `describeCustomMetricData` | `client.describeCustomMetricData(request)` |

## Python SDK Usage

### Installation

```bash
pip install jdcloud_sdk
```

### Initialize Client

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.services.monitor.client import MonitorClient

# Use environment variables for credentials (recommended)
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# Create client
config = Config(timeout=30)
client = MonitorClient(config, credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

### Query Monitoring Services

```python
from jdcloud_sdk.services.monitor.apis.DescribeServicesRequest import DescribeServicesRequest

request = DescribeServicesRequest({
    "regionId": "cn-north-1"
})

response = client.describeServices(request)
# JSON path: $.result.services[*].serviceCode
for service in response.result.services:
    print(f"Service: {service.serviceCode} - {service.serviceName}")
```

### Query Metric Data

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
# JSON path: $.result.metricDatas[*].value
for data in response.result.metricDatas:
    print(f"Time: {data.timestamp}, Value: {data.value}, Unit: {data.unit}")
```

### Create Alarm Rule

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
# JSON path: $.result.alarmId
alarm_id = response.result.alarmId
print(f"Alarm created: {alarm_id}")
```

### Query Alarm Rules List

```python
from jdcloud_sdk.services.monitor.apis.DescribeAlarmsRequest import DescribeAlarmsRequest

request = DescribeAlarmsRequest({
    "regionId": "cn-north-1",
    "serviceCode": "vm",
    "pageNumber": 1,
    "pageSize": 20
})

response = client.describeAlarms(request)
# JSON path: $.result.alarms[*].alarmId
for alarm in response.result.alarms:
    print(f"Alarm: {alarm.alarmName}, Status: {alarm.status}, ID: {alarm.alarmId}")
```

### Delete Alarm Rule

```python
from jdcloud_sdk.services.monitor.apis.DeleteAlarmsRequest import DeleteAlarmsRequest

request = DeleteAlarmsRequest({
    "regionId": "cn-north-1",
    "alarmIds": ["alarm-xxx"]
})

response = client.deleteAlarms(request)
# Returning requestId indicates success
print(f"Delete request ID: {response.requestId}")
```

### Push Custom Metric Data

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

## Request/Response Field Description

### Create Alarm Rule (createAlarm)

**Required Request Fields**:
| Field | Type | Description |
|-------|------|-------------|
| regionId | string | Region ID |
| alarmName | string | Alarm rule name |
| serviceCode | string | Service code |
| resourceId | string | Resource ID |
| metricName | string | Metric name |
| comparisonOperator | string | Comparison operator (gt/lt/ge/le/eq/ne) |
| threshold | number | Threshold |
| period | integer | Statistics period (seconds) |
| evaluationPeriods | integer | Number of consecutive periods |

**Response Fields**:
| Field | JSON path | Type | Description |
|-------|-----------|------|-------------|
| alarmId | `$.result.alarmId` | string | Alarm rule ID |

### Query Metric Data (describeMetricData)

**Required Request Fields**:
| Field | Type | Description |
|-------|------|-------------|
| regionId | string | Region ID |
| metric | string | Metric name |
| serviceCode | string | Service code |
| resourceId | string | Resource ID |
| startTime | string | Start time (ISO8601) |
| endTime | string | End time (ISO8601) |

**Response Fields**:
| Field | JSON path | Type | Description |
|-------|-----------|------|-------------|
| metricDatas | `$.result.metricDatas` | array | Metric data array |
| timestamp | `$.result.metricDatas[*].timestamp` | string | Timestamp |
| value | `$.result.metricDatas[*].value` | number | Metric value |
| unit | `$.result.metricDatas[*].unit` | string | Unit |

### Query Alarm List (describeAlarms)

**Response Fields**:
| Field | JSON path | Type | Description |
|-------|-----------|------|-------------|
| alarms | `$.result.alarms` | array | Alarm rule array |
| alarmId | `$.result.alarms[*].alarmId` | string | Alarm ID |
| alarmName | `$.result.alarms[*].alarmName` | string | Alarm name |
| status | `$.result.alarms[*].status` | string | Status (ALARM/OK/INSUFFICIENT_DATA) |

## Pagination

CloudMonitor API uses standard pagination parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| pageNumber | integer | Page number, default 1 |
| pageSize | integer | Items per page, default 20, max 100 |

```python
# Pagination example
page_number = 1
while True:
    request = DescribeAlarmsRequest({
        "regionId": "cn-north-1",
        "pageNumber": page_number,
        "pageSize": 50
    })
    response = client.describeAlarms(request)
    
    for alarm in response.result.alarms:
        print(alarm.alarmId)
    
    if len(response.result.alarms) < 50:
        break
    page_number += 1
```

## Error Handling

```python
from jdcloud_sdk.core.exception import ClientException
from jdcloud_sdk.core.exception import ServerException

try:
    response = client.describeMetricData(request)
except ClientException as e:
    # Client error (parameter issues, etc.)
    print(f"Client error: {e.error_msg}")
    if "InvalidParameter" in e.error_msg:
        # Check parameter format
        pass
except ServerException as e:
    # Server error
    print(f"Server error: {e.error_msg}")
    if "InternalError" in e.error_msg:
        # Retryable
        pass
```

## Common Error Codes

| Error Code | HTTP Status | Description | Agent Action |
|------------|-------------|-------------|--------------|
| `InvalidParameter` | 400 | Invalid parameter | Check parameter format, fix and retry (max 1 time) |
| `MetricNotFound` | 404 | Metric not found | Confirm name via describeMetrics, then retry |
| `ResourceNotFound` | 404 | Resource not found | HALT, inform user resource ID is wrong |
| `AlarmNotFound` | 404 | Alarm rule not found | HALT, inform user alarm ID is wrong |
| `QuotaExceeded` | 403 | Quota exceeded | HALT, inform user quota is full (max 500 per region) |
| `RateLimitExceeded` | 429 | Request rate exceeded | Exponential backoff retry (max 3 times) |
| `InternalError` | 500 | Internal error | Exponential backoff retry (max 3 times) |

## SDK vs CLI Comparison

| Operation | SDK Support | CLI Support | Recommendation |
|-----------|-------------|-------------|----------------|
| Query service list | ✓ | ✓ | CLI (quick query) |
| Query metric data | ✓ | ✓ | SDK (batch/complex queries) |
| Create alarm rule | ✓ | ✓ | SDK (automation/integration) |
| Delete alarm rule | ✓ | ✓ | CLI (quick operations) |
| Push custom metric data | ✓ | ✓ | SDK (programmatic push) |

**Path Preference**:
- **No Python runtime** → Use `jdc` CLI
- **Batch operations / integration testing** → Use SDK
- **Quick one-off queries** → Use CLI