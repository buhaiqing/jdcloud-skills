# MongoDB Index Advisor

## Goal

Generate conservative, explain-backed index recommendations for MongoDB slow queries. Never auto-create indexes.

## Input

- Normalized slow query records
- `explain("executionStats")`
- Existing indexes: `db.collection.getIndexes()`
- Collection stats and write rate
- Sort and projection fields

## Compound Index Ordering

Recommended order:

```text
equality filters → range filters → sort fields → projection cover fields
```

Example:

```javascript
// Query
find({ tenantId: "t1", status: "PAID", createdAt: { $gte: ISODate(...) } })
  .sort({ createdAt: -1 })

// Candidate
db.orders.createIndex({ tenantId: 1, status: 1, createdAt: -1 })
```

## Avoid Bad Recommendations

Do NOT recommend an index when:

- An equivalent or better prefix index already exists.
- The field has very low cardinality and no useful compound prefix.
- The query shape is rare and low total cost.
- The collection is write-heavy and expected benefit is unclear.
- `explain` is unavailable and evidence is insufficient; mark as hypothesis instead.

## Required Output

```json
{
  "index": "{tenantId:1,status:1,createdAt:-1}",
  "namespace": "order.orders",
  "query_shape": "...",
  "reason": ["COLLSCAN", "docsExamined/nReturned=12000", "sort on createdAt"],
  "expected_benefit": "reduce scanned docs and eliminate in-memory sort",
  "risk": "medium: index build may increase write latency",
  "requires_confirmation": true,
  "validation": "rerun explain and observe IXSCAN + lower docsExamined"
}
```

## Safety

Index creation is a production-impacting change. Recommendations must be executed only after human confirmation via `jdcloud-mongodb-ops`, preferably in a low-traffic window.
