"""Smoke tests for jdcloud-oss-ops: verify fixtures and basic setup."""
from pathlib import Path


def test_pytest_works():
    assert 1 + 1 == 2


def test_fixtures_dir_exists(fixtures_dir):
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


def test_all_fixtures_exist(fixtures_dir):
    expected = ["bucket", "lifecycle"]
    for name in expected:
        path = fixtures_dir / f"{name}.json"
        assert path.exists(), f"Missing fixture: {name}.json"


def test_bucket_fixture_content(load_fixture):
    data = load_fixture("bucket")
    assert data["bucketName"] == "oss-test-bucket-001"
    assert data["regionId"] == "cn-north-1"
    assert data["bucketAcl"] == "private"
    assert data["storageClass"] == "Standard"


def test_lifecycle_fixture_content(load_fixture):
    data = load_fixture("lifecycle")
    assert len(data["rules"]) == 1
    rule = data["rules"][0]
    assert rule["id"] == "archive-old-logs"
    assert rule["status"] == "Enabled"
    assert rule["filter"]["prefix"] == "logs/"
    assert len(rule["transitions"]) == 2
    assert rule["transitions"][0]["storageClass"] == "InfrequentAccess"
    assert rule["transitions"][0]["days"] == 30
    assert rule["transitions"][1]["storageClass"] == "Archive"
    assert rule["transitions"][1]["days"] == 180
    assert rule["expiration"]["days"] == 365


def test_rubric_has_five_dimensions(rubric_template):
    assert len(rubric_template["dimensions"]) == 5
    assert "safety" in rubric_template["dimensions"]
    assert rubric_template["safety_abort_on_zero"]


def test_rubric_max_iterations(rubric_template):
    assert rubric_template["max_iterations"] == 3


def test_skilL_metadata_required_fields():
    """Verify SKILL.md frontmatter has required fields."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    assert "name: jdcloud-oss-ops" in content
    assert "cli_applicability: " in content
    assert "gcl_classification: " in content
    assert "gcl_max_iter: " in content


def test_cli_applicability_is_sdk_only():
    """Verify OSS is SDK-only (no jdc CLI)."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    assert "cli_applicability: sdk-only" in content


def test_bucket_name_validation():
    """Test bucket name validation rules match core-concepts.md."""
    valid_names = [
        "my-bucket-001",
        "test-bucket-cn-north-1",
        "a" * 63,
        "abc-123-def",
    ]
    invalid_names = [
        "",
        "a" * 64,
        "UPPERCASE",
        "bucket_name",
        "bucket.name",
        "192.168.0.1",
        "-starts-with-hyphen",
        "ends-with-hyphen-",
        "a",
        "ab",
    ]

    import re
    bucket_name_pattern = re.compile(r'^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$')

    def is_ip_format(name: str) -> bool:
        parts = name.split(".")
        if len(parts) != 4:
            return False
        return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)

    def _valid_bucket_name(name: str) -> bool:
        if len(name) < 3 or len(name) > 63:
            return False
        if not bucket_name_pattern.match(name):
            return False
        if is_ip_format(name):
            return False
        return True

    for name in valid_names:
        assert _valid_bucket_name(name), f"Valid name rejected: {name}"
    for name in invalid_names:
        assert not _valid_bucket_name(name), f"Invalid name passed: {name}"