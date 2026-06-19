"""Kubeconfig / credential retrieval snippet.

Retrieves the base64-encoded kubeconfig for a cluster.
SECURITY: Never log or print the raw kubeconfig — it grants admin access.
"""

import base64

from jdcloud_sdk.services.nc.apis.DescribeClusterCredentialRequest import (
    DescribeClusterCredentialRequest,
    DescribeClusterCredentialParameters,
)


def get_kubeconfig_raw(client, region_id: str, cluster_id: str) -> str:
    """Return base64-encoded kubeconfig string from API."""
    params = DescribeClusterCredentialParameters(
        regionId=region_id, clusterId=cluster_id
    )
    req = DescribeClusterCredentialRequest(parameters=params)
    resp = client.send(req)
    return resp.result["kubeconfig"]


def get_kubeconfig_decoded(client, region_id: str, cluster_id: str) -> str:
    """Return decoded YAML kubeconfig. Handle securely — do not log."""
    raw = get_kubeconfig_raw(client, region_id, cluster_id)
    return base64.b64decode(raw).decode("utf-8")


def save_kubeconfig(client, region_id: str, cluster_id: str, path: str) -> str:
    """Decode and write kubeconfig to file. Returns the file path.

    SECURITY: File is written with 0600 permissions.
    """
    import os
    import stat

    content = get_kubeconfig_decoded(client, region_id, cluster_id)
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    return path
