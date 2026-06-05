# Monitoring JD Cloud RDS PostgreSQL

## Key Metrics

JD Cloud CloudMonitor provides the following metrics for RDS PostgreSQL instances:

| Metric | Namespace | Description | Unit |
|--------|-----------|-------------|------|
| CPUUtilization | rds | CPU usage percentage | % |
| MemoryUtilization | rds | Memory usage percentage | % |
| DiskUtilization | rds | Disk usage percentage | % |
| IOPSRead | rds | Read IOPS count | Count/s |
| IOPSWrite | rds | Write IOPS count | Count/s |
| NetworkIn | rds | Inbound network traffic | Bytes/s |
| NetworkOut | rds | Outbound network traffic | Bytes/s |
| Connections | rds | Active connections count | Count |
| SlowQueries | rds | Slow query count per minute | Count/min |
| AbortedConnections | rds | Aborted connections count | Count |

## Alert Examples

### High CPU Usage Alert

```json
{
  "metric": "CPUUtilization",
  "namespace": "rds",
  "dimensions": {
    "instanceId": "{{user.instance_id}}"
  },
  "threshold": 80,
  "comparisonOperator": ">=",
  "period": 300,
  "statistics": "Average",
  "evaluationCount": 3,
  "alarmName": "PostgreSQL High CPU Alert"
}
```

### High Connection Count Alert

```json
{
  "metric": "Connections",
  "namespace": "rds",
  "dimensions": {
    "instanceId": "{{user.instance_id}}"
  },
  "threshold": 500,
  "comparisonOperator": ">=",
  "period": 60,
  "statistics": "Maximum",
  "evaluationCount": 1,
  "alarmName": "PostgreSQL High Connection Alert"
}
```

### Slow Queries Alert

```json
{
  "metric": "SlowQueries",
  "namespace": "rds",
  "dimensions": {
    "instanceId": "{{user.instance_id}}"
  },
  "threshold": 10,
  "comparisonOperator": ">=",
  "period": 60,
  "statistics": "Sum",
  "evaluationCount": 5,
  "alarmName": "PostgreSQL Slow Queries Alert"
}
```

## Monitoring Best Practices

1. **Set baseline:** Establish normal metric ranges for your workload
2. **Configure alerts:** Set appropriate thresholds for critical metrics
3. **Monitor trends:** Track metric changes over time
4. **Correlate metrics:** Look for relationships between CPU, IOPS, and connections
5. **Use dashboards:** Create custom dashboards in CloudMonitor
6. **Set up notifications:** Configure alert notifications via email/SMS/webhook

## Logs

### Slow Query Log

The Slow Query Log captures SQL statements that take longer than `log_min_duration_statement` (default 1 second) to execute. JD Cloud provides the `describe-slow-logs` API to query slow query summaries programmatically.

#### Key Features
- **Time-based queries:** Query by arbitrary time range (max 7 days)
- **Aggregation:** Groups similar SQL patterns for easier analysis
- **Metrics:** Execution count, time statistics, rows examined
- **Filtering:** Filter by database account or SQL keyword
- **Sorting:** Sort by various execution metrics

#### Slow Query Log API

| API | SDK Method | Description |
|-----|------------|-------------|
| `describeSlowLogs` | `DescribeSlowLogsRequest` | Query slow query summaries by time range (PostgreSQL only) |

**Time window constraints:**
- Maximum: 7 days from start time to current time
- Format: `YYYY-MM-DD HH:mm:ss` (24-hour format, strict)
- Start time must be ≤ end time

**Common metrics returned:**
| Metric | Description | Usage |
|--------|-------------|-------|
| `executionCount` | Times this SQL pattern executed | Identify frequently slow queries |
| `executionTimeAvg` | Average execution time (ms) | Find consistently slow queries |
| `executionTimeMax` | Maximum execution time (ms) | Find worst-case outliers |
| `executionTimeSum` | Total execution time (ms) | Identify highest-impact queries |
| `rowsExaminedSum` | Total rows scanned | Identify missing indexes (seq scans) |
| `rowsSentSum` | Total rows returned | Identify over-fetching |
| `lockTimeSum` | Total lock wait time (ms) | Identify lock contention |

#### CLI Usage Examples

```bash
# Query last 7 days of slow logs
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-xxx \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-07 23:59:59" \
  --page-size 100

# Filter by specific account
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-xxx \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --filters '[{"name":"account","operator":"eq","values":["app_user"]}]'

# Sort by execution time (find slowest queries)
jdc --output json rds describe-slow-logs \
  --region-id cn-north-1 \
  --instance-id rds-xxx \
  --start-time "2026-06-01 00:00:00" \
  --end-time "2026-06-03 23:59:59" \
  --sorts '[{"name":"executionTimeMax","direction":"DESC"}]' \
  --page-size 20
```

See `references/cli-usage.md` and `references/api-sdk-usage.md` for complete documentation.

#### PostgreSQL-specific Configuration

PostgreSQL slow query logging is controlled by these parameters:
- `log_min_duration_statement`: Minimum execution time to log (default 1000ms)
- `log_statement`: Type of statements to log (`none`, `ddl`, `mod`, `all`)
- `log_line_prefix`: Format of log lines

These can be modified via `modifyInstanceAttribute` with parameter group settings.

### Error Log
- Records database errors and warnings
- Useful for troubleshooting instance issues
- Access via `describe-error-logs` API or JD Cloud console

### General Log
- Records all connections and queries
- Useful for auditing and debugging
- Enable with caution due to performance impact

## Tools

- **JD Cloud CloudMonitor:** Native monitoring service
- **JD Cloud RDS API / jdc CLI:** Programmatic access to slow query logs
- **pgAdmin:** GUI tool for database management
- **Prometheus + Grafana:** Custom monitoring stack
- **pg_stat_statements:** PostgreSQL extension for query statistics (alternative to slow log)

## Performance Analysis Workflow

1. **Monitor SlowQueries metric** via CloudMonitor for trends
2. **Query Slow Query Log** via `describe-slow-logs` to identify specific problematic queries
3. **Analyze patterns:**
   - High `executionCount` + high `executionTimeAvg` = Hot slow query
   - High `rowsExaminedSum` / low `rowsSentSum` = Missing index (seq scan)
   - High `lockTimeSum` = Lock contention issue
4. **Optimize:**
   - Add indexes (`CREATE INDEX`)
   - Rewrite queries (avoid `SELECT *`, add `LIMIT`)
   - Tune `work_mem`, `shared_buffers` parameters
   - Consider `pg_stat_statements` for more detailed analysis
5. **Verify:** Re-query slow logs to confirm improvement