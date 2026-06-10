---
runbook_id: "01"
scenario: "K8s 集群健康巡检"
version: "1.0.0"
last_updated: "2026-06-10"
trigger: "定时调度（每 6 小时）/ 人工触发"
risk_level: "低"
execution_time_estimate: "5-10 分钟（5 个集群以内）"
---

# K8s 集群健康巡检

## 1. 场景描述

对指定客户在京东云上的全部 K8s 集群进行日常健康检查，覆盖集群状态、节点健康、Pod 分布、Ingress 健康、安全态势等核心维度，输出健康评分和风险项。

### 背景

DOPS 实际案例（近 5 天）：
- DOPS-85665/85695：名创优品生产 k8s 集群巡检
- DOPS-85663/85708：海鼎生产青岛 k8s 集群巡检
- DOPS-85655：海鼎生产17 k8s 集群巡检
- DOPS-85650：联华华商阿里云生产 k8s 集群巡检

### 适用条件

- 集群资源已按 `客户` 标签归类（通过 `kubernetes.jdcloud.com/cluster_id` 标签关联 VM/CLB）
- JDC AK/SK 已配置且具有 K8s 读权限
- 支持的 JD Cloud 区域：cn-north-1, cn-east-2, cn-south-1, cn-east-1

---

## 2. 执行流程

### Phase 1: 感知 — 集群发现与基础信息采集（约 2 分钟）

```yaml
steps:
  - id: "list_clusters"
    description: "列出所有 K8s 集群"
    cli:
      command: >
        jdc --output json nc describe-clusters
        --region-id "{{user.region}}"
        --page-number 1 --page-size 100
      json_path: "$.result.clusters"
    sdk_fallback:
      api: "DescribeClusters"
      params: { regionId: "{{user.region}}", pageNumber: 1, pageSize: 100 }

  - id: "filter_by_customer"
    description: "按客户标签过滤集群"
    method: |
      1. 通过集群关联的 VM 标签 kubernetes.jdcloud.com/cluster_id 识别
      2. 检查 VM 的 客户 标签是否匹配目标客户
      3. 同时检查 CLB 的 kubernetes.jdcloud.com/created_by 标签

  - id: "collect_cluster_info"
    description: "采集每个集群的基础信息"
    fields:
      - "clusterId: 集群 ID"
      - "clusterName: 集群名称"
      - "state: 集群状态 (running/creating/deleting/error)"
      - "masterVersion: Kubernetes 版本"
      - "endpoint: API Server 地址"
      - "vpcId / subnetId: 网络信息"

  - id: "collect_node_groups"
    description: "列出每个集群的节点组"
    cli:
      command: >
        jdc --output json nc describe-node-groups
        --region-id "{{user.region}}"
        --cluster-id "{{cluster_id}}"
    fields:
      - "nodeGroupId: 节点组 ID"
      - "name: 节点组名称"
      - "state: 节点组状态"
      - "instanceType: 节点规格"
      - "nodeCount: 当前节点数"
      - "minCount / maxCount: 自动伸缩范围"

  - id: "collect_nodes"
    description: "通过标签关联获取集群节点 VM 列表"
    method: "查询带有 kubernetes.jdcloud.com/cluster_id={{cluster_id}} 标签的 VM"
    fields:
      - "instanceId: VM ID"
      - "instanceName: VM 名称"
      - "status: VM 状态"
      - "instanceType: 实例规格"
      - "privateIpAddress: 内网 IP"
```

### Phase 2: 推理 — 指标采集与分析（约 5-8 分钟）

```yaml
steps:
  - id: "check_cluster_status"
    description: "检查集群控制平面状态"
    rules:
      - condition: "state != 'running'"
        severity: "critical"
        message: "集群状态异常: {state}"
        action: "检查集群事件日志; 如长时间异常则联系京东云技术支持"
      - condition: "state == 'running'"
        severity: "info"
        message: "集群控制平面正常"

  - id: "check_version"
    description: "检查 Kubernetes 版本"
    rules:
      - condition: "masterVersion < '1.24'"
        severity: "warning"
        message: "Kubernetes 版本 {version} 已 EOL 或即将 EOL"
        action: "计划升级到 1.26+; 注意 API 弃用变更"
        ops_skill: "jdcloud-kubernetes-ops (modify-cluster)"
      - condition: "masterVersion < '1.26'"
        severity: "info"
        message: "Kubernetes 版本 {version}，建议升级到最新稳定版"

  - id: "check_node_health"
    description: "检查节点健康状态"
    rules:
      - condition: "存在 status != 'running' 的节点 VM"
        severity: "critical"
        message: "{count} 个节点状态异常"
        action: "检查节点 VM 状态; 如节点不可恢复则替换节点"
      - condition: "节点组 nodeCount < minCount"
        severity: "warning"
        message: "节点组 {name} 节点数 {count} 低于最小 {min}"
        action: "检查是否因资源不足导致扩容失败"
      - condition: "节点组 nodeCount == maxCount"
        severity: "info"
        message: "节点组 {name} 已达最大节点数 {max}"
        action: "如需继续扩容，调整 maxCount"

  - id: "check_node_distribution"
    description: "检查节点多 AZ 分布"
    rules:
      - condition: "所有节点在同一 AZ"
        severity: "warning"
        message: "所有节点集中在单个 AZ，存在单点故障风险"
        action: "建议在至少 2 个 AZ 部署节点组"
      - condition: "某 AZ 节点数 < 总节点数 * 20%"
        severity: "info"
        message: "AZ {az} 节点分布不均"
        action: "考虑调整节点组 AZ 分布"

  - id: "check_pod_distribution"
    description: "检查 Pod 分布与资源使用（通过 JD Cloud 监控或 kube-state-metrics）"
    metrics:
      - "kube_node_status_allocatable_cpu_cores"   # 节点可分配 CPU
      - "kube_node_status_allocatable_memory_bytes" # 节点可分配内存
      - "kube_pod_container_resource_requests"      # Pod CPU 请求
      - "kube_pod_container_resource_requests_memory_bytes" # Pod 内存请求
    rules:
      - condition: "节点 Pod 分配率 (requested/allocatable) > 80%"
        severity: "warning"
        message: "节点 {node} Pod 分配率 {rate}%，接近上限"
        action: "考虑扩容节点组或优化 Pod request"
        ops_skill: "jdcloud-kubernetes-ops (modify-node-group)"
      - condition: "节点 Pod 分配率 > 90%"
        severity: "critical"
        message: "节点 {node} Pod 分配率 {rate}%，新 Pod 可能无法调度"
        action: "立即扩容节点组"

  - id: "check_resource_requests_limits"
    description: "检查 Pod requests/limits 配置合理性"
    rules:
      - condition: "Pod 未设置 CPU requests"
        severity: "warning"
        message: "Pod {pod} 未设置 CPU requests，可能被 QoS 降级"
        action: "为所有 Pod 设置合理的 CPU/Memory requests"
      - condition: "Pod 未设置 Memory limits"
        severity: "warning"
        message: "Pod {pod} 未设置 Memory limits，可能 OOM 影响节点"
        action: "为所有 Pod 设置 Memory limits"
      - condition: "Pod Memory limits < Xmx (Java 应用)"
        severity: "warning"
        message: "Pod {pod} Memory limits ({limit}) < JVM Xmx ({xmx})"
        action: "调整 Memory limits >= Xmx + 512MB (堆外内存余量)"
        ops_skill: "jdcloud-kubernetes-ops (通过 deployment 更新)"

  - id: "check_hpa"
    description: "检查 HPA 配置合理性"
    rules:
      - condition: "HPA 存在但从未触发扩容"
        severity: "info"
        message: "HPA {name} 从未触发扩容，可能阈值设置过高"
        action: "检查 HPA 指标阈值是否合理"
      - condition: "HPA 频繁扩缩容（1h 内 > 5 次）"
        severity: "warning"
        message: "HPA {name} 频繁扩缩容（{count}次/h），存在抖动"
        action: "调整 HPA 阈值或增加 stabilizationWindowSeconds"
      - condition: "HPA 触发条件不合理（CPU > 50% 但实际 CPU < 10%）"
        severity: "warning"
        message: "HPA {name} 触发阈值 {threshold}% 远低于实际使用率 {actual}%"
        action: "调整 HPA 阈值到合理水平（如 CPU > 70%）"

  - id: "check_ingress_health"
    description: "检查 Ingress / CLB 健康状态"
    rules:
      - condition: "CLB 后端健康检查失败率 > 5%"
        severity: "warning"
        message: "Ingress CLB {name} 后端健康检查失败率 {rate}%"
        action: "检查后端 Pod 健康状态; 检查健康检查配置"
      - condition: "CLB 后端健康检查失败率 > 20%"
        severity: "critical"
        message: "Ingress CLB {name} 后端大量不健康"
        action: "立即检查后端服务状态"
      - condition: "CLB 无后端服务器"
        severity: "critical"
        message: "Ingress CLB {name} 无后端服务器"
        action: "检查 Service/Endpoints 配置"

  - id: "check_security"
    description: "安全检查"
    rules:
      - condition: "集群 API Server 公网可访问"
        severity: "warning"
        message: "集群 API Server 公网可访问"
        action: "建议配置 API Server 访问白名单或使用内网访问"
      - condition: "节点安全组允许 0.0.0.0/0 访问 10250 端口 (kubelet)"
        severity: "critical"
        message: "kubelet 端口对公网开放"
        action: "立即限制 kubelet 端口访问来源"
      - condition: "节点安全组允许 0.0.0.0/0 访问 22 端口"
        severity: "warning"
        message: "SSH 端口对公网开放"
        action: "限制 SSH 访问来源 IP"

  - id: "check_certificate"
    description: "检查 Ingress 证书有效期"
    rules:
      - condition: "TLS 证书有效期 < 30 天"
        severity: "warning"
        message: "Ingress {name} TLS 证书将在 {days} 天后过期"
        action: "更新 TLS 证书"
      - condition: "TLS 证书已过期"
        severity: "critical"
        message: "Ingress {name} TLS 证书已过期"
        action: "立即更新 TLS 证书"
```

### Phase 3: 执行 — 建议生成（只读）

```yaml
steps:
  - id: "generate_health_score"
    description: "计算每个集群的健康评分（0-100）"
    scoring:
      base: 100
      deductions:
        - "集群状态异常: -50"
        - "版本 EOL: -20"
        - "版本偏旧: -10"
        - "节点异常: -30"
        - "单 AZ 部署: -15"
        - "Pod 分配率 > 90%: -20"
        - "Pod 分配率 > 80%: -10"
        - "Pod 无 requests: -10"
        - "Pod 无 limits: -10"
        - "HPA 频繁抖动: -10"
        - "Ingress 后端不健康 > 20%: -20"
        - "kubelet 端口公网开放: -30"
        - "SSH 端口公网开放: -10"
        - "TLS 证书过期: -20"
        - "TLS 证书即将过期: -10"

  - id: "generate_suggestions"
    description: "按严重程度排序生成修复建议"
    output_format: "Markdown 表格"
    columns:
      - "优先级 (P0/P1/P2)"
      - "集群名称"
      - "问题描述"
      - "当前值"
      - "阈值"
      - "建议操作"
      - "委托 Skill"

  - id: "output_report"
    description: "输出巡检报告"
    outputs:
      - path: "reports/output/k8s-health-{customer}-{date}.md"
        format: "Markdown"
      - path: "reports/output/k8s-health-{customer}-{date}.json"
        format: "JSON"
```

---

## 3. 阈值定义

| 维度 | 指标 | Warning 阈值 | Critical 阈值 | 说明 |
|------|------|-------------|---------------|------|
| 集群 | 状态 | — | != running | 控制平面不可用 |
| 集群 | K8s 版本 | < 1.26 | < 1.24 | 旧版本缺少安全补丁 |
| 节点 | 状态 | — | != running | 节点不可用 |
| 节点 | Pod 分配率 | > 80% | > 90% | 新 Pod 无法调度 |
| 节点 | 多 AZ 分布 | 单 AZ | — | 单点故障风险 |
| Pod | CPU requests | 未设置 | — | QoS 降级风险 |
| Pod | Memory limits | 未设置 | — | OOM 影响节点 |
| Pod | Mem limits < Xmx | 存在 | — | Java OOMKilled |
| HPA | 频繁扩缩容 | > 5次/h | — | 抖动影响稳定性 |
| HPA | 阈值不合理 | 实际 < 阈值*0.3 | — | 浪费资源 |
| Ingress | 后端不健康率 | > 5% | > 20% | 流量中断 |
| 安全 | kubelet 公网 | — | 0.0.0.0/0 | 集群入侵风险 |
| 安全 | SSH 公网 | 0.0.0.0/0 | — | 暴力破解风险 |
| 证书 | TLS 过期 | < 30天 | 已过期 | HTTPS 不可用 |

---

## 4. 告警联动

| 告警类型 | 触发条件 | 自动动作 | 委托 Skill |
|----------|----------|----------|------------|
| 集群状态异常 | state != running | 创建 DOPS 工单 | 人工排查 |
| 节点 Pod 分配率过高 | > 90% | 创建 DOPS 扩容工单 | `jdcloud-kubernetes-ops` (modify-node-group) |
| kubelet 端口公网开放 | 0.0.0.0/0 | 创建 DOPS 安全工单 | `jdcloud-vpc-ops` (安全组) |
| TLS 证书过期 | 已过期 | 创建 DOPS 证书更新工单 | 人工更新 |

---

## 5. 闭环改进

| 反馈来源 | 触发条件 | 改进动作 | 责任人 |
|----------|----------|----------|--------|
| 误报 | Pod 分配率告警但实际正常 | 调整阈值或增加白名单 | 运维负责人 |
| 漏报 | 集群异常但未检测到 | 增加检查维度 | 运维负责人 |
| 新版本 | K8s 新版本发布 | 更新版本 EOL 阈值 | 脚本维护者 |

---

## 6. Changelog

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-06-10 | 初始版本，定义 K8s 集群健康巡检完整流程 |
