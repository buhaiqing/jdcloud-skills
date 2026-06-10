# 云监控执行流程

> 本文档从 `SKILL.md` 提取，包含云监控核心操作的详细执行流程。
> 每个操作遵循：**前置检查 → 执行（jdc 主路径 / SDK 降级） → 后置验证 → 失败恢复**。

## jdc-first 策略

Agent **必须**优先尝试 `jdc` CLI（主路径）。若 `jdc` 失败后（指数退避 **3 次重试**：0s → 2s → 4s），降级到 SDK/API。

---

## 操作：创建告警规则

### 前置检查

| 检查项 | 方法 | 期望 | 失败处理 |
|--------|------|------|---------|
| CLI 已安装 | `jdc --version` | exit code 0 | 最多重试 3 次，然后降级到 SDK |
| SDK 已安装 | `python -c "import jdcloud_sdk"` | 无错误 | 引导安装（降级路径） |
| 凭证有效 | `jdc --output json monitor describe-services --region-id cn-north-1` | `$.error == null` | 提示配置 CLI 凭证（`~/.jdc/config`）或 SDK 环境变量 |
| 区域可用 | SDK/CLI 调用 describeServices | 返回服务列表非空 | 建议最近可用区域 |

### 执行 — CLI (`jdc`) [主路径]

```bash
jdc --output json monitor create-alarm \
  --region-id {{user.region}} \
  --alarm-name "{{user.alarm_name}}" \
  --service-code {{user.service_code}} \
  --resource-id {{user.resource_id}} \
  --metric-name {{user.metric_name}} \
  --comparison-operator {{user.comparison}} \
  --threshold {{user.threshold}} \
  --period {{user.period}} \
  --evaluation-periods {{user.eval_periods}} \
  --contact-group-id {{user.contact_group_id}} \
  --notice-type "{{user.notice_type}}"
```

### 执行 — SDK (降级路径 — 3 次 jdc 失败后)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.CreateAlarmRequest import CreateAlarmRequest

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = MonitorClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

request = CreateAlarmRequest({
    "regionId": "{{user.region}}",
    "alarmName": "{{user.alarm_name}}",
    "serviceCode": "{{user.service_code}}",
    "resourceId": "{{user.resource_id}}",
    "metricName": "{{user.metric_name}}",
    "comparisonOperator": "{{user.comparison}}",
    "threshold": {{user.threshold}},
    "period": {{user.period}},
    "evaluationPeriods": {{user.eval_periods}},
    "contactGroupId": {{user.contact_group_id}},
    "noticeType": "{{user.notice_type}}"
})

response = client.createAlarm(request)
# JSON 路径: $.result.alarmId
alarm_id = response.result.alarmId
```

### 后置验证

1. 从 CLI JSON `$.result.alarmId` 或 SDK `response.result.alarmId` 捕获 `{{output.alarm_id}}`
2. 验证告警已创建（CLI 优先）：
   ```bash
   # CLI 验证（主路径）
   jdc --output json monitor describe-alarm \
     --region-id {{user.region}} \
     --alarm-id {{output.alarm_id}} | jq -r '.result.alarm.status'
   ```
   ```python
   # SDK 验证（降级路径）
   from jdcloud_sdk.services.monitor.apis.DescribeAlarmRequest import DescribeAlarmRequest
   req = DescribeAlarmRequest({"regionId": "{{user.region}}", "alarmId": "{{output.alarm_id}}"})
   resp = client.describeAlarm(req)
   status = resp.result.alarm.status  # ALARM/OK/INSUFFICIENT_DATA
   ```
3. 若返回有效状态 → 操作成功，向用户报告 `{{output.alarm_id}}`
4. 若返回错误 → 捕获错误信息，进入失败恢复

### 失败恢复

| 错误模式 (regex) | 最大重试 | 退避策略 | Agent 动作 |
|-----------------|---------|---------|-----------|
| `InvalidParameter` | 1 | - | 检查参数格式，修正后重试 |
| `QuotaExceeded` | 0 | - | 停止。告知用户告警规则配额已满（每区域最多 500 条） |
| `MetricNotFound` | 1 | - | 确认监控项名称，用 `describe-metrics` 查询可用项后重试 |
| `ResourceAlreadyExists` | 0 | - | 告警名称已存在，询问用户是否复用或换名 |
| `InternalError` | 3 | 2s, 4s, 8s | 指数退避重试。第 3 次失败后报告用户 |

---

## 操作：查询监控数据

### 执行 — CLI (`jdc`) [主路径]

```bash
jdc --output json monitor describe-metric-data \
  --region-id {{user.region}} \
  --metric {{user.metric}} \
  --service-code {{user.service_code}} \
  --resource-id {{user.resource_id}} \
  --start-time "{{user.start_time}}" \
  --end-time "{{user.end_time}}" \
  --aggr-type avg
```

### 执行 — SDK (降级路径 — 3 次 jdc 失败后)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = MonitorClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

request = DescribeMetricDataRequest({
    "regionId": "{{user.region}}",
    "metric": "{{user.metric}}",
    "serviceCode": "{{user.service_code}}",
    "resourceId": "{{user.resource_id}}",
    "startTime": "{{user.start_time}}",
    "endTime": "{{user.end_time}}",
    "aggrType": "avg"
})

response = client.describeMetricData(request)
# JSON 路径: $.result.metricDatas[*].value
for data in response.result.metricDatas:
    print(f"Time: {data.timestamp}, Value: {data.value}, Unit: {data.unit}")
```

### 后置验证

1. 检查 SDK `response.result.metricDatas` 或 CLI JSON `$.result.metricDatas` 是否非空
2. 若为空 → 可能原因：资源刚创建无数据、时间范围错误、监控项名错误
3. 以表格形式展示：时间戳 | 数值 | 单位

### 失败恢复

| 错误模式 (regex) | 最大重试 | 退避策略 | Agent 动作 |
|-----------------|---------|---------|-----------|
| `RateLimitExceeded` | 3 | 2s, 4s, 8s | 降低频率重试 |
| `ResourceNotFound` | 0 | - | 停止。告知用户资源 ID 不存在 |
| `MetricNotFound` | 1 | - | 用 `describe-metrics` 确认名称后重试 |

---

## 操作：删除告警规则

### 前置检查（安全门）

- **必须**询问用户："确认删除告警规则 `{{user.alarm_name}}` ({{user.alarm_id}})？此操作不可撤销。"
- **必须**等待用户明确回复"确认"或"yes"后才继续（SDK 和 CLI 路径均需此安全门）

### 执行 — CLI (`jdc`) [主路径]

```bash
jdc --output json monitor delete-alarms \
  --region-id {{env.JDC_REGION}} \
  --alarm-ids '["{{user.alarm_id}}"]'
```

### 执行 — SDK (降级路径 — 3 次 jdc 失败后)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DeleteAlarmsRequest import DeleteAlarmsRequest

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = MonitorClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

request = DeleteAlarmsRequest({
    "regionId": "{{env.JDC_REGION}}",
    "alarmIds": ["{{user.alarm_id}}"]
})

response = client.deleteAlarms(request)
# 返回 requestId 表示成功
print(f"Delete request accepted: {response.requestId}")
```

### 后置验证

1. 再次查询确认不存在（CLI 优先）：
   ```bash
   # CLI 验证（主路径）
   jdc --output json monitor describe-alarm \
     --region-id {{env.JDC_REGION}} \
     --alarm-id {{user.alarm_id}} 2>&1
   ```
   ```python
   # SDK 验证（降级路径）
   from jdcloud_sdk.services.monitor.apis.DescribeAlarmRequest import DescribeAlarmRequest
   req = DescribeAlarmRequest({"regionId": "{{env.JDC_REGION}}", "alarmId": "{{user.alarm_id}}"})
   try:
       client.describeAlarm(req)
   except Exception as e:
       if "AlarmNotFound" in str(e) or "ResourceNotFound" in str(e):
           print("Alarm deleted successfully")
   ```
2. 期望返回 `AlarmNotFound` 错误 → 删除成功
