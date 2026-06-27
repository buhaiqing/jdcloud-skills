"""
jdcloud-aiops-cruise / analyzers / rds_mysql_analyzer.py
=======================================================
RDS MySQL Slow Query Analyzer.

Discovers MySQL instances by customer tag and delegates slow-query
diagnosis to jdcloud-mysql-ops skill. This analyzer is read-only:
it does NOT generate DDL/DML recommendations such as CREATE INDEX.
"""

from . import register
from .base_analyzer import BaseAnalyzer


class RdsMysqlAnalyzer(BaseAnalyzer):
    """RDS MySQL Slow Query Analyzer."""

    service_name = "rds_mysql"
    icon = "[数据库]"

    def discover(self, topology: dict) -> list:
        """Extract MySQL instances tagged with the target customer."""
        self.discover_by_tag(topology, "rds")
        self.resources = [r for r in self.resources if r.get("engine") == "MySQL"]
        return self.resources

    def query_metrics(self, client, hours: int = 6) -> None:
        """Query slow logs for discovered instances.

        Note: JD Cloud RDS API does not expose slow query logs via standard API.
        This is a placeholder - actual slow log analysis requires:
        1. Database user credentials
        2. Direct mysql.slow_log table access or PERFORMANCE_SCHEMA
        3. jdcloud-mysql-ops skill delegation
        """
        self.metrics = {}
        # Placeholder: mark that we need to delegate to jdcloud-mysql-ops
        for instance in self.resources:
            self.metrics[instance.get("instanceId")] = []

    def analyze(self) -> list:
        """Generate info-level findings and delegate slow-query analysis."""
        findings = []

        # Since we cannot get slow logs via JD Cloud API directly,
        # we generate info-level findings about the instances
        for instance in self.resources:
            instance_id = instance.get("instanceId", "unknown")
            instance_name = instance.get("instanceName", "")
            engine_version = instance.get("engineVersion", "")
            instance_class = instance.get("instanceClass", "")
            storage_gb = instance.get("instanceStorageGB", 0)

            findings.append(
                {
                    "resource": instance_name,
                    "resource_id": instance_id,
                    "resource_type": "rds_mysql",
                    "severity": "info",
                    "message": f"MySQL {engine_version}, {instance_class}, {storage_gb}GB storage",
                    "action": "Slow query analysis requires jdcloud-mysql-ops skill with DB credentials",
                    "ops_skill": "jdcloud-mysql-ops",
                    "requires_confirmation": True,
                }
            )

        self.findings = findings
        return findings

    def report(self) -> dict:
        """Generate analysis report."""
        return {
            "service": self.service_name,
            "resource_count": len(self.resources),
            "finding_count": len(self.findings),
            "findings": self.findings,
        }


# Register the analyzer
register("rds_mysql", RdsMysqlAnalyzer)
