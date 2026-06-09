# Integration

## Environment Setup (uv)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
```

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.apigateway.client import ApigatewayClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = ApigatewayClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

## SDK Endpoint

The API Gateway SDK uses the following endpoint:
- **Base**: `https://apigateway.jdcloud-api.com`
- **Region-aware**: The client constructor accepts a region parameter that determines the endpoint

## Authentication

The SDK uses JD Cloud signature V3 authentication:
- Access Key ID + Secret Key
- Request signing is handled automatically by the SDK

## Integration with Other Skills

### With Function Compute (`jdcloud-fc-ops`)
```python
# 1. Create function via jdcloud-fc-ops
# 2. Create API Gateway API with FC backend (this skill)
# 3. Deploy API to stage (this skill)
```

### With WAF (`jdcloud-waf-ops`)
```python
# 1. Create API Gateway APIs and deploy (this skill)
# 2. Add custom domain to API Gateway
# 3. Configure WAF protection for the domain (jdcloud-waf-ops)
```

### with CloudMonitor (`jdcloud-cloudmonitor-ops`)
```python
# Set up alarms on:
# - ApiGatewayInvocationErrorCount
# - ApiGatewayInvocationLatency
# - ApiGatewayThrottledCount
# - ApiGateway5xxErrorCount
```

### with CLB (`jdcloud-clb-ops`)
```python
# API Gateway can route to CLB backends:
# 1. Configure CLB with backend servers (jdcloud-clb-ops)
# 2. Set CLB endpoint as API Gateway backend (this skill)
```

## Version Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.10 | Required; 3.12 not supported |
| jdcloud_sdk | >=1.6.26 | Verify against OpenAPI |
| API Gateway API | v1.0 | Current stable version |

## SDK-only Notes

Since API Gateway is **not supported** by the `jdc` CLI:
- All operations MUST use the Python SDK
- No CLI verification step is available
- Use SDK health checks to verify connectivity:
  ```python
  # Verify by describing API groups
  req = DescribeApiGroupsRequest(regionId="cn-north-1", pageNumber=1, pageSize=1)
  resp = client.describeApiGroups(req)
  print(f"SDK connection OK. Total groups: {resp.result.totalCount}")
  ```
