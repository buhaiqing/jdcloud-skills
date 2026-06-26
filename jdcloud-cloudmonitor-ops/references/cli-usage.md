# CLI — CloudMonitor (`jdc`)

## Quick Command Reference

### List Monitoring Services
```bash
jdc --output json monitor describe-services --region-id cn-north-1
```

### Query Metrics for a Specific Product
```bash
jdc --output json monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx
```

### Query Monitoring Data
```bash
jdc --output json monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```

### Query Latest Monitoring Data (Downsampled)
```bash
jdc --output json monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metrics '["vm.cpu.util","vm.memory.util"]'
```

### Create Alarm Rule
```bash
jdc --output json monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "HighCPUAlarm" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

### Query Alarm Rule List
```bash
jdc --output json monitor describe-alarms \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
```

### Enable/Disable Alarm Rule
```bash
# Enable alarm
jdc --output json monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled true

# Disable alarm
jdc --output json monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled false
```

### Query Alarm History
```bash
jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z"
```

### Report Custom Monitoring Data
```bash
jdc --output json monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --value 100 \
  --dimensions '{"instance":"app-server-01"}'
```

### Query Custom Monitoring Data
```bash
jdc --output json monitor describe-custom-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```

---

## Installation and Configuration

- Installation: Refer to [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **Important: `jdc` CLI only reads credentials from the `~/.jdc/config` INI file, it does NOT support `JDC_ACCESS_KEY`/`JDC_SECRET_KEY` environment variables**
- In sandbox environments, redirect HOME to a writable directory and pre-create the config file (see SKILL.md "Critical jdc CLI Behavioral Notes")

## Conventions (Agent Execution)

- `--output json` is a **top-level parameter** and must be placed **before** the subcommand: `jdc --output json monitor <command> ...`
- `--no-interactive` does **not** exist in the `jdc` CLI — all commands are non-interactive by default; remove this flag
- JSON paths must be verified through actual API calls; CLI output may differ from raw API field names

## CLI vs API Coverage Comparison

| Operation (API / SDK) | CLI Support | Description |
|-----------------------|-------------|-------------|
| describeServices | ✓ | List monitoring services |
| describeMetrics | ✓ | Query metric items |
| describeMetricData | ✓ | Query monitoring data |
| lastDownsample | ✓ | Query latest data (downsampled) |
| createAlarm | ✓ | Create alarm rule |
| describeAlarms | ✓ | Query alarm list |
| describeAlarm | ✓ | Query alarm details |
| updateAlarm | ✓ | Modify alarm rule |
| enableAlarm | ✓ | Enable/disable alarm |
| deleteAlarms | ✓ | Delete alarm rules |
| describeAlarmHistory | ✓ | Query alarm history |
| describeAlarmContacts | ✓ | Query alarm contacts |
| putMetricData | ✓ | Report custom data |
| describeCustomMetricData | ✓ | Query custom data |

> **Coverage**: CLI covers all core CloudMonitor API operations, no SDK-only operations.

## Command Overview

CloudMonitor CLI commands are unified under the `jdc monitor` namespace.

```bash
jdc monitor <command> [options]
```

## Common Command Categories

| Category | Command | Description |
|----------|---------|-------------|
| Service Query | describe-services | List supported monitoring services |
| Metric Query | describe-metrics | Query metrics for a specific service |
| Data Query | describe-metric-data | Query monitoring data |
| Data Query | last-downsample | Query latest monitoring data |
| Alarm Management | create-alarm | Create alarm rule |
| Alarm Management | describe-alarms | Query alarm rule list |
| Alarm Management | describe-alarm | Query alarm rule details |
| Alarm Management | update-alarm | Modify alarm rule |
| Alarm Management | enable-alarm | Enable/disable alarm rule |
| Alarm Management | delete-alarms | Delete alarm rules |
| Alarm History | describe-alarm-history | Query alarm history |
| Alarm Contacts | describe-alarm-contacts | Query alarm contacts |
| Custom Monitoring | put-metric-data | Report custom monitoring data |
| Custom Monitoring | describe-custom-metric-data | Query custom monitoring data |

## Detailed Command Reference

### 1. describe-services — List Monitoring Services

List all services supported by CloudMonitor.

```bash
jdc --output json monitor describe-services \
  --region-id cn-north-1
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --service-code | string | No | Filter by service code |
| --page-number | integer | No | Page number, default 1 |
| --page-size | integer | No | Items per page, default 20 |

**Response Example**

```json
{
  "result": {
    "services": [
      {
        "serviceCode": "vm",
        "serviceName": "云主机",
        "description": "云服务器监控"
      }
    ]
  }
}
```

### 2. describe-metrics — Query Metrics

Query the list of metrics for a specified service.

```bash
jdc --output json monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --service-code | string | Yes | Service code |
| --resource-id | string | No | Resource ID |
| --metric | string | No | Filter by metric name |
| --page-number | integer | No | Page number |
| --page-size | integer | No | Items per page |

**Response Example**

```json
{
  "result": {
    "metrics": [
      {
        "metric": "vm.cpu.util",
        "metricName": "CPU使用率",
        "unit": "%",
        "period": 60
      }
    ]
  }
}
```

### 3. describe-metric-data — Query Monitoring Data

Query monitoring data within a specified time range.

```bash
jdc --output json monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z" \
  --aggr-type avg
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --metric | string | Yes | Metric name |
| --service-code | string | Yes | Service code |
| --resource-id | string | Yes | Resource ID |
| --start-time | string | Yes | Start time (ISO8601) |
| --end-time | string | Yes | End time (ISO8601) |
| --aggr-type | string | No | Aggregation type (avg/max/min/sum) |
| --period | integer | No | Time granularity (seconds) |
| --dimensions | string | No | Dimension filter (JSON) |

**Response Example**

```json
{
  "result": {
    "metricDatas": [
      {
        "timestamp": "2024-01-01T00:00:00Z",
        "value": 45.2,
        "unit": "%"
      }
    ]
  }
}
```

### 4. last-downsample — Query Latest Monitoring Data

Query the latest monitoring data point for a resource.

```bash
jdc --output json monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metrics '["vm.cpu.util","vm.memory.util"]'
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --service-code | string | Yes | Service code |
| --resource-id | string | Yes | Resource ID |
| --metrics | string | Yes | Metric list (JSON array) |
| --start-time | string | No | Query start time |
| --end-time | string | No | Query end time |

**Response Example**

```json
{
  "result": {
    "items": [
      {
        "metric": "vm.cpu.util",
        "timestamp": "2024-01-01T00:00:00Z",
        "value": 45.2,
        "unit": "%"
      }
    ]
  }
}
```

### 5. create-alarm — Create Alarm Rule

Create a new alarm rule.

```bash
jdc --output json monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "HighCPUAlarm" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.cpu.util" \
  --comparison-operator "gt" \
  --threshold 80 \
  --period 300 \
  --evaluation-periods 2 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --alarm-name | string | Yes | Alarm rule name |
| --service-code | string | Yes | Service code |
| --resource-id | string | Yes | Resource ID |
| --metric-name | string | Yes | Metric name |
| --comparison-operator | string | Yes | Comparison operator (gt/lt/ge/le/eq/ne) |
| --threshold | number | Yes | Threshold |
| --period | integer | Yes | Statistical period (seconds) |
| --evaluation-periods | integer | Yes | Number of consecutive periods |
| --contact-group-id | integer | No | Contact group ID |
| --notice-type | string | No | Notification type (sms/email/callback) |
| --notice-period | integer | No | Notification period (minutes) |
| --notice-time | string | No | Notification time window |

**Response Example**

```json
{
  "result": {
    "alarmId": "alarm-xxx"
  }
}
```

### 6. describe-alarms — Query Alarm Rule List

Query the list of alarm rules.

```bash
jdc --output json monitor describe-alarms \
  --region-id cn-north-1 \
  --service-code vm \
  --page-number 1 \
  --page-size 20
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --service-code | string | No | Filter by service code |
| --resource-id | string | No | Filter by resource ID |
| --alarm-name | string | No | Filter by alarm name |
| --alarm-status | string | No | Filter by alarm status |
| --page-number | integer | No | Page number |
| --page-size | integer | No | Items per page |

**Response Example**

```json
{
  "result": {
    "alarms": [
      {
        "alarmId": "alarm-xxx",
        "alarmName": "HighCPUAlarm",
        "serviceCode": "vm",
        "resourceId": "i-xxx",
        "metricName": "vm.cpu.util",
        "status": "OK"
      }
    ]
  }
}
```

### 7. describe-alarm — Query Alarm Rule Details

Query detailed information for a single alarm rule.

```bash
jdc --output json monitor describe-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --alarm-id | string | Yes | Alarm rule ID |

### 8. update-alarm — Modify Alarm Rule

Modify alarm rule configuration.

```bash
jdc --output json monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --alarm-name "UpdatedAlarmName" \
  --threshold 90
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --alarm-id | string | Yes | Alarm rule ID |
| --alarm-name | string | No | New alarm name |
| --threshold | number | No | New threshold |
| --period | integer | No | New statistical period |
| --evaluation-periods | integer | No | New consecutive period count |
| --contact-group-id | integer | No | New contact group ID |
| --notice-type | string | No | New notification type |

### 9. enable-alarm — Enable/Disable Alarm Rule

Enable or disable an alarm rule.

```bash
# Enable alarm
jdc --output json monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled true

# Disable alarm
jdc --output json monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled false
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --alarm-id | string | Yes | Alarm rule ID |
| --enabled | boolean | Yes | Whether enabled (true/false) |

### 10. delete-alarms — Delete Alarm Rules

Delete alarm rules.

```bash
jdc --output json monitor delete-alarms \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --alarm-id | string | Yes | Alarm rule ID |

### 11. describe-alarm-history — Query Alarm History

Query alarm trigger history.

```bash
jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z"
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --alarm-id | string | No | Filter by alarm rule ID |
| --service-code | string | No | Filter by service code |
| --resource-id | string | No | Filter by resource ID |
| --start-time | string | No | Start time |
| --end-time | string | No | End time |
| --page-number | integer | No | Page number |
| --page-size | integer | No | Items per page |

**Response Example**

```json
{
  "result": {
    "alarmHistories": [
      {
        "alarmId": "alarm-xxx",
        "alarmName": "HighCPUAlarm",
        "status": "ALARM",
        "triggerTime": "2024-01-01T12:00:00Z",
        "value": 85.2
      }
    ]
  }
}
```

### 12. describe-alarm-contacts — Query Alarm Contacts

Query alarm contact information.

```bash
jdc --output json monitor describe-alarm-contacts \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --contact-group-id | integer | No | Filter by contact group ID |
| --page-number | integer | No | Page number |
| --page-size | integer | No | Items per page |

### 13. put-metric-data — Report Custom Monitoring Data

Report custom monitoring data points.

```bash
jdc --output json monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace "my-namespace" \
  --metric-name "order-count" \
  --value 100 \
  --dimensions '{"service":"order-service","env":"prod"}' \
  --timestamp "2024-01-01T00:00:00Z"
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --namespace | string | Yes | Namespace |
| --metric-name | string | Yes | Metric name |
| --value | number | Yes | Metric value |
| --dimensions | string | No | Dimensions (JSON) |
| --timestamp | string | No | Timestamp (default: current time) |
| --unit | string | No | Unit |

### 14. describe-custom-metric-data — Query Custom Monitoring Data

Query custom monitoring data.

```bash
jdc --output json monitor describe-custom-metric-data \
  --region-id cn-north-1 \
  --namespace "my-namespace" \
  --metric-name "order-count" \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```

**Parameter Reference**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| --region-id | string | Yes | Region ID |
| --namespace | string | Yes | Namespace |
| --metric-name | string | Yes | Metric name |
| --start-time | string | Yes | Start time |
| --end-time | string | Yes | End time |
| --dimensions | string | No | Dimension filter |
| --period | integer | No | Time granularity |
| --aggr-type | string | No | Aggregation type |

## Common Scenario Examples

### Scenario 1: Batch Query CPU Usage for Multiple VMs

```bash
for vm_id in i-xxx1 i-xxx2 i-xxx3; do
  echo "Querying CPU for $vm_id"
  jdc --output json monitor last-downsample \
    --region-id cn-north-1 \
    --service-code vm \
    --resource-id $vm_id \
    --metrics '["vm.cpu.util"]'
done
```

### Scenario 2: Create Disk Usage Alarm

```bash
jdc --output json monitor create-alarm \
  --region-id cn-north-1 \
  --alarm-name "DiskUsageAlarm" \
  --service-code vm \
  --resource-id i-xxx \
  --metric-name "vm.disk.util" \
  --comparison-operator "gt" \
  --threshold 85 \
  --period 300 \
  --evaluation-periods 1 \
  --contact-group-id 1 \
  --notice-type "sms,email"
```

### Scenario 3: Query Alarm History for the Past 7 Days

```bash
# Calculate time range
start_time=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ")
end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 \
  --start-time "$start_time" \
  --end-time "$end_time" \
  --page-size 100
```

### Scenario 4: Report Business Custom Metrics

```bash
# Report order count metric
jdc --output json monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace "ecommerce-metrics" \
  --metric-name "order-count-per-minute" \
  --value 150 \
  --dimensions '{"region":"cn-north-1","category":"electronics"}' \
  --unit "Count"
```

## Output Formats

The CLI supports multiple output formats, specified via the `--output` top-level parameter. Note: `--output` must be placed **before the subcommand**.

| Format | Description |
|--------|-------------|
| json | JSON format (recommended for automation) |
| table | Table format |
| text | Plain text format |

Example:
```bash
jdc --output table monitor describe-alarms --region-id cn-north-1
```

## Global Parameters

All commands support the following global parameters:

| Parameter | Description |
|-----------|-------------|
| --debug | Show debug information |
| --output | Output format (json/table/text) — must be placed before the subcommand |
| --profile | Use the specified profile |
| --region-id | Region ID |