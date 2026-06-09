# API & SDK — Audit Log

> **⚠️ 当前状态说明**：当前仓库锁定的 JD Cloud SDK 中未发现 `jdcloud_sdk.services.audit` 模块；以下 SDK 代码均为期望语法示例。实际执行前必须确认官方 SDK 真实服务名，或直接通过 OpenAPI REST API (`https://audit.jdcloud-api.com/v1/...`) 调用。
>
> **脱敏要求**：任何 `requestParameters` / `responseElements` 输出或外发前必须调用 `mask_sensitive(data)` / `redact_sensitive_fields(data)`。必须脱敏字段：`password`, `passwd`, `pwd`, `secret`, `secretKey`, `accessKeySecret`, `accessKey`, `token`, `authorization`, `credential`, `privateKey`, `sessionKey`, `apiKey`；手机号、邮箱等 PII 按策略 mask/hash。

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
# REST API 伪代码（当前 SDK 模块不可用，建议直接调用 OpenAPI）
import os, json, requests

# 签名工具：JD Cloud V3 签名需按官方规范实现，此处为示意
# 详见 https://docs.jdcloud.com/cn/signed-request

def _make_auth_headers(access_key, secret_key, region, method, path, query=""):
    """生成带 V3 签名的请求头（伪代码，需替换为真实签名实现）。"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"JDCLOUD {access_key}:<signed>",
        "Jdcloud-Date": "20260609T120000Z",
    }
```

### Query Events

```python
# REST API 伪代码（当前 SDK 模块不可用，建议直接调用 OpenAPI）
import os, json, requests

region = "cn-north-1"
endpoint = f"https://audit.jdcloud-api.com/v1/regions/{region}/events"

headers = _make_auth_headers(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
    region, "GET", "/v1/regions/cn-north-1/events"
)

params = {
    "startTime": "2026-06-01T00:00:00+08:00",
    "endTime": "2026-06-03T23:59:59+08:00",
    "pageNumber": 1,
    "pageSize": 50,
}

resp = requests.get(endpoint, headers=headers, params=params, timeout=30)

if resp.status_code == 200:
    data = resp.json()
    events = data.get("result", {}).get("events", [])
    for event in events:
        safe_event = mask_sensitive(event, mode="masked_default")
        print(f"{safe_event.get('eventTime')}: {safe_event.get('username')} performed {safe_event.get('eventName')}")
else:
    print(f"Error: {resp.status_code} - {resp.text}")
```

### Get Event Detail

```python
# REST API 伪代码（当前 SDK 模块不可用，建议直接调用 OpenAPI）
import os, json, requests

region = "cn-north-1"
event_id = "evt-abc123"
endpoint = f"https://audit.jdcloud-api.com/v1/regions/{region}/events/{event_id}"

headers = _make_auth_headers(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
    region, "GET", f"/v1/regions/{region}/events/{event_id}"
)

resp = requests.get(endpoint, headers=headers, timeout=30)

if resp.status_code == 200:
    data = resp.json()
    detail = data.get("result", {}).get("eventDetail", {})
    print(f"Event: {detail.get('eventName')}")
    # ⚠️ 敏感字段脱敏：requestParameters / responseElements 中可能包含 password、secretKey、accessKey、token、PII 等，输出前必须脱敏
    print(f"Request: {mask_sensitive(detail.get('requestParameters', {}))}")
    print(f"Response: {mask_sensitive(detail.get('responseElements', {}))}")
else:
    print(f"Error: {resp.status_code} - {resp.text}")
```

## Pagination Handling

For large result sets, implement pagination:

```python
def get_all_events(region_id, start_time, end_time):
    """REST API 分页示例（当前 SDK 模块不可用，建议直接调用 OpenAPI）。"""
    import os, requests

    all_events = []
    page_number = 1
    page_size = 100
    endpoint = f"https://audit.jdcloud-api.com/v1/regions/{region_id}/events"

    while True:
        headers = _make_auth_headers(
            os.environ["JDC_ACCESS_KEY"],
            os.environ["JDC_SECRET_KEY"],
            region_id, "GET", f"/v1/regions/{region_id}/events"
        )
        params = {
            "startTime": start_time,
            "endTime": end_time,
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        response = requests.get(endpoint, headers=headers, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} {response.text}")

        data = response.json()
        # ⚠️ 如果 event 中含 requestParameters / responseElements，追加前必须先脱敏
        events = [redact_sensitive_fields(e) for e in data.get("result", {}).get("events", [])]
        all_events.extend(events)

        total = data.get("result", {}).get("totalCount", 0)
        if len(all_events) >= total or len(events) == 0:
            break

        page_number += 1

    return all_events
```
