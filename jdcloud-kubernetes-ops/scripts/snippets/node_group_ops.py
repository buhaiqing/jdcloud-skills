"""Node Group CRUD snippets — composable building blocks for LLM.

Each function is a single-responsibility SDK call. Combine with
cluster_ops.py and wait_utils.py to build multi-step workflows.
"""

from jdcloud_sdk.services.nc.apis.CreateNodeGroupRequest import (
    CreateNodeGroupRequest,
    CreateNodeGroupParameters,
)
from jdcloud_sdk.services.nc.apis.DescribeNodeGroupRequest import (
    DescribeNodeGroupRequest,
    DescribeNodeGroupParameters,
)
from jdcloud_sdk.services.nc.apis.DescribeNodeGroupsRequest import (
    DescribeNodeGroupsRequest,
    DescribeNodeGroupsParameters,
)
from jdcloud_sdk.services.nc.apis.ModifyNodeGroupRequest import (
    ModifyNodeGroupRequest,
    ModifyNodeGroupParameters,
)
from jdcloud_sdk.services.nc.apis.DeleteNodeGroupRequest import (
    DeleteNodeGroupRequest,
    DeleteNodeGroupParameters,
)


def create_node_group(
    client,
    region_id: str,
    cluster_id: str,
    name: str,
    instance_type: str,
    node_count: int,
    subnet_id: str,
) -> dict:
    """Create a node group. Returns {"nodeGroupId": "ng-xxx"}."""
    ng_spec = {
        "name": name,
        "instanceType": instance_type,
        "nodeCount": node_count,
        "subnetId": subnet_id,
    }
    params = CreateNodeGroupParameters(
        regionId=region_id, clusterId=cluster_id, nodeGroupSpec=ng_spec
    )
    req = CreateNodeGroupRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def describe_node_group(
    client, region_id: str, cluster_id: str, node_group_id: str
) -> dict:
    """Describe a single node group. Returns {"nodeGroup": {...}}."""
    params = DescribeNodeGroupParameters(
        regionId=region_id, clusterId=cluster_id, nodeGroupId=node_group_id
    )
    req = DescribeNodeGroupRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def list_node_groups(client, region_id: str, cluster_id: str) -> dict:
    """List all node groups in a cluster. Returns {"nodeGroups": [...]}."""
    params = DescribeNodeGroupsParameters(regionId=region_id, clusterId=cluster_id)
    req = DescribeNodeGroupsRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def scale_node_group(
    client, region_id: str, cluster_id: str, node_group_id: str, node_count: int
) -> dict:
    """Scale a node group to target count. Returns {"nodeGroupId": "ng-xxx"}."""
    params = ModifyNodeGroupParameters(
        regionId=region_id, clusterId=cluster_id, nodeGroupId=node_group_id
    )
    params.setNodeCount(node_count)
    req = ModifyNodeGroupRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def delete_node_group(
    client, region_id: str, cluster_id: str, node_group_id: str
) -> dict:
    """Delete a node group. Returns {"requestId": "..."}.

    SAFETY: Caller MUST confirm with user before calling.
    All VM instances in the node group will be terminated.
    """
    params = DeleteNodeGroupParameters(
        regionId=region_id, clusterId=cluster_id, nodeGroupId=node_group_id
    )
    req = DeleteNodeGroupRequest(parameters=params)
    resp = client.send(req)
    return resp.result
