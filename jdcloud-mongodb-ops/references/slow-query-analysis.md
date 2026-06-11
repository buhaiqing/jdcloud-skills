# MongoDB Slow Query Analysis

## Structured Fields

Every slow query record should be normalized into:

| Field | Meaning |
|---|---|
| namespace | `db.collection` |
| operation | find / aggregate / update / delete / count / command |
| duration_ms | execution time |
| plan_summary | COLLSCAN / IXSCAN / FETCH / SORT |
| keys_examined | index keys scanned |
| docs_examined | documents scanned |
| n_returned | returned documents |
| query_shape | literals removed query pattern |
| sort_shape | sort pattern |
| app_name / client | source if available |

## Aggregations

Rank by:

1. Total time = `count * avg(duration_ms)`
2. P95 duration
3. `docs_examined / max(n_returned, 1)`
4. Frequency
5. Collection impact

## Diagnosis Rules

| Rule | Condition | Finding |
|---|---|---|
| Collection scan | `plan_summary=COLLSCAN` | Missing or unusable index |
| Inefficient scan | `docs_examined/n_returned > 1000` | Low-selectivity query or wrong compound index |
| In-memory sort | plan contains `SORT` without matching index | Add sort field to compound index |
| Heavy aggregation | `$lookup/$group/$sort` before selective `$match` | Move `$match` earlier and reduce input |
| Unsafe bulk write | updateMany/deleteMany empty filter | Safety fail; require explicit confirmation |

## Output Example

```json
{
  "query_shape": "{tenantId:?, status:?, createdAt:{$gte:?}}",
  "namespace": "order.orders",
  "count": 128,
  "p95_ms": 1800,
  "plan_summary": "COLLSCAN",
  "docs_examined_per_returned": 12000,
  "root_cause": "缺少复合索引",
  "suggested_next_step": "执行 explain 并评估 {tenantId:1,status:1,createdAt:-1}"
}
```
