# API & SDK — JD Cloud Load Balancer (CLB)

> **ponytail: operation map + required fields kept. Full request/response examples in SKILL.md execution flows.**

## SDK Operations Map

| Goal | SDK Method | CLI Command |
|------|------------|-------------|
| Create LB | `CreateLoadBalancerRequest` | `lb create-load-balancer` |
| Describe LB | `DescribeLoadBalancerRequest` | `lb describe-load-balancer` |
| List LBs | `DescribeLoadBalancersRequest` | `lb describe-load-balancers` |
| Modify LB | `ModifyLoadBalancerRequest` | `lb modify-load-balancer` |
| Delete LB | `DeleteLoadBalancerRequest` | `lb delete-load-balancer` |
| Create Listener | `CreateListenerRequest` | `lb create-listener` |
| Describe Listeners | `DescribeListenersRequest` | `lb describe-listeners` |
| Modify Listener | `ModifyListenerRequest` | `lb modify-listener` |
| Delete Listener | `DeleteListenerRequest` | `lb delete-listener` |
| Register Targets | `RegisterTargetsRequest` | `lb register-targets` |
| Deregister Targets | `DeregisterTargetsRequest` | `lb deregister-targets` |
| Describe Targets | `DescribeTargetsRequest` | `lb describe-targets` |
| Update Health Check | `UpdateHealthCheckRequest` | `lb update-health-check` |
| Describe Health Check | `DescribeHealthCheckRequest` | `lb describe-health-check` |

## Required Fields

### Create Load Balancer

| Field | Type | Description |
|-------|------|-------------|
| `loadBalancerName` | string | LB name |
| `vpcId` | string | VPC ID |
| `subnetId` | string | Subnet ID |
| `azs` | array | Availability zones |
| `loadBalancerSpec` | string | Optional: small/medium/large |

### Create Listener

| Field | Type | Description |
|-------|------|-------------|
| `loadBalancerId` | string | LB ID |
| `protocol` | string | TCP/UDP/HTTP/HTTPS |
| `port` | integer | 1-65535 |
| `backendPort` | integer | 1-65535 |

### Register Targets

| Field | Type | Description |
|-------|------|-------------|
| `loadBalancerId` | string | LB ID |
| `targetGroupId` | string | Target group ID |
| `instanceId` | string | VM instance ID |
| `port` | integer | Target port |
| `weight` | integer | Optional: 1-100, default 100 |

## SDK Import Pattern

```python
from jdcloud_sdk.services.lb.client.LbClient import LbClient
# API request classes follow: from jdcloud_sdk.services.lb.apis.<Operation>Request import <Operation>Request, <Operation>Parameters
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| InvalidParameter | 400 | Bad request |
| ResourceNotFound | 404 | Resource not found |
| ResourceAlreadyExists | 409 | Duplicate resource |
| QuotaExceeded | 400 | Quota limit |
| InsufficientBalance | 400 | Insufficient funds |
| InternalError | 500 | Server error |
| ServiceUnavailable | 503 | Temporarily unavailable |