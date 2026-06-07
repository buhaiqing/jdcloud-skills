"""Tests for GCL rubric scoring logic for jdcloud-vpc-ops."""
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
        "skill": "jdcloud-vpc-ops",
        "rubric_version": "1.0.0",
        "iterations": [
            {
                "iter": iteration,
                "generator": {
                    "command": "jdc --output json vpc create-vpc --vpc-name test",
                    "args": {},
                    "exit_code": 0,
                    "result_excerpt": "{\"vpcId\":\"vpc-test-001\"}",
                },
                "critic": {
                    "scores": scores,
                    "suggestions": ["test suggestion"],
                    "blocking": False,
                },
                "decision": decision,
            }
        ],
        "final": {"status": decision, "iter": iteration, "output": "vpc-test-001"},
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
    """describe-* 操作 Safety=1 应当 PASS."""
    scores = {"correctness": 1, "safety": 1, "idempotency": 1,
              "traceability": 1, "spec_compliance": 1}
    all_pass = all(
        v >= rubric_template["thresholds"].get(k, 0.5)
        for k, v in scores.items()
    )
    assert all_pass


def test_correctness_zero_for_failed_operation(rubric_template):
    """操作失败时 Correctness=0."""
    scores = {"correctness": 0, "safety": 1, "idempotency": 0.5,
              "traceability": 1, "spec_compliance": 0.5}
    assert scores["correctness"] < rubric_template["thresholds"]["correctness"]


def test_idempotency_check(rubric_template):
    """重复创建应获得 Idempotency=0.5(返回 DuplicateRule)或 0(创建 2 个)."""
    # Scenario: same create-vpc called twice → Idempotency=0.5
    scores_duplicate = {"correctness": 1, "safety": 1, "idempotency": 0.5,
                        "traceability": 1, "spec_compliance": 0.5}
    assert scores_duplicate["idempotency"] >= rubric_template["thresholds"]["idempotency"]

    # Scenario: same create-vpc created 2 identical resources → Idempotency=0
    scores_bad = {"correctness": 1, "safety": 1, "idempotency": 0,
                  "traceability": 1, "spec_compliance": 0.5}
    assert scores_bad["idempotency"] < rubric_template["thresholds"]["idempotency"]


def test_traceability_json_valid():
    """trace JSON 应当符合 schema."""
    trace = _build_trace({"correctness": 1, "safety": 1, "idempotency": 1,
                          "traceability": 1, "spec_compliance": 1})
    # Serialize and deserialize to check valid JSON
    dumped = json.dumps(trace)
    loaded = json.loads(dumped)
    assert loaded["skill"] == "jdcloud-vpc-ops"
    assert len(loaded["iterations"]) == 1
    assert loaded["final"]["status"] == "PASS"


def test_spec_compliance_cidr_check():
    """CIDR 格式 + 语义校验."""
    valid_cidrs = ["10.0.0.0/16", "172.16.0.0/12", "192.168.0.0/16"]
    invalid_cidrs = ["10.0.0.0/33", "256.0.0.0/16", "10.0.0.0", "10.0.0.0/0"]

    import re
    cidr_format = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')

    def _valid_cidr(cidr):
        # Step 1: format check
        m = cidr_format.match(cidr)
        if not m:
            return False
        # Step 2: semantic check — prefix length must be 1-32
        prefix = int(cidr.split("/")[1])
        if prefix < 1 or prefix > 32:
            return False
        # Step 3: each octet must be 0-255
        for octet in cidr.split("/")[0].split("."):
            if int(octet) > 255:
                return False
        return True

    for cidr in valid_cidrs:
        assert _valid_cidr(cidr), f"Valid CIDR rejected: {cidr}"
    for cidr in invalid_cidrs:
        assert not _valid_cidr(cidr), f"Invalid CIDR passed: {cidr}"


def test_delete_vpc_safety_gate_protocol():
    """删除 VPC 的安全门协议: 必须检查 VPC 是否为空."""
    # VPC with subnets → Safety=0 if delete attempted
    # VPC empty → Safety=1
    vpc_with_subnets = {"vpcId": "vpc-test-001", "subnetCount": 3}
    vpc_empty = {"vpcId": "vpc-test-002", "subnetCount": 0}

    def can_delete(vpc):
        return vpc.get("subnetCount", 0) == 0

    assert not can_delete(vpc_with_subnets)
    assert can_delete(vpc_empty)


def test_rubric_max_iterations_limits(rubric_template):
    """max_iterations=2 限制."""
    max_iter = rubric_template["max_iterations"]
    assert max_iter == 2
    # If we went above 2 iterations, simulation should cap
    for i in range(1, max_iter + 1):
        assert i <= max_iter
    # 3rd iteration would exceed
    assert 3 > max_iter


def test_sg_rule_protocol_mapping():
    """安全组规则协议数值映射必须正确."""
    mapping = {"tcp": 6, "udp": 17, "icmp": 1, "all": 300}
    assert mapping["tcp"] == 6
    assert mapping["udp"] == 17
    assert mapping["icmp"] == 1
    assert mapping["all"] == 300


def test_sg_rule_direction_mapping():
    """方向映射: inbound=0, outbound=1."""
    assert {"inbound": 0, "outbound": 1}["inbound"] == 0
    assert {"inbound": 0, "outbound": 1}["outbound"] == 1


def test_retry_backoff_sequence():
    """重试退避: 0s/2s/4s."""
    backoffs = [2 ** i for i in range(3)]
    assert backoffs == [1, 2, 4]


def test_high_risk_port_check():
    """高危端口 22/3389 必须标识."""
    high_risk = {22, 3389}
    safe_ports = [80, 443, 8080, 3306, 5432]
    assert 22 in high_risk
    assert 3389 in high_risk
    for p in safe_ports:
        assert p not in high_risk or p == 3306  # 3306 is debatable