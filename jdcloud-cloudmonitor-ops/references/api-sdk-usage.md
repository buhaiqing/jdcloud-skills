# API & SDK — 云监控(CloudMonitor)

## OpenAPI 规格

- **API 文档**: https://docs.jdcloud.com/cn/monitoring/api/overview
- **服务标识**: `monitor`
- **基础路径**: `monitor.jdcloud-api.com`
- **API 版本**: v1

## SDK 操作映射

| 目标 | API operationId | SDK 方法 (Python) |
|------|-----------------|-------------------|
| 查询服务列表 | `describeServices` | `client.describeServices(request)` |
| 查询监控项 | `describeMetrics` | `client.describeMetrics(request)` |
| 查询监控数据 | `describeMetricData` | `client.describeMetricData(request)` |
| 查询最新数据 | `lastDownsample` | `client.lastDownsample(request)` |
| 创建告警规则 | `createAlarm` | `client.createAlarm(request)` |
| 查询告警列表 | `describeAlarms` | `client.describeAlarms(request)` |
| 查询告警详情 | `describeAlarm` | `client.describeAlarm(request)` |
| 修改告警规则 | `updateAlarm` | `client.updateAlarm(request)` |
| 启用/禁用告警 | `enableAlarm` | `client.enableAlarm(request)` |
| 删除告警规则 | `deleteAlarms` | `client.deleteAlarms(request)` |
| 查询告警历史 | `describeAlarmHistory` | `client.describeAlarmHistory(request)` |
| 查询告警联系人 | `describeAlarmContacts` | `client.describeAlarmContacts(request)` |
| 上报自定义数据 | `putMetricData` | `client.putMetricData(request)` |
| 查询自定义数据 | `describeCustomMetricData` | `client.describeCustomMetricData(request)` |

## Python SDK 使用

### 安装

```bash
pip install jdcloud_sdk
```

### 初始化客户端

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

### 查询监控服务列表

```python
from jdcloud_sdk.services.monitor.apis.DescribeServicesRequest import DescribeServicesRequest

request = DescribeServicesRequest({
    "regionId": "cn-north-1"
})

response = client.describeServices(request)
# JSON 路径: $.result.services[*].serviceCode
for service in response.result.services:
    print(f"Service: {service.serviceCode} - {service.serviceName}")
```

### 查询监控数据

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
# JSON 路径: $.result.metricDatas[*].value
for data in response.result.metricDatas:
    print(f"Time: {data.timestamp}, Value: {data.value}, Unit: {data.unit}")
```

### 创建告警规则

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
# JSON 路径: $.result.alarmId
alarm_id = response.result.alarmId
print(f"Alarm created: {alarm_id}")
```

### 查询告警规则列表

```python
from jdcloud_sdk.services.monitor.apis.DescribeAlarmsRequest import DescribeAlarmsRequest

request = DescribeAlarmsRequest({
    "regionId": "cn-north-1",
    "serviceCode": "vm",
    "pageNumber": 1,
    "pageSize": 20
})

response = client.describeAlarms(request)
# JSON 路径: $.result.alarms[*].alarmId
for alarm in response.result.alarms:
    print(f"Alarm: {alarm.alarmName}, Status: {alarm.status}, ID: {alarm.alarmId}")
```

### 删除告警规则

```python
from jdcloud_sdk.services.monitor.apis.DeleteAlarmsRequest import DeleteAlarmsRequest

request = DeleteAlarmsRequest({
    "regionId": "cn-north-1",
    "alarmIds": ["alarm-xxx"]
})

response = client.deleteAlarms(request)
# 返回 requestId 表示成功
print(f"Delete request ID: {response.requestId}")
```

### 上报自定义监控数据

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

## 请求/响应字段说明

### 创建告警规则 (createAlarm)

**请求必填字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| regionId | string | 区域 ID |
| alarmName | string | 告警规则名称 |
| serviceCode | string | 服务代码 |
| resourceId | string | 资源 ID |
| metricName | string | 监控项名称 |
| comparisonOperator | string | 比较运算符 (gt/lt/ge/le/eq/ne) |
| threshold | number | 阈值 |
| period | integer | 统计周期（秒） |
| evaluationPeriods | integer | 连续周期数 |

**响应字段**:
| 字段 | JSON 路径 | 类型 | 说明 |
|------|-----------|------|------|
| alarmId | `$.result.alarmId` | string | 告警规则 ID |

### 查询监控数据 (describeMetricData)

**请求必填字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| regionId | string | 区域 ID |
| metric | string | 监控项名称 |
| serviceCode | string | 服务代码 |
| resourceId | string | 资源 ID |
| startTime | string | 开始时间 (ISO8601) |
| endTime | string | 结束时间 (ISO8601) |

**响应字段**:
| 字段 | JSON 路径 | 类型 | 说明 |
|------|-----------|------|------|
| metricDatas | `$.result.metricDatas` | array | 监控数据数组 |
| timestamp | `$.result.metricDatas[*].timestamp` | string | 时间戳 |
| value | `$.result.metricDatas[*].value` | number | 监控值 |
| unit | `$.result.metricDatas[*].unit` | string | 单位 |

### 查询告警列表 (describeAlarms)

**响应字段**:
| 字段 | JSON 路径 | 类型 | 说明 |
|------|-----------|------|------|
| alarms | `$.result.alarms` | array | 告警规则数组 |
| alarmId | `$.result.alarms[*].alarmId` | string | 告警 ID |
| alarmName | `$.result.alarms[*].alarmName` | string | 告警名称 |
| status | `$.result.alarms[*].status` | string | 状态 (ALARM/OK/INSUFFICIENT_DATA) |

## 分页处理

云监控 API 使用标准分页参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| pageNumber | integer | 页码，默认 1 |
| pageSize | integer | 每页数量，默认 20，最大 100 |

```python
# 分页查询示例
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

## 错误处理

```python
from jdcloud_sdk.core.exception import ClientException
from jdcloud_sdk.core.exception import ServerException

try:
    response = client.describeMetricData(request)
except ClientException as e:
    # 客户端错误（参数问题等）
    print(f"Client error: {e.error_msg}")
    if "InvalidParameter" in e.error_msg:
        # 检查参数格式
        pass
except ServerException as e:
    # 服务端错误
    print(f"Server error: {e.error_msg}")
    if "InternalError" in e.error_msg:
        # 可重试
        pass
```

## 常见错误码

| 错误码 | HTTP 状态 | 说明 | Agent 动作 |
|--------|-----------|------|-----------|
| `InvalidParameter` | 400 | 参数无效 | 检查参数格式，修正后重试（最多1次） |
| `MetricNotFound` | 404 | 监控项不存在 | 用 describeMetrics 确认名称后重试 |
| `ResourceNotFound` | 404 | 资源不存在 | HALT，告知用户资源 ID 错误 |
| `AlarmNotFound` | 404 | 告警规则不存在 | HALT，告知用户告警 ID 错误 |
| `QuotaExceeded` | 403 | 配额超限 | HALT，告知用户配额已满（每区域最多500条） |
| `RateLimitExceeded` | 429 | 请求频率超限 | 指数退避重试（最多3次） |
| `InternalError` | 500 | 内部错误 | 指数退避重试（最多3次） |

## SDK 与 CLI 对比

| 操作 | SDK 支持 | CLI 支持 | 推荐 |
|------|---------|---------|------|
| 查询服务列表 | ✓ | ✓ | CLI（快速查询） |
| 查询监控数据 | ✓ | ✓ | SDK（批量/复杂查询） |
| 创建告警规则 | ✓ | ✓ | SDK（集成/自动化） |
| 删除告警规则 | ✓ | ✓ | CLI（快速操作） |
| 上报自定义数据 | ✓ | ✓ | SDK（程序上报） |

**路径偏好**:
- **无 Python 运行时** → 使用 `jdc` CLI
- **批量操作/集成测试** → 使用 SDK
- **快速一次性查询** → 使用 CLI