"""Smoke tests for jdcloud-vpc-ops: verify fixtures and basic setup."""
from pathlib import Path


def test_pytest_works():
    assert 1 + 1 == 2


def test_fixtures_dir_exists(fixtures_dir):
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


def test_all_fixtures_exist(fixtures_dir):
    expected = ["vpc", "subnet", "security-group", "security-group-rule"]
    for name in expected:
        path = fixtures_dir / f"{name}.json"
        assert path.exists(), f"Missing fixture: {name}.json"


def test_vpc_fixture_content(load_fixture):
    data = load_fixture("vpc")
    assert data["vpcId"] == "vpc-test-001"
    assert data["vpcName"] == "test-vpc"
    assert data["addressPrefix"] == "10.0.0.0/16"


def test_subnet_fixture_content(load_fixture):
    data = load_fixture("subnet")
    assert data["subnetId"] == "subnet-test-001"
    assert data["vpcId"] == "vpc-test-001"
    assert data["addressPrefix"] == "10.0.1.0/24"
    assert data["az"] == "cn-north-1a"


def test_security_group_fixture_content(load_fixture):
    data = load_fixture("security-group")
    assert data["networkSecurityGroupId"] == "sg-test-001"
    assert data["networkSecurityGroupName"] == "web-sg"
    assert data["vpcId"] == "vpc-test-001"


def test_security_group_rule_fixture_content(load_fixture):
    data = load_fixture("security-group-rule")
    assert data["protocol"] == 6
    assert data["direction"] == 0
    assert data["fromPort"] == 80
    assert data["toPort"] == 80
    assert data["addressPrefix"] == "0.0.0.0/0"


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
    assert "name: jdcloud-vpc-ops" in content
    assert "cli_applicability: " in content
    assert "gcl_classification: " in content
    assert "gcl_max_iter: " in content
