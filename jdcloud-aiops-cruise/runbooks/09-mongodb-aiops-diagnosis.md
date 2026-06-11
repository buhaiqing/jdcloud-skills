---
runbook_id: "09"
scenario: "MongoDB AIOps 诊断"
version: "1.0.0"
last_updated: "2026-06-12"
trigger: "定时 / 告警 / 人工触发"
risk_level: "中"
execution_time_estimate: "5-20 分钟"
---

# MongoDB AIOps 诊断

## 1. 目标

将 MongoDB 纳入 `jdcloud-aiops-cruise` 全链路巡检，支持实例健康、性能故障、容量风险、慢查询/索引、复制延迟的根因候选输出。

## 2. Perceive

- 从拓扑 `raw.mongodb` / `raw.mongo` 读取 MongoDB 实例。
- 按 `客户={{user.customer}}` 标签过滤。
- 查询 CloudMonitor 指标：CPU、内存、磁盘、IOPS、连接、吞吐、延迟、复制延迟、oplog window。
- 可选关联：审计事件、应用日志、告警历史、慢查询结构化结果。

## 3. Reason

由 `scripts/02-reason/analyzers/mongodb_analyzer.py` 执行：

| 问题 | 推理 |
|---|---|
| 高 CPU | 区分低效查询、流量突增、IOPS 压力 |
| 高延迟 | 关联 slow query、query_rate、IOPS |
| 连接风暴 | 连接使用率与 opcounters 联合判断 |
| 磁盘风险 | 当前水位 + 增长趋势 |
| 复制延迟 | repl_lag + write rate + IOPS + oplog window |

## 4. Execute

本 runbook 只输出建议：

- MongoDB 变更建议 → `jdcloud-mongodb-ops`
- 监控/告警 → `jdcloud-cloudmonitor-ops`
- 网络/安全组 → `jdcloud-vpc-ops`
- 变更事件 → `jdcloud-audit-ops`

任何建索引、扩容、恢复、删除、参数调整均需人工确认。

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-12 | Added MongoDB AIOps cruise runbook. |
