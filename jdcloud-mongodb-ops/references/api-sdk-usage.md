# API & SDK — JD Cloud MongoDB

## OpenAPI Specification

- **Service**: JCS for MongoDB
- **API Documentation**: https://docs.jdcloud.com/cn/jcs-for-mongodb/api-overview
- **Base Endpoint**: `mongodb.jdcloud-api.com`
- **API Version**: v1.0

## API Operations Map

### Instance Lifecycle

| Goal | API operationId | SDK Method (Python) | CLI Command |
|------|-----------------|---------------------|-------------|
| Create replica set | `createInstance` | `create_instance()` | `jdc mongodb create-instance` |
| Create sharded cluster | `createShardingInstance` | `create_sharding_instance()` | `jdc mongodb create-sharding-instance` |
| Describe instances | `describeInstances` | `describe_instances()` | `jdc mongodb describe-instances` |
| Modify instance spec | `modifyInstanceSpec` | `modify_instance_spec()` | `jdc mongodb modify-instance-spec` |
| Modify instance name | `modifyInstanceName` | `modify_instance_name()` | `jdc mongodb modify-instance-name` |
| Modify node spec | `modifyNodeSpec` | `modify_node_spec()` | `jdc mongodb modify-node-spec` |
| Restart instance | `restartInstance` | `restart_instance()` | `jdc mongodb restart-instance` |
| Restart node | `restartNode` | `restart_node()` | `jdc mongodb restart-node` |
| Delete instance | `deleteInstance` | `delete_instance()` | `jdc mongodb delete-instance` |
| Reset password | `resetPassword` | `reset_password()` | `jdc mongodb reset-password` |
| Restore instance | `restoreInstance` | `restore_instance()` | `jdc mongodb restore-instance` |

### Backup Management

| Goal | API operationId | SDK Method (Python) | CLI Command |
|------|-----------------|---------------------|-------------|
| Create backup | `createBackup` | `create_backup()` | `jdc mongodb create-backup` |
| Describe backups | `describeBackups` | `describe_backups()` | `jdc mongodb describe-backups` |
| Delete backup | `deleteBackup` | `delete_backup()` | `jdc mongodb delete-backup` |
| Get backup download URL | `backupDownloadURL` | `backup_download_url()` | `jdc mongodb backup-download-url` |
| Describe backup policy | `describeBackupPolicy` | `describe_backup_policy()` | `jdc mongodb describe-backup-policy` |
| Modify backup policy | `modifyBackupPolicy` | `modify_backup_policy()` | `jdc mongodb modify-backup-policy` |

### Security Management

| Goal | API operationId | SDK Method (Python) | CLI Command |
|------|-----------------|---------------------|-------------|
| Describe whitelist | `describeSecurityIps` | `describe_security_ips()` | `jdc mongodb describe-security-ips` |
| Modify whitelist | `modifySecurityIps` | `modify_security_ips()` | `jdc mongodb modify-security-ips` |

### Metadata Queries

| Goal | API operationId | SDK Method (Python) | CLI Command |
|------|-----------------|---------------------|-------------|
| Query available zones | `describeAvailableZones` | `describe_available_zones()` | `jdc mongodb describe-available-zones` |
| Query instance specs | `describeFlavors` | `describe_flavors()` | `jdc mongodb describe-flavors` |

## Request Parameters

### Create Instance (Replica Set)

**Required Parameters**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `regionId` | String | Region identifier | `cn-north-1` |
| `instanceName` | String | Instance name (1-32 chars) | `my-mongodb-prod` |
| `instanceClass` | String | Spec code | `mongodb.s.1.large` |
| `engineVersion` | String | MongoDB version | `4.0` |
| `vpcId` | String | VPC ID | `vpc-xxxx` |
| `subnetId` | String | Subnet ID | `subnet-xxxx` |
| `azId` | String | Availability zone ID | `cn-north-1a` |

**Optional Parameters**:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `chargeMode` | String | Billing mode | `postpaid_by_duration` |
| `chargeUnit` | String | Billing unit (month/year) | - |
| `chargeDuration` | Integer | Billing duration | - |
| `password` | String | Root password | Auto-generated |
| `instanceType` | String | Architecture type | `replica` |

### Create Instance (Sharded Cluster)

**Required Parameters**:

Same as replica set, plus:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `mongosSpec` | String | Mongos node spec | `mongodb.s.1.medium` |
| `mongosNodeNum` | Integer | Number of Mongos nodes (2-32) | `3` |
| `shardSpec` | String | Shard node spec | `mongodb.s.1.large` |
| `shardNodeNum` | Integer | Number of shards (2-32) | `2` |
| `shardStorage` | Integer | Storage per shard (GB) | `100` |
| `configSpec` | String | Config server spec | `mongodb.s.1.small` |

## Response Fields

### Common Response Structure

```json
{
  "requestId": "bc7d7fxxxxxx",
  "result": {
    "instanceId": "mongodb-xxxx",
    "instanceName": "my-mongodb",
    "status": "creating",
    ...
  }
}
```

### Instance Response Fields

| Field | Type | Description | Path |
|-------|------|-------------|------|
| `instanceId` | String | Instance ID | `$.result.instanceId` |
| `instanceName` | String | Instance name | `$.result.instanceName` |
| `status` | String | Current state | `$.result.status` |
| `instanceType` | String | Architecture (replica/sharding) | `$.result.instanceType` |
| `engineVersion` | String | MongoDB version | `$.result.engineVersion` |
| `instanceClass` | String | Spec code | `$.result.instanceClass` |
| `createTime` | String | Creation time (ISO 8601) | `$.result.createTime` |
| `connectionDomain` | String | Connection domain | `$.result.connectionDomain` |
| `port` | Integer | Connection port | `$.result.port` |

### Backup Response Fields

| Field | Type | Description | Path |
|-------|------|-------------|------|
| `backupId` | String | Backup ID | `$.result.backupId` |
| `backupName` | String | Backup name | `$.result.backupName` |
| `backupStatus` | String | Backup status | `$.result.backupStatus` |
| `backupSizeByte` | Integer | Backup size (bytes) | `$.result.backupSizeByte` |
| `backupStartTime` | String | Start time | `$.result.backupStartTime` |
| `backupEndTime` | String | End time | `$.result.backupEndTime` |

## Pagination

For list operations (describeInstances, describeBackups):

| Parameter | Type | Description | Default | Max |
|-----------|------|-------------|---------|-----|
| `pageNumber` | Integer | Page number | 1 | - |
| `pageSize` | Integer | Items per page | 10 | 100 |

**Response pagination fields**:

```json
{
  "result": {
    "instances": [...],
    "totalCount": 50,
    "pageNumber": 1,
    "pageSize": 10
  }
}
```

## Error Codes

| Code | HTTP Status | Meaning | Agent Action |
|------|-------------|---------|--------------|
| `InvalidParameter` | 400 | Invalid request parameter | Fix per OpenAPI spec |
| `MissingParameter` | 400 | Required parameter missing | Add missing parameter |
| `ResourceAlreadyExists` | 409 | Instance name duplicate | Use different name |
| `ResourceNotFound` | 404 | Instance not found | Verify instance ID |
| `QuotaExceeded` | 403 | Account quota exceeded | User raises quota |
| `InsufficientBalance` | 403 | Account balance insufficient | User tops up |
| `InternalError` | 500 | Service internal error | Retry with backoff |
| `ServiceUnavailable` | 503 | Service temporarily unavailable | Retry later |

## SDK Usage Examples

### Python SDK Setup

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.mongodb.client import MongodbClient

# Configure credentials
credential = Credential(
    access_key=os.environ["JDC_ACCESS_KEY"],
    secret_key=os.environ["JDC_SECRET_KEY"]
)

# Initialize client
client = MongodbClient(credential, region="cn-north-1")
```

### Create Replica Set Instance

```python
from jdcloud_sdk.services.mongodb.apis.CreateInstanceRequest import CreateInstanceRequest

req = CreateInstanceRequest(
    regionId="cn-north-1",
    instanceName="my-mongodb-prod",
    instanceClass="mongodb.s.1.large",
    engineVersion="4.0",
    vpcId="vpc-xxxx",
    subnetId="subnet-xxxx",
    azId="cn-north-1a",
    password="MySecurePass123!"
)

resp = client.create_instance(req)
instance_id = resp.result.instanceId
print(f"Created instance: {instance_id}")
```

### Describe Instance

```python
from jdcloud_sdk.services.mongodb.apis.DescribeInstancesRequest import DescribeInstancesRequest

req = DescribeInstancesRequest(
    regionId="cn-north-1",
    instanceId="mongodb-xxxx"
)

resp = client.describe_instances(req)
instance = resp.result.instance
print(f"Status: {instance.status}")
print(f"Connection: {instance.connectionDomain}:{instance.port}")
```

### Create Backup

```python
from jdcloud_sdk.services.mongodb.apis.CreateBackupRequest import CreateBackupRequest

req = CreateBackupRequest(
    regionId="cn-north-1",
    instanceId="mongodb-xxxx",
    backupName="pre-upgrade-backup"
)

resp = client.create_backup(req)
backup_id = resp.result.backupId
print(f"Backup created: {backup_id}")
```

### Modify Whitelist

```python
from jdcloud_sdk.services.mongodb.apis.ModifySecurityIpsRequest import ModifySecurityIpsRequest

req = ModifySecurityIpsRequest(
    regionId="cn-north-1",
    instanceId="mongodb-xxxx",
    securityIps=["192.168.1.0/24", "10.0.0.100"]  # Allow specific IPs/CIDRs
)

resp = client.modify_security_ips(req)
print("Whitelist updated")
```

## Async Operations

Operations that change instance state (create, modify, restart, restore) are asynchronous:

1. API returns immediately with `requestId` and initial state
2. Poll `describeInstances` until terminal state (`running`, `error`, `deleted`)
3. Use recommended poll interval and max wait from SKILL.md

## Rate Limits

| API Category | Rate Limit | Notes |
|--------------|------------|-------|
| Read operations | 100 req/min | describe*, list operations |
| Write operations | 20 req/min | create, modify, delete operations |
| Backup operations | 10 req/min | backup create, delete |

> Retry with exponential backoff on 429 (TooManyRequests).

## Idempotency

- **Create**: Duplicate instance names → `ResourceAlreadyExists` error; ask user to use new name
- **Modify**: Multiple requests → last request wins; use instanceId as natural key
- **Delete**: Already deleted → `ResourceNotFound` error (acceptable)
- **Backup**: Manual backup names can duplicate; each creates new backupId

## Best Practices

1. **Region Selection**: Choose region nearest to your application servers
2. **VPC Planning**: Create dedicated subnet for MongoDB instances
3. **Naming Convention**: Use descriptive names with environment suffix (e.g., `mongodb-prod-1`)
4. **Spec Selection**: Start with moderate specs, scale based on monitoring data
5. **Backup Strategy**: Enable daily automated backups, test restore monthly
6. **Whitelist Management**: Only allow application server IPs, update on deployment changes
7. **Password Management**: Rotate passwords quarterly, use strong passwords
8. **Monitoring**: Set alerts for CPU, memory, connections, disk usage

## Related Documentation

- [Core Concepts](core-concepts.md)
- [CLI Usage](cli-usage.md)
- [Troubleshooting](troubleshooting.md)
- [Monitoring](monitoring.md)