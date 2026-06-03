# JD Cloud Audit Log Quick Reference

> This document provides the most commonly used audit log operations commands for quick reference. For detailed usage, refer to the [CLI Usage Guide](references/cli-usage.md).

## Audit Log Quick Reference

### 1. Query Events
```bash
# List events by time range
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  --page-number 1 \
  --page-size 50

# Filter by event name
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  --event-name CreateInstances

# Filter by username
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  --username admin

# Filter by resource type
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  --resource-type vm
```

### 2. Get Event Detail
```bash
# Get detailed information for a specific event
jdc --output json audit describe-event-detail \
  --region-id cn-north-1 \
  --event-id evt-xxxxx
```

### 3. List Trails
```bash
# List configured audit trails
jdc --output json audit describe-trails --region-id cn-north-1
```

## Common Event Names Quick Reference

| Event Name | Description |
|------------|-------------|
| CreateInstances | Create VM instance |
| DeleteInstance | Delete VM instance |
| StartInstance | Start VM instance |
| StopInstance | Stop VM instance |
| CreateDisk | Create cloud disk |
| DeleteDisk | Delete cloud disk |
| CreateSecurityGroup | Create security group |
| AuthorizeSecurityGroup | Add security group rules |
| CreateVpc | Create VPC |
| CreateSubnet | Create subnet |
| CreateElasticIp | Create elastic IP |
| AssociateElasticIp | Associate EIP to instance |

## JSON Output Quick Reference

### Extract Key Information
```bash
# Extract event list in table format
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  | jq -r '.result.events[] | "\(.eventTime)\t\(.username)\t\(.eventName)\t\(.resourceId)"' \
  | column -t -s $'\t'

# Extract single event detail
jdc --output json audit describe-event-detail \
  --region-id cn-north-1 \
  --event-id evt-xxxxx \
  | jq '.result.eventDetail'
```

### Common JSON Paths
| Field | JSON Path |
|-------|-----------|
| Event ID | `$.result.events[0].eventId` |
| Event Time | `$.result.events[0].eventTime` |
| Username | `$.result.events[0].username` |
| Event Name | `$.result.events[0].eventName` |
| Resource Type | `$.result.events[0].resourceType` |
| Resource ID | `$.result.events[0].resourceId` |
| Source IP | `$.result.events[0].sourceIpAddress` |
| Total Count | `$.result.totalCount` |

## Time Range Quick Reference

### Example Time Formats
```bash
# ISO 8601 format with timezone
--start-time "2026-06-01T00:00:00+08:00"
--end-time "2026-06-03T23:59:59+08:00"

# Last 24 hours (Linux/macOS)
--start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)"
--end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Last 7 days
--start-time "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)"
--end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### Common Time Ranges
| Range | Description |
|-------|-------------|
| Last 1 hour | Recent activity |
| Last 24 hours | Daily audit |
| Last 7 days | Weekly review |
| Last 30 days | Monthly compliance |

> **Note**: Audit log queries typically support a maximum 90-day window. For longer periods, make multiple sequential queries.

## Common Region IDs

| Region | ID |
|--------|-----|
| Beijing (North) | cn-north-1 |
| Shanghai (East) | cn-east-1 |
| Guangzhou (South) | cn-south-1 |

## Security Analysis Best Practices

### 1. Unauthorized Access Check
```bash
# Query failed login events
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  --event-name Login \
  | jq '.result.events[] | select(.errorCode != null)'
```

### 2. Privilege Escalation Check
```bash
# Query IAM-related events
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  --resource-type iam
```

### 3. Resource Deletion Check
```bash
# Query deletion events
jdc --output json audit describe-events \
  --region-id cn-north-1 \
  --start-time "2026-06-01T00:00:00+08:00" \
  --end-time "2026-06-03T23:59:59+08:00" \
  | jq '.result.events[] | select(.eventName | test("Delete|Remove"))'
```

## Python SDK Quick Start

### Query Events
```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.audit.client import AuditClient
from jdcloud_sdk.services.audit.apis.DescribeEventsRequest import DescribeEventsRequest, DescribeEventsParameters

# Initialize
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)
client = AuditClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

# Query events
params = DescribeEventsParameters(
    regionId='cn-north-1',
    startTime='2026-06-01T00:00:00+08:00',
    endTime='2026-06-03T23:59:59+08:00',
    pageNumber=1,
    pageSize=50
)
request = DescribeEventsRequest(parameters=params)
response = client.describeEvents(request)

if response.error is None:
    for event in response.result.events:
        print(f"{event.eventTime}: {event.username} - {event.eventName}")
```

### Get Event Detail
```python
from jdcloud_sdk.services.audit.apis.DescribeEventDetailRequest import DescribeEventDetailRequest, DescribeEventDetailParameters

params = DescribeEventDetailParameters(
    regionId='cn-north-1',
    eventId='evt-xxxxx'
)
request = DescribeEventDetailRequest(parameters=params)
response = client.describeEventDetail(request)

if response.error is None:
    detail = response.result.eventDetail
    print(f"Event: {detail.eventName}")
    print(f"Request: {detail.requestParameters}")
    print(f"Response: {detail.responseElements}")
```

### List Trails
```python
from jdcloud_sdk.services.audit.apis.DescribeTrailsRequest import DescribeTrailsRequest, DescribeTrailsParameters

params = DescribeTrailsParameters(
    regionId='cn-north-1'
)
request = DescribeTrailsRequest(parameters=params)
response = client.describeTrails(request)

if response.error is None:
    for trail in response.result.trails:
        print(f"{trail.trailId}: {trail.trailName} - {trail.status}")
```

## Troubleshooting Quick Reference

### Query Returns No Results
```bash
# 1. Check time range is valid
# 2. Try expanding the time window
# 3. Verify region is correct
# 4. Check filters are not too restrictive
```

### Invalid Time Range Error
```bash
# Ensure start time is before end time
# Check timezone format is correct
# Maximum query window is typically 90 days
```

### Permission Denied
```bash
# 1. Verify credentials in ~/.jdc/config
# 2. Check IAM permissions for audit log access
# 3. Confirm account has audit log service enabled
```

## Operational Best Practices Quick Reference

- **Regular Auditing**: Review audit logs daily for unusual activity
- **Time Range**: Keep query windows reasonable (max 90 days)
- **Filtering**: Use filters to reduce query scope and improve performance
- **Retention**: Understand your audit log retention policy
- **Export**: Export important events for compliance records
- **Alerting**: Set up alerts for critical events (delegate to monitoring skill)

## Related Documents

| Document | Description |
|----------|-------------|
| [CLI Usage Guide](references/cli-usage.md) | Complete CLI command reference |
| [Core Concepts](references/core-concepts.md) | Core concepts explanation |
| [API & SDK Usage](references/api-sdk-usage.md) | Detailed API/SDK guide |
| [Troubleshooting](references/troubleshooting.md) | Detailed troubleshooting guide |
| [Monitoring](references/monitoring.md) | Monitoring & alert configuration |
| [Integration](references/integration.md) | SDK/MCP integration |
| [Official Docs](https://docs.jdcloud.com/cn/audit-log) | JD Cloud official documentation |
| [API Docs](https://docs.jdcloud.com/cn/api/audit) | API reference documentation |
| [Console](https://console.jdcloud.com) | JD Cloud Console |
