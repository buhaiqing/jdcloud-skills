"""Tests for the MAPPINGS registry and individual resource type mappings (JD Cloud)."""
import pytest
from scripts.lib.mappings import MAPPINGS
from scripts.lib.field_mapper import FieldMapper


def test_all_resource_types_have_terraform_type():
    """Every MappingSpec must have a terraform_type (placeholder for JD Cloud)."""
    for rt, spec in MAPPINGS.items():
        assert spec.terraform_type, f"{rt} missing terraform_type"
        # All JD Cloud placeholder types should be prefixed with jdcloud_
        assert spec.terraform_type.startswith("jdcloud_"), (
            f"{rt}: {spec.terraform_type} should start with 'jdcloud_'"
        )


def test_all_mappings_have_at_least_one_rule():
    """Every MappingSpec must have at least one mapping rule."""
    for rt, spec in MAPPINGS.items():
        assert len(spec.rules) > 0, f"{rt} has no mapping rules"


def test_vpc_fixture_can_be_mapped(load_fixture):
    """VPC fixture should map to HCL without errors."""
    data = load_fixture("vpc")
    spec = MAPPINGS["vpc"]
    block_name = FieldMapper.generate_block_name(spec.terraform_type, data, spec)
    hcl = FieldMapper().map_resource("vpc", data, spec, block_name)
    assert "resource \"jdcloud_vpc\"" in hcl


def test_subnet_fixture_can_be_mapped(load_fixture):
    """Subnet fixture should map to HCL with parent_ref to VPC."""
    data = load_fixture("subnet")
    spec = MAPPINGS["subnet"]
    assert spec.parent_ref == "vpcId", "Subnet should declare vpcId as parent"
    block_name = FieldMapper.generate_block_name(spec.terraform_type, data, spec)
    hcl = FieldMapper().map_resource("subnet", data, spec, block_name)
    assert "resource \"jdcloud_subnet\"" in hcl


def test_vm_fixture_can_be_mapped(load_fixture):
    """VM fixture should map to HCL with parent_ref to Subnet."""
    data = load_fixture("vm")
    spec = MAPPINGS["vm"]
    assert spec.parent_ref == "subnetId", "VM should declare subnetId as parent"
    hcl = FieldMapper().map_resource("vm", data, spec, "vm1")
    assert "resource \"jdcloud_instance\"" in hcl


def test_mysql_fixture_can_be_mapped(load_fixture):
    """MySQL fixture should map to HCL with parent_ref to Subnet."""
    data = load_fixture("mysql")
    spec = MAPPINGS["mysql"]
    assert spec.parent_ref == "subnetId"
    hcl = FieldMapper().map_resource("mysql", data, spec, "db1")
    assert "resource \"jdcloud_rds_instance\"" in hcl
    # Sensitive accountPassword should be in rules but masked
    has_sensitive = any(r.sensitive for r in spec.rules)
    assert has_sensitive, "MySQL mapping should have a sensitive accountPassword rule"


def test_redis_fixture_can_be_mapped(load_fixture):
    """Redis fixture should map to HCL."""
    data = load_fixture("redis")
    spec = MAPPINGS["redis"]
    hcl = FieldMapper().map_resource("redis", data, spec, "redis1")
    assert "resource \"jdcloud_cache_instance\"" in hcl


def test_clb_fixture_can_be_mapped(load_fixture):
    """CLB fixture should map to HCL."""
    data = load_fixture("clb")
    spec = MAPPINGS["clb"]
    hcl = FieldMapper().map_resource("clb", data, spec, "lb1")
    assert "resource \"jdcloud_lb\"" in hcl


def test_eip_fixture_can_be_mapped(load_fixture):
    """EIP fixture should map to HCL."""
    data = load_fixture("eip")
    spec = MAPPINGS["eip"]
    hcl = FieldMapper().map_resource("eip", data, spec, "eip1")
    assert "resource \"jdcloud_eip\"" in hcl


def test_sg_fixture_can_be_mapped(load_fixture):
    """SecurityGroup fixture should map to HCL."""
    data = load_fixture("sg")
    spec = MAPPINGS["sg"]
    hcl = FieldMapper().map_resource("sg", data, spec, "sg1")
    assert "resource \"jdcloud_security_group\"" in hcl


def test_kms_fixture_can_be_mapped(load_fixture):
    """KMS fixture should map to HCL."""
    data = load_fixture("kms")
    spec = MAPPINGS["kms"]
    hcl = FieldMapper().map_resource("kms", data, spec, "k1")
    assert "resource \"jdcloud_kms_key\"" in hcl


def test_iam_fixture_can_be_mapped(load_fixture):
    """IAM fixture should map to HCL."""
    data = load_fixture("iam")
    spec = MAPPINGS["iam"]
    hcl = FieldMapper().map_resource("iam", data, spec, "user1")
    assert "resource \"jdcloud_iam_sub_user\"" in hcl


def test_minimum_resource_types_phase1():
    """Phase 1 must cover at least the top 9 resource types."""
    required = ["vpc", "subnet", "vm", "mysql", "redis", "clb", "eip", "sg", "kms"]
    for rt in required:
        assert rt in MAPPINGS, f"Phase 1 missing resource type: {rt}"


def test_jdcloud_no_official_provider_note():
    """All terraform_types should be placeholders, signaling no official provider.

    This test serves as a documentation check: if any future change makes
    these real types, this test should be updated and a real provider noted.
    """
    for rt, spec in MAPPINGS.items():
        # The naming pattern (e.g. jdcloud_vpc) signals "placeholder"
        # If a real provider is released, this assertion would need to be revisited
        assert spec.terraform_type.startswith("jdcloud_"), (
            f"{rt}: terraform_type should be jdcloud_-prefixed placeholder"
        )
