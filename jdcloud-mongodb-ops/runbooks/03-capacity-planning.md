---
runbook_id: "03"
scenario: "MongoDB 容量规划"
version: "1.0.0"
last_updated: "2026-06-12"
trigger: "每日 / 每周定时"
risk_level: "中"
execution_time_estimate: "5-10 分钟"
---

# MongoDB 容量规划

## 1. 目标

预测 MongoDB 实例未来容量风险，提前发现磁盘、连接、CPU、内存和 oplog window 风险。

## 2. Perceive

```yaml
window:
  short: 最近 24 小时
  baseline: 最近 7 天同周期
  capacity: 最近 14-30 天
metrics:
  - mongodb_disk_usage
  - mongodb_memory_usage
  - mongodb_cpu_utilization
  - mongodb_connections_usage
  - mongodb_oplog_window
  - mongodb_insert_rate
  - mongodb_update_rate
```

可选 DB 内部采集：

```javascript
db.stats()
db.getCollectionNames().map(c => db[c].stats())
db.getCollectionInfos({ "options.expireAfterSeconds": { $exists: true } })
```

## 3. Reason

| 检查项 | Warning | Critical | 建议 |
|---|---:|---:|---|
| 磁盘当前使用率 | > 80% | > 90% | 扩容/清理历史集合 |
| 磁盘 7d 增长 | > 10pp | > 20pp | 定位增长集合 |
| 预计到 90% 剩余天数 | < 30 天 | < 7 天 | 排期扩容或清理 |
| 连接 P95 使用率 | > 70% | > 85% | 调整连接池或升配 |
| Oplog window | < 24h | < 6h | 评估 oplog 容量和写入量 |

## 4. 输出示例

```json
{
  "capacity_risks": [
    {
      "resource": "mongo-xxx",
      "metric": "disk_usage",
      "current": 82.1,
      "growth_7d_pp": 12.4,
      "days_to_90": 6.3,
      "severity": "critical",
      "action": "7 天内扩容或清理增长最快集合"
    }
  ]
}
```

## 5. Execute

- 扩容：委派 `jdcloud-mongodb-ops`，人工确认。
- 告警：委派 `jdcloud-cloudmonitor-ops`。
- 数据清理：必须由业务确认保留策略，禁止自动删除。
