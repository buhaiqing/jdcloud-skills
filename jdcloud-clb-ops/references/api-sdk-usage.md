# API & SDK — JD Cloud Load Balancer

## OpenAPI Reference

### Application Load Balancer (ALB)

- **Spec**: JD Cloud ALB OpenAPI v1
- **Base Path**: `https://alb.jdcloud-api.com/v1/regions/{regionId}/`
- **Doc**: https://docs.jdcloud.com/cn/application-load-balancer/api-overview

### Network Load Balancer (NLB)

- **Spec**: JD Cloud NLB OpenAPI v1
- **Base Path**: `https://nlb.jdcloud-api.com/v1/regions/{regionId}/`
- **Doc**: https://docs.jdcloud.com/cn/network-load-balancer/api-overview

### API Style

- RESTful with JD Cloud signature mechanism
- HTTP methods: GET (query), POST (create), PUT/PATCH (modify), DELETE (delete)
- Authentication: Access Key + Secret Key signing

## SDK Operations Map (ALB/NLB)

### Load Balancer Operations

| Goal | API operationId | SDK Method | HTTP Method |
|------|-----------------|------------|-------------|
| Create LB | `createLoadBalancer` | `client.createLoadBalancer(req)` | POST |
| Describe LB | `describeLoadBalancer` | `client.describeLoadBalancer(req)` | GET |
| List LBs | `describeLoadBalancers` | `client.describeLoadBalancers(req)` | GET |
| Update LB | `updateLoadBalancer` | `client.updateLoadBalancer(req)` | PATCH |
| Delete LB | `deleteLoadBalancer` | `client.deleteLoadBalancer(req)` | DELETE |
| Bind EIP | `associateElasticIp` | `client.associateElasticIp(req)` | POST |
| Unbind EIP | `disassociateElasticIp` | `client.disassociateElasticIp(req)` | POST |
| Bind Security Group | `associateSecurityGroup` | `client.associateSecurityGroup(req)` | POST |
| Unbind Security Group | `disassociateSecurityGroup` | `client.disassociateSecurityGroup(req)` | POST |

### Listener Operations

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Listener | `createListener` | `client.createListener(req)` |
| Describe Listener | `describeListener` | `client.describeListener(req)` |
| List Listeners | `describeListeners` | `client.describeListeners(req)` |
| Update Listener | `updateListener` | `client.updateListener(req)` |
| Delete Listener | `deleteListener` | `client.deleteListener(req)` |
| Add Listener Certificates | `addListenerCertificates` | `client.addListenerCertificates(req)` |
| Delete Listener Certificates | `deleteListenerCertificates` | `client.deleteListenerCertificates(req)` |
| Update Listener Certificates | `updateListenerCertificates` | `client.updateListenerCertificates(req)` |

### Backend Service Operations

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Backend | `createBackend` | `client.createBackend(req)` |
| Describe Backend | `describeBackend` | `client.describeBackend(req)` |
| List Backends | `describeBackends` | `client.describeBackends(req)` |
| Update Backend | `updateBackend` | `client.updateBackend(req)` |
| Delete Backend | `deleteBackend` | `client.deleteBackend(req)` |
| Describe Target Health | `describeTargetHealth` | `client.describeTargetHealth(req)` |
| Describe AG Targets | `describeAgTargets` | `client.describeAgTargets(req)` |
| Update AG Targets | `updateAgTargets` | `client.updateAgTargets(req)` |

### Target Group Operations

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Target Group | `createTargetGroup` | `client.createTargetGroup(req)` |
| Describe Target Group | `describeTargetGroup` | `client.describeTargetGroup(req)` |
| List Target Groups | `describeTargetGroups` | `client.describeTargetGroups(req)` |
| Update Target Group | `updateTargetGroup` | `client.updateTargetGroup(req)` |
| Delete Target Group | `deleteTargetGroup` | `client.deleteTargetGroup(req)` |
| Register Targets | `registerTargets` | `client.registerTargets(req)` |
| Deregister Targets | `deRegisterTargets` | `client.deRegisterTargets(req)` |
| Update Targets | `updateTargets` | `client.updateTargets(req)` |
| Describe Targets | `describeTargets` | `client.describeTargets(req)` |

### Forwarding Rule Operations (ALB Only)

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create UrlMap | `createUrlMap` | `client.createUrlMap(req)` |
| Describe UrlMap | `describeUrlMap` | `client.describeUrlMap(req)` |
| List UrlMaps | `describeUrlMaps` | `client.describeUrlMaps(req)` |
| Update UrlMap | `updateUrlMap` | `client.updateUrlMap(req)` |
| Delete UrlMap | `deleteUrlMap` | `client.deleteUrlMap(req)` |
| Add Rules | `addRules` | `client.addRules(req)` |
| Update Rules | `updateRules` | `client.updateRules(req)` |
| Delete Rules | `deleteRules` | `client.deleteRules(req)` |

### TLS Security Policy Operations

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Security Policy | `createSecurityPolicy` | `client.createSecurityPolicy(req)` |
| Describe Security Policy | `describeSecurityPolicy` | `client.describeSecurityPolicy(req)` |
| List Security Policies | `describeSecurityPolicies` | `client.describeSecurityPolicies(req)` |
| Update Security Policy | `updateSecurityPolicy` | `client.updateSecurityPolicy(req)` |
| Delete Security Policy | `deleteSecurityPolicy` | `client.deleteSecurityPolicy(req)` |
| Describe Supported Ciphers | `describeSupportedCiphers` | `client.describeSupportedCiphers(req)` |

## Request / Response Notes

### Common Request Structure

```json
{
  "regionId": "cn-north-1",
  "loadBalancerId": "lb-xxxx",
  // operation-specific parameters
}
```

### Pagination

- Parameters: `pageNumber` (default: 1), `pageSize` (default: 20, max: 100)
- Response: `totalCount`, `pageNumber`, `pageSize`, plus result array

### Required Fields by Operation

#### createLoadBalancer

| Field | Required | Description |
|-------|----------|-------------|
| regionId | Yes | Target region |
| name | Yes | LB name (unique in region) |
| vpcId | Yes | VPC ID |
| type | Yes | `application` / `network` |
| azs | Yes (ALB) | Availability zone mappings |
| subnetMappings | Yes (ALB) | Subnet and AZ configuration |
| chargeMode | No | Default: `postpaid_by_usage` |

#### createListener

| Field | Required | Description |
|-------|----------|-------------|
| regionId | Yes | Target region |
| loadBalancerId | Yes | Parent LB ID |
| protocol | Yes | HTTP / HTTPS / TCP / UDP |
| port | Yes | Listener port (1-65535) |
| certificateSpec | Yes (HTTPS/TLS) | Certificate binding |

#### registerTargets

| Field | Required | Description |
|-------|----------|-------------|
| regionId | Yes | Target region |
| targetGroupId | Yes | Target group ID |
| targets | Yes | List of target specs (targetId, port, weight) |

### Response Status Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | InvalidParameter — request validation failed |
| 401 | Authentication failed |
| 403 | Permission denied / IAM policy restriction |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate name) |
| 429 | Request throttled |
| 500 | InternalError — retry with backoff |

### Response JSON Structure

```json
{
  "requestId": "bcf...xxx",
  "result": {
    "loadBalancerId": "lb-abc123",
    "name": "my-alb",
    "status": "active",
    "vip": "10.0.1.100",
    "eip": null,
    // additional fields
  },
  "error": null
}
```

Error response:

```json
{
  "requestId": "bcf...xxx",
  "error": {
    "code": "InvalidParameter",
    "message": "Name already exists",
    "status": 400
  }
}
```

## Idempotency

- **Create Operations**: LB names must be unique within region. Duplicate name returns `NameAlreadyExists` error — NOT auto-idempotent.
- **Delete Operations**: Deleting non-existent LB returns 404 (safe to retry).
- **Update Operations**: Same state update returns success (idempotent).

## SDK Code Examples

### Python SDK Setup

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.alb.client import AlbClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = AlbClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

### Create ALB Instance

```python
from jdcloud_sdk.services.alb.apis.CreateLoadBalancerRequest import (
    CreateLoadBalancerRequest,
    CreateLoadBalancerSpec,
    AzSpec
)

azs = [
    AzSpec(azId="cn-north-1a", subnetId="subnet-aaa"),
    AzSpec(azId="cn-north-1b", subnetId="subnet-bbb"),
]

spec = CreateLoadBalancerSpec(
    name="web-alb",
    vpcId="vpc-xxx",
    type="application",
    azs=azs,
    chargeMode="postpaid_by_usage"
)

req = CreateLoadBalancerRequest(regionId="cn-north-1", spec=spec)
resp = client.createLoadBalancer(req)

lb_id = resp.result.loadBalancerId
print(f"Created LB: {lb_id}")
```

### Create HTTPS Listener

```python
from jdcloud_sdk.services.alb.apis.CreateListenerRequest import (
    CreateListenerRequest,
    CreateListenerSpec,
    CertificateSpec
)

cert_spec = CertificateSpec(certificateId="cert-xxx")

spec = CreateListenerSpec(
    loadBalancerId="lb-abc",
    protocol="https",
    port=443,
    certificateSpec=cert_spec,
    tlsSecurityPolicyId="tls-policy-default"
)

req = CreateListenerRequest(regionId="cn-north-1", spec=spec)
resp = client.createListener(req)

listener_id = resp.result.listenerId
print(f"Created Listener: {listener_id}")
```

### Register Backend Targets

```python
from jdcloud_sdk.services.alb.apis.RegisterTargetsRequest import (
    RegisterTargetsRequest,
    TargetSpec
)

targets = [
    TargetSpec(targetId="i-vm001", port=8080, weight=10),
    TargetSpec(targetId="i-vm002", port=8080, weight=10),
]

req = RegisterTargetsRequest(
    regionId="cn-north-1",
    targetGroupId="tg-web",
    targets=targets
)

resp = client.registerTargets(req)
print(f"Registered targets, requestId: {resp.requestId}")
```

### Describe Load Balancer

```python
from jdcloud_sdk.services.alb.apis.DescribeLoadBalancerRequest import DescribeLoadBalancerRequest

req = DescribeLoadBalancerRequest(
    regionId="cn-north-1",
    loadBalancerId="lb-abc"
)

resp = client.describeLoadBalancer(req)
lb = resp.result.loadBalancer

print(f"Name: {lb.name}")
print(f"Status: {lb.status}")
print(f"VIP: {lb.vip}")
print(f"EIP: {lb.eip}")
```

### List Load Balancers with Pagination

```python
from jdcloud_sdk.services.alb.apis.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest

req = DescribeLoadBalancersRequest(
    regionId="cn-north-1",
    pageNumber=1,
    pageSize=20
)

resp = client.describeLoadBalancers(req)
lbs = resp.result.loadBalancers

for lb in lbs:
    print(f"ID: {lb.loadBalancerId}, Name: {lb.name}, Status: {lb.status}")
```

## API Coverage Gap Note

**CLI Coverage**: JD Cloud CLI (`jdc`) does NOT support Load Balancer products. All operations are SDK/API-only. This document covers the complete API surface for ALB and NLB.

## See Also

- [Integration](integration.md) for SDK installation and credential setup
- [Troubleshooting](troubleshooting.md) for error handling patterns
- [SSL Certificate Management](ssl-certificate-management.md) for HTTPS/TLS certificate operations