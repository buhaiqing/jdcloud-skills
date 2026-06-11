# MongoDB AIOps Diagnosis Reference

## 1. Diagnosis Model

MongoDB AIOps diagnosis follows **Perceive → Reason → Execute**:

1. **Perceive**: collect instance snapshot, CloudMonitor metrics, slow query logs, DB internal signals, backup state, and change/audit events.
2. **Reason**: correlate signals by time window, match root-cause patterns, rank candidates by confidence.
3. **Execute**: produce read-only recommendations and delegate mutations to the proper ops skill with human confirmation.

## 2. Root Cause Confidence

```text
confidence = metric_match * 0.4
           + db_evidence * 0.3
           + time_correlation * 0.2
           + change_correlation * 0.1
```

| Component | Evidence examples |
|---|---|
| metric_match | CPU, memory, disk, IOPS, latency, connections, repl_lag |
| db_evidence | slow query, currentOp, explain, index list, collection stats |
| time_correlation | symptom start time aligns with metric inflection |
| change_correlation | app release, parameter change, restore, backup, network/security change |

## 3. Standard Root Cause Output

```json
{
  "cause": "缺少索引导致 COLLSCAN",
  "confidence": 0.86,
  "severity": "warning",
  "evidence": [
    "CPU max 88%",
    "read latency max 430ms",
    "slow query planSummary=COLLSCAN",
    "docsExamined/nReturned > 10000"
  ],
  "recommended_actions": [
    "对 Top query shape 执行 explain",
    "低峰期创建复合索引",
    "观察 CPU/read_latency 30 分钟"
  ],
  "delegate_to": "jdcloud-mongodb-ops",
  "requires_confirmation": true
}
```

## 4. Cross-Skill Correlation

| Need | Delegate |
|---|---|
| CloudMonitor metrics / alarms | `jdcloud-cloudmonitor-ops` |
| Audit/change event lookup | `jdcloud-audit-ops` |
| Alert grouping and suppression | `jdcloud-alert-intelligence` |
| VPC / security group / whitelist | `jdcloud-vpc-ops` |
| Full-link topology RCA | `jdcloud-aiops-cruise` |
