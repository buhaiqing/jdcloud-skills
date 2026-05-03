# JD Cloud VPC API & SDK Usage Guide

## OpenAPI Reference

- **API Documentation**: https://docs.jdcloud.com/cn/virtual-private-cloud/api
- **OpenAPI Spec**: https://docs.jdcloud.com/cn/common/spec
- **SDK Version**: jdcloud_sdk >= 1.0.0

## SDK Operations Map

### VPC Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create VPC | `createVpc` | `VpcClient.create_vpc()` | `jdc vpc create-vpc` |
| Describe VPCs | `describeVpcs` | `VpcClient.describe_vpcs()` | `jdc vpc describe-vpcs` |
| Describe VPC | `describeVpc` | `VpcClient.describe_vpc()` | `jdc vpc describe-vpc` |
| Modify VPC | `modifyVpc` | `VpcClient.modify_vpc()` | `jdc vpc modify-vpc` |
| Delete VPC | `deleteVpc` | `VpcClient.delete_vpc()` | `jdc vpc delete-vpc` |

### Subnet Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Subnet | `createSubnet` | `VpcClient.create_subnet()` | `jdc vpc create-subnet` |
| Describe Subnets | `describeSubnets` | `VpcClient.describe_subnets()` | `jdc vpc describe-subnets` |
| Describe Subnet | `describeSubnet` | `VpcClient.describe_subnet()` | `jdc vpc describe-subnet` |
| Modify Subnet | `modifySubnet` | `VpcClient.modify_subnet()` | `jdc vpc modify-subnet` |
| Delete Subnet | `deleteSubnet` | `VpcClient.delete_subnet()` | `jdc vpc delete-subnet` |

### Security Group Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Security Group | `createNetworkSecurityGroup` | `VpcClient.create_network_security_group()` | `jdc vpc create-network-security-group` |
| Describe Security Groups | `describeNetworkSecurityGroups` | `VpcClient.describe_network_security_groups()` | `jdc vpc describe-network-security-groups` |
| Add Security Group Rules | `addNetworkSecurityGroupRules` | `VpcClient.add_network_security_group_rules()` | `jdc vpc add-network-security-group-rules` |
| Remove Security Group Rules | `removeNetworkSecurityGroupRules` | `VpcClient.remove_network_security_group_rules()` | `jdc vpc remove-network-security-group-rules` |

### Network ACL Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Network ACL | `createNetworkAcl` | `VpcClient.create_network_acl()` | `jdc vpc create-network-acl` |
| Describe Network ACLs | `describeNetworkAcls` | `VpcClient.describe_network_acls()` | `jdc vpc describe-network-acls` |
| Add Network ACL Rules | `addNetworkAclRules` | `VpcClient.add_network_acl_rules()` | `jdc vpc add-network-acl-rules` |

### Route Table Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Route Table | `createRouteTable` | `VpcClient.create_route_table()` | `jdc vpc create-route-table` |
| Describe Route Tables | `describeRouteTables` | `VpcClient.describe_route_tables()` | `jdc vpc describe-route-tables` |
| Add Route Table Rules | `addRouteTableRules` | `VpcClient.add_route_table_rules()` | `jdc vpc add-route-table-rules` |

### NAT Gateway Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create NAT Gateway | `createNatGateway` | `VpcClient.create_nat_gateway()` | `jdc vpc create-nat-gateway` |
| Describe NAT Gateways | `describeNatGateways` | `VpcClient.describe_nat_gateways()` | `jdc vpc describe-nat-gateways` |

### VPC Peering Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create VPC Peering | `createVpcPeering` | `VpcClient.create_vpc_peering()` | `jdc vpc create-vpc-peering` |
| Describe VPC Peerings | `describeVpcPeerings` | `VpcClient.describe_vpc_peerings()` | `jdc vpc describe-vpc-peerings` |

## SDK Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpc.client import VpcClient

# Initialize credentials from environment
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# Create VPC client
vpc_client = VpcClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

> **Rule**: Use `os.environ['KEY']` for secrets (fail-fast if missing). Use `os.environ.get('KEY', default)` for optional config.

## Request/Response Structure

### Create VPC

**Request Fields (Required)**:
| Field | Type | Description |
|-------|------|-------------|
| `regionId` | string | Region ID (e.g., `cn-north-1`) |
| `vpcName` | string | VPC name |
| `cidrBlock` | string | CIDR block (e.g., `10.0.0.0/16`) |

**Response Fields**:
| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `vpcId` | `$.data.vpcId` | string | Created VPC ID |
| `requestId` | `$.requestId` | string | Request tracking ID |

### Describe VPC

**Request Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `regionId` | string | Yes | Region ID |
| `vpcId` | string | Yes | VPC ID |

**Response Fields**:
| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `vpcId` | `$.data.vpcId` | string | VPC ID |
| `vpcName` | `$.data.vpcName` | string | VPC name |
| `cidrBlock` | `$.data.cidrBlock` | string | CIDR block |
| `status` | `$.data.status` | string | VPC status |
| `createTime` | `$.data.createTime` | string | Creation time |

### VPC Status Values

| Status | Description |
|--------|-------------|
| `creating` | VPC being created |
| `running` | VPC running normally |
| `deleting` | VPC being deleted |
| `error` | VPC in error state |

## Pagination

All list/describe APIs support pagination:

```python
# Paginated query example
pageNumber = 1
pageSize = 50
all_vpcs = []

while True:
    request = DescribeVpcsRequest({
        "regionId": "cn-north-1",
        "pageNumber": pageNumber,
        "pageSize": pageSize
    })
    response = vpc_client.describe_vpcs(request)
    
    if response.error is not None:
        break
    
    vpcs = response.result.vpcs
    all_vpcs.extend(vpcs)
    
    if len(vpcs) < pageSize:
        break
    pageNumber += 1
```

## Error Handling

### Common API Error Codes

| Code | HTTP Status | Description | Agent Action |
|------|-------------|-------------|--------------|
| `InvalidParameter` | 400 | Parameter validation failed | Check parameters per OpenAPI, retry once |
| `InvalidCidrBlock` | 400 | CIDR block invalid or overlapping | Verify CIDR format and conflicts |
| `QuotaExceeded` | 400 | Quota limit exceeded | HALT; suggest quota increase |
| `InsufficientBalance` | 400 | Account balance insufficient | HALT; user tops up |
| `ResourceNotFound` | 404 | Resource not found | Verify resource ID |
| `ResourceAlreadyExists` | 400 | Resource already exists | **Idempotent**: Return existing resource ID |
| `DependencyError` | 400 | Resource has dependencies | Check dependent resources |
| `ForbiddenOperation` | 403 | Permission denied | Check IAM policies |
| `InternalError` | 500 | Internal server error | Retry with exponential backoff |

### SDK Error Handling Pattern

```python
from jdcloud_sdk.core.exception import ClientException, ServerException

try:
    response = vpc_client.create_vpc(request)
    
    if response.error is not None:
        error_code = response.error.code
        error_msg = response.error.message
        
        if error_code == 'QuotaExceeded':
            print("Quota exceeded. Please request quota increase.")
        elif error_code == 'ResourceAlreadyExists':
            # Idempotent handling: find and return existing VPC
            existing_vpcs = vpc_client.describe_vpcs(describe_request)
            for vpc in existing_vpcs.result.vpcs:
                if vpc.vpc_name == request.vpc_name:
                    print(f"VPC already exists: {vpc.vpc_id}")
                    break
        else:
            print(f"API Error: {error_code} - {error_msg}")
            
except ClientException as e:
    print(f"Client error: {e.error_msg}")
    
except ServerException as e:
    print(f"Server error: {e.error_code} - {e.error_msg}")
```

## CLI vs SDK Coverage Gap

| Operation | SDK Available | CLI Available | Notes |
|-----------|---------------|---------------|-------|
| Create VPC | Yes | Yes | Full coverage |
| Describe VPCs | Yes | Yes | Full coverage |
| Describe VPC | Yes | Yes | Full coverage |
| Modify VPC | Yes | Yes | Full coverage |
| Delete VPC | Yes | Yes | Full coverage |
| Create Subnet | Yes | Yes | Full coverage |
| Describe Subnets | Yes | Yes | Full coverage |
| Delete Subnet | Yes | Yes | Full coverage |
| Security Group Operations | Yes | Yes | Full coverage |
| Network ACL Operations | Yes | Yes | Full coverage |
| Route Table Operations | Yes | Yes | Full coverage |
| NAT Gateway Operations | Yes | Yes | Full coverage |
| VPC Peering Operations | Yes | Yes | Full coverage |

> **Note**: VPC operations are fully covered by both SDK and CLI. No SDK-only operations for this product.

## Idempotency Notes

VPC operations are designed with explicit idempotency handling:

- **Create VPC**: API may return `ResourceAlreadyExists` if VPC with same name exists. Implement check-before-create pattern.
- **Delete VPC**: API may return `ResourceNotFound` if VPC already deleted. Implement check-before-delete pattern.
- **Modify VPC**: Safe to retry on transient errors.

See [Idempotency Checklist](references/idempotency-checklist.md) for detailed verification steps.

## Path Preference (SDK vs CLI)

| Scenario | Recommended Path | Reason |
|----------|------------------|--------|
| Idempotent automation | SDK | Easier to implement check-before-create/delete patterns |
| Automation scripts / CI/CD | SDK | Better error handling, retry logic |
| Quick ad-hoc operations | CLI | Faster iteration, less code |
| Complex multi-step workflows | SDK | Easier state management, conditional logic |
| No Python runtime available | CLI | CLI is standalone tool |
| Resource querying with jq | CLI | Native JSON output + jq pipeline |

> **Default preference for agent execution**: Prefer **SDK** for idempotent operations and complex workflows; prefer **CLI** for simple queries.