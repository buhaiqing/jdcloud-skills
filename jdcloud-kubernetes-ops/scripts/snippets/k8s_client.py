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
from typing import Optional, Callable, Any
from functools import wraps

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except ImportError:
    raise ImportError(
        "kubernetes package not installed. Run: pip install kubernetes>=25.3.0"
    )

logger = logging.getLogger(__name__)


class K8sClientError(Exception):
    """Base exception for K8s client errors."""
    pass


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
    exceptions: tuple = (ApiException, K8sConnectionError),
) -> Callable:
    """Decorator for retrying operations on transient failures.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries (seconds).
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated function with retry logic.
    """
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


def get_k8s_client(kubeconfig_path: Optional[str] = None) -> client.CoreV1Api:
    """Initialize K8s CoreV1Api client.

    Args:
        kubeconfig_path: Path to kubeconfig file. If None, uses default
                        (~/.kube/config) or in-cluster config.

    Returns:
        client.CoreV1Api: Initialized K8s API client.

    Raises:
        K8sConnectionError: If client initialization fails.
    """
    try:
        if kubeconfig_path and os.path.exists(kubeconfig_path):
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()

        return client.CoreV1Api()
    except Exception as e:
        raise K8sConnectionError(
            f"Failed to initialize K8s client: {e}. "
            f"Verify kubeconfig exists and is valid."
        ) from e


def get_apps_v1_client(kubeconfig_path: Optional[str] = None) -> client.AppsV1Api:
    """Initialize K8s AppsV1Api client for Deployments/StatefulSets/DaemonSets.

    Args:
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        client.AppsV1Api: Initialized AppsV1 API client.
    """
    try:
        if kubeconfig_path and os.path.exists(kubeconfig_path):
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()

        return client.AppsV1Api()
    except Exception as e:
        raise K8sConnectionError(
            f"Failed to initialize AppsV1 client: {e}. "
            f"Verify kubeconfig exists and is valid."
        ) from e


def get_autoscaling_v1_client(kubeconfig_path: Optional[str] = None) -> client.AutoscalingV1Api:
    """Initialize K8s AutoscalingV1Api client for HPA.

    Args:
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        client.AutoscalingV1Api: Initialized AutoscalingV1 API client.
    """
    try:
        if kubeconfig_path and os.path.exists(kubeconfig_path):
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()

        return client.AutoscalingV1Api()
    except Exception as e:
        raise K8sConnectionError(
            f"Failed to initialize AutoscalingV1 client: {e}. "
            f"Verify kubeconfig exists and is valid."
        ) from e


def get_networking_v1_client(kubeconfig_path: Optional[str] = None) -> client.NetworkingV1Api:
    """Initialize K8s NetworkingV1Api client for Ingress.

    Args:
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        client.NetworkingV1Api: Initialized NetworkingV1 API client.
    """
    try:
        if kubeconfig_path and os.path.exists(kubeconfig_path):
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()

        return client.NetworkingV1Api()
    except Exception as e:
        raise K8sConnectionError(
            f"Failed to initialize NetworkingV1 client: {e}. "
            f"Verify kubeconfig exists and is valid."
        ) from e


def get_storage_v1_client(kubeconfig_path: Optional[str] = None) -> client.StorageV1Api:
    """Initialize K8s StorageV1Api client for StorageClass.

    Args:
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        client.StorageV1Api: Initialized StorageV1 API client.
    """
    try:
        if kubeconfig_path and os.path.exists(kubeconfig_path):
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()

        return client.StorageV1Api()
    except Exception as e:
        raise K8sConnectionError(
            f"Failed to initialize StorageV1 client: {e}. "
            f"Verify kubeconfig exists and is valid."
        ) from e
