# API & SDK — JD Cloud VPN

## OpenAPI

- **Service Endpoint**: `https://vpn.jdcloud-api.com`
- **API Version**: v1
- **Base Path**: `/v1/regions/{regionId}/vpnGateways/{vpnGatewayId}/...`
- **Spec Reference**: JD Cloud OpenAPI documentation — VPN product

## SDK Operations Map

| Goal | API operationId | SDK Class (illustrative) | jdc CLI Command |
|------|----------------|--------------------------|-----------------|
| Create VpnGateway | createVpnGateway | `CreateVpnGatewayRequest` | `jdc vpn create-vpn-gateway` |
| Describe VpnGateway | describeVpnGateway | `DescribeVpnGatewayRequest` | `jdc vpn describe-vpn-gateway` |
| Describe VpnGateways | describeVpnGateways | `DescribeVpnGatewaysRequest` | `jdc vpn describe-vpn-gateways` |
| Delete VpnGateway | deleteVpnGateway | `DeleteVpnGatewayRequest` | `jdc vpn delete-vpn-gateway` |
| Create CustomerGateway | createCustomerGateway | `CreateCustomerGatewayRequest` | `jdc vpn create-customer-gateway` |
| Describe CustomerGateway | describeCustomerGateway | `DescribeCustomerGatewayRequest` | `jdc vpn describe-customer-gateway` |
| Describe CustomerGateways | describeCustomerGateways | `DescribeCustomerGatewaysRequest` | `jdc vpn describe-customer-gateways` |
| Delete CustomerGateway | deleteCustomerGateway | `DeleteCustomerGatewayRequest` | `jdc vpn delete-customer-gateway` |
| Create VpnConnection | createVpnConnection | `CreateVpnConnectionRequest` | `jdc vpn create-vpn-connection` |
| Describe VpnConnection | describeVpnConnection | `DescribeVpnConnectionRequest` | `jdc vpn describe-vpn-connection` |
| Describe VpnConnections | describeVpnConnections | `DescribeVpnConnectionsRequest` | `jdc vpn describe-vpn-connections` |
| Delete VpnConnection | deleteVpnConnection | `DeleteVpnConnectionRequest` | `jdc vpn delete-vpn-connection` |

> **Note:** SDK class names above are illustrative. Verify exact names against the installed `jdcloud_sdk` package under `jdcloud_sdk.services.vpn.apis`.

## SDK Client Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpn.client.VpnClient import VpnClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = VpnClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

## Request / Response Notes

### Pagination

List APIs (`describeVpnGateways`, `describeCustomerGateways`, `describeVpnConnections`) support pagination:
- `pageNumber`: 1-based page index
- `pageSize`: Items per page (max 100)
- Response contains `totalCount` for total items

### Filters

Some list APIs support filters (verify in OpenAPI spec):
- `vpcId` for `describeVpnGateways`
- `vpnGatewayId` for `describeVpnConnections`

### Error Codes (Common)

| Code | HTTP | Meaning |
|------|------|---------|
| `InvalidParameter` | 400 | Request validation failed |
| `ResourceNotFound` | 404 | Resource does not exist |
| `ResourceInUse` | 409 | Resource is referenced by other resources |
| `QuotaExceeded` | 400 | Quota limit reached |
| `InternalError` | 500 | Server-side error |

### Idempotency

- VPN Gateway creation is **not** idempotent by name. Check for existing resources before creating.
- Customer Gateway creation with the same IP may succeed or fail depending on API behavior; verify by listing first.
- Delete operations are idempotent after the resource is already deleted (may return `ResourceNotFound`).