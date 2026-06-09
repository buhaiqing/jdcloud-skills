# LogService Core Concepts

## LogSet (日志集)

A **LogSet** is the top-level organizational unit in JD Cloud LogService. It acts as a logical container for related LogTopics.

### Key Attributes

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `uid` | string | System-generated unique identifier | Immutable, alphanumeric |
| `name` | string | Human-readable name | 1–128 chars, UTF-8 |
| `description` | string | Optional description | ≤ 512 chars |
| `retention` | int | Log retention period | 1–3650 days |
| `createTime` | string | Creation timestamp | ISO 8601 |
| `updateTime` | string | Last update timestamp | ISO 8601 |

### Retention Policy

- Logs older than the retention period are **automatically purged**
- Retention can be increased or decreased via UpdateLogSet
- Decreasing retention immediately schedules deletion of logs outside the new window
- **Cost impact**: Longer retention = higher storage cost

## LogTopic (日志主题)

A **LogTopic** is a log stream within a LogSet. It receives, stores, and indexes logs from one or more collection sources.

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `uid` | string | System-generated unique identifier |
| `name` | string | Human-readable name (1–128 chars) |
| `logsetUID` | string | Parent LogSet UID |
| `description` | string | Optional description |
| `collectionInfo` | object | Log collection configuration |
| `createTime` | string | Creation timestamp |

### Collection Types

| Type | Source | Typical Paths |
|------|--------|---------------|
| `cloud_vm` | JD Cloud VM instances | `/var/log/messages`, `/var/log/syslog` |
| `container` | Kubernetes containers | Stdout/stderr, container logs |
| `clb` | Cloud Load Balancer | Access logs, health check logs |
| `custom` | Custom push via API/SDK | User-defined ingestion |

## Log Entry

A single log record within a LogTopic:

```json
{
  "time": "2026-06-08T10:30:00+08:00",
  "content": "{"level":"ERROR","service":"api","status":500,"message":"connection timeout"}"
}
```

- **time**: Ingestion timestamp (set by server)
- **content**: Raw log content, typically JSON or plain text

## Index

Indexes enable fast log search by pre-building inverted indices on specified fields.

### Index Field Types

| Type | Use Case | Example |
|------|----------|---------|
| `text` | Full-text search | Error messages, descriptions |
| `keyword` | Exact match, aggregation | Log level, service name, host |
| `long` | Numeric range queries | HTTP status codes, response times |
| `date` | Time-based filtering | Custom timestamps |
| `double` | Floating-point metrics | CPU usage, memory percent |

### Index Best Practices

1. Index fields you query frequently (`level`, `service`, `status`)
2. Do NOT index high-cardinality fields (trace IDs) unless necessary — increases cost
3. Index size affects search speed and storage cost

## Search Query Syntax

LogService supports a Lucene-like query language:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `term` | Full-text search | `timeout` |
| `field:value` | Field match | `level:ERROR` |
| `field:[a TO b]` | Range (inclusive) | `status:[500 TO 599]` |
| `field:{a TO b}` | Range (exclusive) | `response_time:{100 TO 500}` |
| `term1 AND term2` | Boolean AND | `error AND api` |
| `term1 OR term2` | Boolean OR | `warn OR error` |
| `NOT term` | Negation | `NOT debug` |
| `field:prefix*` | Prefix wildcard | `service:payment*` |
| `"exact phrase"` | Phrase match | `"connection refused"` |
