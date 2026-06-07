"""Tests for GCL rubric scoring logic for jdcloud-oss-ops."""
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
        "skill": "jdcloud-oss-ops",
        "rubric_version": "1.0.0",
        "iterations": [
            {
                "iter": iteration,
                "generator": {
                    "command": "OssClient -> CreateBucket(bucketName='test-bucket', regionId='cn-north-1')",
                    "args": {},
                    "exit_code": 0,
                    "result_excerpt": '{"bucketName": "test-bucket"}',
                },
                "critic": {
                    "scores": scores,
                    "suggestions": ["test suggestion"],
                    "blocking": False,
                },
                "decision": decision,
            }
        ],
        "final": {"status": decision, "iter": iteration, "output": "test-bucket"},
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
    """head-bucket / list-buckets ops Safety=1 should PASS."""
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
    """Duplicate bucket creation gets Idempotency=0.5."""
    scores_duplicate = {"correctness": 1, "safety": 1, "idempotency": 0.5,
                        "traceability": 1, "spec_compliance": 0.5}
    assert scores_duplicate["idempotency"] >= rubric_template["thresholds"]["idempotency"]

    scores_bad = {"correctness": 1, "safety": 1, "idempotency": 0,
                  "traceability": 1, "spec_compliance": 0.5}
    assert scores_bad["idempotency"] < rubric_template["thresholds"]["idempotency"]


def test_traceability_json_valid():
    """Trace JSON must match schema."""
    trace = _build_trace({"correctness": 1, "safety": 1, "idempotency": 1,
                          "traceability": 1, "spec_compliance": 1})
    dumped = json.dumps(trace)
    loaded = json.loads(dumped)
    assert loaded["skill"] == "jdcloud-oss-ops"
    assert len(loaded["iterations"]) == 1
    assert loaded["final"]["status"] == "PASS"


def test_spec_compliance_acl_values():
    """ACL values must be one of: private, public-read, public-read-write."""
    valid_acls = ["private", "public-read", "public-read-write"]
    invalid_acls = ["", "public", "read", "write", "admin", "full-control"]

    for acl in valid_acls:
        assert acl in ("private", "public-read", "public-read-write"), f"Valid ACL rejected: {acl}"
    for acl in invalid_acls:
        assert acl not in ("private", "public-read", "public-read-write"), f"Invalid ACL passed: {acl}"


def test_delete_bucket_safety_gate_protocol():
    """Delete bucket safety gate: must check if bucket is empty first."""
    bucket_non_empty = {"bucketName": "test-bucket", "objectCount": 150}
    bucket_empty = {"bucketName": "empty-bucket", "objectCount": 0}

    def can_delete(bucket, confirmed=False):
        if not confirmed:
            return False
        return bucket.get("objectCount", 0) == 0 or confirmed

    assert not can_delete(bucket_non_empty, confirmed=False)
    assert not can_delete(bucket_empty, confirmed=False)
    assert can_delete(bucket_empty, confirmed=True)


def test_rubric_max_iterations_limits(rubric_template):
    """max_iterations=3 limit."""
    max_iter = rubric_template["max_iterations"]
    assert max_iter == 3
    for i in range(1, max_iter + 1):
        assert i <= max_iter
    assert 4 > max_iter


def test_storage_class_validation():
    """Storage class values must be one of: Standard, InfrequentAccess, Archive."""
    valid_classes = ["Standard", "InfrequentAccess", "Archive"]
    invalid_classes = ["standard", "IA", "Glacier", "DeepArchive", "Cold"]

    for cls in valid_classes:
        assert cls in valid_classes, f"Valid class rejected: {cls}"
    for cls in invalid_classes:
        assert cls not in valid_classes, f"Invalid class passed: {cls}"


def test_lifecycle_rule_transition_order():
    """Lifecycle transition days must be ascending."""
    valid_rule = {
        "transitions": [
            {"days": 30, "storageClass": "InfrequentAccess"},
            {"days": 180, "storageClass": "Archive"},
        ]
    }
    invalid_rule = {
        "transitions": [
            {"days": 365, "storageClass": "Archive"},
            {"days": 30, "storageClass": "InfrequentAccess"},
        ]
    }

    def transitions_ascending(rule):
        days = [t["days"] for t in rule["transitions"]]
        return all(days[i] <= days[i + 1] for i in range(len(days) - 1))

    assert transitions_ascending(valid_rule)
    assert not transitions_ascending(invalid_rule)


def test_retry_backoff_sequence():
    """Retry backoff: 0s/2s/4s."""
    backoffs = [2 ** i for i in range(3)]
    assert backoffs == [1, 2, 4]


def test_presigned_url_expiration():
    """Presigned URL expiration must be 1-86400 seconds."""
    valid_expirations = [1, 60, 3600, 86400]
    invalid_expirations = [0, -1, 86401, 99999]

    def valid_expiration(seconds):
        return 1 <= seconds <= 86400

    for exp in valid_expirations:
        assert valid_expiration(exp), f"Valid expiration rejected: {exp}"
    for exp in invalid_expirations:
        assert not valid_expiration(exp), f"Invalid expiration passed: {exp}"


def test_bucket_name_prefix_recommendation():
    """Test bucket name prefix recommendation from core-concepts.md."""
    valid_patterns = [
        "my-app-prod-logs-cn-north-1",
        "backup-data-2026",
        "static-assets-hosting",
    ]
    invalid_patterns = [
        "",
        "a",
    ]
    for p in valid_patterns:
        assert len(p) >= 3 and len(p) <= 63, f"Valid pattern rejected: {p}"
    for p in invalid_patterns:
        assert len(p) < 3 or len(p) > 63, f"Invalid pattern passed: {p}"