"""Polling helpers — wait for cluster / node group state transitions.

Based on the state transition table in SKILL.md:
  - Create Cluster:  poll 30s, max 600s, target state "running"
  - Create Node Group: poll 15s, max 300s, target state "running"
  - Scale Node Group: poll 15s, max 300s, target state "running"
  - Delete Cluster:  poll 30s, max 600s, target = 404 (NotFound)
  - Delete Node Group: poll 15s, max 300s, target = 404 (NotFound)
"""

import time

from jdcloud_sdk.core.exception import ServerException

from snippets.cluster_ops import describe_cluster
from snippets.node_group_ops import describe_node_group


class WaitTimeoutError(RuntimeError):
    """Raised when polling exceeds max_wait without reaching target state."""


def wait_cluster_running(
    client, region_id: str, cluster_id: str, poll_interval: int = 30, max_wait: int = 600
) -> dict:
    """Poll until cluster state == 'running'. Returns final describe result."""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        result = describe_cluster(client, region_id, cluster_id)
        state = result["cluster"]["state"]
        if state == "running":
            return result
        if state in ("error", "deleted"):
            raise RuntimeError(f"Cluster entered terminal state: {state}")
        time.sleep(poll_interval)
    raise WaitTimeoutError(
        f"Cluster {cluster_id} not running after {max_wait}s (last state: {state})"
    )


def _is_not_found(exc: Exception) -> bool:
    """Return True if exception indicates a 404 / NotFound response."""
    if isinstance(exc, ServerException):
        return exc.status == 404 or "NotFound" in (exc.code or "")
    # Fallback for non-SDK exceptions (e.g. wrapped HTTP errors)
    return "NotFound" in str(exc) or "404" in str(exc)


def wait_cluster_deleted(
    client, region_id: str, cluster_id: str, poll_interval: int = 30, max_wait: int = 600
) -> None:
    """Poll until describe returns 404 / NotFound."""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        try:
            describe_cluster(client, region_id, cluster_id)
        except Exception as e:
            if _is_not_found(e):
                return
            raise
        time.sleep(poll_interval)
    raise WaitTimeoutError(f"Cluster {cluster_id} still exists after {max_wait}s")


def wait_node_group_running(
    client,
    region_id: str,
    cluster_id: str,
    node_group_id: str,
    poll_interval: int = 15,
    max_wait: int = 300,
) -> dict:
    """Poll until node group state == 'running'."""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        result = describe_node_group(client, region_id, cluster_id, node_group_id)
        state = result["nodeGroup"]["state"]
        if state == "running":
            return result
        if state in ("error", "deleted"):
            raise RuntimeError(f"Node group entered terminal state: {state}")
        time.sleep(poll_interval)
    raise WaitTimeoutError(
        f"Node group {node_group_id} not running after {max_wait}s (last state: {state})"
    )


def wait_node_group_deleted(
    client,
    region_id: str,
    cluster_id: str,
    node_group_id: str,
    poll_interval: int = 15,
    max_wait: int = 300,
) -> None:
    """Poll until node group describe returns 404 / NotFound."""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        try:
            describe_node_group(client, region_id, cluster_id, node_group_id)
        except Exception as e:
            if _is_not_found(e):
                return
            raise
        time.sleep(poll_interval)
    raise WaitTimeoutError(
        f"Node group {node_group_id} still exists after {max_wait}s"
    )
