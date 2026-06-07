"""
jdcloud-aiops-cruise / analyzers / eip_analyzer.py
=================================================
Elastic IP analyzer.

Checks: bandwidth utilization, association status.
"""

import sys, os
_scripts_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from analyzers import register
from analyzers.base_analyzer import BaseAnalyzer
from lib.jdc_client import get_tag


class EipAnalyzer(BaseAnalyzer):
    service_name = "eip"
    icon = "🌐"

    def discover(self, topology: dict) -> list:
        self.topology = topology
        customer = topology.get("customer", "")
        all_eips = topology.get("raw", {}).get("eips", [])
        self.resources = [e for e in all_eips if get_tag(e, "客户") == customer]
        return self.resources

    def query_metrics(self, client) -> dict:
        for eip in self.resources:
            rid = eip.get("elasticIpId") or eip.get("id")
            if not rid:
                continue
            try:
                pts = client.get_metrics_batch(rid, ["eip.bandwidth.in", "eip.bandwidth.out"],
                                               hours=6, region=client.region)
                if pts:
                    self.metrics[rid] = pts
            except Exception:
                continue
        return self.metrics

    def analyze(self) -> list:
        self.findings = []
        for eip in self.resources:
            rid = eip.get("elasticIpId") or eip.get("id")
            ip = eip.get("elasticIpAddress", rid)
            bandwidth_mbps = eip.get("bandwidthMbps", 1000)  # default 1Gbps
            metrics = self.metrics.get(rid, {})

            for direction, label in [("eip.bandwidth.in", "入带宽"),
                                       ("eip.bandwidth.out", "出带宽")]:
                pts = metrics.get(direction, [])
                if pts:
                    peak = max(v for _, v in pts) / 1_000_000  # bps → Mbps
                    ratio = peak / bandwidth_mbps if bandwidth_mbps > 0 else 0
                    if ratio > 0.8:
                        self._add_finding("warning",
                            f"{label}峰值{peak:.1f}Mbps 达规格上限{bandwidth_mbps}Mbps的{ratio*100:.0f}%",
                            "考虑升配带宽", ip)
                    elif ratio > 0.5:
                        self._add_finding("info",
                            f"{label}峰值{peak:.1f}Mbps ({ratio*100:.0f}%)",
                            "建议关注", ip)

            # Association
            instance_type = eip.get("chargeOnStopped", "")  # not standard, just checking
            self._add_finding("info",
                f"EIP {ip} (带宽{bandwidth_mbps}Mbps)",
                "", ip)

        return self.findings


register("eip", EipAnalyzer)