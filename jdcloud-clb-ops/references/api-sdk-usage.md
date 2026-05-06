# API & SDK — JD Cloud Load Balancer (CLB)

## OpenAPI Specification

- **Base URL**: `https://lb.jdcloud-api.com/v1`
- **API Version**: v1
- **Protocol**: HTTPS
- **Authentication**: Access Key + Secret Key (HMAC-SHA256)

## SDK Operations Map

| Goal | API Operation ID | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Load Balancer | createLoadBalancer | `CreateLoadBalancerRequest` | `lb create-load-balancer` |
| Describe Load Balancer | describeLoadBalancer | `DescribeLoadBalancerRequest` | `lb describe-load-balancer` |
| Describe Load Balancers | describeLoadBalancers | `DescribeLoadBalancersRequest` | `lb describe-load-balancers` |
| Modify Load Balancer | modifyLoadBalancer | `ModifyLoadBalancerRequest` | `lb modify-load-balancer` |
| Delete Load Balancer | deleteLoadBalancer | `DeleteLoadBalancerRequest` | `lb delete-load-balancer` |
| Create Listener | createListener | `CreateListenerRequest` | `lb create-listener` |
| Describe Listener | describeListener | `DescribeListenerRequest` | `lb describe-listener` |
| Describe Listeners | describeListeners | `DescribeListenersRequest` | `lb describe-listeners` |
| Modify Listener | modifyListener | `ModifyListenerRequest` | `lb modify-listener` |
| Delete Listener | deleteListener | `DeleteListenerRequest` | `lb delete-listener` |
| Register Targets | registerTargets | `RegisterTargetsRequest` | `lb register-targets` |
| Deregister Targets | deregisterTargets | `DeregisterTargetsRequest` | `lb deregister-targets` |
| Describe Targets | describeTargets | `DescribeTargetsRequest` | `lb describe-targets` |
| Update Health Check | updateHealthCheck | `UpdateHealthCheckRequest` | `lb update-health-check` |
| Describe Health Check | describeHealthCheck | `DescribeHealthCheckRequest` | `lb describe-health-check` |

## Request/Response Examples

### Create Load Balancer

**Request:**
```json
{
  "regionId": "cn-north-1",
  "loadBalancerSpec": {
    "loadBalancerName": "my-lb",
    "vpcId": "vpc-xxx",
    "subnetId": "subnet-xxx",
    "azs": ["cn-north-1a"],
    "loadBalancerSpec": "small"
  }
}
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "loadBalancerId": "lb-xxx"
  }
}
```

### Create Listener

**Request:**
```json
{
  "regionId": "cn-north-1",
  "loadBalancerId": "lb-xxx",
  "listenerSpec": {
    "protocol": "TCP",
    "port": 80,
    "backendPort": 8080,
    "listenerName": "http-listener"
  }
}
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "listenerId": "listener-xxx"
  }
}
```

### Register Targets

**Request:**
```json
{
  "regionId": "cn-north-1",
  "loadBalancerId": "lb-xxx",
  "targetGroupId": "tg-xxx",
  "targetSpecs": [
    {
      "instanceId": "vm-xxx",
      "port": 8080,
      "weight": 100
    }
  ]
}
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "targetIds": ["target-xxx"]
  }
}
```

## Required Fields

### Create Load Balancer

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| regionId | string | Yes | Region ID |
| loadBalancerName | string | Yes | Load balancer name |
| vpcId | string | Yes | VPC ID |
| subnetId | string | Yes | Subnet ID |
| azs | array | Yes | Availability zones |
| loadBalancerSpec | string | No | Specification (small/medium/large) |

### Create Listener

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| regionId | string | Yes | Region ID |
| loadBalancerId | string | Yes | Load balancer ID |
| protocol | string | Yes | Protocol (TCP/UDP/HTTP/HTTPS) |
| port | integer | Yes | Listener port (1-65535) |
| backendPort | integer | Yes | Backend port (1-65535) |
| listenerName | string | No | Listener name |

### Register Targets

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| regionId | string | Yes | Region ID |
| loadBalancerId | string | Yes | Load balancer ID |
| targetGroupId | string | Yes | Target group ID |
| instanceId | string | Yes | VM instance ID |
| port | integer | Yes | Target port |
| weight | integer | No | Weight (1-100, default: 100) |

## Pagination

List operations support pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| pageNumber | integer | 1 | Page number |
| pageSize | integer | 20 | Items per page (max: 100) |

**Response pagination fields:**
```json
{
  "result": {
    "loadBalancers": [...],
    "totalCount": 50
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| InvalidParameter | 400 | Invalid request parameter |
| ResourceNotFound | 404 | Resource does not exist |
| ResourceAlreadyExists | 409 | Resource already exists |
| QuotaExceeded | 400 | Quota limit exceeded |
| InsufficientBalance | 400 | Account balance insufficient |
| InternalError | 500 | Internal server error |
| ServiceUnavailable | 503 | Service temporarily unavailable |

## SDK Import Pattern

```python
# Client
from jdcloud_sdk.services.lb.client.LbClient import LbClient

# APIs
from jdcloud_sdk.services.lb.apis.CreateLoadBalancerRequest import CreateLoadBalancerRequest, CreateLoadBalancerParameters
from jdcloud_sdk.services.lb.apis.DescribeLoadBalancerRequest import DescribeLoadBalancerRequest, DescribeLoadBalancerParameters
from jdcloud_sdk.services.lb.apis.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest, DescribeLoadBalancersParameters
from jdcloud_sdk.services.lb.apis.ModifyLoadBalancerRequest import ModifyLoadBalancerRequest, ModifyLoadBalancerParameters
from jdcloud_sdk.services.lb.apis.DeleteLoadBalancerRequest import DeleteLoadBalancerRequest, DeleteLoadBalancerParameters
from jdcloud_sdk.services.lb.apis.CreateListenerRequest import CreateListenerRequest, CreateListenerParameters
from jdcloud_sdk.services.lb.apis.DescribeListenersRequest import DescribeListenersRequest, DescribeListenersParameters
from jdcloud_sdk.services.lb.apis.ModifyListenerRequest import ModifyListenerRequest, ModifyListenerParameters
from jdcloud_sdk.services.lb.apis.DeleteListenerRequest import DeleteListenerRequest, DeleteListenerParameters
from jdcloud_sdk.services.lb.apis.RegisterTargetsRequest import RegisterTargetsRequest, RegisterTargetsParameters
from jdcloud_sdk.services.lb.apis.DeregisterTargetsRequest import DeregisterTargetsRequest, DeregisterTargetsParameters
from jdcloud_sdk.services.lb.apis.DescribeTargetsRequest import DescribeTargetsRequest, DescribeTargetsParameters
from jdcloud_sdk.services.lb.apis.UpdateHealthCheckRequest import UpdateHealthCheckRequest, UpdateHealthCheckParameters
from jdcloud_sdk.services.lb.apis.DescribeHealthCheckRequest import DescribeHealthCheckRequest, DescribeHealthCheckParameters
```
