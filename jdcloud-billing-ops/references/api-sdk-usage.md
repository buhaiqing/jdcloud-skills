# API & SDK — JD Cloud Billing

## OpenAPI Reference

- **Billing Service**: `https://billing.jdcloud-api.com`
- **Asset Service**: `https://asset.jdcloud-api.com`
- **InstanceVoucher Service**: `https://instancevoucher.jdcloud-api.com`
- **API Version**: v1

## SDK Operations Map

| Goal | Service | Request Class | Parameters Class |
|------|---------|---------------|------------------|
| Query Account Balance | `asset` | `DescribeAccountAmountRequest` | `DescribeAccountAmountParameters` |
| Query Consumption Summary | `billing` | `QueryBillSummaryRequest` | `QueryBillSummaryParameters` |
| Query Bill Details | `billing` | `QueryBillDetailRequest` | `QueryBillDetailParameters` |
| Query Vouchers | `instancevoucher` | `DescribeInstanceVouchersRequest` | dict parameters |
| Calculate Total Price | `billing` | `CalculateTotalPriceRequest` | `CalculateTotalPriceParameters` |

**All request classes use `client.send(req)` pattern — no named methods.**

## SDK Pattern

```python
from jdcloud_sdk.services.billing.apis.QueryBillSummaryRequest import (
    QueryBillSummaryRequest,
    QueryBillSummaryParameters,
)

params = QueryBillSummaryParameters(regionId="cn-north-1", startTime="...", endTime="...")
params.setPageIndex(1)
params.setPageSize(100)

req = QueryBillSummaryRequest(parameters=params)
resp = billing_client.send(req)
```

## Request / Response Details

### DescribeAccountAmount (Asset Service)

**Request:**
```python
from jdcloud_sdk.services.asset.apis.DescribeAccountAmountRequest import (
    DescribeAccountAmountRequest,
    DescribeAccountAmountParameters,
)

params = DescribeAccountAmountParameters(regionId="cn-north-1")
req = DescribeAccountAmountRequest(parameters=params)
resp = asset_client.send(req)
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `totalAmount` | number | Total account balance |
| `availableAmount` | number | Available balance |
| `frozenAmount` | number | Frozen amount |
| `withdrawAmount` | number | Withdrawable amount |
| `withdrawingAmount` | number | Amount being withdrawn |

### QueryBillSummary (Billing Service)

**Request:**
```python
from jdcloud_sdk.services.billing.apis.QueryBillSummaryRequest import (
    QueryBillSummaryRequest,
    QueryBillSummaryParameters,
)

params = QueryBillSummaryParameters(
    regionId="cn-north-1",
    startTime="2026-05-01 00:00:00",  # yyyy-MM-dd HH:mm:ss
    endTime="2026-05-31 23:59:59",
)
params.setAppCode(None)      # Optional: product line code
params.setServiceCode(None)  # Optional: product code
params.setPageIndex(1)
params.setPageSize(100)

req = QueryBillSummaryRequest(parameters=params)
resp = billing_client.send(req)
```

**Parameters:**
| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `regionId` | Yes | string | Region ID |
| `startTime` | Yes | string | Start time (yyyy-MM-dd HH:mm:ss) |
| `endTime` | Yes | string | End time (yyyy-MM-dd HH:mm:ss) |
| `appCode` | No | string | Product line code filter |
| `serviceCode` | No | string | Product code filter |
| `pageIndex` | No | int | Page number (default: 1) |
| `pageSize` | No | int | Page size (max: 1000) |

**Response:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of `BillSummary` |
| `totalCount` | int | Total record count |

**BillSummary fields:** `pin`, `appCode`, `serviceCode`, `resourceId`, `totalFee`, `discountFee`, `realTotalFee`, `cashCouponPayFee`, `balancePayFee`, `cashPayFee`, `arrearFee`

### QueryBillDetail (Billing Service)

**Request:**
```python
from jdcloud_sdk.services.billing.apis.QueryBillDetailRequest import (
    QueryBillDetailRequest,
    QueryBillDetailParameters,
)

params = QueryBillDetailParameters(
    regionId="cn-north-1",
    startTime="2026-05-01 00:00:00",
    endTime="2026-05-31 23:59:59",
)
params.setBillingType(3)  # 1=pay-as-you-go 2=pay-by-usage 3=monthly/yearly 4=per-execution
params.setPageIndex(1)
params.setPageSize(100)

req = QueryBillDetailRequest(parameters=params)
resp = billing_client.send(req)
```

**Parameters:**
| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `regionId` | Yes | string | Region ID |
| `startTime` | Yes | string | Start time |
| `endTime` | Yes | string | End time |
| `billingType` | No | int | 1=pay-as-you-go 2=pay-by-usage 3=monthly/yearly 4=per-execution |
| `appCode` | No | string | Product line code |
| `serviceCode` | No | string | Product code |
| `pageIndex` | No | int | Page number |
| `pageSize` | No | int | Page size (max: 1000) |

**Response:**
| Field | Type | Description |
|-------|------|-------------|
| `data` | array | List of `ConsumeBillQueryResultItem` |
| `totalCount` | int | Total record count |

**ConsumeBillQueryResultItem fields:** `billId`, `appCode`, `serviceCode`, `resourceId`, `billingType`, `billFee`, `totalFee`, `cashPayFee`, `cashCouponPayFee`, `balancePayFee`, `discountFee`, `arrearFee`

### DescribeInstanceVouchers (InstanceVoucher Service)

**Request:**
```python
from jdcloud_sdk.services.instancevoucher.apis.DescribeInstanceVouchersRequest import (
    DescribeInstanceVouchersRequest,
)

req = DescribeInstanceVouchersRequest(parameters={
    'regionId': 'cn-north-1',
    'pageNumber': 1,
    'pageSize': 100,
})
resp = voucher_client.send(req)
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `instanceVouchers` | array | List of instance vouchers |
| `totalCount` | int | Total count |

### CalculateTotalPrice (Billing Service)

**Request:**
```python
from jdcloud_sdk.services.billing.apis.CalculateTotalPriceRequest import (
    CalculateTotalPriceRequest,
    CalculateTotalPriceParameters,
)

params = CalculateTotalPriceParameters(
    regionId="cn-north-1",
    cmd=1,        # 1=create 2=renew 3=upgrade 4=delete
    packageCount=1,
)
params.setOrderList([{
    "appCode": "jcloud",
    "serviceCode": "vm",
    "region": "cn-north-1",
    "billingType": 3,       # monthly/yearly
    "timeSpan": 1,
    "timeUnit": "month",
    "spec": "c.n1.large",
}])

req = CalculateTotalPriceRequest(parameters=params)
resp = billing_client.send(req)
```

**Response Fields (OrderPrice):**
| Field | Type | Description |
|-------|------|-------------|
| `totalPrice` | number | Total price |
| `discountedTotalPrice` | number | Price after discount |
| `totalDiscount` | number | Total discount amount |
| `totalOriginalPrice` | number | Original price |

## Pagination Pattern

```python
def query_all_bill_summaries(client, region_id, start_time, end_time):
    all_data = []
    page_index = 1
    page_size = 1000

    while True:
        params = QueryBillSummaryParameters(
            regionId=region_id,
            startTime=start_time,
            endTime=end_time,
        )
        params.setPageIndex(page_index)
        params.setPageSize(page_size)

        req = QueryBillSummaryRequest(parameters=params)
        resp = client.send(req)

        if resp.error:
            raise Exception(f"API Error: {resp.error}")

        all_data.extend(resp.result.data)

        if len(all_data) >= resp.result.totalCount:
            break

        page_index += 1
        if page_index > 100:
            raise Exception("Pagination limit exceeded")

    return all_data
```

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `InvalidParameter` | 400 | Invalid request parameters |
| `InvalidDateRange` | 400 | Date range too large or invalid |
| `Unauthorized` | 401 | Invalid credentials |
| `Forbidden` | 403 | Insufficient permissions |
| `InternalError` | 500 | Internal server error |
| `Throttling` | 429 | Rate limit exceeded |
