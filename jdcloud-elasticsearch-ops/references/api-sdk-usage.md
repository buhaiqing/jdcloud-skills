# API & SDK — JD Cloud Elasticsearch

## OpenAPI

- Base URL: `https://es.jdcloud-api.com/v1`
- Protocol: HTTPS
- Format: JSON
- Authentication: Access Key + Secret Key (HMAC-SHA256)

## SDK Operations Map

| Goal | API operationId | SDK Method |
|------|-----------------|------------|
| Create Instance | createInstance | `EsClient.send(CreateInstanceRequest)` |
| Describe Instance | describeInstance | `EsClient.send(DescribeInstanceRequest)` |
| Describe Instances | describeInstances | `EsClient.send(DescribeInstancesRequest)` |
| Modify Instance Attribute | modifyInstanceAttribute | `EsClient.send(ModifyInstanceAttributeRequest)` |
| Modify Instance Spec | modifyInstanceSpec | `EsClient.send(ModifyInstanceSpecRequest)` |
| Delete Instance | deleteInstance | `EsClient.send(DeleteInstanceRequest)` |
| Create Snapshot | createSnapshot | `EsClient.send(CreateSnapshotRequest)` |
| Describe Snapshots | describeSnapshots | `EsClient.send(DescribeSnapshotsRequest)` |
| Restore Snapshot | restoreSnapshot | `EsClient.send(RestoreSnapshotRequest)` |
| Delete Snapshot | deleteSnapshot | `EsClient.send(DeleteSnapshotRequest)` |
| Describe Instance Class | describeInstanceClass | `EsClient.send(DescribeInstanceClassRequest)` |

## Request / Response Notes

### CreateInstance

**Required Fields:**
- `regionId` - Region identifier
- `instanceName` - Instance name
- `instanceClass` - Instance specification
- `version` - ES version (e.g., "7.10.0")
- `vpcId` - VPC ID
- `subnetId` - Subnet ID
- `azId` - Availability zone ID
- `dataNode` - Data node configuration
  - `nodeAmount` - Number of data nodes
  - `nodeClass` - Data node specification
  - `nodeDiskType` - Disk type (cloud_ssd, cloud_efficiency, local_ssd)
  - `nodeDiskSize` - Disk size in GB

**Optional Fields:**
- `masterNode` - Master node configuration
  - `nodeAmount` - Number of master nodes (recommended: 3)
  - `nodeClass` - Master node specification
- `kibanaNode` - Kibana node configuration
  - `nodeClass` - Kibana node specification
- `tags` - Resource tags

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "instanceId": "es-abc123def"
  }
}
```

### DescribeInstance

**Required Fields:**
- `regionId`
- `instanceId`

**Response Fields:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "instance": {
      "instanceId": "es-xxx",
      "instanceName": "my-es",
      "instanceClass": "es.n1.small",
      "version": "7.10.0",
      "status": "running",
      "vpcId": "vpc-xxx",
      "subnetId": "subnet-xxx",
      "azId": "cn-north-1a",
      "esUrl": "http://es-xxx.es.jdcloud.com:9200",
      "kibanaUrl": "http://es-xxx.kibana.jdcloud.com:5601",
      "dataNode": {
        "nodeAmount": 3,
        "nodeClass": "es.n1.small",
        "nodeDiskType": "cloud_ssd",
        "nodeDiskSize": 100
      },
      "masterNode": {
        "nodeAmount": 3,
        "nodeClass": "es.n1.small"
      },
      "kibanaNode": {
        "nodeClass": "es.n1.small"
      },
      "createTime": "2026-06-03T10:00:00+08:00",
      "tags": [
        {"key": "环境", "value": "production"}
      ]
    }
  }
}
```

### DescribeInstances

**Required Fields:**
- `regionId`

**Optional Fields:**
- `pageNumber` - Default: 1
- `pageSize` - Default: 20, Max: 100
- `filters` - Filter conditions

### ModifyInstanceAttribute

**Required Fields:**
- `regionId`
- `instanceId`

**Modifiable Fields:**
- `instanceName` - New instance name

### ModifyInstanceSpec

**Required Fields:**
- `regionId`
- `instanceId`

**Modifiable Fields:**
- `instanceClass` - New instance class
- `dataNodeAmount` - New data node count
- `dataNodeClass` - New data node class
- `dataNodeDiskSize` - New data node disk size
- `masterNodeAmount` - New master node count
- `masterNodeClass` - New master node class

### CreateSnapshot

**Required Fields:**
- `regionId`
- `instanceId`
- `snapshotName`

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "snapshotId": "snap-xxx"
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `OK` | 200 | Success |
| `InvalidParameter` | 400 | Invalid parameter |
| `MissingParameter` | 400 | Missing required parameter |
| `ResourceNotFound` | 404 | Resource not found |
| `ResourceInUse` | 409 | Resource is in use |
| `QuotaExceeded` | 429 | Quota exceeded |
| `InternalError` | 500 | Internal server error |

## Pagination

List operations support pagination:

```python
params = DescribeInstancesParameters(regionId="cn-north-1")
params.setPageNumber(1)
params.setPageSize(100)
req = DescribeInstancesRequest(parameters=params)
resp = client.send(req)

# Check for more pages
total_count = resp.result.get("totalCount", 0)
current_page = 1
page_size = 100
```

## Python SDK Example

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import (
    DescribeInstancesRequest, DescribeInstancesParameters
)

# Initialize credential
credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)

# Create client
client = EsClient(credential, "cn-north-1")

# Build request
params = DescribeInstancesParameters(regionId="cn-north-1")
params.setPageNumber(1)
params.setPageSize(50)
req = DescribeInstancesRequest(parameters=params)

# Send request
resp = client.send(req)

# Process response
for instance in resp.result.get("instances", []):
    print(f"Instance: {instance['instanceId']} - {instance['instanceName']}")
```
