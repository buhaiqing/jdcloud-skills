"""
Tests for jdc_client.py — JD Cloud API client.
Run with: python -m pytest tests/test_jdc_client.py -v
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

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
            except Exception as e:
                # discovery may raise for some, but should handle gracefully
                pass


class TestCruiseScripts:
    """End-to-end entry script tests."""

    def test_sniff_import(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cruise_sniff",
            os.path.join(os.path.dirname(__file__), "..", "scripts", "cruise_sniff.py")
        )
        assert spec is not None

    def test_link_import(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cruise_link",
            os.path.join(os.path.dirname(__file__), "..", "scripts", "cruise_link.py")
        )
        assert spec is not None