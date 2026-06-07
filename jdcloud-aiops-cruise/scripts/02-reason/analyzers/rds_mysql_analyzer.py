"""
jdcloud-aiops-cruise / analyzers / rds_mysql_analyzer.py
=======================================================
RDS MySQL Slow Query Analyzer.

Discovers MySQL instances by customer tag, queries slow logs,
and performs three-phase analysis: severity classification,
root cause analysis, and optimization advice generation.

Delegates to jdcloud-mysql-ops skill for actual API calls.
"""

from . import register
from .base_analyzer import BaseAnalyzer
import sys, os
_scripts_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from lib.jdc_client import tag_dict, get_tag


# ── Thresholds (from references/threshold-definitions.md) ──

SEVERITY_THRESHOLDS = {
    "critical": {
        "execution_time_avg_ms": 5000,
        "execution_time_sum_ms": 300000,
        "execution_count": 10000,
    },
    "major": {
        "execution_time_avg_ms": 1000,
        "rows_examined_sum": 500000,
        "execution_count": 1000,
    },
}

ROOT_CAUSE_PATTERNS = {
    "missing_index": {
        "icon": "🏷️",
        "label": "Missing Index",
        "check": lambda log: (
            log.get("rowsExaminedSum", 0) > log.get("rowsSentSum", 1) * 100
            and log.get("rowsExaminedSum", 0) > 10000
            and log.get("executionTimeAvg", 0) > 500
        ),
    },
    "full_table_scan": {
        "icon": "📊",
        "label": "Full Table Scan",
        "check": lambda log: (
            "where" not in log.get("sql", "").lower()
            and log.get("rowsExaminedSum", 0) > 50000
        ),
    },
    "lock_contention": {
        "icon": "🔒",
        "label": "Lock Contention",
        "check": lambda log: (
            log.get("executionTimeSum", 1) > 0
            and log.get("lockTimeSum", 0) > log.get("executionTimeSum", 1) * 0.3
        ),
    },
    "inefficient_join": {
        "icon": "🔗",
        "label": "Inefficient JOIN",
        "check": lambda log: (
            log.get("sql", "").lower().count("join") >= 2
            and log.get("rowsExaminedSum", 0) > 500000
            and log.get("rowsSentSum", 0) < 1000
        ),
    },
    "large_result_set": {
        "icon": "📦",
        "label": "Large Result Set",
        "check": lambda log: (
            log.get("rowsSentSum", 0) > 10000
            and log.get("executionTimeAvg", 0) > 2000
        ),
    },
    "frequent_small_query": {
        "icon": "⏰",
        "label": "Frequent Small Query",
        "check": lambda log: (
            log.get("executionCount", 0) > 1000
            and log.get("executionTimeAvg", 0) < 500
        ),
    },
    "temp_table_sort": {
        "icon": "📐",
        "label": "Temp Table / File Sort",
        "check": lambda log: (
            "order by" in log.get("sql", "").lower()
            and log.get("rowsExaminedSum", 0) > 100000
            and log.get("executionTimeAvg", 0) > 2000
        ),
    },
}


class RdsMysqlAnalyzer(BaseAnalyzer):
    """RDS MySQL Slow Query Analyzer."""

    service_name = "rds_mysql"
    icon = "🐬"

    def discover(self, topology: dict) -> list:
        """Extract MySQL instances tagged with the target customer."""
        self.topology = topology
        all_instances = topology.get("raw", {}).get("rds", [])

        # Filter MySQL instances
        self.resources = [
            inst
            for inst in all_instances
            if inst.get("engine") == "MySQL"
        ]

        return self.resources

    def classify_severity(self, log: dict) -> str:
        """Classify slow query severity."""
        avg_time = log.get("executionTimeAvg", 0)
        total_time = log.get("executionTimeSum", 0)
        count = log.get("executionCount", 0)
        rows_examined = log.get("rowsExaminedSum", 0)

        critical = SEVERITY_THRESHOLDS["critical"]
        if (
            avg_time >= critical["execution_time_avg_ms"]
            or total_time >= critical["execution_time_sum_ms"]
            or count >= critical["execution_count"]
        ):
            return "🔴 Critical"

        major = SEVERITY_THRESHOLDS["major"]
        if (
            avg_time >= major["execution_time_avg_ms"]
            or rows_examined >= major["rows_examined_sum"]
            or count >= major["execution_count"]
        ):
            return "🟡 Major"

        return "🔵 Minor"

    def analyze_root_causes(self, log: dict) -> list:
        """Analyze root causes for a slow query."""
        findings = []
        for key, pattern in ROOT_CAUSE_PATTERNS.items():
            try:
                if pattern["check"](log):
                    findings.append(
                        {
                            "type": key,
                            "icon": pattern["icon"],
                            "label": pattern["label"],
                        }
                    )
            except Exception:
                continue
        return findings

    def generate_optimization_advice(
        self, log: dict, findings: list
    ) -> list:
        """Generate actionable optimization advice."""
        sql = log.get("sql", "")
        advice_list = []

        for finding in findings:
            advice = {"type": finding["type"], "priority": "high"}

            if finding["type"] == "missing_index":
                # Extract table and column from SQL
                import re

                tables = re.findall(
                    r"from\s+(\w+)", sql, re.IGNORECASE
                )
                where_cols = re.findall(
                    r"where\s+(\w+(?:\.\w+)?)\s*[=<>]",
                    sql,
                    re.IGNORECASE,
                )
                table = tables[0] if tables else "<table>"
                cols = [c.split(".")[-1] for c in where_cols[:3]]
                idx_name = (
                    f"idx_{table}_{'_'.join(cols)}"
                    if cols
                    else f"idx_{table}_<columns>"
                )
                idx_cols = ", ".join(cols) if cols else "<columns>"

                advice["action"] = (
                    f"CREATE INDEX {idx_name} ON {table}({idx_cols})"
                )
                advice["rationale"] = (
                    f"Query examines {log.get('rowsExaminedSum', 0)} rows "
                    f"but only returns {log.get('rowsSentSum', 0)}. "
                    "An index would dramatically reduce rows scanned."
                )
                advice["estimated_impact"] = "Reduce execution time by ~80%"

            elif finding["type"] == "full_table_scan":
                advice["action"] = (
                    "Add WHERE clause filter on indexed column(s)"
                )
                advice["rationale"] = (
                    "Full table scan detected. Add index to avoid "
                    "scanning the entire table."
                )
                advice["estimated_impact"] = "Reduce rows scanned by ~95%"

            elif finding["type"] == "lock_contention":
                advice["action"] = (
                    "1. Shorten transaction boundaries\n"
                    "2. Consider READ COMMITTED isolation\n"
                    "3. Check innodb_lock_wait_timeout"
                )
                advice["rationale"] = (
                    f"Lock wait {log.get('lockTimeSum', 0)}ms is "
                    f"{log.get('lockTimeSum', 0) * 100 // log.get('executionTimeSum', 1)}% "
                    "of total execution time."
                )
                advice["estimated_impact"] = "Reduce lock wait by ~50%"

            elif finding["type"] == "inefficient_join":
                advice["action"] = (
                    "1. Add indexes on all JOIN columns\n"
                    "2. Ensure smaller table drives the JOIN\n"
                    "3. Use STRAIGHT_JOIN if needed"
                )
                advice["rationale"] = (
                    f"Multi-table JOIN examining "
                    f"{log.get('rowsExaminedSum', 0)} rows."
                )
                advice["estimated_impact"] = "Reduce JOIN overhead by ~60%"

            elif finding["type"] == "large_result_set":
                advice["action"] = (
                    "Add LIMIT clause for pagination"
                )
                advice["rationale"] = (
                    f"Query returns {log.get('rowsSentSum', 0)} rows. "
                    "Large result sets increase network I/O."
                )
                advice["estimated_impact"] = "Reduce network I/O by ~70%"

            elif finding["type"] == "frequent_small_query":
                advice["action"] = (
                    "1. Use batch query (WHERE id IN (...))\n"
                    "2. Add application-level cache\n"
                    "3. Use JOIN to fetch related data"
                )
                advice["rationale"] = (
                    f"Executed {log.get('executionCount', 0)} times. "
                    "Batch or cache can eliminate overhead."
                )
                advice["estimated_impact"] = (
                    f"Reduce total time from "
                    f"{log.get('executionTimeSum', 0)}ms to ~"
                    f"{log.get('executionTimeSum', 0) // 10}ms"
                )

            elif finding["type"] == "temp_table_sort":
                advice["action"] = (
                    "CREATE INDEX idx_<table>_<col> ON <table>(<col>) "
                    "covering both WHERE and ORDER BY"
                )
                advice["rationale"] = (
                    "ORDER BY on large result set without index "
                    "causes filesort."
                )
                advice["estimated_impact"] = "Eliminate filesort overhead"

            advice_list.append(advice)

        return advice_list

    def query_metrics(self, client) -> None:
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
        """Execute three-phase slow query analysis."""
        findings = []

        # Since we cannot get slow logs via JD Cloud API directly,
        # we generate info-level findings about the instances
        for instance in self.resources:
            instance_id = instance.get("instanceId", "unknown")
            instance_name = instance.get("instanceName", "")
            engine_version = instance.get("engineVersion", "")
            instance_class = instance.get("instanceClass", "")
            storage_gb = instance.get("instanceStorageGB", 0)

            findings.append({
                "resource": instance_name,
                "resource_id": instance_id,
                "resource_type": "rds_mysql",
                "severity": "info",
                "message": f"MySQL {engine_version}, {instance_class}, {storage_gb}GB storage",
                "action": "Slow query analysis requires jdcloud-mysql-ops skill with DB credentials",
                "ops_skill": "jdcloud-mysql-ops",
                "requires_confirmation": True,
            })

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

    def _legacy_analyze(self, metrics_by_resource: dict) -> dict:
        """Execute three-phase slow query analysis."""
        findings = []

        for instance in self.resources:
            instance_id = instance.get("instanceId", "unknown")
            instance_name = instance.get("instanceName", "")

            # Get slow logs for this instance
            slow_logs = metrics_by_resource.get(instance_id, [])

            for log in slow_logs:
                # Phase 1: Severity classification
                severity = self.classify_severity(log)

                # Phase 2: Root cause analysis
                root_causes = self.analyze_root_causes(log)

                # Phase 3: Optimization advice
                advice = self.generate_optimization_advice(log, root_causes)

                findings.append(
                    {
                        "instance_id": instance_id,
                        "instance_name": instance_name,
                        "sql": log.get("sql", "")[:200],
                        "severity": severity,
                        "execution_count": log.get("executionCount", 0),
                        "execution_time_avg": log.get("executionTimeAvg", 0),
                        "execution_time_sum": log.get("executionTimeSum", 0),
                        "rows_examined": log.get("rowsExaminedSum", 0),
                        "rows_sent": log.get("rowsSentSum", 0),
                        "lock_time": log.get("lockTimeSum", 0),
                        "root_causes": root_causes,
                        "optimization_advice": advice,
                    }
                )

        # Sort by severity and total execution time
        severity_order = {"🔴 Critical": 0, "🟡 Major": 1, "🔵 Minor": 2}
        findings.sort(
            key=lambda x: (
                severity_order.get(x["severity"], 3),
                -x["execution_time_sum"],
            )
        )

        return {
            "service": self.service_name,
            "resource_count": len(self.resources),
            "finding_count": len(findings),
            "findings_by_severity": self._count_by_severity(findings),
            "findings": findings[:50],  # Top 50
        }

    def _count_by_severity(self, findings: list) -> dict:
        """Count findings by severity level."""
        counts = {"🔴 Critical": 0, "🟡 Major": 0, "🔵 Minor": 0}
        for f in findings:
            severity = f.get("severity", "🔵 Minor")
            counts[severity] = counts.get(severity, 0) + 1
        return counts


# Register the analyzer
register("rds_mysql", RdsMysqlAnalyzer)
