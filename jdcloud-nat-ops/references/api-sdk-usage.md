# API & SDK — JD Cloud NAT Gateway

## OpenAPI

- **Service Base Path**: `https://vpc.jdcloud-api.com`
- **API Version**: `v1`
- **Resource Base URL**: `/v1/regions/{regionId}/natGateways/`
- **OpenAPI Specification**: Refer to [JD Cloud VPC OpenAPI](https://docs.jdcloud.com/en/nat-gateway/api/overview)

## Authentication

All API requests require:
- `x-jdcloud-authorization`: HMAC-SHA256 signed authorization header
- `x-jdcloud-date`: ISO 8601 date in request header
- `x-jdcloud-nonce`: Unique nonce per request

The Python SDK handles signing automatically when using `Credential`.

## SDK Operations Map

| Goal | API operationId | SDK Class | SDK Method |
|------|----------------|-----------|------------|
| Create NAT Gateway | `createNatGateway` | `CreateNatGatewayRequest` | `client.send(req)` |
| Describe NAT Gateway | `describeNatGateway` | `DescribeNatGatewayRequest` | `client.send(req)` |
| List NAT Gateways | `describeNatGateways` | `DescribeNatGatewaysRequest` | `client.send(req)` |
| Modify NAT Gateway | `modifyNatGateway` | `ModifyNatGatewayRequest` | `client.send(req)` |
| Delete NAT Gateway | `deleteNatGateway` | `DeleteNatGatewayRequest` | `client.send(req)` |
| Associate EIP | `associateNatGateway` | `AssociateNatGatewayRequest` | `client.send(req)` |
| Disassociate EIP | `disassociateNatGateway` | `DisassociateNatGatewayRequest` | `client.send(req)` |
| Create SNAT Rule | `createSnatRule` | `CreateSnatRuleRequest` | `client.send(req)` |
| Delete SNAT Rule | `deleteSnatRule` | `DeleteSnatRuleRequest` | `client.send(req)` |
| Create DNAT Rule | `createDnatRule` | `CreateDnatRuleRequest` | `client.send(req)` |
| Delete DNAT Rule | `deleteDnatRule` | `DeleteDnatRuleRequest` | `client.send(req)` |

## Request / Response Notes

### Required Fields

| Operation | Required Fields |
|-----------|----------------|
| `createNatGateway` | `regionId`, `natGatewaySpec.natGatewayName`, `natGatewaySpec.vpcId`, `natGatewaySpec.elasticIpIds[0]` |
| `describeNatGateway` | `regionId`, `natGatewayId` |
| `describeNatGateways` | `regionId` |
| `modifyNatGateway` | `regionId`, `natGatewayId` (at least one optional field) |
| `deleteNatGateway` | `regionId`, `natGatewayId` |
| `associateNatGateway` | `regionId`, `natGatewayId`, `elasticIpIds[0]` |
| `disassociateNatGateway` | `regionId`, `natGatewayId`, `elasticIpIds[0]` |
| `createSnatRule` | `regionId`, `natGatewayId`, `snatRuleSpec.subnetId`, `snatRuleSpec.elasticIpIds[0]` |
| `deleteSnatRule` | `regionId`, `natGatewayId`, `snatRuleId` |
| `createDnatRule` | `regionId`, `natGatewayId`, `dnatRuleSpec.protocol`, `dnatRuleSpec.privateIp`, `dnatRuleSpec.privatePort`, `dnatRuleSpec.elasticIpId`, `dnatRuleSpec.publicPort` |
| `deleteDnatRule` | `regionId`, `natGatewayId`, `dnatRuleId` |

### Pagination

- `describeNatGateways` supports `pageNumber` (default 1) and `pageSize` (default 20, max 100)
- Response includes `totalCount` for total matching resources

### Error Response Shape

```json
{
  "requestId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "error": {
    "code": "InvalidParameter",
    "message": "Human-readable error description",
    "status": "BAD_REQUEST"
  }
}
```

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `InvalidParameter` | Required field missing or invalid |
| 404 | `NotFound` | Resource not found |
| 404 | `NatGateway.NotFound` | NAT gateway not found |
| 429 | `Throttling` | Request rate exceeded |
| 500 | `InternalError` | Server-side error |