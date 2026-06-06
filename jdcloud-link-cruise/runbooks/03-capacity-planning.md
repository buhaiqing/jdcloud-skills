---
runbook_id: "03"
scenario: "容量规划检查"
version: "1.0.0"
trigger: "每周定时 / 人工触发"
risk_level: "中"
---

# 容量规划检查

## 1. 场景

评估未来 30-90 天的资源是否充足，提前发现扩容需求。关注**趋势**而非瞬时状态。

## 2. 流程

```yaml
steps:
  - id: "discover"          # 同日常巡检

  - id: "collect_7d_metrics"
    description: "采集最近 7 天的监控数据（1h 粒度）"
    window: "最近 7 天"
    metrics:
      disk_usage: true       # 磁盘 → 预测满盘日
      memory_usage: true     # 内存 → 预测OOM日
      redis_memory: true     # Redis → 预测OOM日
      iops_trend: true       # IOPS → 是否需要升配
      bandwidth_trend: true  # 带宽 → 是否需升配

  - id: "predict_capacity"
    method: "线性回归（最近 7 天数据点）"
    horizon_days: 90
    outputs:
      - "磁盘满盘日预测"
      - "Redis OOM 日预测"
      - "网络带宽打满日预测"
      - "IOPS 规格上限日预测"

  - id: "cost_optimization"
    description: "检查是否存在低利用率资源，建议降配"
    rules:
      - condition: "CPU 7天平均 < 20% AND 内存 7天平均 < 40%"
        action: "建议降配（如 c.n3.2xlarge → c.n3.xlarge）"
      - condition: "磁盘使用率 7天平均 < 20%"
        action: "建议缩小云盘容量"
      - condition: "Redis 内存使用率 7天平均 < 40%"
        action: "建议降配 Redis 规格"

  - id: "report"
    outputs:
      markdown: true
      json: true
      format: "趋势预测式（历史折线 + 预测延长线 + 建议）"
```

## 3. 关键预测

| 指标 | 预测方法 | 输出 |
|---|---|---|
| 磁盘满 | 线性回归（磁盘使用率 %） | "预计在 YYYY-MM-DD 达到 90%" |
| Redis OOM | 线性回归（内存使用率 %） | "预计在 YYYY-MM-DD 达到 85%" |
| IOPS 达上限 | 线性回归（IOPS / 规格上限 %） | "预计在 YYYY-MM-DD 达到 80%" |
| 带宽达上限 | 线性回归（带宽 / 规格上限 %） | "预计在 YYYY-MM-DD 达到 80%" |