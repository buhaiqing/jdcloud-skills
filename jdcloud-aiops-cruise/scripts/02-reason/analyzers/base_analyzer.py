"""
jdcloud-aiops-cruise / analyzers / base_analyzer.py
=================================================
Abstract base class for all service Analyzers.

Each finding now carries instance-level context: resource_id, resource_name,
resource_ip, instance_type, and a structured action with step-by-step
instructions and referenced ops skill.
"""

from abc import ABC, abstractmethod

from lib.jdc_client import get_tag


class BaseAnalyzer(ABC):
    service_name = "base"
    icon = "[待确认]"

    def __init__(self):
        self.resources = []
        self.topology = None
        self.metrics = {}
        self.alarms = []
        self.spec_limits = {}
        self.findings = []

    # ── Common discovery helper ──

    def discover_by_tag(self, topology: dict, resource_key: str,
                        tag_key: str = "客户") -> list:
        """Filter resources from topology by customer tag."""
        self.topology = topology
        customer = topology.get("customer", "")
        all_items = topology.get("raw", {}).get(resource_key, [])
        self.resources = [r for r in all_items if get_tag(r, tag_key) == customer]
        return self.resources

    # ── Common metrics query helper ──

    def query_metrics_batch(self, client, id_field: str = "instanceId",
                            metrics: list = None, hours: int = 6,
                            service_code: str = "vm") -> dict:
        """Query CloudMonitor metrics for all discovered resources."""
        metrics = metrics or []
        for r in self.resources:
            rid = r.get(id_field)
            if not rid:
                continue
            try:
                pts = client.get_metrics_batch(rid, metrics, hours=hours,
                                               region=getattr(client, 'region', None),
                                               service_code=service_code)
                if pts:
                    self.metrics[rid] = pts
            except Exception:
                continue
        return self.metrics

    @abstractmethod
    def discover(self, topology: dict) -> list:
        ...

    @abstractmethod
    def query_metrics(self, client, hours: int = 6) -> dict:
        ...

    @abstractmethod
    def analyze(self) -> list:
        ...

    def report(self) -> dict:
        return {
            "service": self.service_name,
            "icon": self.icon,
            "resources_count": len(self.resources),
            "resources": self._resource_summary(),
            "metrics": self._summarize_metrics(),
            "findings": self.findings,
            "spec_water_level": self._compute_water_level(),
        }

    def _resource_summary(self) -> list:
        """Return key details for each resource. Override in subclass for richer info."""
        return self.resources

    def _summarize_metrics(self) -> dict:
        summary = {}
        for rid, mdict in self.metrics.items():
            summary[rid] = {}
            for mname, pts in mdict.items():
                if not pts:
                    continue
                vals = [v for _, v in pts]
                summary[rid][mname] = {
                    "current": vals[-1] if vals else None,
                    "avg": sum(vals) / len(vals) if vals else None,
                    "max": max(vals) if vals else None,
                    "min": min(vals) if vals else None,
                    "points": len(pts),
                }
        return summary

    def _compute_water_level(self) -> dict:
        return {}

    def _add_finding(self, severity: str, message: str, action: str = "",
                     resource: str = "", resource_id: str = "",
                     resource_ip: str = "", instance_type: str = "",
                     ops_skill: str = ""):
        """Add a finding with full instance context.

        Args:
            severity: critical|warning|info
            message: human-readable description of the problem
            action: step-by-step action plan (semicolon-separated steps)
            resource: resource name (shown in report header)
            resource_id: JD Cloud resource ID
            resource_ip: internal IP address
            instance_type: instance specification
            ops_skill: which JD Cloud Skill to delegate changes to
        """
        self.findings.append({
            "severity": severity,
            "resource": resource,
            "resource_id": resource_id,
            "resource_ip": resource_ip,
            "instance_type": instance_type,
            "message": message,
            "action": action,
            "ops_skill": ops_skill,
        })
