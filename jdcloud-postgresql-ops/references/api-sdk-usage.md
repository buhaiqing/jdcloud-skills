# API & SDK — JD Cloud RDS PostgreSQL

## OpenAPI

- **Base URL:** `https://rds.jdcloud-api.com/v1`
- **Region:** `cn-north-1`, `cn-east-1`, `cn-east-2`, `cn-south-1`
- **Authentication:** Access key + secret key

## SDK Operations Map

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Instance | createInstance | CreateInstanceRequest |
| Describe Instance | describeInstance | DescribeInstanceRequest |
| Describe Instances | describeInstances | DescribeInstancesRequest |
| Modify Instance Attribute | modifyInstanceAttribute | ModifyInstanceAttributeRequest |
| Delete Instance | deleteInstance | DeleteInstanceRequest |
| Create Backup | createBackup | CreateBackupRequest |
| Describe Backups | describeBackups | DescribeBackupsRequest |
| Restore Instance | restoreInstance | RestoreInstanceRequest |
| **Describe Slow Logs** | **describeSlowLogs** | **DescribeSlowLogsRequest** |

## Request / Response Notes

### Required Fields for Create Instance

| Field | Type | Description |
|-------|------|-------------|
| regionId | string | Region ID |
| instanceName | string | Instance name |
| instanceClass | string | Instance class code |
| engine | string | Database engine (PostgreSQL) |
| engineVersion | string | Engine version (10, 11, 12, 13, 14) |
| vpcId | string | VPC ID |
| subnetId | string | Subnet ID |
| azId | string | Availability Zone ID |
| storageType | string | Storage type |
| storageSize | int | Storage size in GB |
| username | string | Admin username |
| password | string | Admin password |

### Pagination

Most list APIs support pagination:
- `pageNumber`: Starting from 1
- `pageSize`: Maximum 100

### Response Structure

```json
{
  "requestId": "string",
  "result": { ... },
  "error": null or { "code": "string", "message": "string" }
}
```

## SDK Bootstrap Example

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.rds.client.RdsClient import RdsClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = RdsClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

## Slow Log Query Examples

### Basic slow log query by time range
```python
from jdcloud_sdk.services.rds.apis.DescribeSlowLogsRequest import DescribeSlowLogsRequest, DescribeSlowLogsParameters

params = DescribeSlowLogsParameters(
    regionId="cn-north-1",
    instanceId="rds-abc123",
    startTime="2026-06-01 00:00:00",
    endTime="2026-06-03 23:59:59"
)
params.setPageNumber(1)
params.setPageSize(50)

req = DescribeSlowLogsRequest(parameters=params)
resp = client.send(req)

# Process results
slow_logs = resp.result.get("slowLogs", [])
total_count = resp.result.get("totalCount", 0)

print(f"Total slow query patterns: {total_count}")
for log in slow_logs:
    print(f"SQL: {log.get('sql', 'N/A')[:80]}...")
    print(f"  Executed: {log.get('executionCount', 0)} times")
    print(f"  Avg time: {log.get('executionTimeAvg', 0)} ms")
    print(f"  Max time: {log.get('executionTimeMax', 0)} ms")
    print(f"  Total time: {log.get('executionTimeSum', 0)} ms")
    print(f"  Rows examined: {log.get('rowsExaminedSum', 0)}")
    print(f"  Lock time: {log.get('lockTimeSum', 0)} ms")
    print()
```

### Filter by account and SQL keyword
```python
from jdcloud_sdk.services.rds.apis.DescribeSlowLogsRequest import DescribeSlowLogsRequest, DescribeSlowLogsParameters

params = DescribeSlowLogsParameters(
    regionId="cn-north-1",
    instanceId="rds-abc123",
    startTime="2026-06-01 00:00:00",
    endTime="2026-06-03 23:59:59"
)

# Filter: specific account or SQL keyword
filters = [
    {
        "name": "account",
        "operator": "eq",  # or "in" for multiple values
        "values": ["app_user"]
    },
    {
        "name": "keyword",
        "operator": "eq",  # SQL keyword fuzzy match
        "values": ["SELECT * FROM orders"]
    }
]
params.setFilters(filters)
params.setPageNumber(1)
params.setPageSize(20)

req = DescribeSlowLogsRequest(parameters=params)
resp = client.send(req)

filtered_logs = resp.result.get("slowLogs", [])
print(f"Filtered results: {len(filtered_logs)} patterns")
```

### Sort by execution metrics
```python
from jdcloud_sdk.services.rds.apis.DescribeSlowLogsRequest import DescribeSlowLogsRequest, DescribeSlowLogsParameters

params = DescribeSlowLogsParameters(
    regionId="cn-north-1",
    instanceId="rds-abc123",
    startTime="2026-06-01 00:00:00",
    endTime="2026-06-03 23:59:59"
)

# Sort options: rowsExaminedSum, rowsSentSum, lockTimeSum, executionCount, executionTimeSum
sorts = [
    {
        "name": "executionTimeMax",  # Find slowest individual queries
        "direction": "DESC"
    }
]
params.setSorts(sorts)
params.setPageNumber(1)
params.setPageSize(20)

req = DescribeSlowLogsRequest(parameters=params)
resp = client.send(req)

# Top 20 slowest queries
top_slow_queries = resp.result.get("slowLogs", [])
```

### Query last 24 hours with automatic date calculation
```python
from datetime import datetime, timedelta
from jdcloud_sdk.services.rds.apis.DescribeSlowLogsRequest import DescribeSlowLogsRequest, DescribeSlowLogsParameters

# Calculate time range (last 24 hours)
end_time = datetime.now()
start_time = end_time - timedelta(days=1)

params = DescribeSlowLogsParameters(
    regionId="cn-north-1",
    instanceId="rds-abc123",
    startTime=start_time.strftime("%Y-%m-%d %H:%M:%S"),
    endTime=end_time.strftime("%Y-%m-%d %H:%M:%S")
)
params.setPageNumber(1)
params.setPageSize(100)

req = DescribeSlowLogsRequest(parameters=params)
resp = client.send(req)

recent_slow_logs = resp.result.get("slowLogs", [])
print(f"Slow queries in last 24h: {len(recent_slow_logs)} patterns")
```

### Paginate through all results
```python
def get_all_slow_logs(client, region_id, instance_id, start_time, end_time):
    """Fetch all slow logs across multiple pages"""
    all_logs = []
    page_number = 1
    page_size = 100  # Maximum allowed
    
    while True:
        params = DescribeSlowLogsParameters(
            regionId=region_id,
            instanceId=instance_id,
            startTime=start_time,
            endTime=end_time
        )
        params.setPageNumber(page_number)
        params.setPageSize(page_size)
        
        req = DescribeSlowLogsRequest(parameters=params)
        resp = client.send(req)
        
        logs = resp.result.get("slowLogs", [])
        all_logs.extend(logs)
        
        total_count = resp.result.get("totalCount", 0)
        if page_number * page_size >= total_count:
            break
        
        page_number += 1
        
        # Safety limit
        if page_number > 100:
            break
    
    return all_logs

# Usage
all_logs = get_all_slow_logs(
    client, "cn-north-1", "rds-abc123",
    "2026-06-01 00:00:00", "2026-06-03 23:59:59"
)
print(f"Total slow query patterns: {len(all_logs)}")
```

### Analyze slow log trends
```python
def analyze_slow_log_trends(client, region_id, instance_id, days=7):
    """Analyze slow query trends over the past N days"""
    from datetime import datetime, timedelta
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    params = DescribeSlowLogsParameters(
        regionId=region_id,
        instanceId=instance_id,
        startTime=start_time.strftime("%Y-%m-%d %H:%M:%S"),
        endTime=end_time.strftime("%Y-%m-%d %H:%M:%S")
    )
    params.setPageNumber(1)
    params.setPageSize(100)
    params.setSorts([{"name": "executionTimeSum", "direction": "DESC"}])
    
    req = DescribeSlowLogsRequest(parameters=params)
    resp = client.send(req)
    
    logs = resp.result.get("slowLogs", [])
    total_count = resp.result.get("totalCount", 0)
    
    # Calculate summary statistics
    total_exec_time = sum(log.get("executionTimeSum", 0) for log in logs)
    total_exec_count = sum(log.get("executionCount", 0) for log in logs)
    total_rows_examined = sum(log.get("rowsExaminedSum", 0) for log in logs)
    
    return {
        "unique_patterns": total_count,
        "total_executions": total_exec_count,
        "total_execution_time_ms": total_exec_time,
        "total_rows_examined": total_rows_examined,
        "top_slow_queries": logs[:10]  # Top 10 by execution time
    }

# Usage
trends = analyze_slow_log_trends(client, "cn-north-1", "rds-abc123", days=7)
print(f"Unique slow patterns: {trends['unique_patterns']}")
print(f"Total slow executions: {trends['total_executions']}")
print(f"Total time in slow queries: {trends['total_execution_time_ms'] / 1000:.2f}s")
```

## DescribeSlowLogs Request Parameters

| Parameter | Required | Type | Description | Example |
|-----------|----------|------|-------------|---------|
| `regionId` | Yes | string | Region ID | `cn-north-1` |
| `instanceId` | Yes | string | RDS instance ID | `rds-abc123` |
| `startTime` | Yes | string | Start time (YYYY-MM-DD HH:mm:ss) | `2026-06-01 00:00:00` |
| `endTime` | Yes | string | End time (YYYY-MM-DD HH:mm:ss) | `2026-06-03 23:59:59` |
| `dbName` | No | string | Database name filter (deprecated) | `mydb` |
| `pageNumber` | No | int | Page number (default 1) | `1` |
| `pageSize` | No | int | Items per page [10, 100], default 10 | `50` |
| `filters` | No | array | Filter conditions | `[{"name":"account","operator":"eq","values":["postgres"]}]` |
| `sorts` | No | array | Sort conditions | `[{"name":"executionTimeSum","direction":"DESC"}]` |

### Filter Operators

| Filter Name | Operators | Description |
|-------------|-----------|-------------|
| `account` | `eq`, `in` | Filter by database account name |
| `keyword` | `eq`, `in` | Filter by SQL keyword (fuzzy match) |

### Sort Fields

| Field | Description |
|-------|-------------|
| `rowsExaminedSum` | Total rows examined |
| `rowsSentSum` | Total rows returned |
| `lockTimeSum` | Total lock wait time |
| `executionCount` | Number of executions |
| `executionTimeSum` | Total execution time |
| `executionTimeMax` | Maximum execution time |
| `executionTimeAvg` | Average execution time |

## Response Fields

| Field | Path | Type | Description |
|-------|------|------|-------------|
| `requestId` | `$.requestId` | string | API request ID |
| `totalCount` | `$.result.totalCount` | int | Total matching records |
| `slowLogs` | `$.result.slowLogs` | array | Slow log entries |
| `slowLogs[*].sql` | `$.result.slowLogs[*].sql` | string | SQL statement |
| `slowLogs[*].executionCount` | `$.result.slowLogs[*].executionCount` | int | Execution count |
| `slowLogs[*].executionTimeAvg` | `$.result.slowLogs[*].executionTimeAvg` | int | Avg execution time (ms) |
| `slowLogs[*].executionTimeMax` | `$.result.slowLogs[*].executionTimeMax` | int | Max execution time (ms) |
| `slowLogs[*].executionTimeSum` | `$.result.slowLogs[*].executionTimeSum` | int | Total execution time (ms) |
| `slowLogs[*].rowsExaminedSum` | `$.result.slowLogs[*].rowsExaminedSum` | int | Total rows examined |
| `slowLogs[*].rowsSentSum` | `$.result.slowLogs[*].rowsSentSum` | int | Total rows sent |
| `slowLogs[*].lockTimeSum` | `$.result.slowLogs[*].lockTimeSum` | int | Total lock time (ms) |
| `slowLogs[*].startTime` | `$.result.slowLogs[*].startTime` | string | First occurrence |
| `slowLogs[*].finishTime` | `$.result.slowLogs[*].finishTime` | string | Last occurrence |

## Constraints

- **Engine:** PostgreSQL only (does NOT support MySQL or other engines)
- **Time window:** Maximum 7 days from start time to current time
- **Time format:** `YYYY-MM-DD HH:mm:ss` (strict)
- **Rate limiting:** Subject to standard JD Cloud API rate limits