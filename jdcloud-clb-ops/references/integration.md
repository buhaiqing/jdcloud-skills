# Integration — JD Cloud Load Balancer

## Python SDK Bootstrap

### Installation

```bash
pip install jdcloud-sdk
```

### Version Pinning

For stable integration, pin SDK version to ensure API compatibility:

```bash
pip install jdcloud-sdk==1.6.42
```

#### SDK/CLI Compatibility Matrix

| Release Date | JD Cloud CLI | JD Cloud Python SDK | Recommended for ALB/NLB |
|--------------|--------------|---------------------|-------------------------|
| 2019-09-05 | 1.2.0 | 1.6.10 | Minimum compatible |
| 2019-11-11 | 1.2.2 | 1.6.30 | Stable |
| 2019-12-31 | 1.2.3 | 1.6.38 | Stable |
| 2020-01-19 | 1.2.5 | 1.6.42 | **Recommended** |
| Latest | — | >= 1.6.42 | Current |

> **Note**: JD Cloud CLI does not support ALB/NLB products. SDK-only integration required.

#### Requirements File Example

```text
# requirements.txt for jdcloud-clb-ops integration
jdcloud-sdk==1.6.42
requests>=2.28.0
python-dateutil>=2.8.0
```

#### Version Verification

```python
import jdcloud_sdk
print(f"JD Cloud SDK version: {jdcloud_sdk.__version__}")

# Expected output: 1.6.42 or higher
```

Refer to CLI/SDK compatibility matrix: https://github.com/jdcloud-api/jdcloud-cli

### Client Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.alb.client import AlbClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)

client = AlbClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> **Security Note**: Use `os.environ["KEY"]` for secrets (fail-fast). Use `.get()` only for optional non-secret config.

## Environment Variables

| Variable | Required | Description | Source |
|----------|----------|-------------|--------|
| `JDC_ACCESS_KEY` | Yes | JD Cloud Access Key | JD Cloud Console → Account Management → Access Key |
| `JDC_SECRET_KEY` | Yes | JD Cloud Secret Key | JD Cloud Console (same as above) |
| `JDC_REGION` | No | Default region ID | Default: `cn-north-1` |

### Setting Environment Variables

```bash
# Linux / macOS
export JDC_ACCESS_KEY="your-access-key"
export JDC_SECRET_KEY="your-secret-key"
export JDC_REGION="cn-north-1"

# Windows (PowerShell)
$env:JDC_ACCESS_KEY="your-access-key"
$env:JDC_SECRET_KEY="your-secret-key"
$env:JDC_REGION="cn-north-1"
```

### Credential Verification

```python
# Test credential validity
from jdcloud_sdk.services.alb.apis.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest

req = DescribeLoadBalancersRequest(regionId="cn-north-1", pageNumber=1, pageSize=1)
resp = client.describeLoadBalancers(req)

if resp.error is None:
    print("Credentials valid")
else:
    print(f"Credential error: {resp.error.message}")
```

## API Endpoints

| Service | Public Endpoint | Internal Endpoint (VPC) |
|---------|-----------------|-------------------------|
| ALB | `https://alb.jdcloud-api.com/v1` | `https://alb.internal.{region}.jdcloud-api.com/v1` |
| NLB | `https://nlb.jdcloud-api.com/v1` | `https://nlb.internal.{region}.jdcloud-api.com/v1` |

**Region-specific internal endpoint**: Replace `{region}` with region ID (e.g., `cn-north-1`).

## SDK Modules

### ALB SDK Structure

```
jdcloud_sdk.services.alb
├── client.py                 # AlbClient
├── apis/
│   ├── CreateLoadBalancerRequest.py
│   ├── DescribeLoadBalancerRequest.py
│   ├── DescribeLoadBalancersRequest.py
│   ├── DeleteLoadBalancerRequest.py
│   ├── UpdateLoadBalancerRequest.py
│   ├── CreateListenerRequest.py
│   ├── DescribeListenerRequest.py
│   ├── DescribeListenersRequest.py
│   ├── DeleteListenerRequest.py
│   ├── CreateTargetGroupRequest.py
│   ├── RegisterTargetsRequest.py
│   ├── DescribeTargetHealthRequest.py
│   ├── CreateUrlMapRequest.py
│   ├── CreateSecurityPolicyRequest.py
│   └── ...
└── models/
    └── LoadBalancer, Listener, TargetGroup, etc.
```

### NLB SDK Structure

Similar structure under `jdcloud_sdk.services.nlb`.

## Cross-Product Integration

### VPC Integration

Load Balancer requires VPC. Use `jdcloud-vpc-ops` for VPC/subnet verification:

```python
# Verify VPC exists before creating LB
from jdcloud_sdk.services.vpc.apis.DescribeVpcRequest import DescribeVpcRequest
from jdcloud_sdk.services.vpc.client import VpcClient

vpc_client = VpcClient(credential, region)
vpc_req = DescribeVpcRequest(regionId=region, vpcId=vpc_id)
vpc_resp = vpc_client.describeVpc(vpc_req)

if vpc_resp.result.vpc is None:
    raise ValueError("VPC not found — create VPC first via jdcloud-vpc-ops")
```

### VM Integration

Backend servers are often VMs. Use `jdcloud-vm-ops` to verify VM status:

```python
# Verify VM is running before registering as target
from jdcloud_sdk.services.vm.apis.DescribeInstancesRequest import DescribeInstancesRequest
from jdcloud_sdk.services.vm.client import VmClient

vm_client = VmClient(credential, region)
vm_req = DescribeInstancesRequest(regionId=region, instanceIds=[vm_id])
vm_resp = vm_client.describeInstances(vm_req)

vm_status = vm_resp.result.instances[0].status
if vm_status != "running":
    raise ValueError(f"VM {vm_id} not running — status: {vm_status}")
```

### SSL Certificate Integration

HTTPS listeners require SSL certificates. Certificates are managed in JD Cloud SSL Certificate service.

```python
# Certificate binding for HTTPS listener
cert_spec = {
    "certificateId": "cert-xxx",  # From SSL Certificate service
    "tlsSecurityPolicyId": "tls-policy-default"
}

listener_spec = CreateListenerSpec(
    protocol="https",
    port=443,
    certificateSpec=cert_spec,
    # ...
)
```

For certificate issuance/upload, use `ssl-certificate` skill.

### Cloud Monitor Integration

Metric queries delegate to `jdcloud-cloudmonitor-ops`:

```python
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.services.monitor.apis.DescribeMetricDataRequest import DescribeMetricDataRequest

monitor_client = MonitorClient(credential, region)
metric_req = DescribeMetricDataRequest(
    namespace="alb",
    metric="activeConnections",
    dimensions=[{"loadBalancerId": "lb-abc"}],
    startTime="2026-05-01T00:00:00Z",
    endTime="2026-05-03T00:00:00Z"
)
```

## Error Handling Patterns

### Retry with Exponential Backoff

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "InternalError" in str(e) or "Throttling" in str(e):
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                    else:
                        raise
            raise RuntimeError(f"Max retries exceeded for {func.__name__}")
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def create_loadbalancer_with_retry(client, req):
    return client.createLoadBalancer(req)
```

### Error Classification

```python
def classify_error(resp):
    if resp.error is None:
        return "success"
    
    code = resp.error.code
    if code in ("InvalidParameter", "NameAlreadyExists"):
        return "client_error"  # Do not retry
    elif code in ("QuotaExceeded", "InsufficientBalance"):
        return "business_error"  # HALT
    elif code in ("Throttling", "InternalError"):
        return "retryable_error"  # Retry with backoff
    else:
        return "unknown_error"
```

## Rate Limits

| Operation | Rate Limit | Notes |
|-----------|------------|-------|
| Read operations (describe/list) | 100 req/min | Per account per region |
| Write operations (create/update/delete) | 20 req/min | Per account per region |

**Recommendation**: Batch read operations; throttle write operations; use exponential backoff for throttling errors.

## MCP Integration

For JD Cloud Load Balancer operations via MCP (if MCP server available), follow MCP tool calling patterns per repository MCP documentation.

## Testing

### Unit Test Pattern

```python
import unittest
from unittest.mock import MagicMock

class TestLoadBalancerOps(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=AlbClient)
    
    def test_create_lb_success(self):
        mock_resp = MagicMock()
        mock_resp.result.loadBalancerId = "lb-test"
        self.client.createLoadBalancer.return_value = mock_resp
        
        req = CreateLoadBalancerRequest(regionId="cn-north-1", spec=...)
        resp = self.client.createLoadBalancer(req)
        
        self.assertEqual(resp.result.loadBalancerId, "lb-test")
```

### Integration Test Pattern

```python
def test_lb_lifecycle():
    # Create
    create_req = CreateLoadBalancerRequest(...)
    create_resp = client.createLoadBalancer(create_req)
    lb_id = create_resp.result.loadBalancerId
    
    # Wait for active
    poll_until_active(client, lb_id)
    
    # Describe
    desc_resp = client.describeLoadBalancer(DescribeLoadBalancerRequest(
        regionId=region, loadBalancerId=lb_id
    ))
    assert desc_resp.result.loadBalancer.status == "active"
    
    # Delete
    client.deleteLoadBalancer(DeleteLoadBalancerRequest(
        regionId=region, loadBalancerId=lb_id
    ))
    
    # Wait for deletion
    poll_until_deleted(client, lb_id)
```

## See Also

- [JD Cloud SDK GitHub](https://github.com/jdcloud-api/jdcloud-sdk-python)
- [JD Cloud API Reference](https://docs.jdcloud.com/cn/common-declaration/api/introduction)
- [Core Concepts](core-concepts.md)
- [Troubleshooting](troubleshooting.md)