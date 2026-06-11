---
runbook_id: "05"
scenario: "MongoDB 复制延迟定位"
version: "1.0.0"
last_updated: "2026-06-12"
trigger: "mongodb_repl_lag 告警 / 人工触发"
risk_level: "中"
execution_time_estimate: "5-15 分钟"
---

# MongoDB 复制延迟定位

## 1. 目标

定位副本集复制延迟根因，区分写入峰值、Secondary 读压力、磁盘 I/O、网络抖动、oplog window 不足等场景。

## 2. Perceive

```yaml
metrics:
  - mongodb_repl_lag
  - mongodb_oplog_window
  - mongodb_insert_rate
  - mongodb_update_rate
  - mongodb_delete_rate
  - mongodb_iops
  - mongodb_read_latency
  - mongodb_write_latency
optional_db_commands:
  - rs.status()
  - rs.printSlaveReplicationInfo()
  - db.currentOp({ active: true })
```

## 3. Reason

| 证据 | 根因候选 | 建议 |
|---|---|---|
| repl_lag 高 + write_rate 高 | 写入峰值导致 Secondary 追写不足 | 降低批量写入、扩容、错峰导入 |
| repl_lag 高 + Secondary 读高 | 从库读压力影响复制 | 调整 readPreference / 降低从库查询 |
| repl_lag 高 + IOPS 高 | 磁盘瓶颈 | 优化查询/索引或评估存储规格 |
| oplog_window < 6h | 恢复窗口严重不足 | 评估 oplog 容量和写入量 |
| 单节点异常 | 节点故障或网络抖动 | 收集节点状态，联系云厂商支持 |

## 4. Severity

| 条件 | 级别 |
|---|---|
| repl_lag > 60s 持续 3 个采样点 | critical |
| repl_lag > 10s | warning |
| oplog_window < 6h | critical |
| oplog_window < 24h | warning |

## 5. Execute

- 调整读写策略、扩容、参数变更均需人工确认。
- 若涉及节点异常或数据一致性风险，输出支持工单所需信息：实例 ID、区域、时间窗口、requestId、指标截图/数据。
