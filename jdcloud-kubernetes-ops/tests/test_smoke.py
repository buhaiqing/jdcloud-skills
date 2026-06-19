"""Smoke tests for jdcloud-kubernetes-ops: verify fixtures and basic setup."""
from pathlib import Path


def test_pytest_works():
    assert 1 + 1 == 2


def test_fixtures_dir_exists(fixtures_dir):
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


def test_all_fixtures_exist(fixtures_dir):
    expected = ["cluster", "node-group"]
    for name in expected:
        path = fixtures_dir / f"{name}.json"
        assert path.exists(), f"Missing fixture: {name}.json"


def test_cluster_fixture_content(load_fixture):
    data = load_fixture("cluster")
    assert data["clusterId"] == "c-test-001"
    assert data["clusterName"] == "test-k8s-cluster"
    assert data["state"] == "running"
    assert data["masterVersion"] == "1.28.3"


def test_cluster_fixture_has_node_groups(load_fixture):
    data = load_fixture("cluster")
    assert len(data["nodeGroups"]) == 1
    assert data["nodeGroups"][0]["nodeGroupId"] == "ng-test-001"


def test_node_group_fixture_content(load_fixture):
    data = load_fixture("node-group")
    assert data["nodeGroupId"] == "ng-test-001"
    assert data["name"] == "worker-pool"
    assert data["state"] == "running"
    assert data["instanceType"] == "g.n2.large"
    assert data["nodeCount"] == 3


def test_node_group_fixture_has_scale_range(load_fixture):
    data = load_fixture("node-group")
    assert data["minCount"] == 1
    assert data["maxCount"] == 10


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
    assert "name: jdcloud-kubernetes-ops" in content
    assert "cli_applicability: " in content
    assert "gcl_classification: " in content or "Quality Gate" in content


def test_references_dir_has_all_files():
    """Verify all expected reference files exist."""
    ref_dir = Path(__file__).parent.parent / "references"
    expected = [
        "core-concepts.md",
        "cli-usage.md",
        "api-sdk-usage.md",
        "integration.md",
        "monitoring.md",
        "troubleshooting.md",
        "rubric.md",
        "prompt-templates.md",
    ]
    for name in expected:
        path = ref_dir / name
        assert path.exists(), f"Missing reference: {name}"
        content = path.read_text()
        assert len(content) > 100, f"Reference file {name} is too short"


def test_assets_dir_has_config():
    """Verify assets directory has example-config.yaml."""
    assets_dir = Path(__file__).parent.parent / "assets"
    path = assets_dir / "example-config.yaml"
    assert path.exists()
    assert path.read_text().strip() != ""