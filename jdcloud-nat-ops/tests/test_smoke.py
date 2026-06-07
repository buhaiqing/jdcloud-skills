"""Smoke tests for jdcloud-nat-ops: verify fixtures and basic setup."""
from pathlib import Path


def test_pytest_works():
    assert 1 + 1 == 2


def test_fixtures_dir_exists(fixtures_dir):
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


def test_all_fixtures_exist(fixtures_dir):
    expected = ["nat-gateway", "snat-rule"]
    for name in expected:
        path = fixtures_dir / f"{name}.json"
        assert path.exists(), f"Missing fixture: {name}.json"


def test_nat_gateway_fixture_content(load_fixture):
    data = load_fixture("nat-gateway")
    assert data["natGatewayId"] == "nat-test-001"
    assert data["natGatewayName"] == "test-nat-gateway"
    assert data["vpcId"] == "vpc-test-001"
    assert data["state"] == "available"


def test_snat_rule_fixture_content(load_fixture):
    data = load_fixture("snat-rule")
    assert data["snatRuleId"] == "snat-test-001"
    assert data["natGatewayId"] == "nat-test-001"
    assert data["subnetId"] == "subnet-test-001"
    assert len(data["elasticIpIds"]) >= 1


def test_rubric_has_five_dimensions(rubric_template):
    assert len(rubric_template["dimensions"]) == 5
    assert "safety" in rubric_template["dimensions"]
    assert rubric_template["safety_abort_on_zero"]


def test_rubric_max_iterations(rubric_template):
    assert rubric_template["max_iterations"] == 2


def test_skilL_metadata_required_fields():
    """Verify SKILL.md frontmatter has required fields."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    assert "name: jdcloud-nat-ops" in content
    assert "cli_applicability: jdc-first-with-fallback" in content
    assert "gcl_classification: required" in content
    assert "gcl_max_iter: 2" in content


def test_description_present(load_fixture):
    """NAT gateway fixture should have a description field."""
    data = load_fixture("nat-gateway")
    assert "description" in data


def test_eips_present(load_fixture):
    """NAT gateway fixture must have at least one Elastic IP."""
    data = load_fixture("nat-gateway")
    assert len(data["elasticIpAddresses"]) >= 1
    assert "eip" in data["elasticIpAddresses"][0]