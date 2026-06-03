# API & SDK — JD Cloud EIP

## OpenAPI

- **Spec**: https://docs.jdcloud.com/cn/eip/api-reference
- **Base path**: `https://eip.jdcloud-api.com/v1/regions/{regionId}/addresses`
- **API version**: v1

## SDK Operations Map

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Allocate EIP | allocateAddress | `AllocateAddressRequest` |
| Describe EIP | describeAddress | `DescribeAddressRequest` |
| List EIPs | describeAddresses | `DescribeAddressesRequest` |
| Associate EIP | associateAddress | `AssociateAddressRequest` |
| Dissociate EIP | dissociateAddress | `DissociateAddressRequest` |
| Modify EIP | modifyAddress | `ModifyAddressRequest` |
| Release EIP | releaseAddress | `ReleaseAddressRequest` |

## Request / Response Notes

### Required Fields

- `regionId`: Target region for the EIP operation
- `addressId`: EIP ID for describe, modify, associate, dissociate, and release operations
- `addressName`: Name for the EIP when allocating (optional but recommended)
- `bandwidth`: Bandwidth in Mbps (default: 5 Mbps)

### Optional Fields

- `instanceId`: Target resource ID for association
- `instanceType`: Type of resource (`vm`, `clb`, `nat`)
- `pageNumber`: Page number for pagination (default: 1)
- `pageSize`: Page size for pagination (default: 10, max: 100)

### Response Structure

```json
{
  "result": {
    "addressId": "string",
    "publicIp": "string",
    "addressName": "string",
    "status": "string",
    "bandwidth": "integer",
    "billingType": "string",
    "instanceId": "string",
    "instanceType": "string",
    "createdTime": "string"
  },
  "requestId": "string"
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | InvalidParameter | Invalid input parameters |
| 401 | Unauthorized | Invalid credentials |
| 403 | Forbidden | Insufficient permissions |
| 404 | NotFound | Resource not found |
| 409 | Conflict | Resource conflict (e.g., EIP already associated) |
| 429 | Throttling | Request rate limit exceeded |
| 500 | InternalError | Internal server error |

## Pagination

List operations support pagination:
- `pageNumber`: Starting from 1
- `pageSize`: Maximum 100 items per page

## SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.eip.client.EipClient import EipClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = EipClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

## Example: Allocate EIP

```python
from jdcloud_sdk.services.eip.apis.AllocateAddressRequest import AllocateAddressRequest, AllocateAddressParameters

params = AllocateAddressParameters(regionId="cn-north-1")
params.setAddressName("my-eip")
params.setBandwidth(10)
req = AllocateAddressRequest(parameters=params)
resp = client.send(req)

if resp.error is None:
    print(f"EIP ID: {resp.result['addressId']}")
    print(f"Public IP: {resp.result['publicIp']}")
else:
    print(f"Error: {resp.error.message}")
```
