"""Tests for field mapper (JD Cloud)."""
import pytest
from scripts.lib.field_mapper import FieldMapper, MappingSpec, MappingRule


def test_simple_vpc_mapping(load_fixture):
    """Map a VPC fixture to HCL."""
    data = load_fixture("vpc")
    spec = MappingSpec(
        resource_type="vpc",
        terraform_type="jdcloud_vpc",
        rules=[
            MappingRule(hcl_attr="vpc_name", path="vpcName"),
            MappingRule(hcl_attr="cidr_block", path="addressPrefix"),
            MappingRule(hcl_attr="description", path="description", required=False),
        ],
    )
    block_name = FieldMapper.generate_block_name(spec.terraform_type, data, spec)
    hcl = FieldMapper().map_resource("vpc", data, spec, block_name)

    assert 'resource "jdcloud_vpc"' in hcl
    assert "prod_vpc_beijing" in hcl
    assert 'vpc_name = "prod-vpc-beijing"' in hcl
    assert 'cidr_block = "10.0.0.0/16"' in hcl
    assert 'description = "Production VPC in cn-north-1"' in hcl


def test_missing_required_field_is_skipped(load_fixture):
    """Missing required field should be silently skipped (caller reviews)."""
    data = {"vpcName": "test"}  # missing addressPrefix
    spec = MappingSpec(
        resource_type="vpc",
        terraform_type="jdcloud_vpc",
        rules=[
            MappingRule(hcl_attr="vpc_name", path="vpcName"),
            MappingRule(hcl_attr="cidr_block", path="addressPrefix"),  # required but missing
        ],
    )
    hcl = FieldMapper().map_resource("vpc", data, spec, "test")
    assert 'vpc_name = "test"' in hcl
    assert "cidr_block" not in hcl


def test_optional_field_omitted_when_absent(load_fixture):
    """Optional field should be omitted from HCL when absent."""
    data = {"vpcName": "test", "addressPrefix": "10.0.0.0/16"}  # no description
    spec = MappingSpec(
        resource_type="vpc",
        terraform_type="jdcloud_vpc",
        rules=[
            MappingRule(hcl_attr="vpc_name", path="vpcName"),
            MappingRule(hcl_attr="cidr_block", path="addressPrefix"),
            MappingRule(hcl_attr="description", path="description", required=False),
        ],
    )
    hcl = FieldMapper().map_resource("vpc", data, spec, "test")
    assert "description" not in hcl


def test_int_type_coercion():
    """Integer values should be formatted as HCL numbers (no quotes)."""
    data = {"bandwidthMbps": 100}
    spec = MappingSpec(
        resource_type="eip",
        terraform_type="jdcloud_eip",
        rules=[
            MappingRule(hcl_attr="bandwidth_mbps", path="bandwidthMbps", type="int"),
        ],
    )
    hcl = FieldMapper().map_resource("eip", data, spec, "eip1")
    assert 'bandwidth_mbps = 100' in hcl
    assert 'bandwidth_mbps = "100"' not in hcl


def test_bool_type_coercion():
    """Boolean values should be formatted as true/false."""
    data = {"rotationEnabled": True}
    spec = MappingSpec(
        resource_type="kms",
        terraform_type="jdcloud_kms_key",
        rules=[
            MappingRule(hcl_attr="rotation_enabled", path="rotationEnabled", type="bool"),
        ],
    )
    hcl = FieldMapper().map_resource("kms", data, spec, "k1")
    assert "rotation_enabled = true" in hcl


def test_list_type_coercion(load_fixture):
    """List values should be formatted as HCL array literals."""
    data = {"securityGroupIds": ["sg-001", "sg-002"]}
    spec = MappingSpec(
        resource_type="vm",
        terraform_type="jdcloud_instance",
        rules=[
            MappingRule(hcl_attr="security_group_ids", path="securityGroupIds", type="list"),
        ],
    )
    hcl = FieldMapper().map_resource("vm", data, spec, "vm1")
    assert 'security_group_ids = ["sg-001", "sg-002"]' in hcl


def test_sensitive_field_masking():
    """Sensitive fields should be masked and marked with sensitive=true."""
    data = {"accountPassword": "supersecret123"}
    spec = MappingSpec(
        resource_type="mysql",
        terraform_type="jdcloud_rds_instance",
        rules=[
            MappingRule(hcl_attr="account_password", path="accountPassword", sensitive=True),
        ],
    )
    hcl = FieldMapper().map_resource("mysql", data, spec, "db1")
    assert "supersecret123" not in hcl
    assert "${var.mysql_password}" in hcl
    assert "sensitive = true" in hcl


def test_block_name_from_vpc_name(load_fixture):
    """Block name should be derived from vpcName."""
    data = load_fixture("vpc")
    spec = MappingSpec("vpc", "jdcloud_vpc", rules=[])
    name = FieldMapper.generate_block_name(spec.terraform_type, data, spec)
    assert name == "prod_vpc_beijing"


def test_block_name_fallback_to_id():
    """Block name should fall back to ID when name is missing."""
    data = {"vpcId": "vpc-3p9mkq2v3a"}  # no vpcName
    spec = MappingSpec("vpc", "jdcloud_vpc", rules=[])
    name = FieldMapper.generate_block_name(spec.terraform_type, data, spec)
    assert "vpc" in name.lower()


def test_block_name_with_special_chars():
    """Special chars in names should be slugified to underscores."""
    data = {"vpcName": "Prod-VPC.Beijing!@#"}
    spec = MappingSpec("vpc", "jdcloud_vpc", rules=[])
    name = FieldMapper.generate_block_name(spec.terraform_type, data, spec)
    # All non-alphanumerics should be underscores
    assert all(c.isalnum() or c == "_" for c in name)
    assert name.islower()
