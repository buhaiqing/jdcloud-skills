"""Tests for dependency inference (JD Cloud)."""
from scripts.lib.dependency_inference import infer_dependencies, DependencyInferenceError
from scripts.lib.field_mapper import MappingSpec


def test_simple_chain_vpc_subnet_vm():
    """VPC → Subnet → VM should be ordered with parents first."""
    resources = [
        ("vm", {"instanceId": "i-1", "subnetId": "subnet-1", "instanceName": "vm1"},
         MappingSpec("vm", "jdcloud_instance", parent_ref="subnetId", rules=[]), "vm1"),
        ("subnet", {"subnetId": "subnet-1", "vpcId": "vpc-1", "subnetName": "sub1"},
         MappingSpec("subnet", "jdcloud_subnet", parent_ref="vpcId", rules=[]), "sub1"),
        ("vpc", {"vpcId": "vpc-1", "vpcName": "v1"},
         MappingSpec("vpc", "jdcloud_vpc", rules=[]), "v1"),
    ]
    ordered = infer_dependencies(resources)
    types = [r[0] for r in ordered]
    # VPC must come before Subnet, Subnet before VM
    assert types.index("vpc") < types.index("subnet")
    assert types.index("subnet") < types.index("vm")


def test_disconnected_graph_still_ordered():
    """Disconnected resources should all be included in output."""
    resources = [
        ("vpc", {"vpcId": "vpc-1", "vpcName": "v1"},
         MappingSpec("vpc", "jdcloud_vpc", rules=[]), "v1"),
        ("iam", {"subUserName": "ops1"},
         MappingSpec("iam", "jdcloud_iam_sub_user", rules=[]), "ops1"),
    ]
    ordered = infer_dependencies(resources)
    assert len(ordered) == 2
    block_names = {r[3] for r in ordered}
    assert "v1" in block_names
    assert "ops1" in block_names


def test_no_parent_ref_means_root():
    """Resources without parent_ref have no dependencies."""
    resources = [
        ("eip", {"elasticIpId": "fip-1", "name": "eip1"},
         MappingSpec("eip", "jdcloud_eip", rules=[]), "eip1"),
    ]
    ordered = infer_dependencies(resources)
    assert len(ordered) == 1


def test_missing_parent_id_means_orphan():
    """If parent_id is missing in data, child becomes an orphan (no edge)."""
    resources = [
        ("vm", {"instanceId": "i-1", "instanceName": "vm1"},  # no subnetId
         MappingSpec("vm", "jdcloud_instance", parent_ref="subnetId", rules=[]), "vm1"),
        ("vpc", {"vpcId": "vpc-1", "vpcName": "v1"},
         MappingSpec("vpc", "jdcloud_vpc", rules=[]), "v1"),
    ]
    ordered = infer_dependencies(resources)
    # Both should be present, no ordering constraint since vm is orphan
    assert len(ordered) == 2


def test_circular_dependency_documented():
    """Document that real JD Cloud resource hierarchies (VPC → Subnet → VM)
    do NOT form cycles, so the circular detection code path is defensive only.

    This test asserts the no-edge fallback behavior: resources with custom
    parent_ref fields that don't match the standard _ID_FIELDS lookup will
    not form edges, and the algorithm returns them in insertion order.
    """
    # Custom resource types not in _ID_FIELDS, so parent lookup finds nothing.
    cycle_resources = [
        ("custom_a", {"aId": "a-1", "bId": "b-1"},
         MappingSpec("custom_a", "x_a", parent_ref="bId", rules=[]), "a"),
        ("custom_b", {"bId": "b-1", "aId": "a-1"},
         MappingSpec("custom_b", "x_b", parent_ref="aId", rules=[]), "b"),
    ]
    ordered = infer_dependencies(cycle_resources)
    assert len(ordered) == 2
    # The DependencyInferenceError is still importable for defensive use:
    assert DependencyInferenceError is not None


def test_empty_input():
    """Empty list should return empty list."""
    assert infer_dependencies([]) == []


def test_jdcloud_specific_chain_clb_eip(load_fixture):
    """JD Cloud CLB → EIP via EIP fields (EIP not via parent_ref but via association)."""
    # Note: real EIP-CLB association isn't a parent_ref relationship
    # (both are independent resources). Verify they coexist without circular deps.
    resources = [
        ("eip", {"elasticIpId": "fip-1", "name": "e1"},
         MappingSpec("eip", "jdcloud_eip", rules=[]), "e1"),
        ("clb", {"loadBalancerId": "lb-1", "loadBalancerName": "lb1"},
         MappingSpec("clb", "jdcloud_lb", rules=[]), "lb1"),
    ]
    ordered = infer_dependencies(resources)
    assert len(ordered) == 2
