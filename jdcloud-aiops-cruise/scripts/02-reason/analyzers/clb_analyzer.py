"""
jdcloud-aiops-cruise / analyzers / clb_analyzer.py
=================================================
CLB (Load Balancer) analyzer.

Handles both:
- K8s-managed CLB (Ingress controller) → check nginx-ingress health
- Traditional CLB → check backend instance health

Discovery: CLBs tagged with target customer.
Metrics: active connections, new connections, healthy host count.
Read-only output: upgrade assessment recommendations only; no CLB mutation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from datetime import datetime, timezone
from analyzers import register
from analyzers.base_analyzer import BaseAnalyzer
from lib.jdc_client import tag_dict

K8S_CLB_TAG = "kubernetes.jdcloud.com/created_by"

CLB_THRESHOLDS = {
    "active_connection_warning_ratio": 0.80,
    "active_connection_info_ratio": 0.60,
    "new_connection_warning_ratio": 0.80,
    "new_connection_info_ratio": 0.60,
}

CLB_SPEC_LIMITS = {
    "standard": {"max_active_connections": 500_000, "max_new_connections": 50_000, "bandwidth_gbps": 5},
    "high_performance": {"max_active_connections": 2_000_000, "max_new_connections": 100_000, "bandwidth_gbps": 10},
}


class ClbAnalyzer(BaseAnalyzer):
    service_name = "clb"
    icon = "[负载均衡]"

    CLB_METRICS = [
        "lb.active_connection_count",
        "lb.new_connection_count",
        "lb.backend.healthy.host_count",
    ]

    def discover(self, topology: dict) -> list:
        return self.discover_by_tag(topology, "lbs")

    def query_metrics(self, client, hours: int = 6) -> dict:
        return self.query_metrics_batch(client, id_field="loadBalancerId",
                                        metrics=self.CLB_METRICS, hours=hours,
                                        service_code="lb")

    def analyze(self) -> list:
        self.findings = []
        for lb in self.resources:
            rid = lb.get("loadBalancerId")
            name = lb.get("loadBalancerName", rid)
            tags = tag_dict(lb)
            is_k8s = K8S_CLB_TAG in tags
            metrics = self.metrics.get(rid, {})
            spec = self._infer_spec(lb)
            limits = CLB_SPEC_LIMITS.get(spec, CLB_SPEC_LIMITS["standard"])

            ctx = {"resource": name, "resource_id": rid,
                   "instance_type": spec}

            # Active connections / upgrade assessment
            conn = metrics.get("lb.active_connection_count", [])
            if conn:
                avg_c = sum(v for _, v in conn) / len(conn)
                max_c = max(v for _, v in conn)
                limit = limits["max_active_connections"]
                ratio = max_c / limit if limit else 0
                if ratio >= CLB_THRESHOLDS["active_connection_warning_ratio"]:
                    self._add_finding("warning",
                        f"CLB并发连接峰值{max_c:.0f}，达到{spec}规格上限{limit:.0f}的{ratio*100:.0f}%",
                        "只读建议：确认业务峰值与后端容量；如连续多个周期高于阈值，由人工通过 jdcloud-clb-ops 评估升配/升级",
                        ops_skill="jdcloud-clb-ops", **ctx)
                elif ratio >= CLB_THRESHOLDS["active_connection_info_ratio"]:
                    self._add_finding("info",
                        f"CLB并发连接峰值{max_c:.0f}，达到{spec}规格上限的{ratio*100:.0f}%",
                        "建议纳入容量观察", **ctx)
                elif avg_c > 5000:
                    self._add_finding("info",
                        f"CLB并发连接平均{avg_c:.0f}",
                        "建议关注连接趋势", **ctx)

            # New connections / traffic burst risk
            new_conn = metrics.get("lb.new_connection_count", [])
            if new_conn:
                peak_new = max(v for _, v in new_conn)
                limit = limits["max_new_connections"]
                ratio = peak_new / limit if limit else 0
                if ratio >= CLB_THRESHOLDS["new_connection_warning_ratio"]:
                    self._add_finding("warning",
                        f"CLB新建连接峰值{peak_new:.0f}/s，达到{spec}规格上限{limit:.0f}/s的{ratio*100:.0f}%",
                        "只读建议：检查短连接/突发流量；需要变更时通过 jdcloud-clb-ops 人工执行升配/架构调整",
                        ops_skill="jdcloud-clb-ops", **ctx)
                elif ratio >= CLB_THRESHOLDS["new_connection_info_ratio"]:
                    self._add_finding("info",
                        f"CLB新建连接峰值{peak_new:.0f}/s，达到规格上限的{ratio*100:.0f}%",
                        "建议关注突发流量", **ctx)

            # Healthy backend ratio
            health = metrics.get("lb.backend.healthy.host_count", [])
            if health:
                for t, v in health:
                    if v < 2:  # less than 2 healthy backends
                        self._add_finding("critical",
                            f"健康后端数={v:.0f} @ {datetime.fromtimestamp(t/1000, timezone.utc).strftime('%H:%M')}",
                            "只读建议：检查后端VM/容器健康状态；如需摘除/调整后端，由人工通过 jdcloud-clb-ops 执行",
                            ops_skill="jdcloud-clb-ops", **ctx)
                        break

            # Deployment mode
            if is_k8s:
                svc_name = tags.get("serviceName", "unknown")
                cluster_id = tags.get("kubernetes.jdcloud.com/cluster_id", "unknown")
                self._add_finding("info",
                    f"K8s Ingress ({svc_name}, cluster={cluster_id})",
                    "Pod级分析请使用k8s_analyzer", **ctx)
            else:
                self._add_finding("info",
                    "传统CLB部署",
                    "无K8s关联", **ctx)

        return self.findings

    def _summarize_metrics(self):
        summary = {}
        for rid, mdict in self.metrics.items():
            summary[rid] = {}
            for mname, pts in mdict.items():
                if not pts:
                    continue
                vals = [v for _, v in pts]
                summary[rid][mname] = {
                    "current": vals[-1],
                    "avg": sum(vals) / len(vals),
                    "max": max(vals),
                    "min": min(vals),
                    "points": len(pts),
                }
        return summary

    def _infer_spec(self, lb: dict) -> str:
        raw = " ".join(str(lb.get(k, "")) for k in (
            "spec", "specType", "loadBalancerSpec", "type", "loadBalancerType", "instanceType"
        )).lower()
        if any(token in raw for token in ("high", "performance", "hpa", "高性能")):
            return "high_performance"
        return "standard"


register("clb", ClbAnalyzer)
