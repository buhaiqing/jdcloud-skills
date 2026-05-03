# API & SDK Usage - JD Cloud Redis

## OpenAPI Overview

- **Base URL**: `https://redis.jdcloud-api.com/v1/regions/{regionId}/...`
- **Protocol**: HTTPS
- **Method**: POST for mutations, GET for queries
- **Authentication**: Signature-based (same as JD Cloud SDK)
- **Documentation**: https://docs.jdcloud.com/cn/jcs-for-redis/api/overview

## SDK Installation

```bash
pip install jdcloud-sdk
```

Python SDK bootstrap:

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.redis.client import RedisClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = RedisClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

## SDK Operations Map

### Instance Management

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Create instance | `createCacheInstance` | `create_cache_instance` | Create a Redis instance with specified configuration |
| Describe instance | `describeCacheInstance` | `describe_cache_instance` | Get details of a single Redis instance |
| List instances | `describeCacheInstances` | `describe_cache_instances` | Query list of Redis instances with pagination |
| Modify instance attribute | `modifyCacheInstanceAttribute` | `modify_cache_instance_attribute` | Modify instance name, description, etc. |
| Modify instance class | `modifyCacheInstanceClass` | `modify_cache_instance_class` | Scale up/down instance specification |
| Delete instance | `deleteCacheInstance` | `delete_cache_instance` | Delete a Redis instance |
| Describe cluster info | `describeClusterInfo` | `describe_cluster_info` | Get cluster node topology (cluster versions) |

### Backup and Recovery

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Create backup | `createBackup` | `create_backup` | Manually create a backup |
| Describe backups | `describeBackups` | `describe_backups` | List available backups |
| Describe backup policy | `describeBackupPolicy` | `describe_backup_policy` | Query automatic backup configuration |
| Modify backup policy | `modifyBackupPolicy` | `modify_backup_policy` | Configure automatic backup schedule |
| Restore instance | `restoreInstance` | `restore_instance` | Restore instance from a backup |
| Describe download URL | `describeDownloadUrl` | `describe_download_url` | Get backup file download link |

### Configuration and Parameters

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Describe instance config | `describeInstanceConfig` | `describe_instance_config` | Query Redis runtime parameters |
| Modify instance config | `modifyInstanceConfig` | `modify_instance_config` | Modify Redis configuration parameters |
| Get disabled commands | `getDisableCommands` | `get_disable_commands` | Query disabled Redis commands |
| Set disabled commands | `setDisableCommands` | `set_disable_commands` | Disable specific Redis commands |

### Network and Security

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Describe IP whitelist | `describeIpWhiteList` | `describe_ip_white_list` | Query allowed client IPs |
| Modify IP whitelist | `modifyIpWhiteList` | `modify_ip_white_list` | Update IP whitelist |
| Reset password | `resetCacheInstancePassword` | `reset_cache_instance_password` | Reset Redis authentication password |
| Describe client list | `describeClientList` | `describe_client_list` | Query connected clients |
| Describe client IP detail | `describeClientIpDetail` | `describe_client_ip_detail` | Get detailed client IP statistics |

### Account Management (Redis 6.2+)

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Create account | `createAccount` | `create_account` | Create a Redis ACL account |
| Describe accounts | `describeAccounts` | `describe_accounts` | List Redis accounts |
| Modify account | `modifyAccount` | `modify_account` | Modify account permissions |
| Delete account | `deleteAccount` | `delete_account` | Delete a Redis account |

### Performance Analysis

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Describe slow log | `describeSlowLog` | `describe_slow_log` | Query Redis slow operation logs |
| Create cache analysis | `createCacheAnalysis` | `create_cache_analysis` | Initiate cache key analysis |
| Describe cache analysis list | `describeCacheAnalysisList` | `describe_cache_analysis_list` | List cache analysis tasks |
| Describe cache analysis result | `describeCacheAnalysisResult` | `describe_cache_analysis_result` | Get cache analysis results |
| Create big key analysis | `createBigKeyAnalysis` | `create_big_key_analysis` | Initiate big key analysis |
| Describe big key list | `describeBigKeyList` | `describe_big_key_list` | List big key analysis tasks |
| Describe big key detail | `describeBigKeyDetail` | `describe_big_key_detail` | Get big key analysis details |

### Data Operations

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Start clear data | `startClearData` | `start_clear_data` | Clear all data in instance (FLUSHALL) |
| Describe clear data | `describeClearData` | `describe_clear_data` | Query data clearing task status |
| Stop cache analysis | `stopCacheAnalysis` | `stop_cache_analysis` | Stop ongoing cache analysis |
| Stop clear data | `stopClearData` | `stop_clear_data` | Stop data clearing task |

### Resource and Spec Queries

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Describe instance class | `describeInstanceClass` | `describe_instance_class` | Query available instance specs (legacy) |
| Describe spec config | `describeSpecConfig` | `describe_spec_config` | Query available spec configurations (recommended) |
| Describe available region | `describeAvailableRegion` | `describe_available_region` | List regions where Redis is available |
| Describe available resource | `describeAvailableResource` | `describe_available_resource` | Query available resources in a region |
| Describe user quota | `describeUserQuota` | `describe_user_quota` | Query user resource quotas |

### Task Management

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Describe task progress | `describeTaskProgressList` | `describe_task_progress_list` | Query task execution progress |

### Analysis Configuration

| Goal | API operationId | SDK Method | Description |
|------|----------------|------------|-------------|
| Describe analysis threshold | `describeAnalysisThreshold` | `describe_analysis_threshold` | Query cache analysis thresholds |
| Modify analysis threshold | `modifyAnalysisThreshold` | `modify_analysis_threshold` | Configure analysis thresholds |
| Describe analysis time | `describeAnalysisTime` | `describe_analysis_time` | Query automatic analysis schedule |
| Modify analysis time | `modifyAnalysisTime` | `modify_analysis_time` | Configure automatic analysis time |

## Request and Response Notes

### Create Instance Request Fields

Required fields for `createCacheInstance`:

- `regionId`: Region ID (cn-north-1, cn-south-1, cn-east-2)
- `cacheInstance.cacheInstanceName`: Instance name
- `cacheInstance.cacheInstanceClass`: Spec code (e.g., redis.cluster.g.micro)
- `cacheInstance.vpcId`: VPC ID
- `cacheInstance.subnetId`: Subnet ID
- `cacheInstance.azIdSpec.master`: Master AZ ID
- `cacheInstance.azIdSpec.slave`: Slave AZ ID

Optional fields:

- `cacheInstance.redisVersion`: 4.0, 5.0, 6.2 (default: 4.0)
- `cacheInstance.cacheInstanceType`: master-slave, cluster, native-cluster
- `cacheInstance.dbNum`: Number of DBs (16-256, default: 16)
- `cacheInstance.replicaNumber`: Replica count (default: 2)
- `cacheInstance.password`: Initial password
- `charge.chargeMode`: prepaid_by_duration, postpaid_by_duration
- `charge.chargeUnit`: month, year (for prepaid)
- `charge.chargeDuration`: Duration (1-9 months or 1-3 years)

### Response Fields

Common response structure:

```json
{
  "requestId": "string",
  "result": {
    "cacheInstanceId": "string",
    ...
  },
  "error": {
    "code": "string",
    "message": "string",
    "status": "string"
  }
}
```

### Pagination

For list operations (`describeCacheInstances`, etc.):

- `pageNumber`: Page number (default: 1)
- `pageSize`: Page size (default: 20, max: 100)
- Response includes `totalCount`, `pageNumber`, `pageSize`

## Error Codes

Common error codes and handling:

| HTTP Code | Error Code | Description | Agent Action |
|-----------|------------|-------------|--------------|
| 400 | InvalidParameter | Parameter validation failed | Check parameter format and values |
| 400 | QuotaExceeded | Resource quota limit reached | HALT; request quota increase |
| 400 | ResourceAlreadyExists | Instance name already exists | Ask user for different name |
| 400 | SubnetIpInsufficient | Subnet lacks available IPs | HALT; expand subnet CIDR |
| 400 | InsufficientBalance | Account balance insufficient | HALT; user tops up account |
| 403 | PermissionDenied | No permission for this operation | HALT; check IAM policies |
| 404 | ResourceNotFound | Instance or resource not found | Verify resource ID |
| 429 | RateLimitExceeded | API rate limit exceeded | Retry with exponential backoff |
| 500 | InternalError | Server internal error | Retry; report requestId if persists |
| 503 | ServiceUnavailable | Service temporarily unavailable | Retry after delay |

## Code Examples

### Create Redis Instance (Python)

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.redis.client import RedisClient
from jdcloud_sdk.services.redis.apis.create_cache_instance_request import CreateCacheInstanceRequest

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = RedisClient(credential, "cn-north-1")

# Build request
az_spec = {
    "azSpecifyType": "SpecifyByReplicaGroup",
    "master": "cn-north-1a",
    "slave": "cn-north-1b"
}

cache_instance_spec = {
    "cacheInstanceName": "my-redis-cluster",
    "cacheInstanceClass": "redis.cluster.g.small",  # 2GB per shard
    "vpcId": "vpc-abc123",
    "subnetId": "subnet-def456",
    "azIdSpec": az_spec,
    "cacheInstanceType": "cluster",  # Proxy cluster
    "redisVersion": "5.0",
    "dbNum": 32,
    "replicaNumber": 2
}

charge_spec = {
    "chargeMode": "postpaid_by_duration"
}

req = CreateCacheInstanceRequest(
    regionId="cn-north-1",
    cacheInstance=cache_instance_spec,
    charge=charge_spec
)

resp = client.create_cache_instance(req)
instance_id = resp.result.cacheInstanceId
print(f"Created Redis instance: {instance_id}")
```

### Describe Redis Instance (Python)

```python
from jdcloud_sdk.services.redis.apis.describe_cache_instance_request import DescribeCacheInstanceRequest

req = DescribeCacheInstanceRequest(
    regionId="cn-north-1",
    cacheInstanceId="redis-abc123"
)

resp = client.describe_cache_instance(req)
instance = resp.result.cacheInstance

print(f"Instance Name: {instance.cacheInstanceName}")
print(f"Status: {instance.status}")
print(f"Redis Version: {instance.redisVersion}")
print(f"Connection: {instance.connectionDomain}:{instance.port}")
```

### Create Backup (Python)

```python
from jdcloud_sdk.services.redis.apis.create_backup_request import CreateBackupRequest

req = CreateBackupRequest(
    regionId="cn-north-1",
    cacheInstanceId="redis-abc123"
)

resp = client.create_backup(req)
backup_id = resp.result.backupId
print(f"Created backup: {backup_id}")
```

### Modify IP Whitelist (Python)

```python
from jdcloud_sdk.services.redis.apis.modify_ip_white_list_request import ModifyIpWhiteListRequest

req = ModifyIpWhiteListRequest(
    regionId="cn-north-1",
    cacheInstanceId="redis-abc123",
    ipWhiteList=["192.168.1.0/24", "10.0.0.100"]
)

resp = client.modify_ip_white_list(req)
print("IP whitelist updated")
```

## Best Practices

### Retry Strategy

- Retry on 5xx errors and 429 (rate limit)
- Use exponential backoff: 2s, 4s, 8s
- Maximum 3 retries
- Do NOT retry on 400 (client error) unless parameter fix

### Idempotency

- Instance creation: Not idempotent by default; use unique names
- Modify operations: Generally idempotent if same parameters
- Delete: Idempotent (deleting non-existent returns 404)

### Polling Strategy

- Poll every 10-15 seconds for instance state changes
- Maximum wait time: 600s for creation, 300s for modification
- Check `status` field for terminal states

### Error Handling

- Parse `error.code` and `error.message` from response
- Log `requestId` for support escalation
- Do NOT expose credentials or sensitive data in error logs