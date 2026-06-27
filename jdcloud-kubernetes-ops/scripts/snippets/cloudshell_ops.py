"""CloudShell integration — remote kubectl execution with graceful degradation.

This module provides:
- CloudShell-based kubectl command execution
- Permission checking and graceful degradation
- Structured error messages with actionable guidance
- Result parsing and normalization

Prerequisites:
    - JD Cloud CloudShell API access
    - Valid kubeconfig in the cluster

When to use:
    - When direct K8s API access is not available
    - When kubectl commands are needed for diagnostics
    - When collecting data from cluster nodes

Degradation strategy:
    1. Try CloudShell API (if available)
    2. Fall back to local kubectl (if kubeconfig available)
    3. Return structured error with manual steps
"""

import os
import json
import shlex
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any

try:
    from jdcloud_sdk.services.cloudshell.client.CloudshellClient import CloudshellClient
    from jdcloud_sdk.services.cloudshell.apis.ExecuteCommandRequest import (
        ExecuteCommandRequest,
        ExecuteCommandParameters,
    )
    from jdcloud_sdk.core.credential import Credential
except ImportError:
    # CloudShell SDK not available — will use fallback
    CloudshellClient = None

from .k8s_client import (
    CloudShellUnavailableError,
)

logger = logging.getLogger(__name__)

# Extra seconds beyond command timeout for network round-trips / SDK handshake
_CLOUDSHELL_NETWORK_OVERHEAD = 10


class CloudShellExecutor:
    """Execute kubectl commands via JD Cloud CloudShell.

    This class provides a safe wrapper around CloudShell API execution,
    with permission checking and graceful degradation.

    Example:
        >>> executor = CloudShellExecutor(region_id="cn-north-1")
        >>> result = executor.execute_kubectl("get pods -n default")
        >>> if result["success"]:
        ...     print(result["output"])
        ... else:
        ...     print(f"Error: {result['error']}")
    """

    def __init__(
        self,
        region_id: str,
        cluster_id: str | None = None,
        kubeconfig_path: str | None = None,
    ):
        """Initialize CloudShell executor.

        Args:
            region_id: JD Cloud region (e.g., "cn-north-1").
            cluster_id: K8s cluster ID (for CloudShell context).
            kubeconfig_path: Path to kubeconfig (for local fallback).
        """
        self.region_id = region_id
        self.cluster_id = cluster_id
        self.kubeconfig_path = kubeconfig_path
        self._client = None
        self._check_cloudshell_available()

    def _check_cloudshell_available(self) -> None:
        """Check if CloudShell API is available and accessible."""
        if CloudshellClient is None:
            logger.warning("CloudShell SDK not available")
            return

        try:
            credential = Credential(
                os.environ.get("JDC_ACCESS_KEY", ""),
                os.environ.get("JDC_SECRET_KEY", ""),
            )
            self._client = CloudshellClient(credential)
            # Test connectivity with a simple command
            logger.info("CloudShell client initialized successfully")
        except Exception as e:
            logger.warning(f"CloudShell initialization failed: {e}")
            self._client = None

    def execute_kubectl(
        self,
        command: str,
        namespace: str | None = "default",
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Execute kubectl command via CloudShell.

        Args:
            command: kubectl command (e.g., "get pods -n default").
            namespace: Kubernetes namespace (default: "default").
            timeout: Command timeout in seconds (default: 60).

        Returns:
            dict: {
                "success": bool,
                "output": str,
                "error": str|None,
                "exit_code": int,
                "method": "cloudshell"|"local"|"manual",
                "fallback_reason": str|None
            }

        Degradation:
            - If CloudShell unavailable, try local kubectl
            - If local kubectl unavailable, return manual steps
        """
        degradation_reasons = []

        # Try CloudShell first
        if self._client:
            try:
                result = self._execute_via_cloudshell(command, namespace, timeout)
                # Only degrade if the execution method itself failed, not if kubectl returned an error
                if result["method"] == "cloudshell" and result["exit_code"] != -1:
                    return result
                degradation_reasons.append(f"CloudShell execution failed: {result.get('error', 'unknown error')}")
                logger.warning(f"CloudShell execution failed: {result.get('error', 'unknown error')}")
            except Exception as e:
                degradation_reasons.append(f"CloudShell exception: {type(e).__name__}: {str(e)}")
                logger.warning(f"CloudShell error: {e}")
        else:
            degradation_reasons.append("CloudShell client not initialized")

        # Fallback to local kubectl
        if self.kubeconfig_path and os.path.exists(self.kubeconfig_path):
            try:
                result = self._execute_via_local_kubectl(command, namespace, timeout)
                # Only degrade if the execution method itself failed
                if result["method"] == "local" and result["exit_code"] != -1:
                    # Include degradation history in result
                    if degradation_reasons:
                        result["degradation_history"] = degradation_reasons
                    return result
                degradation_reasons.append(f"Local kubectl execution failed: {result.get('error', 'unknown error')}")
                logger.warning(f"Local kubectl failed: {result.get('error', 'unknown error')}")
            except Exception as e:
                degradation_reasons.append(f"Local kubectl exception: {type(e).__name__}: {str(e)}")
                logger.warning(f"Local kubectl error: {e}")
        else:
            if not self.kubeconfig_path:
                degradation_reasons.append("kubeconfig_path not provided")
            elif not os.path.exists(self.kubeconfig_path):
                degradation_reasons.append(f"kubeconfig file not found: {self.kubeconfig_path}")

        # Final fallback: return manual steps with degradation history
        manual_result = self._get_manual_execution_result(command, namespace)
        if degradation_reasons:
            manual_result["degradation_history"] = degradation_reasons
        return manual_result

    def _send_with_timeout(self, request, timeout: int):
        """Send SDK request with a client-side socket timeout.

        The SDK ``send()`` call is blocking; this wrapper prevents it from
        hanging indefinitely if the CloudShell service is unreachable.
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._client.send, request)
            return future.result(timeout=timeout)

    def _execute_via_cloudshell(
        self,
        command: str,
        namespace: str,
        timeout: int,
    ) -> dict[str, Any]:
        """Execute command via CloudShell API."""
        if not self._client:
            raise CloudShellUnavailableError("CloudShell client not initialized")

        # Build kubectl command with kubeconfig
        full_command = f"kubectl {command}"
        if self.kubeconfig_path:
            full_command = f"KUBECONFIG={self.kubeconfig_path} {full_command}"

        try:
            params = ExecuteCommandParameters(
                regionId=self.region_id,
                command=full_command,
                timeout=timeout,
            )
            req = ExecuteCommandRequest(parameters=params)
            # Client-side timeout = command timeout + network overhead
            resp = self._send_with_timeout(req, timeout + _CLOUDSHELL_NETWORK_OVERHEAD)

            # Parse response
            output = resp.result.get("output", "")
            error_output = resp.result.get("error", "")
            exit_code = resp.result.get("exitCode", 0)

            return {
                "success": exit_code == 0,
                "output": output,
                "error": error_output if exit_code != 0 else None,
                "exit_code": exit_code,
                "method": "cloudshell",
                "fallback_reason": None,
            }
        except FutureTimeoutError as e:
            return {
                "success": False,
                "output": "",
                "error": f"CloudShell API call timed out after {timeout + _CLOUDSHELL_NETWORK_OVERHEAD}s: {e}",
                "exit_code": -1,
                "method": "cloudshell",
                "fallback_reason": "CloudShell API timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "method": "cloudshell",
                "fallback_reason": "CloudShell API error",
            }

    def _execute_via_local_kubectl(
        self,
        command: str,
        namespace: str,
        timeout: int,
    ) -> dict[str, Any]:
        """Execute command via local kubectl binary."""
        import subprocess

        # Build kubectl command
        full_command = ["kubectl"]
        if self.kubeconfig_path:
            full_command.extend(["--kubeconfig", self.kubeconfig_path])
        full_command.extend(shlex.split(command))

        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "exit_code": result.returncode,
                "method": "local",
                "fallback_reason": None,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {timeout}s",
                "exit_code": -1,
                "method": "local",
                "fallback_reason": "Timeout",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "error": "kubectl binary not found in PATH",
                "exit_code": -1,
                "method": "local",
                "fallback_reason": "kubectl not installed",
            }

    def _get_manual_execution_result(
        self,
        command: str,
        namespace: str,
    ) -> dict[str, Any]:
        """Return structured manual execution steps."""
        return {
            "success": False,
            "output": "",
            "error": "No execution method available",
            "exit_code": -1,
            "method": "manual",
            "fallback_reason": "CloudShell and local kubectl unavailable",
            "manual_steps": {
                "description": "Execute kubectl command manually",
                "steps": [
                    "1. Ensure kubeconfig is configured: kubectl config view",
                    f"2. Run command: kubectl {command}",
                    f"3. If permission denied, check RBAC: kubectl auth can-i {shlex.split(command)[0] if shlex.split(command) else command}",
                ],
                "documentation": [
                    "https://docs.jdcloud.com/cn/jcs-for-kubernetes/kubectl-usage",
                    "https://kubernetes.io/docs/reference/kubectl/cheatsheet/",
                ],
                "troubleshooting": {
                    "permission_denied": "Check RBAC permissions for the service account",
                    "connection_refused": "Verify kubeconfig and cluster connectivity",
                    "not_found": "Ensure kubectl is installed and in PATH",
                },
            },
        }

    def collect_diagnostics(
        self,
        namespace: str,
        resource_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Collect diagnostic information from the cluster.

        Args:
            namespace: Kubernetes namespace to inspect.
            resource_types: List of resource types to collect (default: common types).

        Returns:
            dict: {
                "namespace": str,
                "collected_at": str,
                "resources": {
                    "pods": {...},
                    "services": {...},
                    "deployments": {...},
                    ...
                },
                "events": [...],
                "success": bool,
                "errors": [...]
            }
        """
        if resource_types is None:
            resource_types = ["pods", "services", "deployments", "events"]

        collected = {
            "namespace": namespace,
            "collected_at": "",
            "resources": {},
            "events": [],
            "success": True,
            "errors": [],
        }

        import datetime
        collected["collected_at"] = datetime.datetime.utcnow().isoformat() + "Z"

        for resource_type in resource_types:
            if resource_type == "events":
                # Collect events separately
                result = self.execute_kubectl(
                    f"get events -n {namespace} --sort-by='.lastTimestamp'",
                    namespace,
                )
                if result["success"]:
                    collected["events"] = result["output"].split("\n")
                else:
                    collected["errors"].append(
                        f"Failed to collect events: {result['error']}"
                    )
            else:
                # Collect resource
                result = self.execute_kubectl(
                    f"get {resource_type} -n {namespace} -o json",
                    namespace,
                )
                if result["success"]:
                    try:
                        collected["resources"][resource_type] = json.loads(
                            result["output"]
                        )
                    except json.JSONDecodeError as e:
                        collected["errors"].append(
                            f"Failed to parse {resource_type} JSON: {e}"
                        )
                else:
                    collected["errors"].append(
                        f"Failed to collect {resource_type}: {result['error']}"
                    )
                    collected["success"] = False

        return collected


def execute_kubectl_with_fallback(
    command: str,
    region_id: str,
    cluster_id: str | None = None,
    kubeconfig_path: str | None = None,
    namespace: str = "default",
) -> dict[str, Any]:
    """Convenience function to execute kubectl with automatic fallback.

    Args:
        command: kubectl command to execute.
        region_id: JD Cloud region.
        cluster_id: K8s cluster ID.
        kubeconfig_path: Path to kubeconfig.
        namespace: Kubernetes namespace.

    Returns:
        dict: Execution result (see CloudShellExecutor.execute_kubectl).

    Example:
        >>> result = execute_kubectl_with_fallback(
        ...     "get pods -n default",
        ...     region_id="cn-north-1",
        ...     kubeconfig_path="~/.kube/config"
        ... )
        >>> if result["success"]:
        ...     print(result["output"])
    """
    executor = CloudShellExecutor(
        region_id=region_id,
        cluster_id=cluster_id,
        kubeconfig_path=kubeconfig_path,
    )
    return executor.execute_kubectl(command, namespace)
