---
runbook_id: "00"
scenario: "MongoDB AIOps Runbook Index"
version: "1.0.0"
last_updated: "2026-06-12"
risk_level: "低"
---

# MongoDB AIOps Runbook Index

本目录定义 `jdcloud-mongodb-ops` 的 AIOps 诊断场景。所有场景遵循 **Perceive → Reason → Execute** 三阶段模型：

| 阶段 | 目标 | 输出 |
|---|---|---|
| Perceive | 采集实例、监控、慢查询、连接、备份、复制、容量数据 | 标准化观测快照 |
| Reason | 多信号关联、异常检测、根因候选排序 | 根因列表、证据、置信度 |
| Execute | 生成只读建议和委派路径 | 人工确认后的修复计划 |

> 安全边界：本 runbook 只做只读诊断。扩容、索引创建、白名单/安全组变更、恢复、删除等操作必须委派给对应 ops skill 并经过人工确认。

## 场景列表

| 编号 | 场景 | 触发方式 | 典型问题 |
|---|---|---|---|
| 01 | [日常健康巡检](01-daily-health-check.md) | 定时 / 人工 | CPU、内存、磁盘、连接、延迟、复制延迟 |
| 02 | [性能故障定位](02-performance-troubleshoot.md) | 告警 / 报障 | 高 CPU、高延迟、连接风暴、IOPS 瓶颈 |
| 03 | [容量规划](03-capacity-planning.md) | 每日 / 每周 | 磁盘剩余天数、连接峰值、资源水位 |
| 04 | [慢查询与索引审计](04-slow-query-index-audit.md) | 慢查询告警 / 人工 | COLLSCAN、无索引 SORT、低效聚合 |
| 05 | [复制延迟定位](05-replica-lag-troubleshoot.md) | repl lag 告警 | 写入峰值、Secondary 读压力、oplog window 过小 |

## 标准输出

每个 runbook 应输出：

```json
{
  "health_score": 0,
  "severity": "ok|info|warning|critical",
  "symptoms": [],
  "root_causes": [
    {
      "cause": "string",
      "confidence": 0.0,
      "evidence": [],
      "recommended_actions": [],
      "delegate_to": "jdcloud-mongodb-ops|jdcloud-cloudmonitor-ops|jdcloud-vpc-ops|jdcloud-aiops-cruise"
    }
  ]
}
```

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-12 | Added MongoDB AIOps runbook index. |
