---
runbook_id: "04"
scenario: "MongoDB 慢查询与索引审计"
version: "1.0.0"
last_updated: "2026-06-12"
trigger: "慢查询告警 / 人工触发 / 每日巡检"
risk_level: "中"
execution_time_estimate: "10-30 分钟"
---

# MongoDB 慢查询与索引审计

## 1. 目标

将慢查询从“日志列表”升级为结构化 AIOps 诊断：按 query shape 聚合、识别缺索引/低效索引、生成可验证的索引建议。

## 2. Perceive

```yaml
collect:
  - slow query logs: 最近 1-24 小时 TopN
  - explain executionStats: 对 Top query shape 抽样执行
  - indexes: db.collection.getIndexes()
  - collection stats: db.collection.stats()
```

结构化字段：

```json
{
  "namespace": "db.collection",
  "operation": "find|aggregate|update|delete|count",
  "duration_ms": 0,
  "plan_summary": "COLLSCAN|IXSCAN|FETCH|SORT",
  "keys_examined": 0,
  "docs_examined": 0,
  "n_returned": 0,
  "query_shape": "{ tenantId: ?, status: ?, createdAt: { $gte: ? } }",
  "sort_shape": "{ createdAt: -1 }"
}
```

## 3. Reason

| 模式 | 判断 | 建议 |
|---|---|---|
| COLLSCAN | `plan_summary=COLLSCAN` | 为高选择性过滤字段建索引 |
| 低效扫描 | `docs_examined / n_returned > 1000` | 优化过滤条件和复合索引顺序 |
| 无索引排序 | `SORT` 且无匹配排序索引 | 将排序字段纳入复合索引 |
| 聚合过重 | `$lookup/$group/$sort` 输入大 | `$match` 前置、缩小数据集 |
| 批量无过滤 | updateMany/deleteMany 过滤为空 | Safety=0，禁止执行 |

## 4. Index Advisor 规则

```text
复合索引顺序：等值过滤字段 → 范围字段 → 排序字段 → 投影覆盖字段
避免建议：
- 已有前缀等价索引
- 低基数字段单列索引
- 写入高峰期新增大索引
- 未验证 explain 的盲目建索引
```

## 5. Execute

只输出建议，不自动建索引：

```javascript
// 建议，需人工确认并低峰执行
db.order.createIndex({ tenantId: 1, status: 1, createdAt: -1 })
```

每条索引建议必须附带：

- 对应 query shape
- explain 前证据
- 预计收益
- 风险说明
- 回滚/删除索引建议
