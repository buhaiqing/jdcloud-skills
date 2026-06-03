# API & SDK — Audit Log

## OpenAPI

- **Service:** audit
- **Base URL:** `https://audit.jdcloud-api.com/v1`
- **Protocol:** HTTPS
- **Authentication:** Access Key / Secret Key (HMAC-SHA256)

## SDK Operations Map

| Goal | API Operation ID | SDK Method | Notes |
|------|------------------|------------|-------|
| List Events | describeEvents | `DescribeEventsRequest` | Query with time range and filters |
| Event Detail | describeEventDetail | `DescribeEventDetailRequest` | Get full event details by ID |
| List Trails | describeTrails | `DescribeTrailsRequest` | List audit trail configurations |

## Request / Response Notes

### Describe Events Request

**Required Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `regionId` | string | Region identifier (e.g., `cn-north-1`) |
| `startTime` | string | Query start time (ISO 8601) |
| `endTime` | string | Query end time (ISO 8601) |

**Optional Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `eventName` | string | Filter by event/operation name |
| `resourceType` | string | Filter by resource type (e.g., `vm`, `vpc`) |
| `username` | string | Filter by username |
| `pageNumber` | integer | Page number (default: 1) |
| `pageSize` | integer | Items per page (default: 20, max: 100) |

### Describe Events Response

```json
{
  "requestId": "req-xxx",
  "result": {
    "events": [
      {
        "eventId": "evt-abc123",
        "eventTime": "2026-06-03T10:30:00+08:00",
        "eventName": "CreateInstances",
        "username": "admin",
        "resourceType": "vm",
        "resourceId": "i-xxx",
        "sourceIpAddress": "192.168.1.1",
        "userAgent": "jdcloud-sdk-python/1.6.26",
        "eventSource": "vm.jdcloud-api.com",
        "eventVersion": "1.0",
        "errorCode": null,
        "errorMessage": null
      }
    ],
    "totalCount": 100
  }
}
```

### Describe Event Detail Request

**Required Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `regionId` | string | Region identifier |
| `eventId` | string | Event ID to retrieve details for |

### Describe Event Detail Response

```json
{
  "requestId": "req-xxx",
  "result": {
    "eventDetail": {
      "eventId": "evt-abc123",
      "eventTime": "2026-06-03T10:30:00+08:00",
      "eventName": "CreateInstances",
      "username": "admin",
      "resourceType": "vm",
      "resourceId": "i-xxx",
      "sourceIpAddress": "192.168.1.1",
      "userAgent": "jdcloud-sdk-python/1.6.26",
      "eventSource": "vm.jdcloud-api.com",
      "eventVersion": "1.0",
      "requestParameters": {
        "regionId": "cn-north-1",
        "instanceType": "g.n2.medium",
        "imageId": "img-xxx",
        "name": "my-vm"
      },
      "responseElements": {
        "instanceIds": ["i-xxx"],
        "requestId": "req-yyy"
      },
      "errorCode": null,
      "errorMessage": null
    }
  }
}
```

### Describe Trails Request

**Required Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `regionId` | string | Region identifier |

### Describe Trails Response

```json
{
  "requestId": "req-xxx",
  "result": {
    "trails": [
      {
        "trailId": "trail-xxx",
        "trailName": "default-trail",
        "status": "active",
        "createTime": "2026-01-01T00:00:00+08:00",
        "updateTime": "2026-06-01T00:00:00+08:00"
      }
    ]
  }
}
```

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `InvalidParameter` | 400 | Request parameter invalid |
| `InvalidTimeRange` | 400 | Time range exceeds maximum or is invalid |
| `EventNotFound` | 404 | Specified event ID not found |
| `Unauthorized` | 403 | Insufficient permissions |
| `InternalError` | 500 | Internal server error |
| `Throttling` | 429 | Rate limit exceeded |

## Python SDK Example

### Setup Client

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.audit.client.AuditClient import AuditClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = AuditClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

### Query Events

```python
from jdcloud_sdk.services.audit.apis.DescribeEventsRequest import (
    DescribeEventsRequest, DescribeEventsParameters
)

params = DescribeEventsParameters(
    regionId="cn-north-1",
    startTime="2026-06-01T00:00:00+08:00",
    endTime="2026-06-03T23:59:59+08:00",
    pageNumber=1,
    pageSize=50
)

request = DescribeEventsRequest(parameters=params)
response = client.send(request)

if response.error is None:
    events = response.result.get("events", [])
    for event in events:
        print(f"{event['eventTime']}: {event['username']} performed {event['eventName']}")
else:
    print(f"Error: {response.error.code} - {response.error.message}")
```

### Get Event Detail

```python
from jdcloud_sdk.services.audit.apis.DescribeEventDetailRequest import (
    DescribeEventDetailRequest, DescribeEventDetailParameters
)

params = DescribeEventDetailParameters(
    regionId="cn-north-1",
    eventId="evt-abc123"
)

request = DescribeEventDetailRequest(parameters=params)
response = client.send(request)

if response.error is None:
    detail = response.result.get("eventDetail", {})
    print(f"Event: {detail['eventName']}")
    print(f"Request: {detail.get('requestParameters', {})}")
    print(f"Response: {detail.get('responseElements', {})}")
```

## Pagination Handling

For large result sets, implement pagination:

```python
def get_all_events(client, region_id, start_time, end_time):
    all_events = []
    page_number = 1
    page_size = 100
    
    while True:
        params = DescribeEventsParameters(
            regionId=region_id,
            startTime=start_time,
            endTime=end_time,
            pageNumber=page_number,
            pageSize=page_size
        )
        request = DescribeEventsRequest(parameters=params)
        response = client.send(request)
        
        if response.error is not None:
            raise Exception(f"API error: {response.error.message}")
        
        events = response.result.get("events", [])
        all_events.extend(events)
        
        total = response.result.get("totalCount", 0)
        if len(all_events) >= total or len(events) == 0:
            break
        
        page_number += 1
    
    return all_events
```
