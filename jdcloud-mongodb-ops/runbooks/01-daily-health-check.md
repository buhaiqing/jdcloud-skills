---
runbook_id: "01"
scenario: "MongoDB 日常健康巡检"
version: "1.0.0"
last_updated: "2026-06-12"
trigger: "定时调度（每 6 小时）/ 人工触发"
risk_level: "低"
execution_time_estimate: "3-8 分钟（10 个实例以内）"
---

# MongoDB 日常健康巡检

## 1. 目标

对指定客户或指定区域的 MongoDB 实例进行只读健康检查，覆盖实例状态、资源水位、连接、延迟、吞吐、复制延迟、备份和基础安全配置。

## 2. Phase 1: Perceive — 观测采集

```yaml
inputs:
  region: "{{user.region}}"
  customer: "{{user.customer}}"
  instance_id: "{{user.instance_id}} 可选"

steps:
  - id: list_instances
    description: "列出 MongoDB 实例并按客户标签过滤"
    cli: "jdc --output json mongodb describe-instances --region-id {{user.region}} --page-number 1 --page-size 100"
    sdk_fallback: "DescribeInstances"

  - id: collect_instance_snapshot
    fields:
      - instanceId
      - instanceName
      - status
      - instanceClass
      - engineVersion
      - storageSizeGB
      - connectionDomain
      - vpcId
      - subnetId
      - replicaSetName
      - tags

  - id: collect_metrics
    time_window: "最近 6 小时，5 分钟或 1 小时粒度"
    metrics:
      - mongodb_cpu_utilization
      - mongodb_memory_usage
      - mongodb_disk_usage
      - mongodb_iops
      - mongodb_connections_current
      - mongodb_connections_usage
      - mongodb_opcounters
      - mongodb_query_rate
      - mongodb_insert_rate
      - mongodb_update_rate
      - mongodb_delete_rate
      - mongodb_read_latency
      - mongodb_write_latency
      - mongodb_command_latency
      - mongodb_repl_lag
      - mongodb_oplog_window

  - id: collect_backups
    description: "查询最近备份状态和最近成功备份时间"
```

## 3. Phase 2: Reason — 健康评分与异常判断

| 维度 | Warning | Critical | 根因提示 |
|---|---:|---:|---|
| CPU | > 70% | > 85% | 慢查询、缺索引、QPS 激增、聚合过重 |
| 内存 | > 75% | > 90% | working set 过大、连接过多、大聚合 |
| 磁盘 | > 80% | > 90% | 数据增长、TTL 缺失、索引膨胀 |
| 连接使用率 | > 70% | > 85% | 连接池配置不当、连接泄漏、短连接风暴 |
| 读/写/命令延迟 | > 100ms | > 500ms | 无索引扫描、IOPS 瓶颈、锁等待 |
| 复制延迟 | > 10s | > 60s | 写入峰值、Secondary 读压力、磁盘/网络瓶颈 |
| Oplog window | < 24h | < 6h | 写入量过大，恢复窗口不足 |

### 关联规则

```yaml
rules:
  - name: high_cpu_with_latency
    if: "cpu.max > 85 AND latency.max > 200 AND query_rate.not_rising"
    root_cause: "缺索引或低效查询导致单请求成本升高"
    confidence: 0.75

  - name: high_cpu_with_qps_spike
    if: "cpu.max > 85 AND (query_rate.rising OR update_rate.rising)"
    root_cause: "流量突增或应用发布导致读写放大"
    confidence: 0.70

  - name: connection_storm
    if: "connections_usage.current > 85 AND opcounters.not_rising"
    root_cause: "连接泄漏或连接池未复用"
    confidence: 0.80

  - name: disk_capacity_risk
    if: "disk.current > 80 OR disk.growth_7d > 10pp"
    root_cause: "容量增长风险，需定位增长集合和索引"
    confidence: 0.65
```

## 4. Phase 3: Execute — 建议生成（只读）

输出建议不得直接执行变更：

| 建议类型 | 委派 |
|---|---|
| 建索引 / 调参数 / 扩容 / 备份恢复 | `jdcloud-mongodb-ops`，需人工确认 |
| 监控指标和告警规则 | `jdcloud-cloudmonitor-ops` |
| VPC / 安全组 / 白名单 | `jdcloud-vpc-ops` |
| 跨服务链路根因 | `jdcloud-aiops-cruise` |

## 5. 验收标准

- 报告包含实例快照、指标摘要、异常项、根因候选、证据和建议。
- `critical` 项必须包含 3 条以上证据或明确说明证据不足。
- 所有变更类建议必须标记 `requires_confirmation=true`。

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-12 | Added MongoDB daily AIOps health check runbook. |
