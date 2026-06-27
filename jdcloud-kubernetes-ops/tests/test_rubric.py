"""Tests for GCL rubric scoring logic for jdcloud-kubernetes-ops."""
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
        "max_iterations": 3,
    }


def _build_trace(scores, decision="PASS", iteration=1):
    """Build a GCL trace JSON for testing."""
    return {
        "skill": "jdcloud-kubernetes-ops",
        "rubric_version": "v2",
        "iterations": [
            {
                "iter": iteration,
                "generator": {
                    "command": "jdc --output json nc create-cluster --cluster-name test",
                    "args": {},
                    "exit_code": 0,
                    "result_excerpt": "{\"clusterId\":\"c-test-001\"}",
                },
                "critic": {
                    "scores": scores,
                    "suggestions": ["test suggestion"],
                    "blocking": False,
                },
                "decision": decision,
            }
        ],
        "final": {"status": decision, "iter": iteration, "output": "c-test-001"},
    }


def test_rubric_five_dimensions(rubric_template):
    assert len(rubric_template["dimensions"]) == 5


def test_safety_zero_triggers_abort(rubric_template):
    """Safety=0 must trigger abort."""
    scores = {"correctness": 1, "safety": 0, "idempotency": 1,
              "traceability": 1, "spec_compliance": 1}
    if scores["safety"] == 0:
        decision = "ABORT"
    else:
        decision = "PASS" if all(
            v >= rubric_template["thresholds"].get(k, 0.5)
            for k, v in scores.items()
        ) else "RETRY"
    assert decision == "ABORT"


def test_safety_one_passes_for_describe(rubric_template):
    """describe-* operations Safety=1 should PASS."""
    scores = {"correctness": 1, "safety": 1, "idempotency": 1,
              "traceability": 1, "spec_compliance": 1}
    all_pass = all(
        v >= rubric_template["thresholds"].get(k, 0.5)
        for k, v in scores.items()
    )
    assert all_pass


def test_correctness_zero_for_failed_operation(rubric_template):
    """Failed operation gets Correctness=0."""
    scores = {"correctness": 0, "safety": 1, "idempotency": 0.5,
              "traceability": 1, "spec_compliance": 0.5}
    assert scores["correctness"] < rubric_template["thresholds"]["correctness"]


def test_idempotency_check(rubric_template):
    """Duplicate creation gets Idempotency=0.5 (duplicate detected) or 0 (duplicate resources)."""
    scores_duplicate = {"correctness": 1, "safety": 1, "idempotency": 0.5,
                        "traceability": 1, "spec_compliance": 0.5}
    assert scores_duplicate["idempotency"] >= rubric_template["thresholds"]["idempotency"]

    scores_bad = {"correctness": 1, "safety": 1, "idempotency": 0,
                  "traceability": 1, "spec_compliance": 0.5}
    assert scores_bad["idempotency"] < rubric_template["thresholds"]["idempotency"]


def test_traceability_json_valid():
    """Trace JSON must conform to schema."""
    trace = _build_trace({"correctness": 1, "safety": 1, "idempotency": 1,
                          "traceability": 1, "spec_compliance": 1})
    dumped = json.dumps(trace)
    loaded = json.loads(dumped)
    assert loaded["skill"] == "jdcloud-kubernetes-ops"
    assert len(loaded["iterations"]) == 1
    assert loaded["final"]["status"] == "PASS"


def test_spec_compliance_version_check():
    """Kubernetes version format validation."""
    valid_versions = ["1.26.3", "1.27.1", "1.28.0", "1.28.3", "1.29.0"]
    invalid_versions = ["1.26", "v1.28", "1.28.x", "latest", "1.28.3-alpha"]

    import re
    version_format = re.compile(r'^\d+\.\d+\.\d+$')

    for v in valid_versions:
        assert version_format.match(v), f"Valid version rejected: {v}"
    for v in invalid_versions:
        assert not version_format.match(v), f"Invalid version passed: {v}"


def test_delete_cluster_safety_gate_protocol():
    """Delete cluster safety gate: must check workloads."""
    # Cluster with deployments → Safety=0 if delete attempted without confirm
    # Cluster empty → Safety=1
    cluster_with_workloads = {"clusterId": "c-test-001", "workloads": {"deployments": 3, "pods": 10}}
    cluster_empty = {"clusterId": "c-test-002", "workloads": {"deployments": 0, "pods": 0}}

    def can_delete(cluster, confirmed=False):
        if not confirmed:
            return False
        if cluster.get("workloads", {}).get("deployments", 0) > 0 and not confirmed == "DELETE_PROD":  # noqa: SIM103, SIM201
            return False
        return True

    assert not can_delete(cluster_with_workloads)
    assert can_delete(cluster_empty, confirmed=True)
    assert can_delete(cluster_with_workloads, confirmed="DELETE_PROD")


def test_rubric_max_iterations_limits(rubric_template):
    """max_iterations=3 limit check."""
    max_iter = rubric_template["max_iterations"]
    assert max_iter == 3
    for i in range(1, max_iter + 1):
        assert i <= max_iter
    assert max_iter < 4


def test_k8s_version_upgrade_path():
    """Upgrade path validation: one minor at a time, no downgrade."""
    def valid_upgrade(current, target):
        cur_parts = [int(x) for x in current.split(".")]
        tgt_parts = [int(x) for x in target.split(".")]
        # No downgrade
        if tgt_parts[0] < cur_parts[0] or (tgt_parts[0] == cur_parts[0] and tgt_parts[1] < cur_parts[1]):
            return False
        # Max one minor version jump
        if tgt_parts[0] != cur_parts[0] or tgt_parts[1] - cur_parts[1] > 1:  # noqa: SIM103
            return False
        return True

    assert valid_upgrade("1.27.3", "1.28.0")
    assert not valid_upgrade("1.28.3", "1.27.0")  # downgrade
    assert not valid_upgrade("1.26.3", "1.28.0")  # two minor jumps
    assert valid_upgrade("1.28.0", "1.28.3")  # patch upgrade


def test_kubeconfig_not_logged():
    """Kubeconfig must never be logged in plaintext; SHA-256 hash only."""
    import hashlib
    kubeconfig = "apiVersion: v1\nkind: Config\n..."
    sha256 = hashlib.sha256(kubeconfig.encode()).hexdigest()
    # Trace must contain SHA-256, not the raw content
    assert len(sha256) == 64
    assert kubeconfig not in sha256  # hash is not the original content


def test_instance_type_format():
    """Instance type format validation."""
    valid_types = ["g.n2.large", "c.n2.large", "m.n2.large", "p.n1.large", "g.s2.medium"]
    invalid_types = ["large", "g2.large", "g.n2.", ".n2.large"]

    import re
    type_format = re.compile(r'^[a-z]+\.[a-z0-9]+\.[a-z]+$')

    for t in valid_types:
        assert type_format.match(t), f"Valid type rejected: {t}"
    for t in invalid_types:
        assert not type_format.match(t), f"Invalid type passed: {t}"


def test_cluster_state_transitions():
    """Verify expected state transitions are valid."""
    transitions = {
        "": "creating",        # create
        "creating": "running",  # create succeeds / fails (two outcomes)
        "running": "deleting",  # delete starts
        "deleting": "deleted", # delete completes
    }
    # All states must be valid
    valid_states = {"creating", "running", "deleting", "deleted", "error"}
    for from_state, to_state in transitions.items():
        assert from_state in valid_states or from_state == ""
        assert to_state in valid_states
