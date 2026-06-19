"""Kubernetes Diagnostics — cross-resource anomaly aggregation and performance analysis.

This module provides:
- Cross-resource health aggregation (Pod → Service → Deployment → Ingress)
- Performance bottleneck detection (CPU/Memory/Restart analysis)
- Root cause analysis orchestration
- Event correlation and pattern matching
- Structured diagnostic reports

Prerequisites:
    pip install kubernetes>=25.3.0

Usage:
    - Use for troubleshooting complex multi-resource issues
    - Use for performance analysis and bottleneck detection
    - Use for generating structured diagnostic reports
"""

import re
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

try:
    from kubernetes import client
    from kubernetes.client.rest import ApiException
except ImportError:
    raise ImportError(
        "kubernetes package not installed. Run: pip install kubernetes>=25.3.0"
    )

from .k8s_client import (
    get_k8s_client,
    get_apps_v1_client,
    handle_k8s_api_errors,
)
from .workload_ops import (
    list_pods,
    list_services,
    list_deployments,
    list_hpas,
    list_ingresses,
    check_pod_health,
    check_deployment_health,
    check_service_health,
    check_hpa_health,
    check_ingress_health,
)
from .storage_ops import check_pvc_health, list_pvcs

logger = logging.getLogger(__name__)


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    """Compile human-readable patterns into regexes with word boundaries.

    Multi-word phrases are matched literally; single words are wrapped with
    ``\\b`` to avoid matching substrings of unrelated words.
    """
    compiled = []
    for pattern in patterns:
        # If the pattern already contains regex meta-characters (e.g. '.*'),
        # keep it as a regex but ensure phrase fragments are word-bounded.
        if re.search(r"[.*+?^${}()|\[\]\\\\]", pattern):
            compiled.append(re.compile(pattern, re.IGNORECASE))
        else:
            compiled.append(re.compile(rf"\\b{re.escape(pattern)}\\b", re.IGNORECASE))
    return compiled


def _matches_any(text: str, compiled_patterns: List[re.Pattern]) -> bool:
    """Return True if text matches any compiled pattern."""
    return any(p.search(text) for p in compiled_patterns)


class DiagnosticReport:
    """Structured diagnostic report for K8s resources.

    This class aggregates health checks across multiple resource types
    and provides root cause analysis.
    """

    def __init__(self, namespace: str):
        """Initialize diagnostic report.

        Args:
            namespace: Kubernetes namespace being analyzed.
        """
        self.namespace = namespace
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.resources: Dict[str, Any] = {
            "pods": [],
            "services": [],
            "deployments": [],
            "hpas": [],
            "ingresses": [],
            "pvcs": [],
        }
        self.issues: List[Dict[str, Any]] = []
        self.root_causes: List[Dict[str, Any]] = []
        self.recommendations: List[str] = []
        self.severity = "info"  # info, warning, critical

    def add_resource_health(
        self,
        resource_type: str,
        resource_name: str,
        health_result: Dict[str, Any],
    ) -> None:
        """Add health check result for a resource.

        Args:
            resource_type: Resource type (pod, service, deployment, etc.).
            resource_name: Resource name.
            health_result: Health check result dict.
        """
        if resource_type not in self.resources:
            self.resources[resource_type] = []

        self.resources[resource_type].append(
            {
                "name": resource_name,
                "health": health_result,
            }
        )

        # Collect issues
        if not health_result.get("healthy", True):
            for issue in health_result.get("issues", []):
                self.issues.append(
                    {
                        "resource_type": resource_type,
                        "resource_name": resource_name,
                        "issue": issue,
                        "severity": self._classify_severity(issue),
                    }
                )

    def _classify_severity(self, issue: str) -> str:
        """Classify issue severity based on keywords.

        Args:
            issue: Issue description.

        Returns:
            str: Severity level (critical, warning, info).
        """
        critical_patterns = _compile_patterns([
            "CrashLoopBackOff",
            "Failed",
            "Lost",
            "no endpoints",
            "not exist",
        ])
        warning_patterns = _compile_patterns([
            "Pending",
            "not ready",
            "restart",
            "unavailable",
        ])

        issue_lower = issue.lower()
        if _matches_any(issue_lower, critical_patterns):
            return "critical"
        if _matches_any(issue_lower, warning_patterns):
            return "warning"
        return "info"

    def analyze_root_causes(self) -> None:
        """Analyze root causes from collected issues.

        This method correlates issues across resources to identify
        common root causes using pattern matching.
        """
        # Use pattern registry for extensible root cause analysis
        for pattern_checker in self._get_pattern_checkers():
            pattern_checker()

        # Set overall severity
        if any(i["severity"] == "critical" for i in self.issues):
            self.severity = "critical"
        elif any(i["severity"] == "warning" for i in self.issues):
            self.severity = "warning"

        # Generate recommendations
        self._generate_recommendations()

    def _get_pattern_checkers(self) -> List[Callable[[], None]]:
        """Get list of pattern checker functions.

        Returns:
            List of callable pattern checkers.
        """
        return [
            self._check_pod_service_endpoint_pattern,
            self._check_pvc_pod_pattern,
            self._check_hpa_scaling_pattern,
            self._check_deployment_replicas_pattern,
            self._check_ingress_backend_pattern,
        ]

    def _check_pod_service_endpoint_pattern(self) -> None:
        """Pattern: Pod failures causing Service endpoint issues."""
        pod_issues = [i for i in self.issues if i["resource_type"] == "pods"]
        service_issues = [i for i in self.issues if i["resource_type"] == "services"]

        if not (pod_issues and service_issues):
            return

        # Check for endpoint-related issues using multiple patterns
        endpoint_patterns = _compile_patterns([
            "no endpoints",
            "endpoint.*not found",
            "service.*has no endpoints",
            "no available endpoints",
        ])

        no_endpoint_services = [
            s
            for s in service_issues
            if _matches_any(s["issue"].lower(), endpoint_patterns)
        ]

        if no_endpoint_services:
            self.root_causes.append(
                {
                    "pattern": "pod_failures_cause_service_endpoints_missing",
                    "description": "Pod failures are causing Services to have no endpoints",
                    "affected_resources": {
                        "pods": [i["resource_name"] for i in pod_issues],
                        "services": [i["resource_name"] for i in no_endpoint_services],
                    },
                    "recommendation": "Fix Pod issues first to restore Service endpoints",
                }
            )

    def _check_pvc_pod_pattern(self) -> None:
        """Pattern: PVC issues causing Pod failures."""
        pvc_issues = [i for i in self.issues if i["resource_type"] == "pvcs"]
        pod_issues = [i for i in self.issues if i["resource_type"] == "pods"]

        if not (pvc_issues and pod_issues):
            return

        # Check for pending PVCs
        pending_pvcs = [
            p
            for p in self.resources.get("pvcs", [])
            if p.get("health", {}).get("status") == "Pending"
        ]

        if pending_pvcs:
            self.root_causes.append(
                {
                    "pattern": "pvc_pending_causes_pod_pending",
                    "description": "Pending PVCs are preventing Pods from starting",
                    "affected_resources": {
                        "pvcs": [p["name"] for p in pending_pvcs],
                        "pods": [i["resource_name"] for i in pod_issues],
                    },
                    "recommendation": "Check StorageClass and PV availability for Pending PVCs",
                }
            )

    def _check_hpa_scaling_pattern(self) -> None:
        """Pattern: HPA scaling issues."""
        hpa_issues = [i for i in self.issues if i["resource_type"] == "hpas"]

        if not hpa_issues:
            return

        # Check for scaling limitations
        scaling_patterns = _compile_patterns([
            "scaling is limited",
            "maximum.*replicas",
            "minimum.*replicas",
            "unable to scale",
        ])

        scaling_limited = [
            h
            for h in self.resources.get("hpas", [])
            if any(
                _matches_any(issue.lower(), scaling_patterns)
                for issue in h.get("health", {}).get("issues", [])
            )
        ]

        if scaling_limited:
            self.root_causes.append(
                {
                    "pattern": "hpa_scaling_limited",
                    "description": "HPA scaling is limited by resource constraints",
                    "affected_resources": {
                        "hpas": [h["name"] for h in scaling_limited],
                    },
                    "recommendation": "Increase resource limits or adjust HPA thresholds",
                }
            )

    def _check_deployment_replicas_pattern(self) -> None:
        """Pattern: Deployment replicas not ready."""
        deployment_issues = [
            i for i in self.issues if i["resource_type"] == "deployments"
        ]

        if not deployment_issues:
            return

        # Check for deployments with unavailable replicas
        not_ready_deployments = [
            d
            for d in self.resources.get("deployments", [])
            if d.get("health", {}).get("ready_replicas", 0)
            < d.get("health", {}).get("replicas", 0)
        ]

        if not_ready_deployments:
            self.root_causes.append(
                {
                    "pattern": "deployment_replicas_not_ready",
                    "description": "Deployments have replicas that are not ready",
                    "affected_resources": {
                        "deployments": [d["name"] for d in not_ready_deployments],
                    },
                    "recommendation": "Check Pod logs and events for deployment issues",
                }
            )

    def _check_ingress_backend_pattern(self) -> None:
        """Pattern: Ingress backend service issues."""
        ingress_issues = [
            i for i in self.issues if i["resource_type"] == "ingresses"
        ]
        service_issues = [i for i in self.issues if i["resource_type"] == "services"]

        if not ingress_issues:
            return

        # Check for backend service issues
        backend_patterns = _compile_patterns([
            "backend.*not exist",
            "service.*not found",
            "backend.*unavailable",
        ])

        backend_issues = [
            ing
            for ing in self.resources.get("ingresses", [])
            if any(
                _matches_any(issue.lower(), backend_patterns)
                for issue in ing.get("health", {}).get("issues", [])
            )
        ]

        if backend_issues:
            self.root_causes.append(
                {
                    "pattern": "ingress_backend_service_issues",
                    "description": "Ingress backends reference non-existent or unavailable Services",
                    "affected_resources": {
                        "ingresses": [ing["name"] for ing in backend_issues],
                    },
                    "recommendation": "Verify backend Services exist and are healthy",
                }
            )

    def _generate_recommendations(self) -> None:
        """Generate actionable recommendations based on root causes."""
        for root_cause in self.root_causes:
            if root_cause["recommendation"] not in self.recommendations:
                self.recommendations.append(root_cause["recommendation"])

        # Add generic recommendations based on issue types
        critical_issues = [i for i in self.issues if i["severity"] == "critical"]
        if critical_issues:
            self.recommendations.append(
                "Review critical issues first: check Pod logs and events"
            )

        crashloop_pattern = re.compile(r"\bCrashLoopBackOff\b")
        if any(crashloop_pattern.search(i["issue"]) for i in self.issues):
            self.recommendations.append(
                "For CrashLoopBackOff: check container logs with 'kubectl logs <pod> --previous'"
            )

        pending_pattern = re.compile(r"\bPending\b")
        if any(pending_pattern.search(i["issue"]) for i in self.issues):
            self.recommendations.append(
                "For Pending resources: check events with 'kubectl describe <resource>'"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary.

        Returns:
            dict: Structured diagnostic report.
        """
        return {
            "namespace": self.namespace,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "summary": {
                "total_issues": len(self.issues),
                "critical_issues": sum(
                    1 for i in self.issues if i["severity"] == "critical"
                ),
                "warning_issues": sum(
                    1 for i in self.issues if i["severity"] == "warning"
                ),
                "root_causes": len(self.root_causes),
            },
            "resources": self.resources,
            "issues": self.issues,
            "root_causes": self.root_causes,
            "recommendations": self.recommendations,
        }


@handle_k8s_api_errors
def diagnose_namespace(
    namespace: str,
    kubeconfig_path: Optional[str] = None,
    include_storage: bool = True,
) -> Dict[str, Any]:
    """Perform comprehensive diagnostic analysis of a namespace.

    This function aggregates health checks across all resource types
    in a namespace and performs root cause analysis.

    Args:
        namespace: Kubernetes namespace to diagnose.
        kubeconfig_path: Path to kubeconfig file.
        include_storage: Whether to include PVC health checks.

    Returns:
        dict: Structured diagnostic report (see DiagnosticReport.to_dict).

    Example:
        >>> report = diagnose_namespace("default")
        >>> if report["severity"] == "critical":
        ...     print(f"Critical issues: {report['summary']['critical_issues']}")
        ...     for rec in report["recommendations"]:
        ...         print(f"  - {rec}")
    """
    report = DiagnosticReport(namespace)

    # Collect Pod health
    pod_result = list_pods(namespace, kubeconfig_path=kubeconfig_path)
    for pod in pod_result["pods"]:
        health = check_pod_health(
            pod["name"], namespace, kubeconfig_path=kubeconfig_path
        )
        report.add_resource_health("pods", pod["name"], health)

    # Collect Service health
    svc_result = list_services(namespace, kubeconfig_path=kubeconfig_path)
    for svc in svc_result["services"]:
        health = check_service_health(
            svc["name"], namespace, kubeconfig_path=kubeconfig_path
        )
        report.add_resource_health("services", svc["name"], health)

    # Collect Deployment health
    deploy_result = list_deployments(namespace, kubeconfig_path=kubeconfig_path)
    for deploy in deploy_result["deployments"]:
        health = check_deployment_health(
            deploy["name"], namespace, kubeconfig_path=kubeconfig_path
        )
        report.add_resource_health("deployments", deploy["name"], health)

    # Collect HPA health
    hpa_result = list_hpas(namespace, kubeconfig_path=kubeconfig_path)
    for hpa in hpa_result["hpas"]:
        health = check_hpa_health(
            hpa["name"], namespace, kubeconfig_path=kubeconfig_path
        )
        report.add_resource_health("hpas", hpa["name"], health)

    # Collect Ingress health
    ingress_result = list_ingresses(namespace, kubeconfig_path=kubeconfig_path)
    for ingress in ingress_result["ingresses"]:
        health = check_ingress_health(
            ingress["name"], namespace, kubeconfig_path=kubeconfig_path
        )
        report.add_resource_health("ingresses", ingress["name"], health)

    # Collect PVC health (optional)
    if include_storage:
        pvc_result = list_pvcs(namespace, kubeconfig_path=kubeconfig_path)
        for pvc in pvc_result["pvcs"]:
            health = check_pvc_health(
                pvc["name"], namespace, kubeconfig_path=kubeconfig_path
            )
            report.add_resource_health("pvcs", pvc["name"], health)

    # Analyze root causes
    report.analyze_root_causes()

    return report.to_dict()


@handle_k8s_api_errors
def analyze_performance_bottlenecks(
    namespace: str,
    kubeconfig_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze performance bottlenecks in a namespace.

    This function identifies common performance issues:
    - High restart counts
    - Resource constraints (CPU/Memory)
    - HPA scaling issues
    - Pod scheduling delays

    Args:
        namespace: Kubernetes namespace to analyze.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "namespace": str,
            "timestamp": str,
            "bottlenecks": [
                {
                    "type": str,
                    "severity": str,
                    "resource": str,
                    "description": str,
                    "recommendation": str
                }
            ],
            "summary": {
                "total_bottlenecks": int,
                "critical": int,
                "warning": int
            }
        }
    """
    bottlenecks = []

    # Analyze Pod restarts
    pod_result = list_pods(namespace, kubeconfig_path=kubeconfig_path)
    for pod in pod_result["pods"]:
        if pod["restarts"] > 10:
            bottlenecks.append(
                {
                    "type": "high_restart_count",
                    "severity": "critical",
                    "resource": f"pod/{pod['name']}",
                    "description": f"Pod has {pod['restarts']} restarts",
                    "recommendation": "Check container logs and liveness probes",
                }
            )
        elif pod["restarts"] > 3:
            bottlenecks.append(
                {
                    "type": "moderate_restart_count",
                    "severity": "warning",
                    "resource": f"pod/{pod['name']}",
                    "description": f"Pod has {pod['restarts']} restarts",
                    "recommendation": "Monitor pod stability",
                }
            )

    # Analyze HPA scaling
    hpa_result = list_hpas(namespace, kubeconfig_path=kubeconfig_path)
    for hpa in hpa_result["hpas"]:
        current_cpu = hpa.get("current_cpu_utilization")
        target_cpu = hpa.get("target_cpu_utilization")
        if current_cpu is not None and target_cpu and target_cpu > 0:
            utilization_ratio = current_cpu / target_cpu
            if utilization_ratio > 0.9:
                bottlenecks.append(
                    {
                        "type": "hpa_near_limit",
                        "severity": "warning",
                        "resource": f"hpa/{hpa['name']}",
                        "description": f"HPA CPU utilization at {current_cpu}% (target: {target_cpu}%)",
                        "recommendation": "Consider increasing resource limits or adjusting HPA thresholds",
                    }
                )

    # Analyze Deployment readiness
    deploy_result = list_deployments(namespace, kubeconfig_path=kubeconfig_path)
    for deploy in deploy_result["deployments"]:
        if deploy["replicas"] > 0:
            readiness_ratio = deploy["ready_replicas"] / deploy["replicas"]
            if readiness_ratio < 0.5:
                bottlenecks.append(
                    {
                        "type": "low_readiness_ratio",
                        "severity": "critical",
                        "resource": f"deployment/{deploy['name']}",
                        "description": f"Only {deploy['ready_replicas']}/{deploy['replicas']} replicas ready",
                        "recommendation": "Check Pod health and resource constraints",
                    }
                )
            elif readiness_ratio < 1.0:
                bottlenecks.append(
                    {
                        "type": "partial_readiness",
                        "severity": "warning",
                        "resource": f"deployment/{deploy['name']}",
                        "description": f"{deploy['ready_replicas']}/{deploy['replicas']} replicas ready",
                        "recommendation": "Monitor deployment progress",
                    }
                )

    # Summarize
    summary = {
        "total_bottlenecks": len(bottlenecks),
        "critical": sum(1 for b in bottlenecks if b["severity"] == "critical"),
        "warning": sum(1 for b in bottlenecks if b["severity"] == "warning"),
    }

    return {
        "namespace": namespace,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "bottlenecks": bottlenecks,
        "summary": summary,
    }


@handle_k8s_api_errors
def correlate_events(
    namespace: str,
    since_minutes: int = 60,
    kubeconfig_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Correlate events across resources in a namespace.

    This function collects recent events and identifies patterns:
    - Recurring error events
    - Event cascades (one resource triggering others)
    - Time-based correlations

    Args:
        namespace: Kubernetes namespace.
        since_minutes: Collect events from the last N minutes.
        kubeconfig_path: Path to kubeconfig file.

    Returns:
        dict: {
            "namespace": str,
            "time_range": str,
            "total_events": int,
            "warning_events": int,
            "error_events": int,
            "patterns": [
                {
                    "type": str,
                    "description": str,
                    "affected_resources": [str],
                    "count": int
                }
            ],
            "events": [...]
        }
    """
    api = get_k8s_client(kubeconfig_path)

    # Calculate time threshold
    since_time = datetime.utcnow() - timedelta(minutes=since_minutes)

    # Collect all events
    events = api.list_namespaced_event(namespace=namespace)

    # Filter and categorize events
    recent_events = []
    warning_count = 0
    error_count = 0

    for event in events.items:
        # Handle both old (last_timestamp) and new (event_time) event formats
        event_time = event.last_timestamp or event.event_time or event.first_timestamp
        if event_time and event_time.replace(tzinfo=None) >= since_time:
            event_dict = {
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "object": f"{event.involved_object.kind}/{event.involved_object.name}",
                "count": event.count,
                "first_timestamp": event.first_timestamp.isoformat()
                if event.first_timestamp
                else None,
                "last_timestamp": event.last_timestamp.isoformat()
                if event.last_timestamp
                else None,
            }
            recent_events.append(event_dict)

            if event.type == "Warning":
                warning_count += 1
                if event.reason in (
                    "Failed",
                    "Error",
                    "BackOff",
                    "CrashLoopBackOff",
                ):
                    error_count += 1

    # Identify patterns
    patterns = []

    # Pattern: Recurring errors
    error_reasons = {}
    for event in recent_events:
        if event["type"] == "Warning":
            reason = event["reason"]
            if reason not in error_reasons:
                error_reasons[reason] = []
            error_reasons[reason].append(event["object"])

    for reason, objects in error_reasons.items():
        if len(objects) >= 3:
            patterns.append(
                {
                    "type": "recurring_error",
                    "description": f"Recurring {reason} events across {len(objects)} resources",
                    "affected_resources": list(set(objects)),
                    "count": len(objects),
                }
            )

    # Pattern: Single resource with multiple errors
    resource_errors = {}
    for event in recent_events:
        if event["type"] == "Warning":
            obj = event["object"]
            if obj not in resource_errors:
                resource_errors[obj] = []
            resource_errors[obj].append(event["reason"])

    for obj, reasons in resource_errors.items():
        if len(reasons) >= 3:
            patterns.append(
                {
                    "type": "resource_error_cascade",
                    "description": f"Resource {obj} has {len(reasons)} error events",
                    "affected_resources": [obj],
                    "count": len(reasons),
                }
            )

    return {
        "namespace": namespace,
        "time_range": f"last {since_minutes} minutes",
        "total_events": len(recent_events),
        "warning_events": warning_count,
        "error_events": error_count,
        "patterns": patterns,
        "events": recent_events,
    }
