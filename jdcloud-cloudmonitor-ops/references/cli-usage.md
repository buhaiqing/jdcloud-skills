# CLI — 云监控(CloudMonitor) (`jdc`)

## 安装和配置

- 安装: 参考 [京东云 CLI](https://github.com/jdcloud-api/jdcloud-cli)
- 配置: `jdc config init` 或通过环境变量 `JDC_ACCESS_KEY` / `JDC_SECRET_KEY`

## 约定（Agent 执行）

- **必须** 追加 `--output json` 用于自动化解析
- **必须** 追加 `--no-interactive`（或等价参数）避免阻塞
- JSON 路径需通过实际调用验证，CLI 输出可能与原始 API 字段名不同

## CLI vs API 覆盖对比

| 操作 (API / SDK) | CLI 支持 | 说明 |
|------------------|---------|------|
| describeServices | ✓ | 查询监控服务列表 |
| describeMetrics | ✓ | 查询监控项 |
| describeMetricData | ✓ | 查询监控数据 |
| lastDownsample | ✓ | 查询最新数据（降采样） |
| createAlarm | ✓ | 创建告警规则 |
| describeAlarms | ✓ | 查询告警列表 |
| describeAlarm | ✓ | 查询告警详情 |
| updateAlarm | ✓ | 修改告警规则 |
| enableAlarm | ✓ | 启用/禁用告警 |
| deleteAlarms | ✓ | 删除告警规则 |
| describeAlarmHistory | ✓ | 查询告警历史 |
| describeAlarmContacts | ✓ | 查询告警联系人 |
| putMetricData | ✓ | 上报自定义数据 |
| describeCustomMetricData | ✓ | 查询自定义数据 |

> **覆盖率**: CLI 覆盖云监控所有核心 API 操作，无 SDK-only 操作。

## 命令概览

云监控相关的 CLI 命令统一在 `jdc monitor` 命名空间下。

```bash
jdc monitor <command> [options]
```

## 常用命令分类

| 分类 | 命令 | 说明 |
|------|------|------|
| 服务查询 | describe-services | 查询支持的监控服务列表 |
| 监控项查询 | describe-metrics | 查询指定服务的监控项 |
| 数据查询 | describe-metric-data | 查询监控数据 |
| 数据查询 | last-downsample | 查询最新监控数据 |
| 告警管理 | create-alarm | 创建告警规则 |
| 告警管理 | describe-alarms | 查询告警规则列表 |
| 告警管理 | describe-alarm | 查询告警规则详情 |
| 告警管理 | update-alarm | 修改告警规则 |
| 告警管理 | enable-alarm | 启用/禁用告警规则 |
| 告警管理 | delete-alarms | 删除告警规则 |
| 告警历史 | describe-alarm-history | 查询告警历史 |
| 告警联系人 | describe-alarm-contacts | 查询告警联系人 |
| 自定义监控 | put-metric-data | 上报自定义监控数据 |
| 自定义监控 | describe-custom-metric-data | 查询自定义监控数据 |

## 详细命令说明

### 1. describe-services - 查询监控服务列表

查询云监控支持的所有服务列表。

```bash
jdc monitor describe-services \
  --region-id cn-north-1
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --service-code | string | 否 | 按服务代码过滤 |
| --page-number | integer | 否 | 页码，默认 1 |
| --page-size | integer | 否 | 每页数量，默认 20 |

**返回示例**

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

### 2. describe-metrics - 查询监控项

查询指定服务的监控项列表。

```bash
jdc monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --service-code | string | 是 | 服务代码 |
| --resource-id | string | 否 | 资源 ID |
| --metric | string | 否 | 监控项名称过滤 |
| --page-number | integer | 否 | 页码 |
| --page-size | integer | 否 | 每页数量 |

**返回示例**

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

### 3. describe-metric-data - 查询监控数据

查询指定时间范围内的监控数据。

```bash
jdc monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z" \
  --aggr-type avg
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --metric | string | 是 | 监控项名称 |
| --service-code | string | 是 | 服务代码 |
| --resource-id | string | 是 | 资源 ID |
| --start-time | string | 是 | 开始时间(ISO8601) |
| --end-time | string | 是 | 结束时间(ISO8601) |
| --aggr-type | string | 否 | 聚合类型(avg/max/min/sum) |
| --period | integer | 否 | 时间粒度(秒) |
| --dimensions | string | 否 | 维度过滤(JSON) |

**返回示例**

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

### 4. last-downsample - 查询最新监控数据

查询资源的最新监控数据点。

```bash
jdc monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metrics '["vm.cpu.util","vm.memory.util"]'
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --service-code | string | 是 | 服务代码 |
| --resource-id | string | 是 | 资源 ID |
| --metrics | string | 是 | 监控项列表(JSON数组) |
| --start-time | string | 否 | 查询起始时间 |
| --end-time | string | 否 | 查询结束时间 |

**返回示例**

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

### 5. create-alarm - 创建告警规则

创建新的告警规则。

```bash
jdc monitor create-alarm \
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

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --alarm-name | string | 是 | 告警规则名称 |
| --service-code | string | 是 | 服务代码 |
| --resource-id | string | 是 | 资源 ID |
| --metric-name | string | 是 | 监控项名称 |
| --comparison-operator | string | 是 | 比较运算符(gt/lt/ge/le/eq/ne) |
| --threshold | number | 是 | 阈值 |
| --period | integer | 是 | 统计周期(秒) |
| --evaluation-periods | integer | 是 | 连续周期数 |
| --contact-group-id | integer | 否 | 联系组 ID |
| --notice-type | string | 否 | 通知类型(sms/email/callback) |
| --notice-period | integer | 否 | 通知周期(分钟) |
| --notice-time | string | 否 | 通知时段 |

**返回示例**

```json
{
  "result": {
    "alarmId": "alarm-xxx"
  }
}
```

### 6. describe-alarms - 查询告警规则列表

查询告警规则列表。

```bash
jdc monitor describe-alarms \
  --region-id cn-north-1 \
  --service-code vm \
  --page-number 1 \
  --page-size 20
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --service-code | string | 否 | 服务代码过滤 |
| --resource-id | string | 否 | 资源 ID 过滤 |
| --alarm-name | string | 否 | 告警名称过滤 |
| --alarm-status | string | 否 | 告警状态过滤 |
| --page-number | integer | 否 | 页码 |
| --page-size | integer | 否 | 每页数量 |

**返回示例**

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

### 7. describe-alarm - 查询告警规则详情

查询单个告警规则的详细信息。

```bash
jdc monitor describe-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --alarm-id | string | 是 | 告警规则 ID |

### 8. update-alarm - 修改告警规则

修改告警规则配置。

```bash
jdc monitor update-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --alarm-name "UpdatedAlarmName" \
  --threshold 90
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --alarm-id | string | 是 | 告警规则 ID |
| --alarm-name | string | 否 | 新告警名称 |
| --threshold | number | 否 | 新阈值 |
| --period | integer | 否 | 新统计周期 |
| --evaluation-periods | integer | 否 | 新连续周期数 |
| --contact-group-id | integer | 否 | 新联系组 ID |
| --notice-type | string | 否 | 新通知类型 |

### 9. enable-alarm - 启用/禁用告警规则

启用或禁用告警规则。

```bash
# 启用告警
jdc monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled true

# 禁用告警
jdc monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled false
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --alarm-id | string | 是 | 告警规则 ID |
| --enabled | boolean | 是 | 是否启用(true/false) |

### 10. delete-alarms - 删除告警规则

删除告警规则。

```bash
jdc monitor delete-alarms \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --alarm-id | string | 是 | 告警规则 ID |

### 11. describe-alarm-history - 查询告警历史

查询告警触发历史。

```bash
jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z"
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --alarm-id | string | 否 | 告警规则 ID 过滤 |
| --service-code | string | 否 | 服务代码过滤 |
| --resource-id | string | 否 | 资源 ID 过滤 |
| --start-time | string | 否 | 开始时间 |
| --end-time | string | 否 | 结束时间 |
| --page-number | integer | 否 | 页码 |
| --page-size | integer | 否 | 每页数量 |

**返回示例**

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

### 12. describe-alarm-contacts - 查询告警联系人

查询告警联系人信息。

```bash
jdc monitor describe-alarm-contacts \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --contact-group-id | integer | 否 | 联系组 ID 过滤 |
| --page-number | integer | 否 | 页码 |
| --page-size | integer | 否 | 每页数量 |

### 13. put-metric-data - 上报自定义监控数据

上报自定义监控数据点。

```bash
jdc monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace "my-namespace" \
  --metric-name "order-count" \
  --value 100 \
  --dimensions '{"service":"order-service","env":"prod"}' \
  --timestamp "2024-01-01T00:00:00Z"
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --namespace | string | 是 | 命名空间 |
| --metric-name | string | 是 | 指标名称 |
| --value | number | 是 | 指标值 |
| --dimensions | string | 否 | 维度(JSON) |
| --timestamp | string | 否 | 时间戳(默认当前时间) |
| --unit | string | 否 | 单位 |

### 14. describe-custom-metric-data - 查询自定义监控数据

查询自定义监控数据。

```bash
jdc monitor describe-custom-metric-data \
  --region-id cn-north-1 \
  --namespace "my-namespace" \
  --metric-name "order-count" \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| --region-id | string | 是 | 区域 ID |
| --namespace | string | 是 | 命名空间 |
| --metric-name | string | 是 | 指标名称 |
| --start-time | string | 是 | 开始时间 |
| --end-time | string | 是 | 结束时间 |
| --dimensions | string | 否 | 维度过滤 |
| --period | integer | 否 | 时间粒度 |
| --aggr-type | string | 否 | 聚合类型 |

## 常用场景示例

### 场景1：批量查询多台云主机的 CPU 使用率

```bash
for vm_id in i-xxx1 i-xxx2 i-xxx3; do
  echo "Querying CPU for $vm_id"
  jdc monitor last-downsample \
    --region-id cn-north-1 \
    --service-code vm \
    --resource-id $vm_id \
    --metrics '["vm.cpu.util"]'
done
```

### 场景2：创建磁盘使用率告警

```bash
jdc monitor create-alarm \
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

### 场景3：查询过去7天的告警历史

```bash
# 计算时间
start_time=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ")
end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jdc monitor describe-alarm-history \
  --region-id cn-north-1 \
  --start-time "$start_time" \
  --end-time "$end_time" \
  --page-size 100
```

### 场景4：上报业务自定义指标

```bash
# 上报订单量指标
jdc monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace "ecommerce-metrics" \
  --metric-name "order-count-per-minute" \
  --value 150 \
  --dimensions '{"region":"cn-north-1","category":"electronics"}' \
  --unit "Count"
```

## 输出格式

CLI 支持多种输出格式，可通过 `--output` 参数指定。

| 格式 | 说明 |
|------|------|
| json | JSON 格式（默认） |
| table | 表格格式 |
| text | 纯文本格式 |

示例：
```bash
jdc monitor describe-alarms --region-id cn-north-1 --output table
```

## 全局参数

所有命令都支持以下全局参数：

| 参数 | 说明 |
|------|------|
| --debug | 显示调试信息 |
| --output | 输出格式(json/table/text) |
| --profile | 使用指定的配置文件 |
| --region-id | 区域 ID |
