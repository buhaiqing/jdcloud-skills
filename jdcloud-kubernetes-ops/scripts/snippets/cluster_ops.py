"""Cluster CRUD snippets — composable building blocks for LLM.

Each function is a single-responsibility SDK call. Combine them to build
workflows (e.g. create cluster → wait running → create node group).

All functions accept an NcClient (from lib.jdc_client.get_client) and
return the raw `resp.result` dict so callers can parse JSON paths
documented in references/api-sdk-usage.md.
"""

from jdcloud_sdk.services.nc.apis.CreateClusterRequest import (
    CreateClusterRequest,
    CreateClusterParameters,
)
from jdcloud_sdk.services.nc.apis.DescribeClusterRequest import (
    DescribeClusterRequest,
    DescribeClusterParameters,
)
from jdcloud_sdk.services.nc.apis.DescribeClustersRequest import (
    DescribeClustersRequest,
    DescribeClustersParameters,
)
from jdcloud_sdk.services.nc.apis.ModifyClusterRequest import (
    ModifyClusterRequest,
    ModifyClusterParameters,
)
from jdcloud_sdk.services.nc.apis.DeleteClusterRequest import (
    DeleteClusterRequest,
    DeleteClusterParameters,
)


def create_cluster(
    client,
    region_id: str,
    cluster_name: str,
    vpc_id: str,
    subnet_id: str,
    master_version: str,
    node_group_name: str,
    instance_type: str,
    node_count: int,
) -> dict:
    """Create a Kubernetes cluster. Returns {"clusterId": "c-xxx"}."""
    cluster_spec = {
        "clusterName": cluster_name,
        "vpcId": vpc_id,
        "subnetId": subnet_id,
        "masterVersion": master_version,
        "nodeGroup": {
            "name": node_group_name,
            "instanceType": instance_type,
            "nodeCount": node_count,
        },
    }
    params = CreateClusterParameters(regionId=region_id, clusterSpec=cluster_spec)
    req = CreateClusterRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def describe_cluster(client, region_id: str, cluster_id: str) -> dict:
    """Describe a single cluster. Returns {"cluster": {...}}."""
    params = DescribeClusterParameters(regionId=region_id, clusterId=cluster_id)
    req = DescribeClusterRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def list_clusters(
    client, region_id: str, page_number: int = 1, page_size: int = 100
) -> dict:
    """List all clusters in a region. Returns {"clusters": [...], "totalCount": N}."""
    params = DescribeClustersParameters(regionId=region_id)
    params.setPageNumber(page_number)
    params.setPageSize(page_size)
    req = DescribeClustersRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def modify_cluster(client, region_id: str, cluster_id: str, master_version: str) -> dict:
    """Upgrade cluster control-plane version. Returns {"clusterId": "c-xxx"}."""
    params = ModifyClusterParameters(
        regionId=region_id, clusterId=cluster_id, masterVersion=master_version
    )
    req = ModifyClusterRequest(parameters=params)
    resp = client.send(req)
    return resp.result


def delete_cluster(client, region_id: str, cluster_id: str) -> dict:
    """Delete a cluster. Returns {"requestId": "..."}.

    SAFETY: Caller MUST confirm with user and run workload check before calling.
    """
    params = DeleteClusterParameters(regionId=region_id, clusterId=cluster_id)
    req = DeleteClusterRequest(parameters=params)
    resp = client.send(req)
    return resp.result
