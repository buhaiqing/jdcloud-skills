# 云监控 CLI 命令速查

> 本文档从 `SKILL.md` 提取。

## 查询监控服务列表

```bash
jdc --output json monitor describe-services --region-id cn-north-1
```

## 查询指定产品的监控项

```bash
jdc --output json monitor describe-metrics \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx
```

## 查询监控数据

```bash
jdc --output json monitor describe-metric-data \
  --region-id cn-north-1 \
  --metric vm.cpu.util \
  --service-code vm \
  --resource-id i-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```

## 查询最新监控数据（降采样）

```bash
jdc --output json monitor last-downsample \
  --region-id cn-north-1 \
  --service-code vm \
  --resource-id i-xxx \
  --metrics '["vm.cpu.util","vm.memory.util"]'
```

## 创建告警规则

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

## 查询告警规则列表

```bash
jdc --output json monitor describe-alarms \
  --region-id cn-north-1 \
  --page-number 1 \
  --page-size 20
```

## 启用/禁用告警规则

```bash
# 启用告警
jdc --output json monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled true

# 禁用告警
jdc --output json monitor enable-alarm \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --enabled false
```

## 查询告警历史

```bash
jdc --output json monitor describe-alarm-history \
  --region-id cn-north-1 \
  --alarm-id alarm-xxx \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z"
```

## 上报自定义监控数据

```bash
jdc --output json monitor put-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --value 100 \
  --dimensions '{"instance":"app-server-01"}'
```

## 查询自定义监控数据

```bash
jdc --output json monitor describe-custom-metric-data \
  --region-id cn-north-1 \
  --namespace custom-namespace \
  --metric-name custom-metric \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T23:59:59Z"
```
