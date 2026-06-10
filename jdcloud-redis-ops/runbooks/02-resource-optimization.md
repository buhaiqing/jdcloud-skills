---
runbook_id: "02"
scenario: "Redis 资源优化分析"
version: "1.0.0"
last_updated: "2026-06-10"
trigger: "每周定时 / 人工触发"
risk_level: "中"
execution_time_estimate: "5-10 分钟（10 个实例以内）"
---

# Redis 资源优化分析

## 1. 场景描述

分析 Redis 实例的资源使用效率，识别低利用率实例并给出降配建议，同时检查是否存在规格不匹配（如内存够但 CPU/连接数不足）的情况，输出成本优化方案。

### 背景

DOPS 实际案例（DOPS-85670）：`2026-06-07-Redis使用率分析-实例降配建议` — 运维团队需要定期分析 Redis 使用率，对长期低利用率的实例进行降配以节省成本。

### 适用条件

- 实例运行时间 > 7 天（需要足够的历史数据）
- JDC AK/SK 已配置且具有 Redis 读权限

---

## 2. 执行流程

### Phase 1: 感知 — 数据采集（约 2 分钟）

```yaml
steps:
  - id: "list_instances"
    description: "列出所有 Redis 实例"
    cli:
      command: >
        jdc --output json redis describe-cache-instances
        --region-id "{{user.region}}"
        --page-number 1 --page-size 100
    filter: "按客户标签过滤"

  - id: "collect_7d_metrics"
    description: "采集最近 7 天的监控数据（1 小时粒度）"
    time_window: "最近 7 天"
    metrics:
      - "redis.memory.usage"       # 内存使用率 (%)
      - "redis.memory.used"        # 已用内存 (MB)
      - "redis.cpu.util"           # CPU 使用率 (%)
      - "redis.connections"        # 连接数
      - "redis.hit_rate"           # 缓存命中率 (%)
      - "redis.network.bytes.in"   # 入网流量
      - "redis.network.bytes.out"  # 出网流量

  - id: "collect_spec_info"
    description: "采集实例规格信息"
    fields:
      - "cacheInstanceClass: 当前规格代码"
      - "cacheInstanceMemoryMB: 内存规格 (MB)"
      - "cacheInstanceType: 实例类型"
      - "redisVersion: Redis 版本"
      - "chargeMode: 计费模式"
```

### Phase 2: 推理 — 资源效率分析（约 3-5 分钟）

```yaml
steps:
  - id: "analyze_utilization"
    description: "计算各维度 7 天利用率"
    metrics_7d:
      memory_avg: "7 天内存使用率平均值"
      memory_p95: "7 天内存使用率 P95"
      memory_max: "7 天内存使用率最大值"
      cpu_avg: "7 天 CPU 使用率平均值"
      cpu_p95: "7 天 CPU 使用率 P95"
      conn_avg: "7 天连接数平均值"
      conn_p95: "7 天连接数 P95"

  - id: "detect_underutilized"
    description: "识别低利用率实例"
    rules:
      - id: "R1_memory_low"
        condition: "memory_p95 < 30% AND memory_max < 50%"
        severity: "info"
        category: "内存严重低利用"
        suggestion: "建议降配到更小规格，可节省约 {saving}% 成本"
        ops_skill: "jdcloud-redis-ops (modify-cache-instance-class)"
      - id: "R2_memory_moderate"
        condition: "memory_p95 < 50% AND memory_max < 70%"
        severity: "info"
        category: "内存中度低利用"
        suggestion: "可考虑降配，预计节省 {saving}% 成本"
      - id: "R3_cpu_low"
        condition: "cpu_p95 < 20% AND cpu_max < 40%"
        severity: "info"
        category: "CPU 低利用"
        suggestion: "当前 CPU 规格可能过高"

  - id: "detect_mismatch"
    description: "识别规格不匹配（某些维度不足，某些维度过剩）"
    rules:
      - id: "M1_memory_ok_cpu_high"
        condition: "memory_p95 < 60% AND cpu_p95 > 70%"
        severity: "warning"
        category: "CPU 瓶颈但内存充足"
        suggestion: "当前实例 CPU 不足但内存有余量，建议升配 CPU 或检查慢查询"
        ops_skill: "jdcloud-redis-ops (modify-cache-instance-class)"
      - id: "M2_memory_ok_conn_high"
        condition: "memory_p95 < 60% AND conn_p95 > 8000"
        severity: "warning"
        category: "连接数瓶颈但内存充足"
        suggestion: "连接数接近上限，检查客户端连接池配置或考虑拆分实例"
      - id: "M3_memory_high_cpu_low"
        condition: "memory_p95 > 70% AND cpu_p95 < 30%"
        severity: "warning"
        category: "内存瓶颈但 CPU 充足"
        suggestion: "纯存储型使用场景，建议扩容内存或清理过期 key"

  - id: "detect_trend"
    description: "分析内存增长趋势，预测何时需要扩容"
    method: "线性回归（7 天数据点）"
    prediction_horizon: "30 天"
    rules:
      - condition: "预测 30 天内内存使用率将达到 85%"
        severity: "warning"
        category: "内存增长趋势预警"
        suggestion: "预计 {date} 内存使用率达到 85%，建议提前规划扩容"
      - condition: "预测 7 天内内存使用率将达到 85%"
        severity: "critical"
        category: "内存即将耗尽"
        suggestion: "预计 {date} 内存使用率达到 85%，请立即扩容"

  - id: "check_cost_efficiency"
    description: "检查计费模式优化空间"
    rules:
      - condition: "chargeMode == 'postpaid_by_usage' AND memory_p95 < 30%"
        severity: "info"
        category: "按量付费低利用"
        suggestion: "按量付费实例长期低利用，建议降配以减少按量费用"
      - condition: "chargeMode == 'prepaid_by_duration' AND memory_p95 < 30%"
        severity: "info"
        category: "包年包月低利用"
        suggestion: "包年包月实例长期低利用，到期续费时建议降配"

  - id: "check_idle_instances"
    description: "检查是否存在闲置实例"
    rules:
      - condition: "redis.connections 7 天平均 < 5 AND redis.network.bytes.in 7 天平均 < 1KB/s"
        severity: "warning"
        category: "疑似闲置实例"
        suggestion: "该实例 7 天内几乎没有流量，请确认是否仍在使用。如已废弃，建议备份后删除以节省成本。"
        ops_skill: "jdcloud-redis-ops (create-backup → delete-cache-instance)"
```

### Phase 3: 执行 — 优化建议生成（只读）

```yaml
steps:
  - id: "rank_suggestions"
    description: "按节省金额排序优化建议"
    ranking:
      priority: "节省金额 > 风险等级 > 实施难度"
    output:
      - "P0: 立即执行（高节省 + 低风险）"
      - "P1: 本周执行（中节省 + 低风险）"
      - "P2: 本月执行（低节省 或 需评估风险）"

  - id: "generate_spec_recommendation"
    description: "生成具体规格推荐"
    method: |
      根据 memory_p95 和 cpu_p95，从可用规格列表中选择最接近的上一档规格：
      - 推荐规格的内存 >= memory_p95 * 当前内存 * 1.3（预留 30% 余量）
      - 推荐规格的 CPU >= cpu_p95 * 当前 CPU * 1.3
    output:
      - "当前规格: {current_class} ({current_memory}MB)"
      - "推荐规格: {recommended_class} ({recommended_memory}MB)"
      - "预计月节省: ¥{saving}/月"

  - id: "generate_cost_summary"
    description: "生成成本优化汇总"
    output_format: "Markdown 表格"
    columns:
      - "实例名称"
      - "当前规格"
      - "7天内存 P95"
      - "7天 CPU P95"
      - "分类"
      - "建议操作"
      - "预计月节省"
      - "优先级"

  - id: "output_report"
    description: "输出优化报告"
    outputs:
      - path: "reports/output/redis-optimization-{customer}-{date}.md"
        format: "Markdown"
      - path: "reports/output/redis-optimization-{customer}-{date}.json"
        format: "JSON"
```

---

## 3. 降配安全规则

| 规则 | 说明 |
|------|------|
| **禁止降配到低于当前已用内存** | 推荐规格内存 >= memory_max * 1.2 |
| **禁止降配到低于 P95 CPU** | 推荐规格 CPU >= cpu_p95 * 1.2 |
| **降配前必须创建备份** | 通过 `jdcloud-redis-ops` create-backup |
| **降配操作需人工确认** | Safety Gate: 降配属于 `modify-cache-instance-class`，需用户确认 |
| **集群版降配需评估数据迁移** | 集群版降配可能涉及 slot 迁移，需评估影响 |
| **生产环境降配建议在低峰期** | 建议在凌晨 2:00-5:00 执行 |

---

## 4. 告警联动

| 告警类型 | 触发条件 | 自动动作 |
|----------|----------|----------|
| 低利用率发现 | memory_p95 < 30% 持续 7 天 | 创建 DOPS 降配建议工单 |
| 内存增长预警 | 预测 30 天内达 85% | 创建 DOPS 扩容预警工单 |
| 闲置实例 | 7 天无流量 | 创建 DOPS 实例清理确认工单 |

---

## 5. Changelog

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-06-10 | 初始版本，定义 Redis 资源优化分析完整流程 |
