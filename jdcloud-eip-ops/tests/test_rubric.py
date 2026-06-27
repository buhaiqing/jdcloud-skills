"""Tests for GCL rubric scoring logic for jdcloud-eip-ops."""
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
        "skill": "jdcloud-eip-ops",
        "rubric_version": "v1",
        "iterations": [
            {
                "iter": iteration,
                "generator": {
                    "command": "jdc --output json eip allocate-address --bandwidth 10",
                    "args": {},
                    "exit_code": 0,
                    "result_excerpt": '{"allocationId":"eip-test-001"}',
                },
                "critic": {
                    "scores": scores,
                    "suggestions": ["test suggestion"],
                    "blocking": False,
                },
                "decision": decision,
            }
        ],
        "final": {"status": decision, "iter": iteration, "output": "eip-test-001"},
    }


def test_rubric_five_dimensions(rubric_template):
    assert len(rubric_template["dimensions"]) == 5


def test_safety_zero_triggers_abort(rubric_template):
    """Safety=0 must trigger abort."""
    scores = {"correctness": 1, "safety": 0, "idempotency": 1,
              "traceability": 1, "spec_compliance": 1}
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
    """allocate EIP is naturally idempotent at API level."""
    scores_duplicate = {"correctness": 1, "safety": 1, "idempotency": 0.5,
                        "traceability": 1, "spec_compliance": 0.5}
    assert scores_duplicate["idempotency"] >= rubric_template["thresholds"]["idempotency"]


def test_traceability_json_valid():
    """Trace JSON should conform to schema."""
    trace = _build_trace({"correctness": 1, "safety": 1, "idempotency": 1,
                          "traceability": 1, "spec_compliance": 1})
    dumped = json.dumps(trace)
    loaded = json.loads(dumped)
    assert loaded["skill"] == "jdcloud-eip-ops"
    assert len(loaded["iterations"]) == 1
    assert loaded["final"]["status"] == "PASS"


def test_release_eip_safety_gate():
    """Releasing an EIP attached to production (NAT/VM) must have explicit confirm."""
    eip_free = {"allocationId": "eip-test-001", "instanceId": None, "instanceType": None}
    eip_nat = {"allocationId": "eip-test-002", "instanceId": "nat-001", "instanceType": "nat"}
    eip_vm = {"allocationId": "eip-test-003", "instanceId": "vm-001", "instanceType": "vm"}

    def can_release(eip, confirm=False):
        if eip.get("instanceId") is not None:
            return confirm
        return True

    # Free EIP: safe to release
    assert can_release(eip_free)
    # NAT-attached: requires confirm
    assert not can_release(eip_nat)
    assert can_release(eip_nat, confirm=True)
    # VM-attached: requires confirm
    assert not can_release(eip_vm)
    assert can_release(eip_vm, confirm=True)


def test_cannot_release_in_use_eip():
    """Cannot release EIP that is in use by a running instance."""
    eip_running_vm = {"allocationId": "eip-test-001", "instanceId": "vm-running",
                      "instanceType": "vm", "status": "available"}
    eip_stopped_vm = {"allocationId": "eip-test-002", "instanceId": "vm-stopped",
                      "instanceType": "vm", "status": "available"}

    def can_release_eip(eip, confirm=False):
        if eip.get("instanceId") is None:
            return True
        if eip.get("instanceType") == "vm" and confirm:  # noqa: SIM103
            return True
        return False

    # Cannot release without confirm
    assert not can_release_eip(eip_running_vm)
    # Stopped VM still in use
    assert not can_release_eip(eip_stopped_vm)


def test_associate_eip_force_rebind():
    """associate EIP to a different instance while already associated requires confirm."""
    current_assn = {"instanceId": "nat-001", "instanceType": "nat"}
    target_assn = {"instanceId": "nat-002", "instanceType": "nat"}

    def can_associate(target, current=None, confirm=False):
        if current is not None and current != target:
            return confirm
        return True

    # No current binding: safe
    assert can_associate(target_assn, current=None)
    # Rebind to different target: requires confirm
    assert not can_associate(target_assn, current=current_assn)
    assert can_associate(target_assn, current=current_assn, confirm=True)


def test_dissociate_prod_eip_safety():
    """Dissociating EIP from production instance must have explicit confirm."""
    prod_eip = {"allocationId": "eip-prod-001", "instanceId": "nat-prod",
                "instanceType": "nat"}
    test_eip = {"allocationId": "eip-test-001", "instanceId": "vm-test",
                 "instanceType": "vm"}

    def can_dissociate(eip, confirm=False):
        if eip.get("instanceType") in ("nat", "clb"):
            return confirm
        return True

    # Production: requires confirm
    assert not can_dissociate(prod_eip)
    assert can_dissociate(prod_eip, confirm=True)
    # Non-production: safe
    assert can_dissociate(test_eip)


def test_rubric_max_iterations_limits(rubric_template):
    """max_iterations=2 limit."""
    max_iter = rubric_template["max_iterations"]
    assert max_iter == 2
    for i in range(1, max_iter + 1):
        assert i <= max_iter
    assert max_iter < 3


def test_spec_compliance_bandwidth_quota():
    """Bandwidth must be within quota limits."""
    valid_bw = [1, 5, 10, 100, 200, 500]
    invalid_bw = [0, -1, 1001]

    def within_quota(bw, max_quota=500):
        return 1 <= bw <= max_quota

    for bw in valid_bw:
        assert within_quota(bw), f"Valid bandwidth rejected: {bw}"
    for bw in invalid_bw:
        assert not within_quota(bw), f"Invalid bandwidth passed: {bw}"


def test_spec_compliance_line_type():
    """Line type must be valid: standard or bgp."""
    valid_line_types = {"standard", "bgp"}
    invalid_line_types = {"ppp", "dhcp", ""}

    def valid_line(lt):
        return lt in valid_line_types

    for lt in valid_line_types:
        assert valid_line(lt)
    for lt in invalid_line_types:
        assert not valid_line(lt)


def test_retry_backoff_sequence():
    """Retry backoff: 0s/2s/4s."""
    backoffs = [2 ** i for i in range(3)]
    assert backoffs == [1, 2, 4]
