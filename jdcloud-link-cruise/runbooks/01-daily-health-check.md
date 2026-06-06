---
runbook_id: "01"
scenario: "日常健康巡检"
version: "1.0.0"
last_updated: "2026-06-06"
trigger: "定时调度（每 6 小时）/ 人工触发"
risk_level: "低"
execution_time_estimate: "10-15 分钟（50 台资源以内）"
---

# 日常健康巡检

## 1. 场景描述

对指定客户（通过 `客户` 标签识别）在京东云上的全部资源进行全链路健康检查，涵盖入口层（EIP/WAF）、分发层（CLB）、计算层（VM/K8s）、数据层（Redis/RDS/ES/MongoDB/...）和出网层（NAT），输出统一的健康评分和风险项。

### 适用条件

- 资源已按 `客户` 标签归类（如 `客户=烟台振华`）
- JDC AK/SK 已配置且具有相关产品线的读权限
- 支持的 JD Cloud 区域：cn-north-1, cn-east-2, cn-south-1, cn-east-1

### 不适用条件

- 资源未打标签 → 需先执行人工确认流程
- 涉及跨账号资源 → 不支持

---

## 2. 执行流程

### Phase 1: 嗅探 + 拓扑初判（约 2-3 分钟）

```yaml
steps:
  - id: "discover_resources"
    description: "扫描指定客户标签下的全部资源（EIP/CLB/VM/REDIS/NAT/K8s/云硬盘/安全组）"
    api_calls:
      - "vm describe-instances"
      - "lb describe-load-balancers"
      - "redis describe-cache-instances"
      - "vpc describe-vpcs"
      - "vpc describe-subnets"
      - "vpc describe-security-groups"
      - "kubernetes describe-clusters"    # SDK 兼容则查，否则跳过
      - "eip describe-elastic-ips"        # 视 CLI 命令名调整
      - "nat describe-nat-gateways"       # 视产品名调整
    region: "自动探测（从已有资源推断）"

  - id: "classify_deployment"
    description: "根据标签对每个资源进行部署模式分类（K8s / 传统 / 未知）"
    confidence_rules:
      - condition: "VM.tags contains 'kubernetes.jdcloud.com/cluster_id'"
        mode: "k8s"
        confidence: 0.95
      - condition: "CLB.tags contains 'kubernetes.jdcloud.com/created_by'"
        mode: "k8s_ingress"
        confidence: 0.95
      - condition: "VM.tags contains '客户' AND no K8s tags"
        mode: "traditional"
        confidence: 0.85
      - condition: "VM has name prefix matching customer name"
        mode: "traditional"
        confidence: 0.60
      - condition: "no identifying tags at all"
        mode: "unknown"
        confidence: 0.30

  - id: "build_topology"
    description: "构建完整拓扑图（VPC → 子网 → 资源分布 → 链路关联）"
    outputs:
      - "VPC 及其子网结构"
      - "子网 → 资源分布"
      - "CLB target group → 后端 VM"
      - "K8s 集群 → 节点 VM → CLB Ingress"
      - "EIP → 关联资源"
      - "安全组允许规则 → 流量路径推断"
      - "未归属资源清单（待确认）"

  - id: "human_confirm"
    description: "如有置信度 ≤ 0.8 的资源，生成待确认清单等待人工复核"
    auto_proceed_threshold: 0.8
    max_wait: "24h（超时则使用最佳推断结果，标记为 LOW_CONFIDENCE）"
```

### Phase 2: 深度巡检（约 8-12 分钟）

```yaml
steps:
  - id: "collect_metrics"
    description: "采集每个资源最近 6 小时的监控指标（5 分钟粒度）"
    time_windows:
      current: "最近 6 小时"
      daily_baseline: "昨日同期（T-24h ~ T-18h）"
      weekly_baseline: "上周同期（T-7d ~ T-7d+6h）"
    metrics_by_service:
      vm:
        - "cpu_util"                    # CPU 使用率
        - "memory.usage"                # 内存使用率
        - "vm.disk.dev.io.read"         # 磁盘读 IOPS
        - "vm.disk.dev.io.write"        # 磁盘写 IOPS
        - "vm.disk.dev.used"            # 磁盘使用率
        - "vm.avg.load1/5/15"           # 系统负载
        - "vm.network.dev.bytes.in/out" # 网络带宽
        - "vm.netstat.tcp.established"  # TCP 连接数
      - "vm.disk.encrypted"            # 云盘加密状态（从实例信息获取）
      clb:
        - "lb.backend.healthy.host_count"
        - "lb.new_connection_count"
        - "lb.active_connection_count"
      redis:
        - "redis.cpu.util"
        - "redis.memory.usage"
        - "redis.hit_rate"
        - "redis.connections"
      eip:
        - "eip.bandwidth.in/out"
      es:
        - "cpu_util"
        - "memory.usage"
        - "vm.disk.dev.used"
      nat:
        - "nat.connections"
        - "nat.bandwidth.in/out"

  - id: "query_alarm_history"
    description: "查询同时间段内各资源的告警历史，用于交叉验证"

  - id: "check_spec_limits"
    description: "将采集到的指标与实例规格上限进行对比，输出资源水位百分比"
    resources:
      - "VM instance type → 网络带宽/PPS/连接数上限"
      - "云盘类型/大小 → 最大 IOPS/吞吐量上限"
      - "CLB 规格 → 最大连接数"
      - "Redis 规格 → 最大内存/连接数"
      - "NAT 规格 → 最大 SNAT 连接数"

  - id: "analyze_each_service"
    description: "按部署模式分派各 Analyzer 执行分析"
    analyzers:
      - "eip_analyzer"
      - "clb_analyzer"
      - "vm_analyzer"
      - "redis_analyzer"
      - "nat_analyzer"
      - "k8s_analyzer"       # 仅在检测到 K8s 时启用
      - "sg_analyzer"

  - id: "correlate_chain"
    description: "链路关联推理：组合多个 Analyzer 的结果定位根因"
    inference_rules:
      - pattern: "CLB 健康检查失败率 > 10% AND VM 状态正常"
        suggest: "查 CLB→VM 网络连通性（安全组规则/子网ACL）"
      - pattern: "VM CPU > 70% AND 内存 > 80%"
        suggest: "查 VM 进程资源占用，考虑升配或拆分服务"
      - pattern: "Redis 命中率 < 90% AND VM CPU 正常"
        suggest: "查 Redis 热 key / 大 key，考虑本地缓存"
      - pattern: "VM IOPS 接近规格上限 AND 磁盘延迟高"
        suggest: "查慢查询，考虑升配云盘或优化查询"
      - pattern: "网络带宽接近规格上限 AND 用户报慢"
        suggest: "查流量来源，考虑升配实例或限流"
      - pattern: "NAT SNAT 连接数 > 80% 规格上限"
        suggest: "查是否存在端口耗尽，考虑增加 NAT 网关规格"
      - pattern: "K8s 节点 Pod 分配率 > 80%"
        suggest: "考虑扩容节点组或优化 Pod request"
      - pattern: "安全规则允许 0.0.0.0/0 访问 DB 端口"
        suggest: "高危配置，建议限制来源 IP"

  - id: "predict_capacity"
    description: "基于趋势线预测资源耗尽时间"
    prediction_horizon: "30 天"
    metrics_for_prediction:
      - "vm.disk.dev.used （磁盘满预测）"
      - "memory.usage （内存耗尽预测）"
      - "redis.memory.usage （Redis OOM 预测）"

  - id: "generate_report"
    description: "输出双格式报告"
    outputs:
      - path: "reports/output/sniff-{customer}-{date}.json"
        format: "JSON（Phase 1 结果 / 拓扑初判）"
      - path: "reports/output/cruise-{customer}-{date}.json"
        format: "JSON（Phase 2 完整报告）"
      - path: "stdout"
        format: "Markdown（给人读的摘要报告）"
```

---

## 3. 阈值定义

> 完整阈值表见 `references/threshold-definitions.md`
> 以下为摘要值。

| 服务 | 指标 | Warning 阈值 | Critical 阈值 |
|---|---|---|---|
| VM | CPU 使用率 | > 70% | > 85% |
| VM | 内存使用率 | > 80% | > 90% |
| VM | 磁盘使用率 | > 75% | > 90% |
| VM | 系统负载（5min / vCPU 数） | > 4.0 | > 6.0 |
| VM | 网络带宽 / 规格上限 | > 60% | > 80% |
| VM | IOPS / 规格上限 | > 70% | > 85% |
| CLB | 后端健康检查失败率 | > 5% | > 20% |
| CLB | 并发连接 / 规格上限 | > 60% | > 80% |
| Redis | 内存使用率 | > 75% | > 85% |
| Redis | 命中率 | < 90% | < 80% |
| Redis | CPU 使用率 | > 70% | > 85% |
| EIP | 带宽使用 / 规格上限 | > 60% | > 80% |
| NAT | SNAT 连接 / 规格上限 | > 70% | > 85% |
| K8s | 节点 Pod 分配率 | > 75% | > 90% |
| 安全组 | 0.0.0.0/0 开放 DB/管理端口 | — | 存在即 Critical |
| VM | 云盘加密状态 | 未加密 → Warning | — |
| VM | 系统盘未加密 | 未加密 → Info | — |

---

## 4. 闭环改进

| 反馈来源 | 触发条件 | 改进动作 | 责任人 |
|---|---|---|---|
| 人工审阅报告 | 发现误报 / 漏报 | 更新阈值定义 + 更新 runbook 版本 | 运维负责人 |
| 巡检执行失败 | API 返回异常 / 超时 | 更新 `jdc_client.py` 兼容逻辑 | 脚本维护者 |
| 新资源类型接入 | 客户新增服务 | 新增 Analyzer + 更新 runbook 步骤 | 脚本维护者 |
| 业务架构变更 | VM 迁移到 K8s | 更新置信度规则 + 测试 | 脚本维护者 |

---

## 5. Changelog

| 版本 | 日期 | 变更内容 |
|---|---|---|
| 1.0.0 | 2026-06-06 | 初始版本，定义日常健康巡检完整流程 |