---
runbook_index: true
version: "1.0.0"
last_updated: "2026-06-10"
---

# jdcloud-disk-ops 巡检 Runbook 索引

## Runbook 列表

| ID | Runbook | 场景 | 触发方式 | 风险等级 | 预估耗时 |
|----|---------|------|----------|----------|----------|
| 01 | [日常健康巡检](01-daily-health-check.md) | 磁盘状态、使用率、IOPS、加密、快照 | 定时（每 6h）/ 人工 | 低 | 3-5 分钟 |
| 02 | [容量预测与规划](02-capacity-planning.md) | 磁盘满预测、IOPS 趋势、成本优化 | 每周 / 人工 | 中 | 5-10 分钟 |

## 与 jdcloud-aiops-cruise 的关系

- `jdcloud-aiops-cruise` 的 `vm_analyzer.py` 负责**拓扑发现**和**基础磁盘使用率检查**
- 本 skill 的 runbook 负责**深度巡检**（磁盘满预测、IOPS/吞吐量趋势、快照策略、加密合规、闲置磁盘清理）
- 两个 skill 通过 `metadata.dependencies` 声明关联，Agent 应优先使用本 skill 的 runbook 做深度检查

## 执行约定

- 所有 runbook 遵循 **Perceive → Reason → Execute** 三阶段模型
- Execute 阶段只生成**建议**，不直接执行变更
- 变更操作通过 `jdcloud-disk-ops` 的 Execution Flows 执行
- 跨产品问题通过 Cross-Skill Delegation 路由到对应 skill

## Changelog

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-10 | 初始版本，包含日常健康巡检和容量预测与规划两个 runbook |
