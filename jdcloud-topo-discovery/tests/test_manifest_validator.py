"""Tests for manifest validator (JD Cloud)."""

import pytest
from scripts.lib.manifest_builder import ManifestBuilder, ManifestValidationError, validate_manifest


def _build_valid():
    builder = ManifestBuilder(
        account_id="1234567890", region="cn-north-1", scope="all", provider_version="n/a"
    )
    return builder.build(
        resource_count=5,
        by_type={"vpc": 1, "vm": 4},
        sensitive_masked=[],
        unsupported_types=[],
        execution_time_ms=1234,
    )


def test_valid_manifest_passes():
    validate_manifest(_build_valid())


def test_missing_required_field_fails():
    m = _build_valid()
    del m["generator"]
    with pytest.raises(ManifestValidationError):
        validate_manifest(m)


def test_invalid_generator_constant_fails():
    m = _build_valid()
    m["generator"] = "alicloud-topo-discovery"
    with pytest.raises(ManifestValidationError):
        validate_manifest(m)


def test_invalid_provider_version_fails():
    m = _build_valid()
    m["provider_version"] = "totally-bogus"
    with pytest.raises(ManifestValidationError):
        validate_manifest(m)


def test_na_provider_version_passes():
    m = _build_valid()
    m["provider_version"] = "n/a"
    validate_manifest(m)


def test_semver_provider_version_passes():
    m = _build_valid()
    m["provider_version"] = "1.0.0"
    validate_manifest(m)


def test_additional_property_fails():
    m = _build_valid()
    m["extra_field"] = "should not be here"
    with pytest.raises(ManifestValidationError):
        validate_manifest(m)


def test_role_arn_format_validated():
    m = _build_valid()
    m["role_arn"] = "arn:acs:ram::1234:role/Topo"
    with pytest.raises(ManifestValidationError):
        validate_manifest(m)
    m["role_arn"] = "jdcloud:ram::1234:role/Topo"
    validate_manifest(m)
