# API & SDK — JD Cloud RDS MySQL

## OpenAPI

- **Base URL:** `https://rds.jdcloud-api.com/v1`
- **Region:** `cn-north-1`, `cn-east-1`, `cn-east-2`, `cn-south-1`
- **Authentication:** Access key + secret key

## SDK Operations Map

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Instance | createInstance | CreateInstanceRequest |
| Describe Instance | describeInstance | DescribeInstanceRequest |
| Describe Instances | describeInstances | DescribeInstancesRequest |
| Modify Instance Attribute | modifyInstanceAttribute | ModifyInstanceAttributeRequest |
| Delete Instance | deleteInstance | DeleteInstanceRequest |
| Create Backup | createBackup | CreateBackupRequest |
| Describe Backups | describeBackups | DescribeBackupsRequest |
| Restore Instance | restoreInstance | RestoreInstanceRequest |

## Request / Response Notes

### Required Fields for Create Instance

| Field | Type | Description |
|-------|------|-------------|
| regionId | string | Region ID |
| instanceName | string | Instance name |
| instanceClass | string | Instance class code |
| engine | string | Database engine (MySQL) |
| engineVersion | string | Engine version (5.7, 8.0) |
| vpcId | string | VPC ID |
| subnetId | string | Subnet ID |
| azId | string | Availability Zone ID |
| storageType | string | Storage type |
| storageSize | int | Storage size in GB |
| username | string | Admin username |
| password | string | Admin password |

### Pagination

Most list APIs support pagination:
- `pageNumber`: Starting from 1
- `pageSize`: Maximum 100

### Response Structure

```json
{
  "requestId": "string",
  "result": { ... },
  "error": null or { "code": "string", "message": "string" }
}
```

## SDK Bootstrap Example

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.rds.client.RdsClient import RdsClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = RdsClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```