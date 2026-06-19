# API & SDK — JD Cloud JCS for Kubernetes

## OpenAPI Specification

- **Base URL**: `https://nc.jdcloud-api.com/v1`
- **API Version**: v1
- **Protocol**: HTTPS
- **Authentication**: Access Key + Secret Key (HMAC-SHA256)
- **Service Code**: `nc` (Native Container)

## SDK Operations Map

| Goal | API Operation ID | SDK Method | CLI Command |
|------|-----------------|------------|-------------|
| Create Cluster | createCluster | `CreateClusterRequest` | `nc create-cluster` |
| Describe Cluster | describeCluster | `DescribeClusterRequest` | `nc describe-cluster` |
| Describe Clusters | describeClusters | `DescribeClustersRequest` | `nc describe-clusters` |
| Modify Cluster | modifyCluster | `ModifyClusterRequest` | `nc modify-cluster` |
| Delete Cluster | deleteCluster | `DeleteClusterRequest` | `nc delete-cluster` |
| Create Node Group | createNodeGroup | `CreateNodeGroupRequest` | `nc create-node-group` |
| Describe Node Group | describeNodeGroup | `DescribeNodeGroupRequest` | `nc describe-node-group` |
| Describe Node Groups | describeNodeGroups | `DescribeNodeGroupsRequest` | `nc describe-node-groups` |
| Modify Node Group | modifyNodeGroup | `ModifyNodeGroupRequest` | `nc modify-node-group` |
| Delete Node Group | deleteNodeGroup | `DeleteNodeGroupRequest` | `nc delete-node-group` |
| Describe Cluster Credential | describeClusterCredential | `DescribeClusterCredentialRequest` | `nc describe-cluster-credential` |

## Response Field Table

| Operation | JSON Path (API) | Type | Description |
|-----------|----------------|------|-------------|
| Create Cluster | `$.result.clusterId` | string | New cluster ID |
| Describe Cluster | `$.result.cluster.state` | string | Cluster state (running, creating, deleting, error) |
| List Clusters | `$.result.clusters[*].clusterId` | array | All cluster IDs |
| Create Node Group | `$.result.nodeGroupId` | string | New node group ID |
| Describe Node Group | `$.result.nodeGroup.state` | string | Node group state |
| Modify Node Group | `$.result.nodeGroupId` | string | Modified node group ID |
| Delete Cluster | `$.requestId` or `$.error` | string / object | Per spec |
| Describe Credentials | `$.result.kubeconfig` | string | Base64-encoded kubeconfig |

## Expected State Transitions

| Operation | Initial State | Target State | Poll Interval | Max Wait |
|-----------|---------------|--------------|---------------|----------|
| Create Cluster | — | `running` | 30s | 600s |
| Create Node Group | — | `running` | 15s | 300s |
| Scale Node Group | `running` | `running` | 15s | 300s |
| Upgrade Cluster | `running` | `running` | 30s | 600s |
| Delete Cluster | any stable state | (404 on describe) | 30s | 600s |
| Delete Node Group | any stable state | (404 on describe) | 15s | 300s |

## Request/Response Examples

### Create Cluster

**Request:**
```json
{
  "regionId": "cn-north-1",
  "clusterSpec": {
    "clusterName": "my-cluster",
    "vpcId": "vpc-xxx",
    "subnetId": "subnet-xxx",
    "masterVersion": "1.28.3",
    "nodeGroup": {
      "name": "worker-pool",
      "instanceType": "g.n2.large",
      "nodeCount": 3
    }
  }
}
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "clusterId": "c-xxx"
  }
}
```

### Create Node Group

**Request:**
```json
{
  "regionId": "cn-north-1",
  "clusterId": "c-xxx",
  "nodeGroupSpec": {
    "name": "gpu-workers",
    "instanceType": "p.n1.large",
    "nodeCount": 2,
    "subnetId": "subnet-xxx"
  }
}
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "nodeGroupId": "ng-xxx"
  }
}
```

### Describe Cluster Credential

**Request:**
```json
{
  "regionId": "cn-north-1",
  "clusterId": "c-xxx"
}
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "kubeconfig": "YXBpVmVyc2lvbjogdjEKa2luZDogQ29uZmln..."
  }
}
```

## Required Fields

### Create Cluster

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| regionId | string | Yes | Region ID |
| clusterName | string | Yes | Cluster name |
| vpcId | string | Yes | VPC ID |
| subnetId | string | Yes | Subnet ID |
| masterVersion | string | Yes | Kubernetes version |
| nodeGroup.name | string | Yes | Node group name |
| nodeGroup.instanceType | string | Yes | VM instance type |
| nodeGroup.nodeCount | integer | Yes | Number of worker nodes |

### Create Node Group

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| regionId | string | Yes | Region ID |
| clusterId | string | Yes | Cluster ID |
| name | string | Yes | Node group name |
| instanceType | string | Yes | VM instance type |
| nodeCount | integer | Yes | Number of nodes |
| subnetId | string | Yes | Subnet ID |

### Modify Node Group (Scale)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| regionId | string | Yes | Region ID |
| clusterId | string | Yes | Cluster ID |
| nodeGroupId | string | Yes | Node group ID |
| nodeCount | integer | Yes | Target node count (within min-max range) |

## Pagination

List operations support pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| pageNumber | integer | 1 | Page number |
| pageSize | integer | 20 | Items per page (max: 100) |

**Response pagination fields:**
```json
{
  "result": {
    "clusters": [...],
    "totalCount": 50
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| InvalidParameter | 400 | Invalid request parameter |
| ResourceNotFound | 404 | Resource does not exist |
| ResourceAlreadyExists | 409 | Resource with same name already exists |
| QuotaExceeded | 400 | Quota limit exceeded |
| InsufficientBalance | 400 | Account balance insufficient |
| InvalidVersion | 400 | Unsupported Kubernetes version |
| InvalidResourceStatus | 400 | Resource in wrong state for operation |
| InternalError | 500 | Internal server error |
| ServiceUnavailable | 503 | Service temporarily unavailable |

## SDK Import Pattern

```python
# Client
from jdcloud_sdk.services.nc.client.NcClient import NcClient

# Cluster APIs
from jdcloud_sdk.services.nc.apis.CreateClusterRequest import CreateClusterRequest, CreateClusterParameters
from jdcloud_sdk.services.nc.apis.DescribeClusterRequest import DescribeClusterRequest, DescribeClusterParameters
from jdcloud_sdk.services.nc.apis.DescribeClustersRequest import DescribeClustersRequest, DescribeClustersParameters
from jdcloud_sdk.services.nc.apis.ModifyClusterRequest import ModifyClusterRequest, ModifyClusterParameters
from jdcloud_sdk.services.nc.apis.DeleteClusterRequest import DeleteClusterRequest, DeleteClusterParameters

# Node Group APIs
from jdcloud_sdk.services.nc.apis.CreateNodeGroupRequest import CreateNodeGroupRequest, CreateNodeGroupParameters
from jdcloud_sdk.services.nc.apis.DescribeNodeGroupRequest import DescribeNodeGroupRequest, DescribeNodeGroupParameters
from jdcloud_sdk.services.nc.apis.DescribeNodeGroupsRequest import DescribeNodeGroupsRequest, DescribeNodeGroupsParameters
from jdcloud_sdk.services.nc.apis.ModifyNodeGroupRequest import ModifyNodeGroupRequest, ModifyNodeGroupParameters
from jdcloud_sdk.services.nc.apis.DeleteNodeGroupRequest import DeleteNodeGroupRequest, DeleteNodeGroupParameters

# Credential APIs
from jdcloud_sdk.services.nc.apis.DescribeClusterCredentialRequest import DescribeClusterCredentialRequest, DescribeClusterCredentialParameters
```