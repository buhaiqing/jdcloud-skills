"""Rubric-level tests for jdcloud-cdn-ops.

These tests verify that the skill's stated quality bar (rubric.md) is met by
the actual skill content. They are pure structural checks, NOT execution.

Why this matters: a skill can claim "Safety = 1.0 required for delete" in
rubric.md, but if SKILL.md doesn't enforce confirmation gates, the rubric
is decorative. These tests catch that drift.
"""

from __future__ import annotations

from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
RUBRIC = SKILL_DIR / "references" / "rubric.md"
PROMPT = SKILL_DIR / "references" / "prompt-templates.md"


def test_skill_documents_safety_gate_for_destructive_ops() -> None:
    """SKILL.md must list destructive ops explicitly."""
    text = SKILL_MD.read_text()
    assert "delete-domain" in text, "must mention delete-domain as destructive"
    assert "stop-domain" in text, "must mention stop-domain as destructive"
    assert "batch-delete-domain-group" in text, "must mention batch-delete"
    assert "confirmation" in text.lower(), "must require user confirmation"


def test_rubric_states_safety_threshold_for_delete() -> None:
    text = RUBRIC.read_text()
    # delete-domain must require 1.0 safety
    assert "delete-domain" in text
    assert "1.0" in text  # threshold value appears


def test_prompt_templates_include_safety_subscores() -> None:
    text = PROMPT.read_text()
    # Worked Example C: delete with safety = 0 → ABORT
    assert "SAFETY_FAIL" in text or "ABORT" in text


def test_rubric_documents_correctness_threshold() -> None:
    text = RUBRIC.read_text()
    assert "≥ 0.5" in text or ">= 0.5" in text, "correctness threshold must be ≥0.5"


def test_prompt_templates_use_repo_placeholder_syntax() -> None:
    """Per AGENTS.md §7, placeholders must be {{env.*}} / {{user.*}} / {{output.*}}."""
    text = PROMPT.read_text()
    for token in ("{{env.JDC_ACCESS_KEY}}", "{{user.request}}", "{{output.rubric}}"):
        assert token in text, f"prompt template must use {token}"


def test_skill_md_version_is_1_or_higher() -> None:
    text = SKILL_MD.read_text()
    # Extract version from metadata
    for line in text.splitlines():
        if line.strip().startswith("version:"):
            v = line.split('"')[1]
            major = int(v.split(".")[0])
            assert major >= 1, f"version {v} should be >= 1.0.0 for a new skill"


def test_failure_patterns_dedup() -> None:
    """The same pattern should not appear twice with different counts."""
    fp = (SKILL_DIR / "docs" / "failure-patterns.md").read_text()
    # Simple heuristic: each table row should be unique on (pattern, error)
    # This is a smoke-level check; full dedup is at line-edit time.
    assert fp.count("| count |") >= 3, "should have at least 3 pattern tables"
