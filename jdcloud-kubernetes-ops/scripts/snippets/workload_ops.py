"""Kubernetes Workload operations — Pod/Service/Deployment/HPA/Ingress management.

Uses the official Kubernetes Python client to manage workload resources
within a JD Cloud JCS for Kubernetes cluster.

Prerequisites:
    pip install kubernetes>=25.3.0

Connection:
    Uses kubeconfig from credential_ops.get_kubeconfig_decoded() or
    standard kubeconfig file (~/.kube/config).

SAFETY:
    - delete_pod() and delete_deployment() require explicit confirmation
    - Always check resource status before deletion
"""


try:
    from kubernetes import client  # noqa: F401
except ImportError:
    raise ImportError(
        "kubernetes package not installed. Run: pip install kubernetes>=25.3.0"
    ) from None

from .k8s_client import (
    get_k8s_client,
    get_apps_v1_client,
    get_autoscaling_v1_client,
    get_networking_v1_client,
    handle_k8s_api_errors,
    K8sResourceNotFoundError,
)


# ============================================================================
# Pod Operations
# ============================================================================


@handle_k8s_api_errors
def list_pods(
    namespace: str,
    label_selector: str | None = None,
    field_selector: str | None = None,
    kubeconfig_path: str | None = None,
) -> dict:
    """List all Pods in a namespace.

    Args:
        namespace: Kubernetes namespace.
        label_selector: Label selector (e.g., "app=nginx").
        field_selector: Field selector (e.g., "status.phase=Running").
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"pods": [...], "total": int}

    Example:
        >>> result = list_pods("default", label_selector="app=nginx")
        >>> for pod in result["pods"]:
        ...     print(f"{pod['name']}: {pod['status']}")
    """
    api = get_k8s_client(kubeconfig_path)

    kwargs = {"namespace": namespace}
    if label_selector:
        kwargs["label_selector"] = label_selector
    if field_selector:
        kwargs["field_selector"] = field_selector

    pod_list = api.list_namespaced_pod(**kwargs)

    pods = []
    for pod in pod_list.items:
        pod_info = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ready": all(
                c.ready for c in (pod.status.container_statuses or [])
            ),
            "restarts": sum(
                c.restart_count for c in (pod.status.container_statuses or [])
            ),
            "node_name": pod.spec.node_name,
            "ip": pod.status.pod_ip,
            "creation_timestamp": pod.metadata.creation_timestamp.isoformat()
            if pod.metadata.creation_timestamp
            else None,
        }
        pods.append(pod_info)

    return {"pods": pods, "total": len(pods)}


@handle_k8s_api_errors
def get_pod_logs(
    name: str,
    namespace: str,
    container: str | None = None,
    tail_lines: int | None = 100,
    since_seconds: int | None = None,
    kubeconfig_path: str | None = None,
) -> dict:
    """Get logs from a Pod.

    Args:
        name: Pod name.
        namespace: Kubernetes namespace.
        container: Container name (for multi-container pods).
        tail_lines: Number of lines to tail from the end.
        since_seconds: Return logs newer than this many seconds.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"name": str, "namespace": str, "logs": str}
    """
    api = get_k8s_client(kubeconfig_path)

    kwargs = {
        "name": name,
        "namespace": namespace,
    }
    if container:
        kwargs["container"] = container
    if tail_lines:
        kwargs["tail_lines"] = tail_lines
    if since_seconds:
        kwargs["since_seconds"] = since_seconds

    logs = api.read_namespaced_pod_log(**kwargs)

    return {
        "name": name,
        "namespace": namespace,
        "container": container,
        "logs": logs,
    }


@handle_k8s_api_errors
def delete_pod(
    name: str,
    namespace: str,
    grace_period_seconds: int = 30,
    wait_for_deletion: bool = False,
    timeout_seconds: int = 60,
    poll_interval: float = 2.0,
    kubeconfig_path: str | None = None,
) -> dict:
    """Delete a Pod with optional wait for deletion completion.

    Args:
        name: Pod name.
        namespace: Kubernetes namespace.
        grace_period_seconds: Grace period for graceful termination.
        wait_for_deletion: If True, wait until Pod is fully deleted.
        timeout_seconds: Maximum time to wait for deletion (if wait_for_deletion=True).
        poll_interval: Initial polling interval in seconds (uses exponential backoff).
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "name": str,
            "namespace": str,
            "deleted": bool,
            "message": str (optional),
            "node_name": str (optional),
            "status_before_delete": str (optional)
        }

    SAFETY:
        - Pod deletion is IRREVERSIBLE
        - If Pod is managed by Deployment/ReplicaSet, it will be recreated
        - Caller MUST confirm with user before calling
        - IDEMPOTENT: If Pod doesn't exist, returns success (target state achieved)
    """
    api = get_k8s_client(kubeconfig_path)

    # Get Pod details for logging (handle case where pod doesn't exist)
    try:
        pod = api.read_namespaced_pod(name=name, namespace=namespace)
        node_name = pod.spec.node_name
        status_before_delete = pod.status.phase
    except K8sResourceNotFoundError:
        # Pod doesn't exist - idempotent operation (target state already achieved)
        return {
            "name": name,
            "namespace": namespace,
            "deleted": True,  # Idempotent: target state achieved
            "message": "Pod does not exist (idempotent)",
        }

    # Delete the Pod
    api.delete_namespaced_pod(
        name=name,
        namespace=namespace,
        grace_period_seconds=grace_period_seconds,
    )

    # Optionally wait for deletion to complete (with exponential backoff)
    if wait_for_deletion:
        import time
        start_time = time.time()
        current_interval = poll_interval
        max_interval = 10.0
        while time.time() - start_time < timeout_seconds:
            try:
                api.read_namespaced_pod(name=name, namespace=namespace)
                time.sleep(current_interval)
                current_interval = min(current_interval * 1.5, max_interval)
            except K8sResourceNotFoundError:
                # Pod is fully deleted
                return {
                    "name": name,
                    "namespace": namespace,
                    "deleted": True,
                    "node_name": node_name,
                    "status_before_delete": status_before_delete,
                    "waited_for_deletion": True,
                }
        # Timeout reached
        return {
            "name": name,
            "namespace": namespace,
            "deleted": True,
            "node_name": node_name,
            "status_before_delete": status_before_delete,
            "waited_for_deletion": False,
            "message": f"Deletion initiated but Pod still exists after {timeout_seconds}s",
        }

    return {
        "name": name,
        "namespace": namespace,
        "deleted": True,
        "node_name": node_name,
        "status_before_delete": status_before_delete,
    }


def _check_pod_status_issues(pod) -> list[str]:
    """Check Pod status for issues.

    Args:
        pod: Pod object from kubernetes client.

    Returns:
        List of issue descriptions.
    """
    issues = []
    status = pod.status.phase

    if status == "Pending":
        issues.append("Pod is Pending (waiting for scheduling or image pull)")
    elif status == "Failed":
        issues.append(f"Pod has Failed: {pod.status.reason or 'unknown reason'}")
    elif status == "Unknown":
        issues.append("Pod status is Unknown")

    return issues


def _check_container_readiness(pod) -> tuple[bool, list[str]]:
    """Check container readiness status.

    Args:
        pod: Pod object from kubernetes client.

    Returns:
        Tuple of (all_ready: bool, issues: List[str]).
    """
    issues = []
    container_statuses = pod.status.container_statuses or []
    all_ready = all(c.ready for c in container_statuses)

    if not all_ready and pod.status.phase == "Running":
        not_ready = [c.name for c in container_statuses if not c.ready]
        issues.append(f"Containers not ready: {', '.join(not_ready)}")

    return all_ready, issues


def _check_container_restarts(pod) -> tuple[int, list[str]]:
    """Check container restart counts.

    Args:
        pod: Pod object from kubernetes client.

    Returns:
        Tuple of (total_restarts: int, issues: List[str]).
    """
    issues = []
    container_statuses = pod.status.container_statuses or []
    total_restarts = sum(c.restart_count for c in container_statuses)

    if total_restarts > 0:
        issues.append(f"Total container restarts: {total_restarts}")

    return total_restarts, issues


def _check_crashloop_backoff(pod) -> list[str]:
    """Check for containers in CrashLoopBackOff state.

    Args:
        pod: Pod object from kubernetes client.

    Returns:
        List of issue descriptions.
    """
    issues = []
    container_statuses = pod.status.container_statuses or []

    for cs in container_statuses:
        if cs.state and cs.state.waiting and cs.state.waiting.reason == "CrashLoopBackOff":
            issues.append(f"Container {cs.name} is in CrashLoopBackOff")

    return issues


def _check_error_events(
    api: client.CoreV1Api, pod_name: str, namespace: str
) -> list[str]:
    """Check for error events related to the Pod.

    Args:
        api: CoreV1Api client.
        pod_name: Pod name.
        namespace: Kubernetes namespace.

    Returns:
        List of issue descriptions.
    """
    issues = []
    events = api.list_namespaced_event(
        namespace=namespace, field_selector=f"involvedObject.name={pod_name}"
    )
    error_events = [
        e
        for e in events.items
        if e.type == "Warning"
        and e.reason in ("FailedScheduling", "FailedMount", "FailedAttachVolume", "Unhealthy")
    ]

    if error_events:
        latest = error_events[-1]
        issues.append(f"Recent error: {latest.reason} - {latest.message}")

    return issues


@handle_k8s_api_errors
def check_pod_health(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Check health status of a Pod.

    Args:
        name: Pod name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "name": str,
            "status": "Running"|"Pending"|"Failed"|"Succeeded"|"Unknown",
            "healthy": bool,
            "ready": bool,
            "restarts": int,
            "issues": [str]
        }

    Health checks:
        - Pod status is "Running" or "Succeeded"
        - All containers are ready
        - No recent restarts
        - No error events
    """
    api = get_k8s_client(kubeconfig_path)

    try:
        pod = api.read_namespaced_pod(name=name, namespace=namespace)
    except K8sResourceNotFoundError:
        return {
            "name": name,
            "namespace": namespace,
            "status": "NotFound",
            "healthy": False,
            "issues": ["Pod does not exist"],
        }

    # Aggregate issues from all checks
    issues = []
    issues.extend(_check_pod_status_issues(pod))

    all_ready, readiness_issues = _check_container_readiness(pod)
    issues.extend(readiness_issues)

    total_restarts, restart_issues = _check_container_restarts(pod)
    issues.extend(restart_issues)

    issues.extend(_check_crashloop_backoff(pod))
    issues.extend(_check_error_events(api, name, namespace))

    return {
        "name": name,
        "namespace": namespace,
        "status": pod.status.phase,
        "healthy": len(issues) == 0 and pod.status.phase in ("Running", "Succeeded"),
        "ready": all_ready,
        "restarts": total_restarts,
        "node_name": pod.spec.node_name,
        "issues": issues,
    }


# ============================================================================
# Service Operations
# ============================================================================


@handle_k8s_api_errors
def list_services(
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """List all Services in a namespace.

    Args:
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"services": [...], "total": int}
    """
    api = get_k8s_client(kubeconfig_path)
    svc_list = api.list_namespaced_service(namespace=namespace)

    services = []
    for svc in svc_list.items:
        svc_info = {
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type,
            "cluster_ip": svc.spec.cluster_ip,
            "external_ip": svc.status.load_balancer.ingress[0].ip
            if svc.status.load_balancer
            and svc.status.load_balancer.ingress
            and len(svc.status.load_balancer.ingress) > 0
            else None,
            "ports": [
                {
                    "port": p.port,
                    "target_port": p.target_port,
                    "protocol": p.protocol,
                }
                for p in (svc.spec.ports or [])
            ],
            "selector": svc.spec.selector or {},
            "creation_timestamp": svc.metadata.creation_timestamp.isoformat()
            if svc.metadata.creation_timestamp
            else None,
        }
        services.append(svc_info)

    return {"services": services, "total": len(services)}


@handle_k8s_api_errors
def check_service_health(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Check health status of a Service.

    Args:
        name: Service name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "name": str,
            "type": str,
            "healthy": bool,
            "endpoints_count": int,
            "issues": [str]
        }

    Health checks:
        - Service has endpoints (backing pods exist)
        - LoadBalancer has external IP (if type=LoadBalancer)
        - No error events
    """
    api = get_k8s_client(kubeconfig_path)

    try:
        svc = api.read_namespaced_service(name=name, namespace=namespace)
    except K8sResourceNotFoundError:
        return {
            "name": name,
            "namespace": namespace,
            "healthy": False,
            "issues": ["Service does not exist"],
        }

    issues = []
    endpoints_count = 0

    # Check endpoints
    try:
        endpoints = api.read_namespaced_endpoints(name=name, namespace=namespace)
        endpoints_count = sum(
            len(subset.addresses or []) for subset in (endpoints.subsets or [])
        )
        if endpoints_count == 0:
            issues.append("Service has no endpoints (no matching pods)")
    except K8sResourceNotFoundError:
        issues.append("Endpoints resource not found")

    # Check LoadBalancer external IP
    if svc.spec.type == "LoadBalancer" and not (svc.status.load_balancer and svc.status.load_balancer.ingress):
            issues.append("LoadBalancer Service has no external IP assigned")

    # Check events for errors
    events = api.list_namespaced_event(
        namespace=namespace, field_selector=f"involvedObject.name={name}"
    )
    error_events = [
        e
        for e in events.items
        if e.type == "Warning" and e.reason in ("FailedCreateEndpoint", "FailedToUpdateEndpoint")
    ]
    if error_events:
        latest = error_events[-1]
        issues.append(f"Recent error: {latest.reason} - {latest.message}")

    return {
        "name": name,
        "namespace": namespace,
        "type": svc.spec.type,
        "cluster_ip": svc.spec.cluster_ip,
        "healthy": len(issues) == 0,
        "endpoints_count": endpoints_count,
        "issues": issues,
    }


# ============================================================================
# Deployment Operations
# ============================================================================


@handle_k8s_api_errors
def list_deployments(
    namespace: str,
    label_selector: str | None = None,
    kubeconfig_path: str | None = None,
) -> dict:
    """List all Deployments in a namespace.

    Args:
        namespace: Kubernetes namespace.
        label_selector: Label selector (e.g., "app=nginx").
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"deployments": [...], "total": int}
    """
    api = get_apps_v1_client(kubeconfig_path)

    kwargs = {"namespace": namespace}
    if label_selector:
        kwargs["label_selector"] = label_selector

    deploy_list = api.list_namespaced_deployment(**kwargs)

    deployments = []
    for deploy in deploy_list.items:
        deploy_info = {
            "name": deploy.metadata.name,
            "namespace": deploy.metadata.namespace,
            "replicas": deploy.spec.replicas or 0,
            "ready_replicas": deploy.status.ready_replicas or 0,
            "available_replicas": deploy.status.available_replicas or 0,
            "updated_replicas": deploy.status.updated_replicas or 0,
            "conditions": [
                {
                    "type": c.type,
                    "status": c.status,
                    "reason": c.reason,
                    "message": c.message,
                }
                for c in (deploy.status.conditions or [])
            ],
            "creation_timestamp": deploy.metadata.creation_timestamp.isoformat()
            if deploy.metadata.creation_timestamp
            else None,
        }
        deployments.append(deploy_info)

    return {"deployments": deployments, "total": len(deployments)}


@handle_k8s_api_errors
def scale_deployment(
    name: str,
    namespace: str,
    replicas: int,
    kubeconfig_path: str | None = None,
) -> dict:
    """Scale a Deployment to the specified number of replicas.

    Args:
        name: Deployment name.
        namespace: Kubernetes namespace.
        replicas: Target replica count.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"name": str, "namespace": str, "replicas": int}
    """
    api = get_apps_v1_client(kubeconfig_path)

    body = {"spec": {"replicas": replicas}}
    result = api.patch_namespaced_deployment_scale(
        name=name, namespace=namespace, body=body
    )

    return {
        "name": name,
        "namespace": namespace,
        "replicas": result.spec.replicas,
    }


@handle_k8s_api_errors
def restart_deployment(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Restart a Deployment by updating the restart annotation.

    Args:
        name: Deployment name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"name": str, "namespace": str, "restarted": True}

    SAFETY:
        - This triggers a rolling restart of all pods
        - Ensure PodDisruptionBudget is configured for zero-downtime
    """
    import datetime

    api = get_apps_v1_client(kubeconfig_path)

    # Get current deployment to preserve existing annotations
    deploy = api.read_namespaced_deployment(name=name, namespace=namespace)
    annotations = deploy.metadata.annotations or {}

    # Update restart annotation to trigger rolling update
    annotations["kubectl.kubernetes.io/restartedAt"] = datetime.datetime.utcnow().isoformat() + "Z"

    body = {"metadata": {"annotations": annotations}}
    api.patch_namespaced_deployment(name=name, namespace=namespace, body=body)

    return {
        "name": name,
        "namespace": namespace,
        "restarted": True,
    }


@handle_k8s_api_errors
def check_deployment_health(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Check health status of a Deployment.

    Args:
        name: Deployment name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "name": str,
            "healthy": bool,
            "replicas": int,
            "ready_replicas": int,
            "issues": [str]
        }

    Health checks:
        - All replicas are ready
        - No unavailable replicas
        - Deployment is not progressing indefinitely
        - No error conditions
    """
    api = get_apps_v1_client(kubeconfig_path)

    try:
        deploy = api.read_namespaced_deployment(name=name, namespace=namespace)
    except K8sResourceNotFoundError:
        return {
            "name": name,
            "namespace": namespace,
            "healthy": False,
            "issues": ["Deployment does not exist"],
        }

    issues = []
    replicas = deploy.spec.replicas or 0
    ready_replicas = deploy.status.ready_replicas or 0
    available_replicas = deploy.status.available_replicas or 0
    updated_replicas = deploy.status.updated_replicas or 0

    # Check replica counts
    if ready_replicas < replicas:
        issues.append(
            f"Only {ready_replicas}/{replicas} replicas are ready"
        )

    if deploy.status.unavailable_replicas and deploy.status.unavailable_replicas > 0:
        issues.append(
            f"{deploy.status.unavailable_replicas} replicas are unavailable"
        )

    # Check if deployment is stuck
    for condition in deploy.status.conditions or []:
        if condition.type == "Progressing" and condition.status == "False":
            issues.append(
                f"Deployment is not progressing: {condition.reason} - {condition.message}"
            )
        if condition.type == "Available" and condition.status == "False":
            issues.append("Deployment is not available")

    # Check if update is stuck
    if deploy.status.observed_generation < deploy.metadata.generation:
        issues.append("Deployment update is in progress")

    return {
        "name": name,
        "namespace": namespace,
        "healthy": len(issues) == 0,
        "replicas": replicas,
        "ready_replicas": ready_replicas,
        "available_replicas": available_replicas,
        "updated_replicas": updated_replicas,
        "issues": issues,
    }


# ============================================================================
# HPA Operations
# ============================================================================


@handle_k8s_api_errors
def list_hpas(
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """List all HorizontalPodAutoscalers in a namespace.

    Args:
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"hpas": [...], "total": int}
    """
    api = get_autoscaling_v1_client(kubeconfig_path)
    hpa_list = api.list_namespaced_horizontal_pod_autoscaler(namespace=namespace)

    hpas = []
    for hpa in hpa_list.items:
        hpa_info = {
            "name": hpa.metadata.name,
            "namespace": hpa.metadata.namespace,
            "target": {
                "kind": hpa.spec.scale_target_ref.kind,
                "name": hpa.spec.scale_target_ref.name,
            },
            "min_replicas": hpa.spec.min_replicas,
            "max_replicas": hpa.spec.max_replicas,
            "current_replicas": hpa.status.current_replicas or 0,
            "desired_replicas": hpa.status.desired_replicas or 0,
            "current_cpu_utilization": hpa.status.current_cpu_utilization_percentage,
            "target_cpu_utilization": hpa.spec.target_cpu_utilization_percentage,
            "conditions": [
                {
                    "type": c.type,
                    "status": c.status,
                    "reason": c.reason,
                    "message": c.message,
                }
                for c in (hpa.status.conditions or [])
            ],
            "creation_timestamp": hpa.metadata.creation_timestamp.isoformat()
            if hpa.metadata.creation_timestamp
            else None,
        }
        hpas.append(hpa_info)

    return {"hpas": hpas, "total": len(hpas)}


@handle_k8s_api_errors
def check_hpa_health(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Check health status of an HPA.

    Args:
        name: HPA name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "name": str,
            "healthy": bool,
            "current_replicas": int,
            "desired_replicas": int,
            "issues": [str]
        }

    Health checks:
        - HPA is able to scale (no scaling limited errors)
        - Target resource exists
        - Metrics are being collected
        - Current replicas within min/max bounds
    """
    api = get_autoscaling_v1_client(kubeconfig_path)

    try:
        hpa = api.read_namespaced_horizontal_pod_autoscaler(
            name=name, namespace=namespace
        )
    except K8sResourceNotFoundError:
        return {
            "name": name,
            "namespace": namespace,
            "healthy": False,
            "issues": ["HPA does not exist"],
        }

    issues = []
    current_replicas = hpa.status.current_replicas or 0
    desired_replicas = hpa.status.desired_replicas or 0

    # Check if scaling is limited
    for condition in hpa.status.conditions or []:
        if condition.type == "ScalingLimited" and condition.status == "True":
            issues.append(
                f"Scaling is limited: {condition.reason} - {condition.message}"
            )
        if condition.type == "AbleToScale" and condition.status == "False":
            issues.append(
                f"Unable to scale: {condition.reason} - {condition.message}"
            )

    # Check replica bounds
    if current_replicas < hpa.spec.min_replicas:
        issues.append(
            f"Current replicas ({current_replicas}) below minimum ({hpa.spec.min_replicas})"
        )
    if current_replicas > hpa.spec.max_replicas:
        issues.append(
            f"Current replicas ({current_replicas}) above maximum ({hpa.spec.max_replicas})"
        )

    # Check if metrics are available
    if hpa.status.current_cpu_utilization_percentage is None:
        issues.append("CPU utilization metrics not available")

    return {
        "name": name,
        "namespace": namespace,
        "healthy": len(issues) == 0,
        "current_replicas": current_replicas,
        "desired_replicas": desired_replicas,
        "min_replicas": hpa.spec.min_replicas,
        "max_replicas": hpa.spec.max_replicas,
        "current_cpu_utilization": hpa.status.current_cpu_utilization_percentage,
        "target_cpu_utilization": hpa.spec.target_cpu_utilization_percentage,
        "issues": issues,
    }


# ============================================================================
# Ingress Operations
# ============================================================================


@handle_k8s_api_errors
def list_ingresses(
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """List all Ingresses in a namespace.

    Args:
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {"ingresses": [...], "total": int}
    """
    api = get_networking_v1_client(kubeconfig_path)
    ingress_list = api.list_namespaced_ingress(namespace=namespace)

    ingresses = []
    for ingress in ingress_list.items:
        ingress_info = {
            "name": ingress.metadata.name,
            "namespace": ingress.metadata.namespace,
            "ingress_class": ingress.spec.ingress_class_name,
            "hosts": list(
                {
                    rule.host
                    for rule in (ingress.spec.rules or [])
                    if rule.host
                }
            ),
            "paths": [
                {
                    "host": rule.host,
                    "path": path.path,
                    "backend_service": path.backend.service.name
                    if path.backend and path.backend.service
                    else None,
                    "backend_port": path.backend.service.port.number
                    if path.backend and path.backend.service and path.backend.service.port
                    else None,
                }
                for rule in (ingress.spec.rules or [])
                if rule.http  # skip rules without http
                for path in (rule.http.paths or [])
            ],
            "tls": [
                {
                    "hosts": tls.hosts or [],
                    "secret_name": tls.secret_name,
                }
                for tls in (ingress.spec.tls or [])
            ],
            "load_balancer_ip": ingress.status.load_balancer.ingress[0].ip
            if ingress.status.load_balancer
            and ingress.status.load_balancer.ingress
            and len(ingress.status.load_balancer.ingress) > 0
            else None,
            "creation_timestamp": ingress.metadata.creation_timestamp.isoformat()
            if ingress.metadata.creation_timestamp
            else None,
        }
        ingresses.append(ingress_info)

    return {"ingresses": ingresses, "total": len(ingresses)}


@handle_k8s_api_errors
def check_ingress_health(
    name: str,
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Check health status of an Ingress.

    Args:
        name: Ingress name.
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "name": str,
            "healthy": bool,
            "load_balancer_ip": str|None,
            "issues": [str]
        }

    Health checks:
        - Ingress has load balancer IP assigned
        - TLS secret exists (if TLS is configured)
        - Backend services exist
        - No error events
    """
    api = get_networking_v1_client(kubeconfig_path)
    core_api = get_k8s_client(kubeconfig_path)

    try:
        ingress = api.read_namespaced_ingress(name=name, namespace=namespace)
    except K8sResourceNotFoundError:
        return {
            "name": name,
            "namespace": namespace,
            "healthy": False,
            "issues": ["Ingress does not exist"],
        }

    issues = []

    # Check load balancer IP
    lb_ip = None
    if (
        ingress.status.load_balancer
        and ingress.status.load_balancer.ingress
        and len(ingress.status.load_balancer.ingress) > 0
    ):
        lb_ip = ingress.status.load_balancer.ingress[0].ip
    else:
        issues.append("Ingress has no load balancer IP assigned")

    # Check TLS secrets exist
    for tls in ingress.spec.tls or []:
        if tls.secret_name:
            try:
                core_api.read_namespaced_secret(
                    name=tls.secret_name, namespace=namespace
                )
            except K8sResourceNotFoundError:
                issues.append(f"TLS secret '{tls.secret_name}' does not exist")

    # Check backend services exist
    for rule in ingress.spec.rules or []:
        if not rule.http:
            continue
        for path in rule.http.paths or []:
            if not path.backend or not path.backend.service:
                continue
            service_name = path.backend.service.name
            if not service_name:
                continue
            try:
                core_api.read_namespaced_service(
                    name=service_name, namespace=namespace
                )
            except K8sResourceNotFoundError:
                issues.append(f"Backend service '{service_name}' does not exist")

    # Check events for errors
    events = core_api.list_namespaced_event(
        namespace=namespace, field_selector=f"involvedObject.name={name}"
    )
    error_events = [
        e
        for e in events.items
        if e.type == "Warning" and e.reason in ("FailedToUpdateEndpoint", "SyncError")
    ]
    if error_events:
        latest = error_events[-1]
        issues.append(f"Recent error: {latest.reason} - {latest.message}")

    return {
        "name": name,
        "namespace": namespace,
        "healthy": len(issues) == 0,
        "ingress_class": ingress.spec.ingress_class_name,
        "load_balancer_ip": lb_ip,
        "issues": issues,
    }


# ============================================================================
# Summary Operations
# ============================================================================


@handle_k8s_api_errors
def get_workload_summary(
    namespace: str,
    kubeconfig_path: str | None = None,
) -> dict:
    """Get workload resource summary for a namespace.

    Args:
        namespace: Kubernetes namespace.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "namespace": str,
            "pods": {"total": int, "running": int, "pending": int, "failed": int},
            "services": {"total": int},
            "deployments": {"total": int, "ready": int},
            "hpas": {"total": int, "scaling": int},
            "ingresses": {"total": int}
        }
    """
    # Pods
    pod_result = list_pods(namespace, kubeconfig_path=kubeconfig_path)
    pods = pod_result["pods"]
    pod_status = {
        "total": len(pods),
        "running": sum(1 for p in pods if p["status"] == "Running"),
        "pending": sum(1 for p in pods if p["status"] == "Pending"),
        "failed": sum(1 for p in pods if p["status"] == "Failed"),
    }

    # Services
    svc_result = list_services(namespace, kubeconfig_path=kubeconfig_path)
    services = {"total": svc_result["total"]}

    # Deployments
    deploy_result = list_deployments(namespace, kubeconfig_path=kubeconfig_path)
    deployments = deploy_result["deployments"]
    deploy_status = {
        "total": len(deployments),
        "ready": sum(
            1
            for d in deployments
            if d["ready_replicas"] == d["replicas"] and d["replicas"] > 0
        ),
    }

    # HPAs
    hpa_result = list_hpas(namespace, kubeconfig_path=kubeconfig_path)
    hpas = hpa_result["hpas"]
    hpa_status = {
        "total": len(hpas),
        "scaling": sum(
            1 for h in hpas if h["current_replicas"] != h["desired_replicas"]
        ),
    }

    # Ingresses
    ingress_result = list_ingresses(namespace, kubeconfig_path=kubeconfig_path)
    ingresses = {"total": ingress_result["total"]}

    return {
        "namespace": namespace,
        "pods": pod_status,
        "services": services,
        "deployments": deploy_status,
        "hpas": hpa_status,
        "ingresses": ingresses,
    }
