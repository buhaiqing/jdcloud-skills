---
runbook_id: "02"
scenario: "MongoDB 性能故障定位"
version: "1.0.0"
last_updated: "2026-06-12"
trigger: "告警触发 / 用户报障"
risk_level: "中"
execution_time_estimate: "5-15 分钟"
---

# MongoDB 性能故障定位

## 1. 适用症状

- CPU 高、内存高、磁盘 IOPS 高
- 读/写/命令延迟升高
- 应用超时、连接池耗尽
- QPS 突增或吞吐下降

## 2. Perceive

```yaml
collect:
  - instance snapshot: status, class, storage, version, topology
  - metrics: cpu, memory, disk, iops, connections, opcounters, latency, repl_lag
  - slow query: slowms window 内 TopN
  - current operations: db.currentOp({active:true})
  - change events: 问题窗口前后 2 小时的发布/变更/审计事件
  - application logs: timeout / connection reset / pool exhausted
```

## 3. Reason

| 证据组合 | 根因候选 | 置信度起点 |
|---|---|---:|
| CPU 高 + latency 高 + QPS 平稳 | 缺索引 / COLLSCAN / 大聚合 | 0.75 |
| CPU 高 + QPS 同步激增 | 流量突增 / 应用发布读写放大 | 0.70 |
| IOPS 高 + latency 高 | 磁盘瓶颈 / 批量扫描 / 备份干扰 | 0.70 |
| connections 高 + QPS 平稳 | 连接泄漏 / 短连接风暴 | 0.80 |
| memory 高 + aggregate/sort 慢 | working set 过大 / 内存排序 | 0.65 |
| repl_lag 高 + write_rate 高 | Secondary 追写不足 | 0.75 |

## 4. Root Cause Ranking

```text
confidence = 指标吻合度 * 0.4
           + 慢查询/currentOp 证据 * 0.3
           + 时间相关性 * 0.2
           + 变更事件相关性 * 0.1
```

## 5. Execute 建议

- 缺索引：生成索引建议，先 explain 验证，再低峰执行。
- 流量突增：关联应用发布，建议限流、回滚或扩容。
- 连接风暴：调整连接池，排查短连接和泄漏。
- IOPS 瓶颈：优化查询和索引，必要时评估存储/规格升级。

所有建议均只读输出，变更委派 `jdcloud-mongodb-ops` 并人工确认。
