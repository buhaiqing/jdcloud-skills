# MongoDB Root Cause Pattern Library

| Pattern | Signals | Root cause | First action |
|---|---|---|---|
| High CPU + high latency + stable QPS | CPU > 85%, latency > 200ms, query_rate not rising | Missing index / inefficient query | Pull slow queries and explain Top query shapes |
| High CPU + QPS spike | CPU > 85%, query/update/insert rising | Traffic surge or application release | Correlate with release/audit events |
| High IOPS + latency | IOPS rising, read/write latency rising | Disk bottleneck or large scan | Check COLLSCAN, backup/import jobs |
| High connections + stable QPS | connection_usage > 85%, opcounters stable | Connection leak or short connection storm | Aggregate client IP and inspect pool settings |
| High memory + slow aggregate | memory > 85%, aggregate/sort slow | Working set exceeds memory or memory sort | Add indexes, reduce aggregation input, scale if needed |
| Disk growth | disk > 80% or growth > 10pp/7d | Data growth, TTL missing, index bloat | Identify top-growing collections and TTL policy |
| Replica lag + write spike | repl_lag > 10s, write rates rising | Secondary cannot keep up | Reduce batch writes, scale, tune read preference |
| Replica lag + IOPS high | repl_lag > 10s, IOPS high | Disk bottleneck on secondary | Optimize queries/indexes or storage class |
| Low oplog window | oplog_window < 24h | Recovery window too small | Evaluate oplog capacity and write growth |
| Backup failure + disk high | backup failure, disk > 90% | Space pressure or task conflict | Expand storage or clear capacity risk first |

## Severity Defaults

- Critical: data availability risk, disk > 90%, repl_lag > 60s, connection_usage > 85%, service not running.
- Warning: performance degradation or capacity risk requiring planned action.
- Info: trend or best-practice recommendation.

## Evidence Rule

A root cause with confidence >= 0.8 SHOULD include at least three independent evidence items. If evidence is missing, downgrade confidence and mark `evidence_gap`.
