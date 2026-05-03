# JD Cloud VM API & SDK Usage Guide

## OpenAPI Reference

- **API Documentation**: https://docs.jdcloud.com/cn/virtual-machines/api
- **OpenAPI Spec**: https://docs.jdcloud.com/cn/common/spec
- **SDK Version**: jdcloud_sdk >= 1.0.0

## SDK Operations Map

### Instance Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Instance | `createInstances` | `VmClient.create_instances()` | `jdc vm create-instances` |
| Describe Instances | `describeInstances` | `VmClient.describe_instances()` | `jdc vm describe-instances` |
| Start Instance | `startInstance` | `VmClient.start_instance()` | `jdc vm start-instance` |
| Stop Instance | `stopInstance` | `VmClient.stop_instance()` | `jdc vm stop-instance` |
| Reboot Instance | `rebootInstance` | `VmClient.reboot_instance()` | `jdc vm reboot-instance` |
| Delete Instance | `deleteInstance` | `VmClient.delete_instance()` | `jdc vm delete-instance` |
| Resize Instance | `resizeInstance` | `VmClient.resize_instance()` | `jdc vm resize-instance` |
| Describe Instance Types | `describeInstanceTypes` | `VmClient.describe_instance_types()` | `jdc vm describe-instance-types` |
| Describe Quota | `describeQuota` | `VmClient.describe_quota()` | `jdc vm describe-quota` |
| Describe AZs | `describeAZs` | `VmClient.describe_azs()` | `jdc vm describe-azs` |

### Image Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Describe Images | `describeImages` | `VmClient.describe_images()` | `jdc vm describe-images` |
| Create Image | `createImage` | `VmClient.create_image()` | `jdc vm create-image` |
| Delete Image | `deleteImage` | `VmClient.delete_image()` | `jdc vm delete-image` |

### Key Pair Operations

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Key Pair | `createKeyPair` | `VmClient.create_keypair()` | `jdc vm create-keypair` |
| Describe Key Pairs | `describeKeyPairs` | `VmClient.describe_keypairs()` | `jdc vm describe-keypairs` |
| Import Key Pair | `importKeyPair` | `VmClient.import_keypair()` | `jdc vm import-keypair` |
| Delete Key Pair | `deleteKeyPair` | `VmClient.delete_keypair()` | `jdc vm delete-keypair` |

### Disk Operations (Disk Service)

| Goal | API operationId | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Disk | `createDisk` | `DiskClient.create_disk()` | `jdc disk create-disk` |
| Describe Disks | `describeDisks` | `DiskClient.describe_disks()` | `jdc disk describe-disks` |
| Attach Disk | `attachDisk` | `DiskClient.attach_disk()` | `jdc disk attach-disk` |
| Detach Disk | `detachDisk` | `DiskClient.detach_disk()` | `jdc disk detach-disk` |
| Resize Disk | `resizeDisk` | `DiskClient.resize_disk()` | `jdc disk resize-disk` |
| Delete Disk | `deleteDisk` | `DiskClient.delete_disk()` | `jdc disk delete-disk` |
| Create Snapshot | `createSnapshot` | `DiskClient.create_snapshot()` | `jdc disk create-snapshot` |
| Describe Snapshots | `describeSnapshots` | `DiskClient.describe_snapshots()` | `jdc disk describe-snapshots` |
| Delete Snapshot | `deleteSnapshot` | `DiskClient.delete_snapshot()` | `jdc disk delete-snapshot` |

## SDK Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.client import VmClient
from jdcloud_sdk.services.disk.client import DiskClient

# Initialize credentials from environment
credential = Credential(
    os.environ['JDC_ACCESS_KEY'],
    os.environ['JDC_SECRET_KEY']
)

# Create VM client
vm_client = VmClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))

# Create Disk client
disk_client = DiskClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

> **Rule**: Use `os.environ['KEY']` for secrets (fail-fast if missing). Use `os.environ.get('KEY', default)` for optional config.

## Request/Response Structure

### Create Instance

**Request Fields (Required)**:
| Field | Type | Description |
|-------|------|-------------|
| `regionId` | string | Region ID (e.g., `cn-north-1`) |
| `az` | string | Availability Zone (e.g., `cn-north-1a`) |
| `instanceType` | string | Instance type (e.g., `g.n2.medium`) |
| `imageId` | string | Image ID (e.g., `img-xxxxx`) |
| `name` | string | Instance name |
| `primaryNetworkInterface` | object | Network interface config with `subnetId` and `securityGroupIds` |
| `systemDisk` | object | System disk config with `diskCategory` and `diskSizeGB` |
| `chargeMode` | string | Billing mode (`postpaid_by_duration` or `prepaid_by_duration`) |

**Response Fields**:
| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `instanceIds` | `$.result.instanceIds` | array | Created instance IDs |
| `requestId` | `$.requestId` | string | Request tracking ID |

### Describe Instances

**Request Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `regionId` | string | Yes | Region ID |
| `instanceIds` | array | No | Instance IDs to query |
| `pageNumber` | integer | No | Page number (default: 1) |
| `pageSize` | integer | No | Page size (default: 20, max: 100) |
| `filters` | array | No | Filter conditions |

**Response Fields**:
| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `instances` | `$.result.instances` | array | Instance list |
| `totalCount` | `$.result.totalCount` | integer | Total count |
| `pageNumber` | `$.result.pageNumber` | integer | Current page |
| `pageSize` | `$.result.pageSize` | integer | Page size |

### Instance Status Values

| Status | Description |
|--------|-------------|
| `creating` | Instance being created |
| `running` | Instance running normally |
| `stopped` | Instance stopped |
| `stopping` | Instance stopping |
| `starting` | Instance starting |
| `rebooting` | Instance rebooting |
| `deleting` | Instance being deleted |
| `error` | Instance in error state |

## Pagination

All list/describe APIs support pagination:

```python
# Paginated query example
pageNumber = 1
pageSize = 50
all_instances = []

while True:
    request = DescribeInstancesRequest({
        "regionId": "cn-north-1",
        "pageNumber": pageNumber,
        "pageSize": pageSize
    })
    response = vm_client.describe_instances(request)
    
    if response.error is not None:
        break
    
    instances = response.result.instances
    all_instances.extend(instances)
    
    if len(instances) < pageSize:
        break
    pageNumber += 1
```

## Error Handling

### Common API Error Codes

| Code | HTTP Status | Description | Agent Action |
|------|-------------|-------------|--------------|
| `InvalidParameter` | 400 | Parameter validation failed | Check parameters per OpenAPI, retry once |
| `InvalidInstanceType` | 400 | Instance type not supported | Query available types, suggest alternatives |
| `InvalidImageId` | 400 | Image ID invalid | Verify image exists |
| `InvalidSubnetId` | 400 | Subnet ID invalid | Verify subnet exists in VPC |
| `QuotaExceeded` | 400 | Quota limit exceeded | HALT; suggest quota increase |
| `InsufficientBalance` | 400 | Account balance insufficient | HALT; user tops up |
| `InsufficientResource` | 400 | Resources insufficient in AZ | Suggest another AZ |
| `ResourceNotFound` | 404 | Resource not found | Verify resource ID |
| `ForbiddenOperation` | 403 | Permission denied | Check IAM policies |
| `InternalError` | 500 | Internal server error | Retry with exponential backoff |
| `ServiceUnavailable` | 503 | Service temporarily unavailable | Retry with exponential backoff |

### SDK Error Handling Pattern

```python
from jdcloud_sdk.core.exception import ClientException, ServerException

try:
    response = vm_client.create_instances(request)
    
    if response.error is not None:
        error_code = response.error.code
        error_msg = response.error.message
        
        if error_code == 'QuotaExceeded':
            print("Quota exceeded. Please request quota increase.")
        elif error_code == 'InvalidParameter':
            print(f"Invalid parameter: {error_msg}")
        else:
            print(f"API Error: {error_code} - {error_msg}")
            
except ClientException as e:
    print(f"Client error: {e.error_msg}")
    # Network or parameter issue
    
except ServerException as e:
    print(f"Server error: {e.error_code} - {e.error_msg}")
    # Server-side issue, retry with backoff
```

## CLI vs SDK Coverage Gap

| Operation | SDK Available | CLI Available | Notes |
|-----------|---------------|---------------|-------|
| Create Instance | Yes | Yes | Full coverage |
| Describe Instances | Yes | Yes | Full coverage |
| Start/Stop/Reboot Instance | Yes | Yes | Full coverage |
| Delete Instance | Yes | Yes | Full coverage |
| Resize Instance | Yes | Yes | Full coverage |
| Describe Instance Types | Yes | Yes | Full coverage |
| Describe Images | Yes | Yes | Full coverage |
| Create/Delete Image | Yes | Yes | Full coverage |
| Key Pair Operations | Yes | Yes | Full coverage |
| Disk Operations | Yes | Yes | Use `disk` subcommand |
| Snapshot Operations | Yes | Yes | Use `disk` subcommand |

> **Note**: VM and Disk operations are fully covered by both SDK and CLI. No SDK-only operations for this product.

## Idempotency Notes

VM operations generally require explicit idempotency handling:

- **Create Instance**: API does NOT guarantee idempotency for same name. Use unique names or check existence before create.
- **Start/Stop/Reboot**: Safe to retry on transient errors; API returns same result for same instance state.
- **Delete Instance**: May return error if already deleted; check existence before delete if needed.

## Path Preference (SDK vs CLI)

| Scenario | Recommended Path | Reason |
|----------|------------------|--------|
| Automation scripts / CI/CD | SDK | Better error handling, retry logic, integration with Python code |
| Quick ad-hoc operations | CLI | Faster iteration, less code |
| Complex multi-step workflows | SDK | Easier state management, variables, conditional logic |
| No Python runtime available | CLI | CLI is standalone tool |
| Integration tests | SDK | Easier to mock/assert response structures |
| Resource querying with jq | CLI | Native JSON output + jq pipeline |

> **Default preference**: For automated agent execution, prefer **SDK** for complex workflows; prefer **CLI** for simple queries and quick operations.