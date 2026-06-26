# Cloud Monitor Execution Flow

> This document is extracted from `SKILL.md` and contains detailed execution flows for core Cloud Monitor operations.
> Each operation follows: **Pre-flight Check → Execute (jdc primary path / SDK fallback) → Post-execution Validation → Failure Recovery**.

## jdc-first Strategy

Agent **must** prefer the `jdc` CLI (primary path). If `jdc` fails after exponential backoff (**3 retries**: 0s → 2s → 4s), fall back to SDK/API.

---

## Operation: Create Alarm Rule

### Pre-flight Check

| Check Item | Method | Expected | Failure Handling |
|-----------|--------|----------|-----------------|
| CLI installed | `jdc --version` | exit code 0 | Retry up to 3 times, then fall back to SDK |
| SDK installed | `python -c "import jdcloud_sdk"` | No error | Guide installation (fallback path) |
| Credentials valid | `jdc --output json monitor describe-services --region-id cn-north-1` | `$.error == null` | Prompt to configure CLI credentials (`~/.jdc/config`) or SDK environment variables |
| Region available | SDK/CLI call describeServices | Service list returned non-empty | Suggest nearest available region |

### Execution — CLI (`jdc`) [Primary Path]

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

### Execution — SDK (Fallback Path — after 3 jdc failures)

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
# JSON path: $.result.alarmId
alarm_id = response.result.alarmId
```

### Post-execution Validation

1. Capture `{{output.alarm_id}}` from CLI JSON `$.result.alarmId` or SDK `response.result.alarmId`
2. Verify alarm was created (CLI preferred):
   ```bash
   # CLI verification (primary path)
   jdc --output json monitor describe-alarm \
     --region-id {{user.region}} \
     --alarm-id {{output.alarm_id}} | jq -r '.result.alarm.status'
   ```
   ```python
   # SDK verification (fallback path)
   from jdcloud_sdk.services.monitor.apis.DescribeAlarmRequest import DescribeAlarmRequest
   req = DescribeAlarmRequest({"regionId": "{{user.region}}", "alarmId": "{{output.alarm_id}}"})
   resp = client.describeAlarm(req)
   status = resp.result.alarm.status  # ALARM/OK/INSUFFICIENT_DATA
   ```
3. If valid status returned → operation success, report `{{output.alarm_id}}` to user
4. If error returned → capture error info, enter failure recovery

### Failure Recovery

| Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|----------------------|------------|---------|-------------|
| `InvalidParameter` | 1 | - | Check parameter format, correct and retry |
| `QuotaExceeded` | 0 | - | Stop. Inform user alarm rule quota is full (max 500 per region) |
| `MetricNotFound` | 1 | - | Confirm metric name, query available metrics with `describe-metrics`, then retry |
| `ResourceAlreadyExists` | 0 | - | Alarm name already exists, ask user whether to reuse or rename |
| `InternalError` | 3 | 2s, 4s, 8s | Exponential backoff retry. Report user after 3rd failure |

---

## Operation: Query Monitoring Data

### Execution — CLI (`jdc`) [Primary Path]

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

### Execution — SDK (Fallback Path — after 3 jdc failures)

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
# JSON path: $.result.metricDatas[*].value
for data in response.result.metricDatas:
    print(f"Time: {data.timestamp}, Value: {data.value}, Unit: {data.unit}")
```

### Post-execution Validation

1. Check SDK `response.result.metricDatas` or CLI JSON `$.result.metricDatas` is not empty
2. If empty → possible causes: resource just created no data yet, time range error, metric name error
3. Display in table format: Timestamp | Value | Unit

### Failure Recovery

| Error Pattern (regex) | Max Retries | Backoff | Agent Action |
|----------------------|------------|---------|-------------|
| `RateLimitExceeded` | 3 | 2s, 4s, 8s | Retry with reduced frequency |
| `ResourceNotFound` | 0 | - | Stop. Inform user resource ID does not exist |
| `MetricNotFound` | 1 | - | Confirm metric name with `describe-metrics`, then retry |

---

## Operation: Delete Alarm Rule

### Pre-flight Check (Safety Gate)

- **Must** ask user: "Confirm delete alarm rule `{{user.alarm_name}}` ({{user.alarm_id}})? This operation is irreversible."
- **Must** wait for explicit user confirmation ("confirm" or "yes") before proceeding (required for both SDK and CLI paths)

### Execution — CLI (`jdc`) [Primary Path]

```bash
jdc --output json monitor delete-alarms \
  --region-id {{env.JDC_REGION}} \
  --alarm-ids '["{{user.alarm_id}}"]'
```

### Execution — SDK (Fallback Path — after 3 jdc failures)

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
# Returns requestId on success
print(f"Delete request accepted: {response.requestId}")
```

### Post-execution Validation

1. Query again to confirm it no longer exists (CLI preferred):
   ```bash
   # CLI verification (primary path)
   jdc --output json monitor describe-alarm \
     --region-id {{env.JDC_REGION}} \
     --alarm-id {{user.alarm_id}} 2>&1
   ```
   ```python
   # SDK verification (fallback path)
   from jdcloud_sdk.services.monitor.apis.DescribeAlarmRequest import DescribeAlarmRequest
   req = DescribeAlarmRequest({"regionId": "{{env.JDC_REGION}}", "alarmId": "{{user.alarm_id}}"})
   try:
       client.describeAlarm(req)
   except Exception as e:
       if "AlarmNotFound" in str(e) or "ResourceNotFound" in str(e):
           print("Alarm deleted successfully")
   ```
2. Expected to return `AlarmNotFound` error → deletion successful