# CLI Usage — jdcloud-billing-ops

## CLI Applicability

**SDK-only**: The `jdc` CLI does **not** expose billing operations. This has been
verified by running `jdc --help` — no billing product is listed.

All billing operations must use the JD Cloud Python SDK (`jdcloud_sdk`).

## SDK Client Setup

| Service | Client Class | Package |
|---------|-------------|---------|
| Billing | `BillingClient` | `jdcloud_sdk.services.billing.client` |
| Asset (balance) | `AssetClient` | `jdcloud_sdk.services.asset.client` |
| InstanceVoucher | `InstancevoucherClient` | `jdcloud_sdk.services.instancevoucher.client` |

## Alternative: SDK Script

```bash
# Install SDK
uv pip install jdcloud_sdk

# Run billing query script
python -c "
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.asset.client.AssetClient import AssetClient
from jdcloud_sdk.services.asset.apis.DescribeAccountAmountRequest import (
    DescribeAccountAmountRequest,
    DescribeAccountAmountParameters,
)

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = AssetClient(credential)

params = DescribeAccountAmountParameters(regionId=os.environ.get('JDC_REGION', 'cn-north-1'))
req = DescribeAccountAmountRequest(parameters=params)
resp = client.send(req)
print(f'Balance: {resp.result.totalAmount}')
"
```
