# API & SDK — LogService

## OpenAPI

- Base URL: `https://logs.jdcloud-api.com/v1`
- Protocol: HTTPS only
- Authentication: JD Cloud signature V3
- SDK Namespace: `jdcloud_sdk.services.logs`

## SDK Operations Map

| Goal | API Operation | SDK Request Class | Notes |
|------|---------------|-------------------|-------|
| Create LogSet | `CreateLogSet` | `CreateLogSetRequest` | Name must be unique in region |
| Describe LogSet | `DescribeLogSet` | `DescribeLogSetRequest` | Query by UID |
| Describe LogSets | `DescribeLogSets` | `DescribeLogSetsRequest` | Pagination supported |
| Update LogSet | `UpdateLogSet` | `UpdateLogSetRequest` | Modify name / description / retention |
| Delete LogSet | `DeleteLogSet` | `DeleteLogSetRequest` | Cascade deletes contained LogTopics |
| Create LogTopic | `CreateLogTopic` | `CreateLogTopicRequest` | Requires valid LogSet UID |
| Describe LogTopic | `DescribeLogTopic` | `DescribeLogTopicRequest` | Query by LogSet UID + LogTopic UID |
| Describe LogTopics | `DescribeLogTopics` | `DescribeLogTopicsRequest` | List by LogSet UID |
| Update LogTopic | `UpdateLogTopic` | `UpdateLogTopicRequest` | Modify name / description / collection |
| Delete LogTopic | `DeleteLogTopic` | `DeleteLogTopicRequest` | Deletes all logs in the topic |
| Search Log | `SearchLog` | `SearchLogRequest` | Lucene-like query syntax |
| Describe Index | `DescribeIndex` | `DescribeIndexRequest` | Get index configuration |
| Update Index | `UpdateIndex` | `UpdateIndexRequest` | Configure index fields |

## Request / Response Notes

### CreateLogSetRequest

```python
req = CreateLogSetRequest(
    regionId="cn-north-1",
    name="prod-logs",
    description="Production application logs",
    retention=30  # days
)
```

**Required fields**: `regionId`, `name`
**Optional fields**: `description`, `retention` (default: 7)

### CreateLogTopicRequest

```python
req = CreateLogTopicRequest(
    regionId="cn-north-1",
    logsetUID="ls-xxxxxx",
    name="nginx-access",
    description="Nginx access logs",
    collectionInfo={
        "type": "cloud_vm",
        "paths": ["/var/log/nginx/access.log"]
    }
)
```

**Required fields**: `regionId`, `logsetUID`, `name`
**Optional fields**: `description`, `collectionInfo`

### SearchLogRequest

```python
req = SearchLogRequest(
    regionId="cn-north-1",
    logtopicUID="lt-xxxxxx",
    query="level:ERROR AND status:500",
    startTime="2026-06-08T00:00:00+08:00",
    endTime="2026-06-08T23:59:59+08:00",
    pageNumber=1,
    pageSize=100
)
```

**Required fields**: `regionId`, `logtopicUID`, `query`, `startTime`, `endTime`
**Optional fields**: `pageNumber` (default: 1), `pageSize` (default: 10, max: 1000)

### Pagination

List operations (`DescribeLogSets`, `DescribeLogTopics`, `SearchLog`) support pagination:

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `pageNumber` | 1 | — | Page index (1-based) |
| `pageSize` | 10 / 50 | 1000 | Items per page |

Response typically includes:
- `result.total` — total matching items
- `result.data` or `result.logsets` / `result.logtopics` — current page items

### Common Response Structure

```json
{
  "requestId": "req-xxxxxxxx",
  "result": {
    "uid": "lt-xxxxxx",
    "name": "nginx-access",
    ...
  }
}
```

- `requestId` — unique per API call, include in support tickets
- `result` — operation-specific payload

### Error Response Structure

```json
{
  "requestId": "req-xxxxxxxx",
  "error": {
    "code": "InvalidParameter",
    "message": "Parameter 'name' is required",
    "status": 400
  }
}
```
