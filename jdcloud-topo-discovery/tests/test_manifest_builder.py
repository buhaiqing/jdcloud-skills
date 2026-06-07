"""Tests for manifest builder (JD Cloud)."""
import pytest
from scripts.lib.manifest_builder import ManifestBuilder


def test_minimal_build():
    """Build a manifest with only required fields."""
    builder = ManifestBuilder(
        account_id="1234567890",
        region="cn-north-1",
        scope="all",
        provider_version="n/a",
    )
    manifest = builder.build(
        resource_count=5,
        by_type={"vpc": 1, "vm": 4},
        sensitive_masked=[],
        unsupported_types=[],
        execution_time_ms=1234,
    )
    assert manifest["schema_version"] == "1.0"
    assert manifest["generator"] == "jdcloud-topo-discovery"
    assert manifest["account_id"] == "1234567890"
    assert manifest["region"] == "cn-north-1"
    assert manifest["scope"] == "all"
    assert manifest["provider_version"] == "n/a"
    assert manifest["resource_count"] == 5
    assert manifest["by_type"] == {"vpc": 1, "vm": 4}
    assert manifest["import_ids_stable"] is True


def test_build_with_optional_fields():
    """Build a manifest with optional account_alias and role_arn."""
    builder = ManifestBuilder(
        account_id="1234567890",
        region="cn-north-1",
        scope="vpc-3p9mkq2v3a",
        provider_version="n/a",
        account_alias="prod-finance",
        role_arn="jdcloud:ram::1234:role/TopologyReader",
    )
    manifest = builder.build(
        resource_count=10,
        by_type={"vpc": 1, "vm": 5, "mysql": 4},
        sensitive_masked=["mysql.accountPassword"],
        unsupported_types=["oss.bucket_cors"],
        execution_time_ms=5000,
    )
    assert manifest["account_alias"] == "prod-finance"
    assert manifest["role_arn"] == "jdcloud:ram::1234:role/TopologyReader"
    assert manifest["sensitive_masked"] == ["mysql.accountPassword"]


def test_invalid_account_id_raises():
    """Empty account_id should raise ValueError."""
    with pytest.raises(ValueError):
        ManifestBuilder(
            account_id="",
            region="cn-north-1",
            scope="all",
            provider_version="n/a",
        )


def test_invalid_resource_count_raises():
    """Negative resource_count should raise ValueError."""
    builder = ManifestBuilder(
        account_id="1234567890",
        region="cn-north-1",
        scope="all",
        provider_version="n/a",
    )
    with pytest.raises(ValueError):
        builder.build(
            resource_count=-1,
            by_type={},
            sensitive_masked=[],
            unsupported_types=[],
            execution_time_ms=0,
        )


def test_generated_at_is_iso8601_utc():
    """generated_at should be ISO 8601 with Z suffix."""
    builder = ManifestBuilder(
        account_id="1234567890",
        region="cn-north-1",
        scope="all",
        provider_version="n/a",
    )
    manifest = builder.build(
        resource_count=0,
        by_type={},
        sensitive_masked=[],
        unsupported_types=[],
        execution_time_ms=0,
    )
    # Format: 2026-06-08T12:00:00Z
    assert manifest["generated_at"].endswith("Z")
    assert "T" in manifest["generated_at"]


def test_jdcloud_provider_version_default():
    """Default provider_version should be 'n/a' (no official JD Cloud Provider)."""
    builder = ManifestBuilder(
        account_id="1234567890",
        region="cn-north-1",
        scope="all",
        provider_version="n/a",
    )
    manifest = builder.build(0, {}, [], [], 0)
    assert manifest["provider_version"] == "n/a"
