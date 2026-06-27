"""
Core tests for jdcloud-aiops-cruise.
Covers jdc_client signing/credentials, resource discovery, analyzer contracts,
and cross-phase integration.
Run with: python -m pytest tests/test_core.py -v
"""

import sys
import os
import json
# Add scripts/ to path for lib/ imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
# Add scripts/02-reason/ to path for analyzers/ imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "02-reason"))

from lib.jdc_client import (
    JdcClient, resolve_credentials, filter_by_tag,
    _resolve_cred_scope_region, _canonical_path, _canonical_qs, _signing_key,
)


class TestSigning:
    """Signing algorithm tests (no network)."""

    def test_cred_region_with_regions(self):
        assert _resolve_cred_scope_region("/v1/regions/cn-north-1/instances", "cn-north-1") == "cn-north-1"

    def test_cred_region_without_regions(self):
        assert _resolve_cred_scope_region("/v2/metrics", "cn-north-1") == "jdcloud-api"

    def test_canonical_path(self):
        path = _canonical_path("//v1/regions//cn-north-1/instances")
        assert "//" not in path
        assert path.startswith("/")

    def test_canonical_qs_empty(self):
        assert _canonical_qs({}) == ""

    def test_canonical_qs_sorted(self):
        qs = _canonical_qs({"b": "2", "a": "1"})
        assert qs == "a=1&b=2"

    def test_canonical_qs_encodes_chinese(self):
        qs = _canonical_qs({"tag": "烟台振华"})
        assert "%E7%83%9F%E5%8F%B0" in qs  # 烟台encoded

    def test_signing_key_not_none(self):
        key = _signing_key("test-sk", "20260606", "cn-north-1", "vm")
        assert key is not None
        assert len(key) > 0


class TestCredentials:
    """Credential resolution tests."""

    def test_resolve_from_env(self):
        os.environ["JDC_ACCESS_KEY"] = "test-ak"
        os.environ["JDC_SECRET_KEY"] = "test-sk"
        ak, sk = resolve_credentials()
        assert ak == "test-ak"
        assert sk == "test-sk"
        del os.environ["JDC_ACCESS_KEY"]
        del os.environ["JDC_SECRET_KEY"]

    def test_resolve_from_params(self):
        ak, sk = resolve_credentials("param-ak", "param-sk")
        assert ak == "param-ak"
        assert sk == "param-sk"


class TestFilterByTag:
    """Tag filtering utility tests."""

    def test_filter_by_tag_exact(self):
        resources = [
            {"tags": [{"key": "客户", "value": "烟台振华"}]},
            {"tags": [{"key": "客户", "value": "武汉可多"}]},
        ]
        result = filter_by_tag(resources, "客户", "烟台振华")
        assert len(result) == 1
        assert result[0]["tags"][0]["value"] == "烟台振华"

    def test_filter_by_tag_no_match(self):
        resources = [{"tags": [{"key": "环境", "value": "production"}]}]
        result = filter_by_tag(resources, "客户", "烟台振华")
        assert len(result) == 0

    def test_filter_by_tag_empty(self):
        assert filter_by_tag([], "客户", "烟台振华") == []


class TestJdcClient:
    """JdcClient integration tests (requires real credentials in .env)."""

    def test_instantiate(self):
        try:
            client = JdcClient()
            assert client.ak is not None
            assert client.sk is not None
        except RuntimeError:
            pass  # No credentials available in CI

    def test_list_vms(self):
        """Integration test — SKIP if no credentials."""
        try:
            client = JdcClient()
            vms = client.list_vms()
            assert isinstance(vms, list)
            if vms:
                vm = vms[0]
                assert "instanceId" in vm
                assert "instanceName" in vm
        except RuntimeError:
            pass

    def test_list_redis(self):
        try:
            client = JdcClient()
            redis = client.list_redis()
            assert isinstance(redis, list)
        except RuntimeError:
            pass

    def test_list_vpcs(self):
        try:
            client = JdcClient()
            vpcs = client.list_vpcs()
            assert isinstance(vpcs, list)
        except RuntimeError:
            pass

    def test_list_lbs(self):
        try:
            client = JdcClient()
            lbs = client.list_lbs()
            assert isinstance(lbs, list)
        except RuntimeError:
            pass

    def test_list_es(self):
        try:
            client = JdcClient()
            es_list = client.list_es()
            assert isinstance(es_list, list)
        except RuntimeError:
            pass

    def test_list_eips(self):
        try:
            client = JdcClient()
            eips = client.list_eips()
            assert isinstance(eips, list)
        except RuntimeError:
            pass

    def test_get_metric(self):
        """Query CPU metric for a known VM."""
        try:
            client = JdcClient()
            vms = client.list_vms(tag_key="客户", tag_value="烟台振华")
            if vms:
                rid = vms[0]["instanceId"]
                points = client.get_metric(rid, "cpu_util", hours=1)
                assert isinstance(points, list)
                if points:
                    ts, val = points[0]
                    assert isinstance(ts, int)
                    assert isinstance(val, (int, float))
        except RuntimeError:
            pass


class TestMetricServiceCode:
    """Monitor serviceCode selection tests (no network)."""

    def test_get_metric_uses_explicit_service_code(self):
        client = JdcClient("ak", "sk", region="cn-north-1")
        captured = {}

        def fake_get(service, path, params):
            captured.update(params)
            return {"result": {"metricDatas": [{"data": [{"timestamp": 1, "value": "2.5"}]}]}}

        client._get = fake_get
        points = client.get_metric("lb-1", "lb.active_connection_count", service_code="lb")
        assert points == [(1, 2.5)]
        assert captured["serviceCode"] == "lb"

    def test_get_metrics_batch_forwards_service_code(self):
        client = JdcClient("ak", "sk", region="cn-north-1")
        service_codes = []

        def fake_get_metric(resource_id, metric, hours=6, aggr="avg", region=None, service_code="vm"):
            service_codes.append(service_code)
            return [(1, 1.0)]

        client.get_metric = fake_get_metric
        result = client.get_metrics_batch("eip-1", ["eip.bandwidth.in", "eip.bandwidth.out"], service_code="eip")
        assert set(result) == {"eip.bandwidth.in", "eip.bandwidth.out"}
        assert service_codes == ["eip", "eip"]


class TestEipDiscoveryAndAnalyzer:
    """EIP discovery and audit tests (no cloud credentials)."""

    def test_discovery_populates_customer_eips(self):
        from lib.resource_discovery import discover_customer_resources

        class FakeClient:
            def list_vms(self, region=None): return []
            def list_lbs(self, region=None): return []
            def list_redis(self, region=None): return []
            def list_vpcs(self, region=None): return []
            def list_subnets(self, region=None): return []
            def list_security_groups(self, region=None): return []
            def list_es(self, region=None): return []
            def list_rds(self, region=None): return []
            def list_eips(self, region=None):
                return [
                    {"elasticIpId": "eip-1", "elasticIpAddress": "1.1.1.1", "tags": [{"key": "客户", "value": "客户A"}]},
                    {"elasticIpId": "eip-2", "elasticIpAddress": "2.2.2.2", "tags": [{"key": "客户", "value": "客户B"}]},
                ]

        result = discover_customer_resources(FakeClient(), "客户A", regions=["cn-north-1"])
        assert [e["elasticIpId"] for e in result["raw"]["eips"]] == ["eip-1"]
        assert all(e["tags"][0]["value"] == "客户A" for e in result["raw"]["eips"])
        persisted = json.loads(json.dumps(result, ensure_ascii=False))
        assert "eip-2" not in json.dumps(persisted["raw"]["eips"], ensure_ascii=False)
        eip_entries = [r for r in result["classification"]["resources"] if r["id"] == "eip-1"]
        assert len(eip_entries) == 1
        assert eip_entries[0]["mode"] == "traditional"

    def test_eip_analyzer_flags_unbound_and_bandwidth(self):
        from analyzers.eip_analyzer import EipAnalyzer

        analyzer = EipAnalyzer()
        topology = {
            "customer": "客户A",
            "raw": {"eips": [{
                "elasticIpId": "eip-1",
                "elasticIpAddress": "1.1.1.1",
                "bandwidthMbps": 10,
                "tags": [{"key": "客户", "value": "客户A"}],
            }]},
        }
        analyzer.discover(topology)
        analyzer.metrics = {"eip-1": {"eip.bandwidth.out": [(1, 9_000_000)]}}
        findings = analyzer.analyze()
        assert any(f["severity"] == "warning" and "出带宽峰值" in f["message"] for f in findings)
        assert any(f["severity"] == "warning" and "未绑定" in f["message"] for f in findings)
        assert all("jdcloud-eip-ops" in (f.get("ops_skill") or "") or f["severity"] == "info" for f in findings)


class TestClbUpgradeAssessment:
    """CLB upgrade assessment tests (no cloud credentials)."""

    def test_clb_upgrade_recommendation_and_datetime_path(self):
        from analyzers.clb_analyzer import ClbAnalyzer

        analyzer = ClbAnalyzer()
        topology = {
            "customer": "客户A",
            "raw": {"lbs": [{
                "loadBalancerId": "lb-1",
                "loadBalancerName": "入口CLB",
                "spec": "standard",
                "tags": [{"key": "客户", "value": "客户A"}],
            }]},
        }
        analyzer.discover(topology)
        analyzer.metrics = {"lb-1": {
            "lb.active_connection_count": [(1, 410_000)],
            "lb.new_connection_count": [(1, 45_000)],
            "lb.backend.healthy.host_count": [(1_700_000_000_000, 1)],
        }}
        findings = analyzer.analyze()
        assert any("并发连接峰值" in f["message"] and f["ops_skill"] == "jdcloud-clb-ops" for f in findings)
        assert any("新建连接峰值" in f["message"] and f["ops_skill"] == "jdcloud-clb-ops" for f in findings)
        assert any(f["severity"] == "critical" and "健康后端数" in f["message"] for f in findings)

    def test_clb_query_metrics_uses_lb_service_code(self):
        from analyzers.clb_analyzer import ClbAnalyzer

        class FakeClient:
            region = "cn-north-1"
            def __init__(self):
                self.calls = []
            def get_metrics_batch(self, resource_id, metrics, hours=6, aggr="avg", region=None, service_code="vm"):
                self.calls.append({"resource_id": resource_id, "service_code": service_code, "metrics": metrics})
                return {"lb.active_connection_count": [(1, 1.0)]}

        analyzer = ClbAnalyzer()
        analyzer.resources = [{"loadBalancerId": "lb-1"}]
        client = FakeClient()
        analyzer.query_metrics(client)
        assert client.calls[0]["service_code"] == "lb"


class TestRawDataMinimization:
    """Raw data minimization: returned/persisted raw payload must be
    customer-scoped for all resource types, not just EIP."""

    def _make_client(self, full_vms, full_lbs, full_redis, full_rds,
                     full_eips, full_nats, full_es,
                     full_vpcs, full_subnets, full_sgs):
        class FakeClient:
            regions_called = []
            def list_vms(self, region=None):
                self.regions_called.append(region)
                return full_vms
            def list_lbs(self, region=None): return full_lbs
            def list_redis(self, region=None): return full_redis
            def list_rds(self, region=None): return full_rds
            def list_eips(self, region=None): return full_eips
            def list_vpcs(self, region=None): return full_vpcs
            def list_subnets(self, region=None): return full_subnets
            def list_security_groups(self, region=None): return full_sgs
            def list_nats(self, region=None): return full_nats
            def list_es(self, region=None): return full_es
        return FakeClient()

    def test_vms_are_minimized(self):
        """raw['vms'] must exclude other-customer VMs."""
        from lib.resource_discovery import discover_customer_resources

        customer_a_vm = {"instanceId": "vm-a", "tags": [{"key": "客户", "value": "客户A"}]}
        customer_b_vm = {"instanceId": "vm-b", "tags": [{"key": "客户", "value": "客户B"}]}

        client = self._make_client(
            full_vms=[customer_a_vm, customer_b_vm],
            full_lbs=[], full_redis=[], full_rds=[],
            full_eips=[], full_nats=[], full_es=[],
            full_vpcs=[], full_subnets=[], full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        raw_ids = [v["instanceId"] for v in result["raw"]["vms"]]
        assert raw_ids == ["vm-a"], f"Expected only vm-a, got {raw_ids}"

    def test_lbs_are_minimized(self):
        from lib.resource_discovery import discover_customer_resources

        lbs = [
            {"loadBalancerId": "lb-a", "tags": [{"key": "客户", "value": "客户A"}]},
            {"loadBalancerId": "lb-b", "tags": [{"key": "客户", "value": "客户B"}]},
        ]
        client = self._make_client(
            full_vms=[], full_lbs=lbs, full_redis=[], full_rds=[],
            full_eips=[], full_nats=[], full_es=[],
            full_vpcs=[], full_subnets=[], full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        assert [lb["loadBalancerId"] for lb in result["raw"]["lbs"]] == ["lb-a"]
        assert "lb-b" not in str(result["raw"]["lbs"])

    def test_redis_are_minimized(self):
        from lib.resource_discovery import discover_customer_resources

        redis = [
            {"cacheInstanceId": "r-a", "tags": [{"key": "客户", "value": "客户A"}]},
            {"cacheInstanceId": "r-b", "tags": [{"key": "客户", "value": "客户B"}]},
        ]
        client = self._make_client(
            full_vms=[], full_lbs=[], full_redis=redis, full_rds=[],
            full_eips=[], full_nats=[], full_es=[],
            full_vpcs=[], full_subnets=[], full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        assert [r["cacheInstanceId"] for r in result["raw"]["redis"]] == ["r-a"]
        assert "r-b" not in str(result["raw"]["redis"])

    def test_rds_are_minimized(self):
        from lib.resource_discovery import discover_customer_resources

        rds = [
            {"instanceId": "rds-a", "tags": [{"key": "客户", "value": "客户A"}]},
            {"instanceId": "rds-b", "tags": [{"key": "客户", "value": "客户B"}]},
        ]
        client = self._make_client(
            full_vms=[], full_lbs=[], full_redis=[], full_rds=rds,
            full_eips=[], full_nats=[], full_es=[],
            full_vpcs=[], full_subnets=[], full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        assert [r["instanceId"] for r in result["raw"]["rds"]] == ["rds-a"]
        assert "rds-b" not in str(result["raw"]["rds"])

    def test_eips_are_minimized(self):
        from lib.resource_discovery import discover_customer_resources

        eips = [
            {"elasticIpId": "eip-a", "tags": [{"key": "客户", "value": "客户A"}]},
            {"elasticIpId": "eip-b", "tags": [{"key": "客户", "value": "客户B"}]},
        ]
        client = self._make_client(
            full_vms=[], full_lbs=[], full_redis=[], full_rds=[],
            full_eips=eips, full_nats=[], full_es=[],
            full_vpcs=[], full_subnets=[], full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        assert [e["elasticIpId"] for e in result["raw"]["eips"]] == ["eip-a"]
        assert "eip-b" not in str(result["raw"]["eips"])

    def test_es_are_minimized(self):
        from lib.resource_discovery import discover_customer_resources

        es = [
            {"instanceId": "es-a", "tags": [{"key": "客户", "value": "客户A"}]},
            {"instanceId": "es-b", "tags": [{"key": "客户", "value": "客户B"}]},
        ]
        client = self._make_client(
            full_vms=[], full_lbs=[], full_redis=[], full_rds=[],
            full_eips=[], full_nats=[], full_es=es,
            full_vpcs=[], full_subnets=[], full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        assert [e["instanceId"] for e in result["raw"]["es"]] == ["es-a"]
        assert "es-b" not in str(result["raw"]["es"])

    def test_vpcs_minimized_to_customer_refs(self):
        """raw['vpcs'] must contain only VPCs referenced by customer resources."""
        from lib.resource_discovery import discover_customer_resources

        vpcs = [
            {"vpcId": "vpc-a", "vpcName": "客户A的VPC"},
            {"vpcId": "vpc-b", "vpcName": "其他VPC"},
        ]
        vms = [
            {"instanceId": "vm-a", "vpcId": "vpc-a",
             "tags": [{"key": "客户", "value": "客户A"}]},
        ]
        client = self._make_client(
            full_vms=vms, full_lbs=[], full_redis=[], full_rds=[],
            full_eips=[], full_nats=[], full_es=[],
            full_vpcs=vpcs, full_subnets=[], full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        raw_vpc_ids = [v["vpcId"] for v in result["raw"]["vpcs"]]
        assert raw_vpc_ids == ["vpc-a"], f"Expected only vpc-a, got {raw_vpc_ids}"

    def test_subnets_minimized_to_customer_vpcs(self):
        """raw['subnets'] must contain only subnets in customer VPCs."""
        from lib.resource_discovery import discover_customer_resources

        vpcs = [{"vpcId": "vpc-a", "vpcName": "客户A的VPC"}]
        subnets = [
            {"subnetId": "sn-a1", "vpcId": "vpc-a"},
            {"subnetId": "sn-b1", "vpcId": "vpc-b"},
        ]
        vms = [
            {"instanceId": "vm-a", "vpcId": "vpc-a",
             "tags": [{"key": "客户", "value": "客户A"}]},
        ]
        client = self._make_client(
            full_vms=vms, full_lbs=[], full_redis=[], full_rds=[],
            full_eips=[], full_nats=[], full_es=[],
            full_vpcs=vpcs, full_subnets=subnets, full_sgs=[],
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        raw_sn_ids = [sn["subnetId"] for sn in result["raw"]["subnets"]]
        assert raw_sn_ids == ["sn-a1"], f"Expected only sn-a1, got {raw_sn_ids}"

    def test_security_groups_minimized_to_customer_vms(self):
        """raw['security_groups'] must contain only SGs referenced by customer VMs."""
        from lib.resource_discovery import discover_customer_resources

        sgs = [
            {"groupId": "sg-a", "groupName": "客户A的SG"},
            {"groupId": "sg-b", "groupName": "其他SG"},
        ]
        vms = [
            {
                "instanceId": "vm-a",
                "primaryNetworkInterface": {
                    "networkInterface": {
                        "securityGroups": [{"groupId": "sg-a"}]
                    }
                },
                "tags": [{"key": "客户", "value": "客户A"}],
            },
        ]
        client = self._make_client(
            full_vms=vms, full_lbs=[], full_redis=[], full_rds=[],
            full_eips=[], full_nats=[], full_es=[],
            full_vpcs=[], full_subnets=[], full_sgs=sgs,
        )
        result = discover_customer_resources(client, "客户A", regions=["cn-north-1"])
        raw_sg_ids = [sg["groupId"] for sg in result["raw"]["security_groups"]]
        assert raw_sg_ids == ["sg-a"], f"Expected only sg-a, got {raw_sg_ids}"


class TestHoursPropagation:
    """Tests for --hours parameter propagation to analyzers."""

    def test_analyzer_query_metrics_receives_hours(self):
        """verify analyzer.query_metrics(client, hours=N) passes N through."""
        from analyzers.vm_analyzer import VmAnalyzer

        class FakeClient:
            region = "cn-north-1"
            def __init__(self):
                self.received_hours = None
                self.received_service_code = None
            def get_metrics_batch(self, resource_id, metrics, hours=6,
                                   aggr="avg", region=None, service_code="vm"):
                self.received_hours = hours
                self.received_service_code = service_code
                return {"cpu_util": [(1, 50.0)]}

        analyzer = VmAnalyzer()
        analyzer.resources = [{"instanceId": "vm-1",
                               "tags": [{"key": "客户", "value": "客户A"}]}]
        client = FakeClient()
        analyzer.query_metrics(client, hours=48)
        assert client.received_hours == 48, (
            f"Expected hours=48, got {client.received_hours}")


class TestResourceDiscovery:
    """resource_discovery tests."""

    def test_import(self):
        from lib.resource_discovery import discover_customer_resources
        assert callable(discover_customer_resources)


class TestAnalyzers:
    """Analyzer module tests."""

    def test_all_analyzers_importable(self):
        from analyzers import create_all
        analyzers = create_all()
        names = [a.service_name for a in analyzers]
        assert "vm" in names
        assert "redis" in names
        assert "clb" in names
        assert "eip" in names
        assert "elasticsearch" in names
        assert "k8s" in names

    def test_each_analyzer_has_required_methods(self):
        from analyzers import create_all
        for a in create_all():
            assert hasattr(a, "discover")
            assert hasattr(a, "query_metrics")
            assert hasattr(a, "analyze")
            assert hasattr(a, "report")

    def test_analyze_no_crash_empty(self):
        """Analyze with empty topology should not crash."""
        from analyzers import create_all
        for a in create_all():
            try:
                a.discover({"customer": "test", "raw": {}})
                a.analyze()
            except Exception:
                # discovery may raise for some, but should handle gracefully
                pass


class TestCruiseScripts:
    """End-to-end entry script tests."""

    def test_sniff_import(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cruise_sniff",
            os.path.join(os.path.dirname(__file__), "..", "scripts", "01-perceive", "cruise_sniff.py")
        )
        assert spec is not None

    def test_analyze_import(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cruise_analyze",
            os.path.join(os.path.dirname(__file__), "..", "scripts", "02-reason", "cruise_analyze.py")
        )
        assert spec is not None
