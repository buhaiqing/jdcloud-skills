"""Kubernetes client utilities — unified client initialization and error handling.

This module provides:
- Centralized K8s client initialization
- Unified error handling and retry logic
- CloudShell integration for remote kubectl execution
- Common decorators for resilience

Prerequisites:
    pip install kubernetes>=25.3.0
"""

import os
import time
import logging
import threading
from typing import Any
from collections.abc import Callable
from functools import wraps

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except ImportError:
    raise ImportError(
        "kubernetes package not installed. Run: pip install kubernetes>=25.3.0"
    ) from None

logger = logging.getLogger(__name__)

# Client cache to avoid repeated kubeconfig loading (thread-safe)
# Cache value format: {"client": <client>, "mtime": <float|None>, "loaded_at": <float>}
_client_cache: dict[str, dict[str, Any]] = {}
_client_cache_lock = threading.Lock()


def _get_kubeconfig_mtime(kubeconfig_path: str | None) -> float | None:
    """Get kubeconfig file modification time.

    Args:
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        float: Modification timestamp, or None for in-cluster/default config.
    """
    if not kubeconfig_path:
        return None
    try:
        return os.path.getmtime(kubeconfig_path)
    except OSError:
        return None


def _is_cache_valid(cache_key: str, current_mtime: float | None) -> bool:
    """Check if cached client is still valid.

    Args:
        cache_key: Cache key to check.
        current_mtime: Current kubeconfig modification time.

    Returns:
        bool: True if cache is valid, False otherwise.
    """
    cached = _client_cache.get(cache_key)
    if not cached:
        return False

    cached_mtime = cached.get("mtime")
    # For explicit kubeconfig paths, invalidate if file changed
    if current_mtime is not None and cached_mtime != current_mtime:
        logger.debug(
            f"Cache invalidated for {cache_key}: kubeconfig changed"
        )
        return False

    return True


class K8sClientError(Exception):
    """Base exception for K8s client errors.

    Attributes:
        message: Human-readable error description.
        resource_type: K8s resource type (e.g., "Pod", "Service").
        resource_name: Name of the affected resource.
        namespace: Kubernetes namespace.
        original_error: The underlying exception that caused this error.
    """

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_name: str | None = None,
        namespace: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.namespace = namespace
        self.original_error = original_error

    def __str__(self) -> str:
        parts = [self.message]
        if self.resource_type:
            parts.append(f"Resource: {self.resource_type}")
        if self.resource_name:
            parts.append(f"Name: {self.resource_name}")
        if self.namespace:
            parts.append(f"Namespace: {self.namespace}")
        return " | ".join(parts)


class K8sConnectionError(K8sClientError):
    """Raised when K8s API connection fails."""
    pass


class K8sResourceNotFoundError(K8sClientError):
    """Raised when a K8s resource is not found."""
    pass


class K8sPermissionError(K8sClientError):
    """Raised when K8s API permission is denied."""
    pass


class CloudShellUnavailableError(K8sClientError):
    """Raised when CloudShell is not available."""
    pass


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = None,
) -> Callable:
    """Decorator for retrying operations on transient failures.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries (seconds).
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exception types to retry on. Defaults to
                    (ApiException, K8sConnectionError, ConnectionError, OSError).

    Returns:
        Decorated function with retry logic.
    """
    if exceptions is None:
        exceptions = (ApiException, K8sConnectionError, ConnectionError, OSError)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            raise last_exception

        return wrapper
    return decorator


def handle_k8s_api_errors(func: Callable) -> Callable:
    """Decorator for handling K8s API errors with user-friendly messages.

    Converts ApiException to specific exception types with actionable messages.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            if e.status == 404:
                raise K8sResourceNotFoundError(
                    f"Resource not found: {e.reason}. "
                    f"Verify the resource name and namespace."
                ) from e
            elif e.status == 403:
                raise K8sPermissionError(
                    f"Permission denied: {e.reason}. "
                    f"Check RBAC permissions for the service account."
                ) from e
            elif e.status == 401:
                raise K8sPermissionError(
                    f"Authentication failed: {e.reason}. "
                    f"Verify kubeconfig credentials are valid."
                ) from e
            elif e.status in (500, 502, 503, 504):
                raise K8sConnectionError(
                    f"K8s API server error ({e.status}): {e.reason}. "
                    f"The API server may be temporarily unavailable."
                ) from e
            else:
                raise K8sClientError(
                    f"K8s API error ({e.status}): {e.reason}"
                ) from e
    return wrapper


def _load_kube_config(kubeconfig_path: str | None = None) -> None:
    """Load kubeconfig from file or in-cluster config.

    Args:
        kubeconfig_path: Path to kubeconfig file. If None, uses default
                        (~/.kube/config) or in-cluster config.
                        If explicitly provided but file does not exist, raises error.

    Raises:
        K8sConnectionError: If config loading fails.
    """
    try:
        if kubeconfig_path:
            # Explicit path provided — must exist, no silent fallback
            if not os.path.exists(kubeconfig_path):
                raise K8sConnectionError(
                    f"Specified kubeconfig not found: {kubeconfig_path}. "
                    f"Verify the file path is correct."
                )
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            # No explicit path — try in-cluster first, then default
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
    except K8sConnectionError:
        raise
    except Exception as e:
        raise K8sConnectionError(
            f"Failed to load kubeconfig: {e}. "
            f"Verify kubeconfig exists and is valid."
        ) from e


def _get_cache_key(kubeconfig_path: str | None, client_type: str) -> str:
    """Generate cache key for client caching.

    Args:
        kubeconfig_path: Path to kubeconfig file.
        client_type: Type of client (e.g., 'CoreV1Api', 'AppsV1Api').

    Returns:
        str: Cache key.
    """
    config_key = kubeconfig_path or "__default__"
    return f"{config_key}:{client_type}"


T = Any


def _get_or_create_client(
    kubeconfig_path: str | None,
    client_type: str,
    client_class,
) -> Any:
    """Get cached client or create a new one with thread-safe invalidation.

    Args:
        kubeconfig_path: Path to kubeconfig file.
        client_type: Type of client (e.g., 'CoreV1Api', 'AppsV1Api').
        client_class: Kubernetes client class to instantiate.

    Returns:
        Any: Cached or newly created Kubernetes API client.
    """
    cache_key = _get_cache_key(kubeconfig_path, client_type)
    mtime = _get_kubeconfig_mtime(kubeconfig_path)

    with _client_cache_lock:
        if not _is_cache_valid(cache_key, mtime):
            _load_kube_config(kubeconfig_path)
            _client_cache[cache_key] = {
                "client": client_class(),
                "mtime": mtime,
                "loaded_at": time.time(),
            }
        return _client_cache[cache_key]["client"]


def get_k8s_client(kubeconfig_path: str | None = None) -> client.CoreV1Api:
    """Initialize K8s CoreV1Api client with caching.

    Args:
        kubeconfig_path: Path to kubeconfig file. If None, uses default
                        (~/.kube/config) or in-cluster config.

    Returns:
        client.CoreV1Api: Initialized K8s API client.

    Raises:
        K8sConnectionError: If client initialization fails.
    """
    return _get_or_create_client(kubeconfig_path, "CoreV1Api", client.CoreV1Api)


def get_apps_v1_client(kubeconfig_path: str | None = None) -> client.AppsV1Api:
    """Initialize K8s AppsV1Api client for Deployments/StatefulSets/DaemonSets with caching."""
    return _get_or_create_client(kubeconfig_path, "AppsV1Api", client.AppsV1Api)


def get_autoscaling_v1_client(kubeconfig_path: str | None = None) -> client.AutoscalingV1Api:
    """Initialize K8s AutoscalingV1Api client for HPA with caching."""
    return _get_or_create_client(kubeconfig_path, "AutoscalingV1Api", client.AutoscalingV1Api)


def get_networking_v1_client(kubeconfig_path: str | None = None) -> client.NetworkingV1Api:
    """Initialize K8s NetworkingV1Api client for Ingress with caching."""
    return _get_or_create_client(kubeconfig_path, "NetworkingV1Api", client.NetworkingV1Api)


def get_storage_v1_client(kubeconfig_path: str | None = None) -> client.StorageV1Api:
    """Initialize K8s StorageV1Api client for StorageClass with caching."""
    return _get_or_create_client(kubeconfig_path, "StorageV1Api", client.StorageV1Api)


def get_batch_v1_client(kubeconfig_path: str | None = None) -> client.BatchV1Api:
    """Initialize K8s BatchV1Api client for Jobs/CronJobs with caching."""
    return _get_or_create_client(kubeconfig_path, "BatchV1Api", client.BatchV1Api)


def get_rbac_authorization_v1_client(
    kubeconfig_path: str | None = None,
) -> client.RbacAuthorizationV1Api:
    """Initialize K8s RbacAuthorizationV1Api client for RBAC with caching."""
    return _get_or_create_client(
        kubeconfig_path, "RbacAuthorizationV1Api", client.RbacAuthorizationV1Api
    )


def clear_client_cache() -> None:
    """Clear the client cache.

    This is useful when kubeconfig changes or when you need to force
    re-initialization of clients.
    """
    global _client_cache
    _client_cache.clear()
    logger.debug("Client cache cleared")
