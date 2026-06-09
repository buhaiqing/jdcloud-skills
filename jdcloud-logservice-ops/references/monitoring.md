# Monitoring LogService

## Key Metrics

LogService exposes metrics via JD Cloud CloudMonitor. Monitor these dimensions to ensure healthy log collection and query performance.

### Collection Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| `Logs.IngestionRate` | `jdcloud/logs` | lines/min | Log ingestion rate per LogTopic |
| `Logs.IngestionLatency` | `jdcloud/logs` | ms | Average delay from log generation to ingestion |
| `Logs.IngestionErrorRate` | `jdcloud/logs` | % | Percentage of failed ingestion attempts |
| `Logs.CollectorStatus` | `jdcloud/logs` | — | Collection agent health (1 = healthy, 0 = unhealthy) |

### Storage Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| `Logs.StorageSize` | `jdcloud/logs` | bytes | Total storage used by LogSet |
| `Logs.StorageGrowthRate` | `jdcloud/logs` | bytes/hour | Storage growth rate |
| `Logs.RetentionUtilization` | `jdcloud/logs` | % | Percentage of retention period utilized |

### Query Metrics

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| `Logs.QueryLatency` | `jdcloud/logs` | ms | Average search query latency |
| `Logs.QueryQPS` | `jdcloud/logs` | req/s | Search query QPS |
| `Logs.QueryErrorRate` | `jdcloud/logs` | % | Percentage of failed queries |

### Alert Examples

#### High Ingestion Error Rate
```json
{
  "metric": "Logs.IngestionErrorRate",
  "namespace": "jdcloud/logs",
  "dimensions": ["logtopicUID"],
  "threshold": 5,
  "comparisonOperator": "GreaterThanOrEqualTo",
  "period": 300,
  "evaluationPeriods": 2,
  "alarmAction": ["notify-oncall"]
}
```

#### Storage Approaching Retention Limit
```json
{
  "metric": "Logs.RetentionUtilization",
  "namespace": "jdcloud/logs",
  "dimensions": ["logsetUID"],
  "threshold": 90,
  "comparisonOperator": "GreaterThanOrEqualTo",
  "period": 3600,
  "evaluationPeriods": 1,
  "alarmAction": ["notify-ops"]
}
```

#### Query Latency Spike
```json
{
  "metric": "Logs.QueryLatency",
  "namespace": "jdcloud/logs",
  "dimensions": ["logtopicUID"],
  "threshold": 10000,
  "comparisonOperator": "GreaterThanOrEqualTo",
  "period": 300,
  "evaluationPeriods": 2,
  "alarmAction": ["notify-dev"]
}
```

> **Note**: For CloudMonitor alarm rule management, delegate to `jdcloud-cloudmonitor-ops`.

## Dashboard Recommendations

A well-designed LogService dashboard should include:

1. **Ingestion Overview**
   - Total ingestion rate across all LogTopics
   - Ingestion latency trend (line chart)
   - Error rate trend (line chart)

2. **Storage Overview**
   - Storage size per LogSet (bar chart)
   - Growth rate trend (area chart)
   - Top 5 largest LogTopics (table)

3. **Query Performance**
   - Average query latency (gauge)
   - Query QPS (line chart)
   - Slow query count (counter)

4. **Collection Health**
   - Agent status per VM/container (heatmap)
   - Offline agents list (table)
