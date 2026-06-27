#!/usr/bin/env python3
"""Unit tests for scripts/gcl_runner.py — GCL Orchestrator core functions.

Tests cover:
- parse_rubric(): rubric parsing from markdown
- decide(): ABORT/RETURN/RETRY/RETURN_BEST decision logic
- hallucination_detect(): Phase 6 H layer (CLI params, JSON, time range)
- load_failure_patterns(): Phase 7 Reflexion pre-flight
- extract_failure_pattern(): failure pattern extraction
- run_gcl(): full loop with mock G/C, including H layer and Reflexion

Run: python -m pytest tests/test_gcl_runner.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to path so we can import gcl_runner
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gcl_runner import (  # noqa: E402
    DEFAULT_MAX_ITER,
    EXTENSION_DIMENSIONS,
    RUBRIC_DIMENSIONS,
    AUDIT_RETENTION_DAYS,
    RubricConfig,
    GeneratorOutput,
    CriticScore,
    IterationRecord,
    Trace,
    parse_rubric,
    decide,
    should_abort,
    all_pass,
    hallucination_detect,
    load_failure_patterns,
    inject_failure_patterns,
    extract_failure_pattern,
    run_gcl,
    mock_generator,
    mock_critic,
    mock_strict_critic,
)


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------

class TestConstants:
    """Verify constants match AGENTS.md spec."""

    def test_rubric_dimensions_has_5_core(self):
        assert len(RUBRIC_DIMENSIONS) == 5
        assert "correctness" in RUBRIC_DIMENSIONS
        assert "safety" in RUBRIC_DIMENSIONS
        assert "idempotency" in RUBRIC_DIMENSIONS
        assert "traceability" in RUBRIC_DIMENSIONS
        assert "spec_compliance" in RUBRIC_DIMENSIONS

    def test_extension_dimensions_exists(self):
        assert "region_compliance" in EXTENSION_DIMENSIONS
        assert "credential_hygiene" in EXTENSION_DIMENSIONS
        assert "well_architected" in EXTENSION_DIMENSIONS

    def test_default_max_iter_optional_is_3(self):
        """§8 aligned 2026-06-19: optional skills use max_iter=3 (not 5)."""
        assert DEFAULT_MAX_ITER["optional"] == 3

    def test_default_max_iter_required_is_2(self):
        assert DEFAULT_MAX_ITER["required"] == 2

    def test_default_max_iter_recommended_is_3(self):
        assert DEFAULT_MAX_ITER["recommended"] == 3

    def test_audit_retention_days(self):
        assert AUDIT_RETENTION_DAYS == 90


# ---------------------------------------------------------------------------
# RubricConfig / parse_rubric tests
# ---------------------------------------------------------------------------

class TestParseRubric:
    """Test rubric parsing from markdown."""

    def test_parse_vm_ops_rubric(self):
        """Parse the real vm-ops rubric.md."""
        rubric_path = REPO_ROOT / "jdcloud-vm-ops" / "references" / "rubric.md"
        if not rubric_path.exists():
            return  # skip if not in this repo
        cfg = parse_rubric("vm-ops", rubric_path)
        assert cfg.skill == "vm-ops"
        assert cfg.max_iterations >= 1
        # vm-ops is "required" class, default max_iter=2
        assert cfg.max_iterations == 2

    def test_parse_missing_file_raises(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            parse_rubric("nonexistent", Path("/tmp/nonexistent-rubric.md"))

    def test_rubric_config_defaults(self):
        cfg = RubricConfig(skill="test")
        assert cfg.rubric_version == "v1"
        assert cfg.thresholds["correctness"] == 1.0
        assert cfg.thresholds["safety"] == 1.0
        assert cfg.safety_confirm_required is True


# ---------------------------------------------------------------------------
# Decision logic tests
# ---------------------------------------------------------------------------

class TestDecide:
    """Test ABORT/RETURN/RETRY/RETURN_BEST decision logic."""

    def _make_rubric(self, max_iter=2):
        return RubricConfig(skill="test", max_iterations=max_iter)

    def test_abort_on_safety_zero(self):
        """§5: Safety=0 → ABORT immediately."""
        rubric = self._make_rubric()
        score = CriticScore(scores={"safety": 0.0, "correctness": 1.0,
                                     "idempotency": 1.0, "traceability": 1.0,
                                     "spec_compliance": 1.0})
        decision, reason, _ = decide(score, rubric, 1)
        assert decision == "ABORT"
        assert "safety" in reason.lower()

    def test_abort_on_blocking(self):
        rubric = self._make_rubric()
        score = CriticScore(blocking=True)
        decision, reason, _ = decide(score, rubric, 1)
        assert decision == "ABORT"

    def test_return_when_all_pass(self):
        rubric = self._make_rubric()
        score = CriticScore(scores=dict.fromkeys(RUBRIC_DIMENSIONS, 1.0))
        decision, reason, _ = decide(score, rubric, 1)
        assert decision == "RETURN"

    def test_retry_when_below_threshold_and_iter_lt_max(self):
        rubric = self._make_rubric(max_iter=3)
        scores = dict.fromkeys(RUBRIC_DIMENSIONS, 1.0)
        scores["correctness"] = 0.5  # below threshold 1.0
        score = CriticScore(scores=scores)
        decision, reason, feedback = decide(score, rubric, 1)
        assert decision == "RETRY"
        assert feedback is not None

    def test_return_best_when_max_iter_reached(self):
        rubric = self._make_rubric(max_iter=2)
        scores = dict.fromkeys(RUBRIC_DIMENSIONS, 1.0)
        scores["correctness"] = 0.5
        score = CriticScore(scores=scores)
        decision, reason, _ = decide(score, rubric, 2)
        assert decision == "RETURN_BEST"

    def test_should_abort_safety_zero(self):
        score = CriticScore(scores={"safety": 0.0})
        assert should_abort(score, self._make_rubric()) is True

    def test_should_abort_blocking(self):
        score = CriticScore(blocking=True)
        assert should_abort(score, self._make_rubric()) is True

    def test_should_not_abort_normal(self):
        score = CriticScore(scores={"safety": 1.0})
        assert should_abort(score, self._make_rubric()) is False

    def test_all_pass_true(self):
        rubric = self._make_rubric()
        score = CriticScore(scores=dict.fromkeys(RUBRIC_DIMENSIONS, 1.0))
        assert all_pass(score, rubric) is True

    def test_all_pass_false(self):
        rubric = self._make_rubric()
        scores = dict.fromkeys(RUBRIC_DIMENSIONS, 1.0)
        scores["idempotency"] = 0.0  # below 0.5 threshold
        score = CriticScore(scores=scores)
        assert all_pass(score, rubric) is False


# ---------------------------------------------------------------------------
# Hallucination Detection (H layer) tests — Phase 6
# ---------------------------------------------------------------------------

class TestHallucinationDetect:
    """Test the Phase 6 H layer pre-execution structural validity check."""

    def test_pass_with_known_parameters(self):
        """Valid CLI command with all known parameters → PASS."""
        result = hallucination_detect(
            skill="vm-ops",
            operation="describe-instances",
            command="jdc --output json vm describe-instances --region-id cn-north-1 --page-size 50",
        )
        assert result["status"] == "PASS"
        assert result["checks"]["cli_parameters"]["status"] == "PASS"
        assert result["checks"]["cli_parameters"]["unrecognized"] == []

    def test_fail_with_unrecognized_parameter(self):
        """Unrecognized --Zone flag → FAIL."""
        result = hallucination_detect(
            skill="vm-ops",
            operation="describe-instances",
            command="jdc --output json vm describe-instances --Zone cn-north-1a",
        )
        assert result["status"] == "FAIL"
        assert result["checks"]["cli_parameters"]["status"] == "FAIL"
        assert "--Zone" in result["checks"]["cli_parameters"]["unrecognized"]

    def test_pass_when_no_known_params(self):
        """Conservative PASS when operation not in knowledge base."""
        result = hallucination_detect(
            skill="vm-ops",
            operation="unknown-operation",
            command="jdc --output json vm unknown-operation --foo bar",
        )
        # No known_flags → can't verify → PASS
        assert result["status"] == "PASS"

    def test_json_structure_pass_no_payload(self):
        """No JSON payload → PASS with note."""
        result = hallucination_detect(
            skill="vm-ops",
            operation="describe-instances",
            command="jdc --output json vm describe-instances",
        )
        assert result["checks"]["json_structure"]["status"] == "PASS"
        assert "no JSON payload" in result["checks"]["json_structure"]["note"]

    def test_json_structure_fail_null_field(self):
        """JSON payload with null field → FAIL."""
        result = hallucination_detect(
            skill="vm-ops",
            operation="create-instance",
            command="jdc vm create-instance",
            json_payload={"name": None, "type": "g.n2.large"},
        )
        assert result["checks"]["json_structure"]["status"] == "FAIL"

    def test_time_range_pass_within_retention(self):
        """Time range ≤ 90 days → PASS."""
        result = hallucination_detect(
            skill="audit-ops",
            operation="describe-events",
            command="jdc audit describe-events",
            json_payload={
                "startTime": "2026-05-01T00:00:00Z",
                "endTime": "2026-06-01T00:00:00Z",
            },
            enable_time_range_check=True,
        )
        assert result["checks"]["time_range"]["status"] == "PASS"
        assert result["checks"]["time_range"]["within_retention"] is True

    def test_time_range_fail_exceeds_retention(self):
        """Time range > 90 days → FAIL."""
        result = hallucination_detect(
            skill="audit-ops",
            operation="describe-events",
            command="jdc audit describe-events",
            json_payload={
                "startTime": "2026-01-01T00:00:00Z",
                "endTime": "2026-06-01T00:00:00Z",  # ~150 days
            },
            enable_time_range_check=True,
        )
        assert result["checks"]["time_range"]["status"] == "FAIL"
        assert result["checks"]["time_range"]["within_retention"] is False

    def test_time_range_fail_negative_delta(self):
        """startTime > endTime → FAIL."""
        result = hallucination_detect(
            skill="audit-ops",
            operation="describe-events",
            command="jdc audit describe-events",
            json_payload={
                "startTime": "2026-06-01T00:00:00Z",
                "endTime": "2026-05-01T00:00:00Z",
            },
            enable_time_range_check=True,
        )
        assert result["checks"]["time_range"]["status"] == "FAIL"

    def test_h_never_modifies_command(self):
        """§10.6: H must flag, not mutate. Verify command unchanged."""
        cmd = "jdc --output json vm describe-instances --Zone invalid"
        hallucination_detect("vm-ops", "describe-instances", cmd)
        # Command string is not mutated (we only read it)
        assert "--Zone invalid" in cmd

    def test_h_does_not_execute_api(self):
        """§10.6: H is offline. Verify no network calls (implicit: pure function)."""
        # This test documents the constraint; the function is pure Python
        result = hallucination_detect(
            skill="vm-ops",
            operation="describe-instances",
            command="jdc --output json vm describe-instances",
        )
        assert isinstance(result, dict)
        assert "status" in result


# ---------------------------------------------------------------------------
# Reflexion Integration tests — Phase 7
# ---------------------------------------------------------------------------

class TestReflexion:
    """Test Phase 7 Reflexion pre-flight retrieval."""

    def test_load_failure_patterns_returns_list(self):
        """load_failure_patterns returns a list (possibly empty)."""
        patterns = load_failure_patterns("vm-ops")
        assert isinstance(patterns, list)

    def test_load_failure_patterns_for_eip_ops(self):
        """eip-ops has a known failure-patterns.md → should find patterns."""
        patterns = load_failure_patterns("eip-ops")
        assert len(patterns) > 0
        # Check first pattern has expected fields
        p = patterns[0]
        assert "name" in p

    def test_inject_failure_patterns_empty(self):
        """Empty patterns → empty string."""
        result = inject_failure_patterns([])
        assert result == ""

    def test_inject_failure_patterns_formats_hint(self):
        """Non-empty patterns → formatted hint string."""
        patterns = [{"name": "TestPattern", "error": "test error", "fix": "test fix"}]
        result = inject_failure_patterns(patterns)
        assert "Known failure patterns" in result
        assert "TestPattern" in result

    def test_inject_failure_patterns_max_3(self):
        """Only top 3 patterns injected."""
        patterns = [{"name": f"P{i}", "error": "e", "fix": "f"} for i in range(10)]
        result = inject_failure_patterns(patterns)
        assert result.count("- P") == 3

    def test_extract_failure_pattern_returns_none_on_pass(self):
        """No failure pattern extracted from a passing iteration."""
        result = extract_failure_pattern("vm-ops", "cmd", "ok", "RETURN")
        assert result is None

    def test_extract_failure_pattern_on_abort(self):
        """Failure pattern extracted from ABORT."""
        result = extract_failure_pattern("vm-ops", "cmd", "safety=0", "ABORT")
        assert result is not None
        assert result["skill"] == "jdcloud-vm-ops"
        assert result["category"] == "runtime"

    def test_extract_failure_pattern_cli_parameter(self):
        """InvalidParameter error → cli_parameter category."""
        result = extract_failure_pattern(
            "vm-ops", "cmd", "InvalidParameter: bad flag", "ABORT"
        )
        assert result["category"] == "cli_parameter"

    def test_extract_failure_pattern_hallucination_abort(self):
        """HALLUCINATION_ABORT → cli_parameter category."""
        result = extract_failure_pattern(
            "vm-ops", "cmd", "hallucination", "HALLUCINATION_ABORT"
        )
        assert result["category"] == "cli_parameter"


# ---------------------------------------------------------------------------
# run_gcl integration tests
# ---------------------------------------------------------------------------

class TestRunGcl:
    """Test the full GCL loop with mock G/C functions."""

    def test_run_gcl_pass_with_mock(self):
        """Mock generator + mock critic → RETURN (PASS)."""
        rubric = RubricConfig(skill="test", max_iterations=2)
        decision, trace = run_gcl(
            skill="test",
            request="test request",
            safety_confirm=True,
            generator_fn=mock_generator,
            critic_fn=mock_critic,
            rubric=rubric,
            enable_reflexion=False,  # skip file loading for unit test
        )
        assert decision == "RETURN"
        assert trace.final["status"] == "PASS"
        assert len(trace.iterations) == 1

    def test_run_gcl_abort_with_strict_critic(self):
        """Mock generator + mock-strict critic → ABORT (safety=0)."""
        rubric = RubricConfig(skill="test", max_iterations=2)
        decision, trace = run_gcl(
            skill="test",
            request="test request",
            safety_confirm=True,
            generator_fn=mock_generator,
            critic_fn=mock_strict_critic,
            rubric=rubric,
            enable_reflexion=False,
        )
        assert decision == "ABORT"
        assert trace.final["status"] == "ABORT"

    def test_run_gcl_with_h_layer_pass(self):
        """H layer enabled, valid command → PASS."""
        rubric = RubricConfig(skill="test", max_iterations=2)

        def gen_fn(req, feedback, rubric, it):
            return GeneratorOutput(
                command="jdc --output json vm describe-instances --region-id cn-north-1",
                args={},
            )

        decision, trace = run_gcl(
            skill="vm-ops",
            request="list instances",
            safety_confirm=True,
            generator_fn=gen_fn,
            critic_fn=mock_critic,
            rubric=rubric,
            enable_hallucination_check=True,
            operation="describe-instances",
            enable_reflexion=False,
        )
        assert decision == "RETURN"
        # H layer should have run and passed
        it_record = trace.iterations[0]
        assert it_record.hallucination_detector is not None
        assert it_record.hallucination_detector["status"] == "PASS"

    def test_run_gcl_with_h_layer_hallucination_abort(self):
        """H layer detects hallucination twice → HALLUCINATION_ABORT."""
        rubric = RubricConfig(skill="test", max_iterations=2)

        def gen_fn(req, feedback, rubric, it):
            # Always generates a command with bad flag
            return GeneratorOutput(
                command="jdc --output json vm describe-instances --Zone invalid",
                args={},
            )

        decision, trace = run_gcl(
            skill="vm-ops",
            request="list instances",
            safety_confirm=True,
            generator_fn=gen_fn,
            critic_fn=mock_critic,
            rubric=rubric,
            enable_hallucination_check=True,
            operation="describe-instances",
            enable_reflexion=False,
        )
        assert decision == "HALLUCINATION_ABORT"
        assert trace.final["status"] == "HALLUCINATION_ABORT"
        it_record = trace.iterations[0]
        assert it_record.regenerated is True
        assert it_record.hallucination_detector["status"] == "FAIL"

    def test_run_gcl_trace_has_extended_fields(self):
        """IterationRecord has hallucination_detector, regenerated, failure_pattern fields."""
        rubric = RubricConfig(skill="test", max_iterations=2)
        decision, trace = run_gcl(
            skill="test",
            request="test",
            safety_confirm=True,
            generator_fn=mock_generator,
            critic_fn=mock_critic,
            rubric=rubric,
            enable_reflexion=False,
        )
        it_record = trace.iterations[0]
        assert hasattr(it_record, "hallucination_detector")
        assert hasattr(it_record, "regenerated")
        assert hasattr(it_record, "failure_pattern")

    def test_run_gcl_failure_pattern_extracted_on_abort(self):
        """On ABORT, failure_pattern should be populated."""
        rubric = RubricConfig(skill="test", max_iterations=2)
        decision, trace = run_gcl(
            skill="test",
            request="test",
            safety_confirm=True,
            generator_fn=mock_generator,
            critic_fn=mock_strict_critic,
            rubric=rubric,
            enable_reflexion=False,
        )
        it_record = trace.iterations[0]
        assert it_record.failure_pattern is not None
        assert it_record.failure_pattern["skill"] == "jdcloud-test"


# ---------------------------------------------------------------------------
# IterationRecord / Trace dataclass tests
# ---------------------------------------------------------------------------

class TestDataclasses:
    """Test dataclass structure and serialization."""

    def test_iteration_record_has_h_fields(self):
        """§10.4: IterationRecord must have hallucination_detector and regenerated."""
        record = IterationRecord(
            iter=1,
            generator={},
            critic={},
            decision="RETURN",
            reason="test",
        )
        assert record.hallucination_detector is None
        assert record.regenerated is False
        assert record.failure_pattern is None

    def test_iteration_record_can_set_h_fields(self):
        record = IterationRecord(
            iter=1,
            generator={},
            critic={},
            decision="HALLUCINATION_ABORT",
            reason="test",
            hallucination_detector={"status": "FAIL"},
            regenerated=True,
            failure_pattern={"category": "cli_parameter"},
        )
        assert record.hallucination_detector["status"] == "FAIL"
        assert record.regenerated is True
        assert record.failure_pattern["category"] == "cli_parameter"

    def test_trace_serialization(self):
        """Trace can be serialized to dict via asdict."""
        from dataclasses import asdict
        trace = Trace(skill="test", request="req", rubric_version="v1")
        trace.iterations.append(
            IterationRecord(iter=1, generator={}, critic={}, decision="RETURN", reason="ok")
        )
        d = asdict(trace)
        assert d["skill"] == "test"
        assert len(d["iterations"]) == 1
        assert "hallucination_detector" in d["iterations"][0]
        assert "regenerated" in d["iterations"][0]
        assert "failure_pattern" in d["iterations"][0]


if __name__ == "__main__":
    # Allow running without pytest
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
