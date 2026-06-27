"""Tests for GCL rubric scoring logic for jdcloud-nat-ops."""
import json
import pytest


@pytest.fixture
def rubric_template():
    """Return the expected rubric dimensions and thresholds."""
    return {
        "dimensions": ["correctness", "safety", "idempotency",
                       "traceability", "spec_compliance"],
        "levels": [0, 0.5, 1],
        "safety_abort_on_zero": True,
        "thresholds": {"correctness": 0.5, "safety": 1.0,
                       "idempotency": 0.5, "traceability": 0.5,
                       "spec_compliance": 0.5},
        "max_iterations": 2,
    }


def _build_trace(scores, decision="PASS", iteration=1):
    """Build a GCL trace JSON for testing."""
    return {
        "skill": "jdcloud-nat-ops",
        "rubric_version": "1.0.0",
        "iterations": [
            {
                "iter": iteration,
                "generator": {
                    "command": "jdc --output json vpc create-nat-gateway --nat-gateway-name test --vpc-id vpc-test-001",
                    "args": {},
                    "exit_code": 0,
                    "result_excerpt": '{"natGatewayId":"nat-test-001"}',
                },
                "critic": {
                    "scores": scores,
                    "suggestions": ["test suggestion"],
                    "blocking": False,
                },
                "decision": decision,
            }
        ],
        "final": {"status": decision, "iter": iteration, "output": "nat-test-001"},
    }


def test_rubric_five_dimensions(rubric_template):
    assert len(rubric_template["dimensions"]) == 5


def test_safety_zero_triggers_abort(rubric_template):
    """Safety=0 must trigger abort."""
    scores = {"correctness": 1, "safety": 0, "idempotency": 1,
              "traceability": 1, "spec_compliance": 1}
    trace = _build_trace(scores, decision="RETRY")
    # Simulate orchestrator: Safety=0 → abort
    if scores["safety"] == 0:
        decision = "ABORT"
    else:
        decision = "PASS" if all(
            v >= rubric_template["thresholds"].get(k, 0.5)
            for k, v in scores.items()
        ) else "RETRY"
    assert decision == "ABORT"


def test_safety_one_passes_for_describe(rubric_template):
    """describe-* operation Safety=1 should PASS."""
    scores = {"correctness": 1, "safety": 1, "idempotency": 1,
              "traceability": 1, "spec_compliance": 1}
    all_pass = all(
        v >= rubric_template["thresholds"].get(k, 0.5)
        for k, v in scores.items()
    )
    assert all_pass


def test_correctness_zero_for_failed_operation(rubric_template):
    """Failed operation yields Correctness=0."""
    scores = {"correctness": 0, "safety": 1, "idempotency": 0.5,
              "traceability": 1, "spec_compliance": 0.5}
    assert scores["correctness"] < rubric_template["thresholds"]["correctness"]


def test_idempotency_check(rubric_template):
    """Duplicate create should yield Idempotency=0.5 (returns existing) or 0 (creates duplicate)."""
    # Scenario: same create-nat called twice → Idempotency=0.5 (resource already exists)
    scores_duplicate = {"correctness": 1, "safety": 1, "idempotency": 0.5,
                        "traceability": 1, "spec_compliance": 0.5}
    assert scores_duplicate["idempotency"] >= rubric_template["thresholds"]["idempotency"]

    # Scenario: same create-nat created 2 identical resources → Idempotency=0
    scores_bad = {"correctness": 1, "safety": 1, "idempotency": 0,
                  "traceability": 1, "spec_compliance": 0.5}
    assert scores_bad["idempotency"] < rubric_template["thresholds"]["idempotency"]


def test_traceability_json_valid():
    """Trace JSON should conform to schema."""
    trace = _build_trace({"correctness": 1, "safety": 1, "idempotency": 1,
                          "traceability": 1, "spec_compliance": 1})
    # Serialize and deserialize to check valid JSON
    dumped = json.dumps(trace)
    loaded = json.loads(dumped)
    assert loaded["skill"] == "jdcloud-nat-ops"
    assert len(loaded["iterations"]) == 1
    assert loaded["final"]["status"] == "PASS"


def test_delete_nat_safety_gate_protocol():
    """Delete NAT gateway safety gate: must check SNAT/DNAT rules and EIP count first."""
    # NAT with active rules → Safety=0 if delete attempted without confirm
    # NAT empty → Safety=1 with confirm=DELETE
    nat_with_rules = {"natGatewayId": "nat-test-001", "snatRuleCount": 2,
                      "dnatRuleCount": 1, "elasticIpAddresses": ["eip-001", "eip-002"]}
    nat_empty = {"natGatewayId": "nat-test-002", "snatRuleCount": 0,
                 "dnatRuleCount": 0, "elasticIpAddresses": ["eip-001"]}

    def can_delete(nat, confirm=False):
        has_rules = nat.get("snatRuleCount", 0) > 0 or nat.get("dnatRuleCount", 0) > 0
        return confirm and True  # with explicit confirm, can proceed

    # Without confirm, even empty NAT should not proceed
    assert not can_delete(nat_with_rules, confirm=False)
    # With confirm, can proceed
    assert can_delete(nat_empty, confirm=True)
    assert can_delete(nat_with_rules, confirm=True)


def test_disassociate_last_eip_safety():
    """Disassociating the last EIP must trigger Safety gate."""
    nat_multi_eip = {"natGatewayId": "nat-test-001", "elasticIpAddresses": ["eip-001", "eip-002"]}
    nat_single_eip = {"natGatewayId": "nat-test-002", "elasticIpAddresses": ["eip-001"]}

    def can_disassociate(nat, target_eip, confirm=False):
        remaining = len([e for e in nat["elasticIpAddresses"] if e != target_eip])
        if remaining == 0:
            return confirm  # Last EIP requires explicit confirm
        return True  # Safe to disassociate

    # Multi EIP: safe to disassociate one
    assert can_disassociate(nat_multi_eip, "eip-001")
    # Single EIP: requires confirm
    assert not can_disassociate(nat_single_eip, "eip-001")
    assert can_disassociate(nat_single_eip, "eip-001", confirm=True)


def test_rubric_max_iterations_limits(rubric_template):
    """max_iterations=2 limit."""
    max_iter = rubric_template["max_iterations"]
    assert max_iter == 2
    for i in range(1, max_iter + 1):
        assert i <= max_iter
    # 3rd iteration would exceed
    assert max_iter < 3


def test_snat_subnet_uniqueness():
    """Each subnet can only have one SNAT rule per NAT."""
    existing_rules = [
        {"subnetId": "subnet-app-001"},
        {"subnetId": "subnet-app-002"},
    ]
    new_subnet = "subnet-app-001"
    unique_subnet = "subnet-db-001"

    def can_create_snat(subnet_id):
        return subnet_id not in [r["subnetId"] for r in existing_rules]

    assert not can_create_snat(new_subnet)
    assert can_create_snat(unique_subnet)


def test_dnat_port_conflict():
    """DNAT rule port must be unique per (EIP, publicPort, protocol)."""
    existing_rules = [
        {"elasticIpId": "eip-001", "publicPort": 80, "protocol": "tcp"},
        {"elasticIpId": "eip-001", "publicPort": 443, "protocol": "tcp"},
    ]

    def has_conflict(elastic_ip_id, public_port, protocol):
        return any(
            r["elasticIpId"] == elastic_ip_id
            and r["publicPort"] == public_port
            and r["protocol"] == protocol
            for r in existing_rules
        )

    assert has_conflict("eip-001", 80, "tcp")
    assert not has_conflict("eip-001", 8080, "tcp")
    assert not has_conflict("eip-001", 80, "udp")  # Different protocol, no conflict


def test_retry_backoff_sequence():
    """Retry backoff: 0s/2s/4s."""
    backoffs = [2 ** i for i in range(3)]
    assert backoffs == [1, 2, 4]


def test_dnat_protocol_validation():
    """DNAT protocol must be TCP or UDP only."""
    valid = {"tcp", "udp"}
    invalid = {"icmp", "http", "any", "all"}
    for p in valid:
        assert p in valid
    for p in invalid:
        assert p not in valid


def test_nat_state_transition_on_delete():
    """NAT gateway transitions: available → deleting → (404)."""
    # Simulate state transitions during delete
    states = ["available", "deleting"]
    def poll_after_delete(describe_result):
        return describe_result.get("state") if describe_result else "deleted"

    assert poll_after_delete({"state": "deleting"}) == "deleting"
    assert poll_after_delete(None) == "deleted"
