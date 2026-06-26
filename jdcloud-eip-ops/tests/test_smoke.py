"""Smoke tests for jdcloud-eip-ops: verify fixtures and basic setup."""
from pathlib import Path


def test_pytest_works():
    assert 1 + 1 == 2


def test_fixtures_dir_exists(fixtures_dir):
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


def test_all_fixtures_exist(fixtures_dir):
    expected = ["eip", "eip-associated"]
    for name in expected:
        path = fixtures_dir / f"{name}.json"
        assert path.exists(), f"Missing fixture: {name}.json"


def test_eip_fixture_content(load_fixture):
    data = load_fixture("eip")
    assert data["allocationId"] == "eip-test-001"
    assert data["status"] == "available"
    assert data["bandwidthMbps"] == 10
    assert data["instanceId"] is None


def test_eip_associated_fixture_content(load_fixture):
    data = load_fixture("eip-associated")
    assert data["allocationId"] == "eip-test-002"
    assert data["instanceType"] == "nat"
    assert data["instanceId"] == "nat-test-001"


def test_rubric_has_five_dimensions(rubric_template):
    assert len(rubric_template["dimensions"]) == 5
    assert "safety" in rubric_template["dimensions"]
    assert rubric_template["safety_abort_on_zero"]


def test_rubric_max_iterations(rubric_template):
    assert rubric_template["max_iterations"] == 2


def test_skill_metadata_required_fields():
    """Verify SKILL.md frontmatter has required fields."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    assert "name: jdcloud-eip-ops" in content or "name: jdcloud-eip-ops" in content
    assert "cli_applicability:" in content
    assert "gcl_max_iter" in content


def test_eip_address_valid_format(load_fixture):
    """EIP address fixture should be a valid IPv4 string."""
    data = load_fixture("eip")
    parts = data["eipAddress"].split(".")
    assert len(parts) == 4
    for part in parts:
        assert 0 <= int(part) <= 255


def test_bandwidth_positive(load_fixture):
    """Bandwidth must be positive integer."""
    data = load_fixture("eip")
    assert data["bandwidthMbps"] > 0
    assert isinstance(data["bandwidthMbps"], int)
