"""Kubernetes Storage operations — PV/PVC/StorageClass management.

Uses the official Kubernetes Python client to manage storage resources
within a JD Cloud JCS for Kubernetes cluster.

Prerequisites:
    pip install kubernetes>=25.3.0

Connection:
    Uses kubeconfig from credential_ops.get_kubeconfig_decoded() or
    standard kubeconfig file (~/.kube/config).

SAFETY:
    - delete_pvc() requires explicit confirmation
    - PVC deletion is IRREVERSIBLE if no PV reclaim policy is set
    - Always check PVC status before deletion
"""


try:
    from kubernetes import client
    from kubernetes.client.rest import ApiException  # noqa: F401
except ImportError:
    raise ImportError(
        "kubernetes package not installed. Run: pip install kubernetes>=25.3.0"
    ) from None

from .k8s_client import (
    get_k8s_client,
    get_storage_v1_client,
    handle_k8s_api_errors,
    K8sResourceNotFoundError,
    K8sClientError,
)


@handle_k8s_api_errors
def list_storage_classes(kubeconfig_path: str | None = None) -> dict:
    """List all StorageClass resources in the cluster.

    Args:
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"storage_classes": [...], "default_class": str|None}

    Example:
        >>> result = list_storage_classes()
        >>> for sc in result["storage_classes"]:
        ...     print(f"{sc['name']}: {sc['provisioner']}")
    """
    api = get_storage_v1_client(kubeconfig_path)
    storage_classes = api.list_storage_class()

    classes = []
    default_class = None

    for sc in storage_classes.items:
        class_info = {
            "name": sc.metadata.name,
            "provisioner": sc.provisioner,
            "reclaim_policy": sc.reclaim_policy,
            "volume_binding_mode": sc.volume_binding_mode,
            "allow_volume_expansion": sc.allow_volume_expansion,
            "parameters": sc.parameters or {},
            "annotations": sc.metadata.annotations or {},
        }
        classes.append(class_info)

        # Check if this is the default StorageClass
        if sc.metadata.annotations and sc.metadata.annotations.get(
            "storageclass.kubernetes.io/is-default-class"
        ) == "true":
                default_class = sc.metadata.name

    return {"storage_classes": classes, "default_class": default_class}


@handle_k8s_api_errors
def create_pvc(
    name: str,
    namespace: str,
    storage_class: str | None = None,
    size: str = "10Gi",
    access_mode: str = "ReadWriteOnce",
    kubeconfig_path: str | None = None,
) -> dict:
    """Create a PersistentVolumeClaim.

    Args:
        name: PVC name.
        namespace: Kubernetes namespace.
        storage_class: StorageClass name. If None, uses default.
        size: Storage size (e.g., "10Gi", "100Gi").
        access_mode: Access mode (ReadWriteOnce, ReadOnlyMany, ReadWriteMany).
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"name": str, "namespace": str, "status": "Pending", "size": str}

    SAFETY:
        - PVC creation is non-destructive
        - PVC will remain Pending until a matching PV is available
        - IDEMPOTENT: If PVC already exists, returns existing PVC info
    """
    api = get_k8s_client(kubeconfig_path)

    # Check if PVC already exists (idempotency)
    try:
        existing_pvc = api.read_namespaced_persistent_volume_claim(
            name=name, namespace=namespace
        )
        return {
            "name": existing_pvc.metadata.name,
            "namespace": existing_pvc.metadata.namespace,
            "status": existing_pvc.status.phase,
            "size": (existing_pvc.spec.resources.requests or {}).get("storage", "unknown"),
            "storage_class": existing_pvc.spec.storage_class_name,
            "access_mode": existing_pvc.spec.access_modes[0] if existing_pvc.spec.access_modes else None,
            "message": "PVC already exists (idempotent)",
        }
    except K8sResourceNotFoundError:
        # PVC doesn't exist, proceed with creation
        pass

    # Validate StorageClass exists if specified
    if storage_class:
        storage_api = get_storage_v1_client(kubeconfig_path)
        try:
            storage_api.read_storage_class(name=storage_class)
        except K8sResourceNotFoundError:
            raise K8sClientError(
                f"StorageClass '{storage_class}' does not exist",
                resource_type="StorageClass",
                resource_name=storage_class,
            ) from None

    pvc_spec = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=[access_mode],
            resources=client.V1ResourceRequirements(
                requests={"storage": size}
            ),
        ),
    )

    if storage_class:
        pvc_spec.spec.storage_class_name = storage_class

    result = api.create_namespaced_persistent_volume_claim(
        namespace=namespace, body=pvc_spec
    )
    return {
        "name": result.metadata.name,
        "namespace": result.metadata.namespace,
        "status": result.status.phase,
        "size": size,
        "storage_class": storage_class,
        "access_mode": access_mode,
        "message": "PVC created",
    }


@handle_k8s_api_errors
def list_pvcs(
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """List all PersistentVolumeClaims in a namespace.

    Args:
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"pvcs": [...], "total": int}

    Example:
        >>> result = list_pvcs("default")
        >>> for pvc in result["pvcs"]:
        ...     print(f"{pvc['name']}: {pvc['status']} ({pvc['size']})")
    """
    api = get_k8s_client(kubeconfig_path)
    pvc_list = api.list_namespaced_persistent_volume_claim(namespace=namespace)

    pvcs = []
    for pvc in pvc_list.items:
        pvc_info = {
            "name": pvc.metadata.name,
            "namespace": pvc.metadata.namespace,
            "status": pvc.status.phase,
            "size": (pvc.spec.resources.requests or {}).get("storage", "unknown"),
            "storage_class": pvc.spec.storage_class_name,
            "access_mode": pvc.spec.access_modes[0] if pvc.spec.access_modes else None,
            "volume_name": pvc.spec.volume_name,
            "creation_timestamp": pvc.metadata.creation_timestamp.isoformat()
            if pvc.metadata.creation_timestamp
            else None,
        }
        pvcs.append(pvc_info)

    return {"pvcs": pvcs, "total": len(pvcs)}


def _get_pods_using_pvc(
    api: client.CoreV1Api, pvc_name: str, namespace: str
) -> list[str]:
    """Find Pod names that are using a given PVC.

    Checks both regular container volumes and init container volumeMounts.

    Args:
        api: CoreV1Api client.
        pvc_name: Name of the PVC to check.
        namespace: Kubernetes namespace.

    Returns:
        List[str]: Sorted, deduplicated Pod names using the PVC.
    """
    pods = api.list_namespaced_pod(namespace=namespace)
    using_pods: set[str] = set()

    for pod in pods.items:
        # Direct volume claim reference
        for volume in (pod.spec.volumes or []):
            if (
                volume.persistent_volume_claim
                and volume.persistent_volume_claim.claim_name == pvc_name
            ):
                using_pods.add(pod.metadata.name)
                break
        else:
            # Defensive check via init container volumeMounts
            for container in (pod.spec.init_containers or []):
                for mount in (container.volume_mounts or []):
                    for volume in (pod.spec.volumes or []):
                        if (
                            volume.name == mount.name
                            and volume.persistent_volume_claim
                            and volume.persistent_volume_claim.claim_name == pvc_name
                        ):
                            using_pods.add(pod.metadata.name)
                            break
                    if pod.metadata.name in using_pods:
                        break
                if pod.metadata.name in using_pods:
                    break

    return sorted(using_pods)


@handle_k8s_api_errors
def delete_pvc(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Delete a PersistentVolumeClaim.

    Args:
        name: PVC name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"name": str, "namespace": str, "deleted": True}

    SAFETY:
        - PVC deletion is IRREVERSIBLE
        - Data on the underlying PV may be lost depending on reclaim policy
        - Caller MUST confirm with user before calling
        - Check PVC status and bound PV before deletion
    """
    api = get_k8s_client(kubeconfig_path)

    # Get PVC details for logging (handle case where PVC doesn't exist)
    try:
        pvc = api.read_namespaced_persistent_volume_claim(
            name=name, namespace=namespace
        )
    except K8sResourceNotFoundError:
        # PVC doesn't exist - return early with appropriate message
        return {
            "name": name,
            "namespace": namespace,
            "deleted": False,
            "message": "PVC does not exist",
        }

    # Check if PVC is in use by any Pod (including init containers)
    using_pods = _get_pods_using_pvc(api, name, namespace)

    if using_pods:
        return {
            "name": name,
            "namespace": namespace,
            "deleted": False,
            "message": f"PVC is in use by Pods: {', '.join(sorted(using_pods))}",
            "bound_volume": pvc.spec.volume_name,
            "status_before_delete": pvc.status.phase,
        }

    # Delete the PVC
    api.delete_namespaced_persistent_volume_claim(
        name=name, namespace=namespace
    )

    return {
        "name": name,
        "namespace": namespace,
        "deleted": True,
        "bound_volume": pvc.spec.volume_name,
        "status_before_delete": pvc.status.phase,
    }


@handle_k8s_api_errors
def list_pvs(kubeconfig_path: str | None = None) -> dict:
    """List all PersistentVolumes in the cluster.

    Args:
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"pvs": [...], "total": int}

    Example:
        >>> result = list_pvs()
        >>> for pv in result["pvs"]:
        ...     print(f"{pv['name']}: {pv['status']} ({pv['capacity']})")
    """
    api = get_k8s_client(kubeconfig_path)
    pv_list = api.list_persistent_volume()

    pvs = []
    for pv in pv_list.items:
        pv_info = {
            "name": pv.metadata.name,
            "status": pv.status.phase if pv.status else "Unknown",
            "capacity": pv.spec.capacity.get("storage", "unknown") if pv.spec.capacity else "unknown",
            "access_mode": pv.spec.access_modes[0] if pv.spec.access_modes else None,
            "reclaim_policy": pv.spec.persistent_volume_reclaim_policy,
            "storage_class": pv.spec.storage_class_name,
            "claim_ref": f"{pv.spec.claim_ref.namespace}/{pv.spec.claim_ref.name}"
            if pv.spec.claim_ref
            else None,
            "creation_timestamp": pv.metadata.creation_timestamp.isoformat()
            if pv.metadata.creation_timestamp
            else None,
        }
        pvs.append(pv_info)

    return {"pvs": pvs, "total": len(pvs)}


@handle_k8s_api_errors
def check_pvc_health(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Check health status of a PVC.

    Args:
        name: PVC name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "name": str,
            "status": "Bound"|"Pending"|"Lost",
            "healthy": bool,
            "bound_volume": str|None,
            "issues": [str]
        }

    Health checks:
        - PVC status is "Bound"
        - Bound PV exists and is "Bound"
        - No events indicating errors
    """
    api = get_k8s_client(kubeconfig_path)

    try:
        pvc = api.read_namespaced_persistent_volume_claim(
            name=name, namespace=namespace
        )
    except K8sResourceNotFoundError:
        return {
            "name": name,
            "namespace": namespace,
            "status": "NotFound",
            "healthy": False,
            "issues": ["PVC does not exist"],
        }

    issues = []
    status = pvc.status.phase
    bound_volume = pvc.spec.volume_name

    # Check PVC status
    if status == "Pending":
        issues.append("PVC is Pending (waiting for PV provisioning)")
    elif status == "Lost":
        issues.append("PVC is Lost (underlying PV may be deleted)")
    elif status != "Bound":
        issues.append(f"PVC status is {status} (expected Bound)")

    # Check bound PV exists
    if bound_volume:
        try:
            pv = api.read_persistent_volume(name=bound_volume)
            if pv.status.phase != "Bound":
                issues.append(f"Bound PV {bound_volume} status is {pv.status.phase}")
        except K8sResourceNotFoundError:
            issues.append(f"Bound PV {bound_volume} does not exist")
    else:
        if status == "Bound":
            issues.append("PVC is Bound but no volume_name set (unusual)")

    # Check events for errors
    events = api.list_namespaced_event(namespace=namespace, field_selector=f"involvedObject.name={name}")
    error_events = [
        e for e in events.items
        if e.type == "Warning" and e.reason in ("FailedMount", "FailedAttachVolume", "ProvisioningFailed")
    ]
    if error_events:
        latest = error_events[-1]
        issues.append(f"Recent error: {latest.reason} - {latest.message}")

    return {
        "name": name,
        "namespace": namespace,
        "status": status,
        "healthy": len(issues) == 0,
        "bound_volume": bound_volume,
        "storage_class": pvc.spec.storage_class_name,
        "size": pvc.spec.resources.requests.get("storage", "unknown"),
        "issues": issues,
    }


@handle_k8s_api_errors
def get_storage_summary(
    namespace: str | None = None,
    kubeconfig_path: str | None = None,
) -> dict:
    """Get storage resource summary for the cluster or namespace.

    Args:
        namespace: If provided, summarize only this namespace. Otherwise cluster-wide.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "storage_classes": int,
            "pvs": {"total": int, "bound": int, "available": int},
            "pvcs": {"total": int, "bound": int, "pending": int, "lost": int}
        }
    """
    # Storage classes
    sc_result = list_storage_classes(kubeconfig_path)

    # PVs (cluster-wide)
    pv_result = list_pvs(kubeconfig_path)
    pv_status = {"total": pv_result["total"], "bound": 0, "available": 0, "released": 0}
    for pv in pv_result["pvs"]:
        if pv["status"] == "Bound":
            pv_status["bound"] += 1
        elif pv["status"] == "Available":
            pv_status["available"] += 1
        elif pv["status"] == "Released":
            pv_status["released"] += 1

    # PVCs
    if namespace:
        pvc_result = list_pvcs(namespace, kubeconfig_path)
        pvcs = pvc_result["pvcs"]
    else:
        # List PVCs across all namespaces
        api = get_k8s_client(kubeconfig_path)
        pvc_list = api.list_persistent_volume_claim_for_all_namespaces()
        pvcs = [
            {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase,
            }
            for pvc in pvc_list.items
        ]

    pvc_status = {"total": len(pvcs), "bound": 0, "pending": 0, "lost": 0}
    for pvc in pvcs:
        if pvc["status"] == "Bound":
            pvc_status["bound"] += 1
        elif pvc["status"] == "Pending":
            pvc_status["pending"] += 1
        elif pvc["status"] == "Lost":
            pvc_status["lost"] += 1

    return {
        "storage_classes": len(sc_result["storage_classes"]),
        "default_storage_class": sc_result["default_class"],
        "pvs": pv_status,
        "pvcs": pvc_status,
    }
