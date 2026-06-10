---
runbook_index: true
version: "1.0.0"
last_updated: "2026-06-10"
---

# jdcloud-kubernetes-ops 巡检 Runbook 索引

## Runbook 列表

| ID | Runbook | 场景 | 触发方式 | 风险等级 | 预估耗时 |
|----|---------|------|----------|----------|----------|
| 01 | [集群健康巡检](01-cluster-health-check.md) | 日常 K8s 集群健康检查 | 定时（每 6h）/ 人工 | 低 | 5-10 分钟 |
| 02 | [资源配置优化](02-resource-optimization.md) | CPU/Mem requests 对齐、HPA 合理性、资源浪费 | 每周 / 人工 | 中 | 10-15 分钟 |

## 与 jdcloud-aiops-cruise 的关系

- `jdcloud-aiops-cruise` 的 `k8s_analyzer.py` 负责**拓扑发现**和**基础状态检查**（集群状态、节点数、版本）
- 本 skill 的 runbook 负责**深度巡检**（Pod 资源使用、HPA 配置、requests/limits 对齐、节点水位）
- 两个 skill 通过 `metadata.dependencies` 声明关联，Agent 应优先使用本 skill 的 runbook 做深度检查

## 执行约定

- 所有 runbook 遵循 **Perceive → Reason → Execute** 三阶段模型
- Execute 阶段只生成**建议**，不直接执行变更
- 变更操作通过 `jdcloud-kubernetes-ops` 的 Execution Flows 执行
- 跨产品问题通过 Cross-Skill Delegation 路由到对应 skill

## Changelog

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-10 | 初始版本，包含集群健康巡检和资源配置优化两个 runbook |
