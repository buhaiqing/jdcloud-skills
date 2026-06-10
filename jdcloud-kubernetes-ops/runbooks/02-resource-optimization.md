---
runbook_id: "02"
scenario: "K8s 资源配置优化"
version: "1.0.0"
last_updated: "2026-06-10"
trigger: "每周定时 / 人工触发"
risk_level: "中"
execution_time_estimate: "10-15 分钟（5 个集群以内）"
---

# K8s 资源配置优化

## 1. 场景描述

分析 K8s 集群的资源使用效率，识别 CPU/Memory requests 配置不合理、HPA 触发条件不当、节点水位不均等问题，输出资源优化和成本节省方案。

### 背景

DOPS 实际案例（近 5 天）：
- DOPS-85667/85668/85669：金色四季/绿叶水果/海鼎测试 更新 k8s CPU 请求配置
- DOPS-85737：检测 pod mem limits 小于 Xmx
- DOPS-85704/85707：HPA 触发条件不合理

### 适用条件

- 集群运行时间 > 7 天
- 可通过 JD Cloud 监控或 kube-state-metrics 获取 Pod 级别指标

---

## 2. 执行流程

### Phase 1: 感知 — 数据采集（约 3 分钟）

```yaml
steps:
  - id: "list_clusters"
    description: "列出所有 K8s 集群"
    cli:
      command: >
        jdc --output json nc describe-clusters
        --region-id "{{user.region}}"
        --page-number 1 --page-size 100

  - id: "collect_node_metrics"
    description: "采集节点 7 天资源使用数据"
    time_window: "最近 7 天（1 小时粒度）"
    metrics:
      - "node_cpu_utilization"          # 节点 CPU 使用率
      - "node_memory_utilization"        # 节点内存使用率
      - "node_cpu_requests_ratio"        # CPU requests / allocatable
      - "node_memory_requests_ratio"     # Memory requests / allocatable
      - "node_cpu_limits_ratio"          # CPU limits / allocatable
      - "node_memory_limits_ratio"       # Memory limits / allocatable

  - id: "collect_pod_metrics"
    description: "采集 Pod 7 天资源使用数据"
    time_window: "最近 7 天（1 小时粒度）"
    metrics:
      - "pod_cpu_usage"                  # Pod 实际 CPU 使用
      - "pod_memory_usage"               # Pod 实际内存使用
      - "pod_cpu_requests"               # Pod CPU requests
      - "pod_memory_requests"            # Pod Memory requests
      - "pod_cpu_limits"                 # Pod CPU limits
      - "pod_memory_limits"              # Pod Memory limits

  - id: "collect_hpa_configs"
    description: "收集所有 HPA 配置"
    fields:
      - "target: 目标资源 (Deployment/StatefulSet)"
      - "minReplicas / maxReplicas"
      - "metrics: 触发指标和阈值"
      - "behavior: 扩缩容行为配置"
```

### Phase 2: 推理 — 资源效率分析（约 5-8 分钟）

```yaml
steps:
  - id: "analyze_requests_vs_usage"
    description: "对比 Pod requests 与实际使用量"
    rules:
      - id: "R1_cpu_over_requested"
        condition: "pod_cpu_requests > pod_cpu_usage_p95 * 5"
        severity: "warning"
        category: "CPU 过度预留"
        message: "Pod {pod} CPU requests ({req}) 远高于实际使用 ({actual}P95)"
        suggestion: "降低 CPU requests 到 {actual}*1.5，释放可调度资源"
        ops_skill: "jdcloud-kubernetes-ops (通过 deployment 更新)"
      - id: "R2_memory_over_requested"
        condition: "pod_memory_requests > pod_memory_usage_p95 * 3"
        severity: "warning"
        category: "内存过度预留"
        message: "Pod {pod} Memory requests ({req}) 远高于实际使用 ({actual}P95)"
        suggestion: "降低 Memory requests 到 {actual}*1.5"
      - id: "R3_cpu_under_requested"
        condition: "pod_cpu_usage_p95 > pod_cpu_requests * 0.8"
        severity: "warning"
        category: "CPU requests 不足"
        message: "Pod {pod} CPU 实际使用 ({actual}P95) 接近 requests ({req})"
        suggestion: "提高 CPU requests 以确保 QoS"
      - id: "R4_memory_under_requested"
        condition: "pod_memory_usage_p95 > pod_memory_requests * 0.8"
        severity: "warning"
        category: "Memory requests 不足"
        message: "Pod {pod} Memory 实际使用 ({actual}P95) 接近 requests ({req})"
        suggestion: "提高 Memory requests 以避免 OOM"

  - id: "analyze_limits_vs_usage"
    description: "对比 Pod limits 与实际使用量"
    rules:
      - id: "L1_memory_limits_low"
        condition: "pod_memory_limits < pod_memory_usage_max * 1.2"
        severity: "warning"
        category: "Memory limits 过低"
        message: "Pod {pod} Memory limits ({limit}) 接近实际最大使用 ({max})"
        suggestion: "提高 Memory limits 以避免 OOMKilled"
      - id: "L2_memory_limits_vs_xmx"
        condition: "Java 应用 AND pod_memory_limits < Xmx + 512MB"
        severity: "warning"
        category: "Java Memory limits 不足"
        message: "Pod {pod} Memory limits ({limit}) < JVM Xmx ({xmx}) + 堆外内存"
        suggestion: "设置 Memory limits >= Xmx + 512MB"
        ops_skill: "jdcloud-kubernetes-ops (通过 deployment 更新)"
      - id: "L3_cpu_limits_unset"
        condition: "pod_cpu_limits 未设置"
        severity: "info"
        category: "CPU limits 未设置"
        message: "Pod {pod} 未设置 CPU limits"
        suggestion: "设置合理的 CPU limits 以防止 CPU 饥饿"

  - id: "analyze_hpa_efficiency"
    description: "分析 HPA 配置效率"
    algorithm_details: |
      三个检测规则覆盖 HPA 全生命周期异常：
      - H1 检测"僵尸 HPA"（阈值虚高，从未工作）
      - H2 检测"抖动 HPA"（频繁扩缩容，影响稳定性）
      - H3 检测"瓶颈 HPA"（已达上限但仍需扩容）
    rules:
      - id: "H1_hpa_never_triggered"
        condition: "HPA 7 天内从未触发扩容 AND 实际指标 P95 < 阈值 * 0.3"
        severity: "info"
        category: "HPA 阈值过高（僵尸 HPA）"
        message: "HPA {name} 阈值 {threshold}% 远高于实际使用 {actual_p95}%（P95），从未触发扩容"
        suggestion: "降低 HPA 阈值到 {actual_p95 * 2}% 或考虑移除 HPA 以简化配置"
        algorithm: |
          输入: HPA 配置 (targetMetric, threshold), Pod 实际指标 7 天 P95 值
          输出: 是否阈值过高

          步骤:
            1. 取 HPA 的 targetMetric 对应的实际指标 7 天 P95 值 → actual_p95
            2. 取 HPA 的 threshold 值 → threshold
            3. 取 HPA 7 天内扩容事件次数 → scale_up_count

          判定:
            IF scale_up_count == 0 AND actual_p95 < threshold * 0.3 THEN
              → 触发告警

          为什么用 threshold * 0.3:
            - 如果实际使用量连阈值的 30% 都不到，说明阈值设得过高
            - 0.3 是经验值：低于此值意味着即使流量翻 3 倍也不会触发扩容
            - 安全余量过大 → HPA 形同虚设

          举例:
            | HPA 配置     | 实际 CPU P95 | threshold*0.3 | 判定        |
            |-------------|-------------|--------------|------------|
            | CPU > 80%   | 15%         | 24%          | ✅ 触发告警  |
            | CPU > 80%   | 60%         | 24%          | ❌ 正常     |
            | CPU > 50%   | 12%         | 15%          | ✅ 触发告警  |

      - id: "H2_hpa_flapping"
        condition: "HPA 7 天内扩缩容总次数 > 20 OR 1 小时内扩缩容 > 5 次"
        severity: "warning"
        category: "HPA 频繁抖动"
        message: "HPA {name} 7 天内扩缩容 {total} 次（最大 {max_per_hour} 次/h），存在抖动"
        suggestion: "增加 stabilizationWindowSeconds >= 300；检查阈值是否与实际使用过于接近"
        algorithm: |
          输入: HPA 7 天内所有扩缩容事件时间戳
          输出: 是否频繁抖动 + 根因诊断

          步骤:
            1. 统计 7 天内 scale_up + scale_down 总次数 → total_events
            2. 按 1 小时滑动窗口统计最大事件数 → max_per_hour

          判定:
            IF total_events > 20 THEN
              → "7 天内扩缩容 {total_events} 次，存在抖动"
            IF max_per_hour > 5 THEN
              → "1 小时内扩缩容 {max_per_hour} 次，严重抖动"

          根因诊断（附加逻辑）:
            a) 检查 stabilizationWindowSeconds:
               IF stabilizationWindowSeconds == 0 OR 未设置 THEN
                 → "缺少缩容稳定窗口，建议设置 >= 300"
            b) 检查阈值是否过于敏感:
               IF threshold - actual_p95 < 10% THEN
                 → "阈值 {threshold}% 与实际 P95 {actual_p95}% 过于接近，轻微波动即触发"
            c) 检查是否同时使用多个指标:
               IF len(metrics) > 1 THEN
                 → "多指标 HPA，检查是否有指标频繁交叉触发"

          举例:
            | 7天扩缩容 | 最大1h内 | 阈值vs实际P95 | 判定 + 根因              |
            |----------|---------|-------------|------------------------|
            | 35次     | 8次     | 70% vs 65%  | 🔴 严重抖动 + 阈值过敏感    |
            | 25次     | 3次     | 70% vs 30%  | 🟡 频繁抖动 + 缺稳定窗口    |
            | 10次     | 2次     | —           | ✅ 正常                  |

      - id: "H3_hpa_maxed_out"
        condition: "HPA 当前副本数 == maxReplicas AND 实际指标当前值 > 阈值"
        severity: "warning"
        category: "HPA 已达上限但仍需扩容"
        message: "HPA {name} 已达 maxReplicas ({max})，但指标 ({actual}%) 仍超阈值 ({threshold}%)"
        suggestion: "提高 maxReplicas 到 {max * 2} 或优化应用性能降低单 Pod 资源消耗"
        algorithm: |
          输入: HPA 配置 (maxReplicas), 当前副本数, 实际指标当前值
          输出: 是否需要提高 maxReplicas

          步骤:
            1. 取当前副本数 → current_replicas
            2. 取 maxReplicas → max_replicas
            3. 取实际指标当前值 → actual_current
            4. 取 HPA threshold → threshold

          判定:
            IF current_replicas == max_replicas AND actual_current > threshold THEN
              → 触发告警

          严重程度分级:
            IF actual_current > threshold * 1.5 THEN
              → critical: "严重超阈值，业务可能受损"
            ELSE
              → warning: "需要扩容但已达上限"

          举例:
            | maxReplicas | 当前副本 | 阈值  | 实际CPU | 判定          |
            |------------|---------|------|--------|--------------|
            | 10         | 10      | 70%  | 85%    | 🟡 warning    |
            | 10         | 10      | 70%  | 95%    | 🔴 critical   |
            | 10         | 6       | 70%  | 85%    | ✅ 正常（还能扩）|

  - id: "analyze_node_water_level"
    description: "分析节点资源水位"
    rules:
      - id: "N1_node_overloaded"
        condition: "node_cpu_requests_ratio > 80% OR node_memory_requests_ratio > 80%"
        severity: "warning"
        category: "节点资源紧张"
        message: "节点 {node} requests 占比 {ratio}%"
        suggestion: "扩容节点组或驱逐低优先级 Pod"
        ops_skill: "jdcloud-kubernetes-ops (modify-node-group)"
      - id: "N2_node_underutilized"
        condition: "node_cpu_requests_ratio < 20% AND node_memory_requests_ratio < 20%"
        severity: "info"
        category: "节点低利用"
        message: "节点 {node} requests 占比仅 {ratio}%"
        suggestion: "考虑缩容节点组或合并工作负载"
      - id: "N3_node_imbalance"
        condition: "节点间 CPU requests 标准差 > 平均值 * 0.5"
        severity: "info"
        category: "节点负载不均"
        message: "节点间 CPU requests 分布不均 (标准差={std})"
        suggestion: "检查 Pod 亲和性/反亲和性配置; 考虑使用 topologySpreadConstraints"

  - id: "analyze_idle_resources"
    description: "识别闲置资源"
    rules:
      - id: "I1_idle_namespace"
        condition: "namespace 7 天内无任何 Pod 运行"
        severity: "info"
        category: "闲置命名空间"
        message: "Namespace {ns} 7 天内无 Pod 运行"
        suggestion: "确认是否仍需要，考虑清理"
      - id: "I2_zero_replica"
        condition: "Deployment/StatefulSet replicas == 0 持续 > 7 天"
        severity: "info"
        category: "零副本工作负载"
        message: "{kind}/{name} 7 天内副本数为 0"
        suggestion: "确认是否仍需要，考虑删除以清理集群"

  - id: "generate_optimization_summary"
    description: "汇总优化建议并估算资源节省"
    output:
      - "可释放 CPU: {cpu_cores} 核"
      - "可释放内存: {memory_gb} GB"
      - "可减少节点数: {node_count} 台"
      - "预计月节省: ¥{saving}/月"
```

### Phase 3: 执行 — 优化建议生成（只读）

```yaml
steps:
  - id: "rank_recommendations"
    description: "按影响程度排序优化建议"
    ranking:
      priority: "资源节省量 > 风险等级 > 实施难度"
    output:
      - "P0: 立即执行（高节省 + 低风险 + 简单变更）"
      - "P1: 本周执行（中节省 + 低风险）"
      - "P2: 本月执行（低节省 或 需评估风险）"

  - id: "generate_action_plan"
    description: "为每个建议生成具体操作步骤"
    format: |
      1. 问题描述
      2. 当前值 vs 建议值
      3. 具体变更命令（kubectl / jdc）
      4. 回滚方案
      5. 验证方法

  - id: "output_report"
    description: "输出优化报告"
    outputs:
      - path: "reports/output/k8s-optimization-{customer}-{date}.md"
        format: "Markdown"
      - path: "reports/output/k8s-optimization-{customer}-{date}.json"
        format: "JSON"
```

---

## 3. 优化安全规则

| 规则 | 说明 |
|------|------|
| **requests 不低于实际 P95 的 50%** | 过低会导致 QoS 降级和 OOM 风险 |
| **requests 不高于实际 P95 的 300%** | 过高浪费可调度资源 |
| **Memory limits >= Xmx + 512MB** | Java 应用需要堆外内存余量 |
| **变更需在低峰期执行** | 建议在凌晨 2:00-5:00 |
| **每次变更只改一个 Deployment** | 逐步灰度，观察稳定性 |
| **变更前记录当前配置** | 便于回滚 |
| **HPA 阈值调整需观察 24h** | 确认不会导致频繁扩缩容 |

---

## 4. 告警联动

| 告警类型 | 触发条件 | 自动动作 |
|----------|----------|----------|
| CPU 过度预留 | requests > usage*5 | 创建 DOPS 优化建议工单 |
| Memory limits 不足 | limits < Xmx+512MB | 创建 DOPS 配置修复工单 |
| HPA 频繁抖动 | 7天 > 20次 | 创建 DOPS HPA 调整工单 |
| 节点资源紧张 | requests > 80% | 创建 DOPS 扩容工单 |

---

## 5. Changelog

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-06-10 | 初始版本，定义 K8s 资源配置优化完整流程 |
