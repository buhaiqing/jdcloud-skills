"""Tests for manifest validator (JD Cloud)."""
import pytest
from scripts.lib.manifest_builder import ManifestBuilder
from scripts.lib.manifest_validator import ManifestValidator, ManifestValidationError


@pytest.fixture
def validator():
    return ManifestValidator()


def _build_valid_manifest():
    builder = ManifestBuilder(
        account_id="1234567890",
        region="cn-north-1",
        scope="all",
        provider_version="n/a",
    )
    return builder.build(
        resource_count=5,
        by_type={"vpc": 1, "vm": 4},
        sensitive_masked=[],
        unsupported_types=[],
        execution_time_ms=1234,
    )


def test_valid_manifest_passes(validator):
    """A well-formed manifest should pass validation."""
    manifest = _build_valid_manifest()
    validator.validate(manifest)  # should not raise


def test_missing_required_field_fails(validator):
    """A manifest missing 'generator' should fail validation."""
    manifest = _build_valid_manifest()
    del manifest["generator"]
    with pytest.raises(ManifestValidationError) as exc_info:
        validator.validate(manifest)
    assert "generator" in str(exc_info.value) or "required" in str(exc_info.value).lower()


def test_invalid_generator_constant_fails(validator):
    """generator must be exactly 'jdcloud-topo-discovery'."""
    manifest = _build_valid_manifest()
    manifest["generator"] = "alicloud-topo-discovery"  # wrong generator
    with pytest.raises(ManifestValidationError):
        validator.validate(manifest)


def test_invalid_provider_version_fails(validator):
    """provider_version must match semver OR 'n/a'."""
    manifest = _build_valid_manifest()
    manifest["provider_version"] = "totally-bogus"
    with pytest.raises(ManifestValidationError):
        validator.validate(manifest)


def test_na_provider_version_passes(validator):
    """provider_version='n/a' should be accepted (JD Cloud has no official Provider)."""
    manifest = _build_valid_manifest()
    manifest["provider_version"] = "n/a"
    validator.validate(manifest)


def test_semver_provider_version_passes(validator):
    """A valid semver string should be accepted (future 3rd-party provider)."""
    manifest = _build_valid_manifest()
    manifest["provider_version"] = "1.0.0"
    validator.validate(manifest)


def test_additional_property_fails(validator):
    """Manifest with extra keys should fail (additionalProperties: false)."""
    manifest = _build_valid_manifest()
    manifest["extra_field"] = "should not be here"
    with pytest.raises(ManifestValidationError):
        validator.validate(manifest)


def test_role_arn_format_validated(validator):
    """role_arn must match jdcloud:ram::<digits>:role/.* pattern."""
    manifest = _build_valid_manifest()
    manifest["role_arn"] = "arn:acs:ram::1234:role/Topo"  # alicloud format - invalid
    with pytest.raises(ManifestValidationError):
        validator.validate(manifest)

    manifest["role_arn"] = "jdcloud:ram::1234:role/Topo"  # correct format
    validator.validate(manifest)
