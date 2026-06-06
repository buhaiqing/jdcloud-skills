"""
jdcloud-link-cruise / analyzers / clb_analyzer.py
=================================================
CLB (Load Balancer) analyzer.

Handles both:
- K8s-managed CLB (Ingress controller) → check nginx-ingress health
- Traditional CLB → check backend instance health

Discovery: CLBs tagged with target customer.
Metrics:  active connections, new connections, healthy host count.
"""

import sys, os
_scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from analyzers import register
from analyzers.base_analyzer import BaseAnalyzer
from lib.jdc_client import get_tag, tag_dict

K8S_CLB_TAG = "kubernetes.jdcloud.com/created_by"


class ClbAnalyzer(BaseAnalyzer):
    service_name = "clb"
    icon = "⚖️"

    def discover(self, topology: dict) -> list:
        self.topology = topology
        customer = topology.get("customer", "")
        all_lbs = topology.get("raw", {}).get("lbs", [])
        self.resources = [lb for lb in all_lbs if get_tag(lb, "客户") == customer]
        return self.resources

    def query_metrics(self, client) -> dict:
        clb_metrics = [
            "lb.active_connection_count",
            "lb.new_connection_count",
            "lb.backend.healthy.host_count",
        ]
        for lb in self.resources:
            rid = lb.get("loadBalancerId")
            if not rid:
                continue
            try:
                pts = client.get_metrics_batch(rid, clb_metrics, hours=6,
                                               region=client.region)
                if pts:
                    self.metrics[rid] = pts
            except Exception:
                continue
        return self.metrics

    def analyze(self) -> list:
        self.findings = []
        for lb in self.resources:
            rid = lb.get("loadBalancerId")
            name = lb.get("loadBalancerName", rid)
            tags = tag_dict(lb)
            is_k8s = K8S_CLB_TAG in tags
            metrics = self.metrics.get(rid, {})

            # Active connections
            conn = metrics.get("lb.active_connection_count", [])
            if conn:
                avg_c = sum(v for _, v in conn) / len(conn)
                max_c = max(v for _, v in conn)
                if max_c > 8000:
                    self._add_finding("warning",
                        f"并发连接峰值{max_c:.0f}",
                        "接近规格上限，考虑升配CLB", name)
                elif avg_c > 5000:
                    self._add_finding("info",
                        f"并发连接平均{avg_c:.0f}",
                        "建议关注", name)

            # Healthy backend ratio
            health = metrics.get("lb.backend.healthy.host_count", [])
            if health:
                for t, v in health:
                    if v < 2:  # less than 2 healthy backends
                        self._add_finding("critical",
                            f"健康后端数={v:.0f} @ {datetime.utcfromtimestamp(t/1000).strftime('%H:%M')}",
                            "检查后端VM状态", name)
                        break

            # Deployment mode
            if is_k8s:
                svc_name = tags.get("serviceName", "unknown")
                cluster_id = tags.get("kubernetes.jdcloud.com/cluster_id", "unknown")
                self._add_finding("info",
                    f"K8s Ingress ({svc_name}, cluster={cluster_id})",
                    "Pod级分析请使用k8s_analyzer", name)
            else:
                self._add_finding("info",
                    "传统CLB部署",
                    "无K8s关联", name)

        return self.findings

    def _summarize_metrics(self):
        from datetime import datetime as dt
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


register("clb", ClbAnalyzer)