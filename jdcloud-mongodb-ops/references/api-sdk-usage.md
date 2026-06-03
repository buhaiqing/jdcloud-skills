# API & SDK — MongoDB

## OpenAPI Specification

- **Base URL**: `https://mongodb.jdcloud-api.com/v1`
- **Protocol**: HTTPS
- **Authentication**: JD Cloud Signature V3
- **Content-Type**: `application/json`

### Common HTTP Status Codes

| Code | Meaning | Agent Action |
|------|---------|--------------|
| 200 | Success | Parse response |
| 400 | Bad Request | Check parameters against OpenAPI spec |
| 401 | Unauthorized | Check credentials |
| 403 | Forbidden | Check IAM permissions |
| 404 | Not Found | Resource does not exist |
| 429 | Too Many Requests | Back off and retry |
| 500 | Internal Server Error | Retry with backoff |

## SDK Operations Map

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Instance | createInstance | `CreateInstanceRequest` |
| Describe Instance | describeInstance | `DescribeInstanceRequest` |
| Describe Instances | describeInstances | `DescribeInstancesRequest` |
| Modify Instance | modifyInstanceAttribute | `ModifyInstanceAttributeRequest` |
| Delete Instance | deleteInstance | `DeleteInstanceRequest` |
| Create Backup | createBackup | `CreateBackupRequest` |
| Describe Backups | describeBackups | `DescribeBackupsRequest` |
| Restore Instance | restoreInstance | `RestoreInstanceRequest` |
| Describe Regions | describeAvailableRegion | `DescribeAvailableRegionRequest` |
| Describe Specs | describeSpecConfig | `DescribeSpecConfigRequest` |
| Reset Password | resetPassword | `ResetPasswordRequest` |
| Create Account | createAccount | `CreateAccountRequest` |
| Describe Accounts | describeAccounts | `DescribeAccountsRequest` |
| Modify Account | modifyAccount | `ModifyAccountRequest` |
| Delete Account | deleteAccount | `DeleteAccountRequest` |

## SDK Import Paths

```python
# Client
from jdcloud_sdk.services.mongodb.client.MongodbClient import MongodbClient

# Credential
from jdcloud_sdk.core.credential import Credential

# Request Classes (examples)
from jdcloud_sdk.services.mongodb.apis.CreateInstanceRequest import CreateInstanceRequest, CreateInstanceParameters
from jdcloud_sdk.services.mongodb.apis.DescribeInstanceRequest import DescribeInstanceRequest, DescribeInstanceParameters
from jdcloud_sdk.services.mongodb.apis.DescribeInstancesRequest import DescribeInstancesRequest, DescribeInstancesParameters
from jdcloud_sdk.services.mongodb.apis.ModifyInstanceAttributeRequest import ModifyInstanceAttributeRequest, ModifyInstanceAttributeParameters
from jdcloud_sdk.services.mongodb.apis.DeleteInstanceRequest import DeleteInstanceRequest, DeleteInstanceParameters
from jdcloud_sdk.services.mongodb.apis.CreateBackupRequest import CreateBackupRequest, CreateBackupParameters
from jdcloud_sdk.services.mongodb.apis.RestoreInstanceRequest import RestoreInstanceRequest, RestoreInstanceParameters
```

## Request / Response Notes

### Create Instance Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `regionId` | string | Region identifier (e.g., cn-north-1) |
| `instanceName` | string | Instance name (1-64 chars) |
| `instanceClass` | string | Instance class code |
| `engineVersion` | string | MongoDB version (4.0, 4.2, 4.4, 5.0, 6.0) |
| `vpcId` | string | VPC ID |
| `subnetId` | string | Subnet ID |
| `azId` | string | Availability Zone ID |
| `storageType` | string | Storage type (local_ssd, cloud_ssd) |
| `storageSize` | integer | Storage size in GB |
| `username` | string | Admin username |
| `password` | string | Admin password |

### Response Structure

All responses follow this envelope:

```json
{
  "requestId": "string",
  "result": {
    // Operation-specific result
  },
  "error": {
    "code": "string",
    "message": "string",
    "status": "string"
  }
}
```

### Pagination

List operations support pagination via:

| Parameter | Type | Description |
|-----------|------|-------------|
| `pageNumber` | integer | Page number (1-based) |
| `pageSize` | integer | Items per page (10-100) |

Response includes:

```json
{
  "result": {
    "instances": [...],
    "totalCount": 100
  }
}
```

## Error Codes Reference

| Code | HTTP | Description | Resolution |
|------|------|-------------|------------|
| `InvalidParameter` | 400 | Parameter validation failed | Check request parameters |
| `ResourceNotFound` | 404 | Instance not found | Verify instance ID |
| `ResourceAlreadyExists` | 409 | Instance name already exists | Use different name |
| `InsufficientBalance` | 403 | Account balance insufficient | Top up account |
| `QuotaExceeded` | 403 | Resource quota exceeded | Request quota increase |
| `InvalidInstanceStatus` | 400 | Instance status not valid for operation | Wait for stable state |
| `InternalError` | 500 | Internal server error | Retry with backoff |
