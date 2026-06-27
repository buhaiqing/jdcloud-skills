"""Smoke tests for jdcloud-cdn-ops.

Verifies skill structure is sane:
- SKILL.md exists with required frontmatter
- All 8 reference docs exist
- example-config.yaml exists and parses
- Fixtures are valid JSON
- GCL rubric exists with required dimensions
- Prompt templates include Generator + Critic skeletons
- Failure patterns file exists

These tests are pure read-only; they do NOT call jdc or any cloud API.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
REFS_DIR = SKILL_DIR / "references"
ASSETS_DIR = SKILL_DIR / "assets"
DOCS_DIR = SKILL_DIR / "docs"
TESTS_DIR = SKILL_DIR / "tests"

REQUIRED_REFS = [
    "cli-usage.md",
    "core-concepts.md",
    "api-sdk-usage.md",
    "integration.md",
    "monitoring.md",
    "troubleshooting.md",
    "rubric.md",
    "prompt-templates.md",
]


def test_skill_md_exists() -> None:
    assert SKILL_MD.is_file(), f"missing SKILL.md at {SKILL_MD}"


def test_skill_md_frontmatter_has_required_fields() -> None:
    """Frontmatter must have name, description, license, metadata.version, etc."""
    text = SKILL_MD.read_text()
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    end = text.find("\n---\n", 4)
    assert end > 0, "frontmatter not closed"
    fm = text[4:end]
    for field in ("name:", "description:", "license:", "metadata:", "version:"):
        assert field in fm, f"frontmatter missing '{field}'"
    assert "name: jdcloud-cdn-ops" in fm, "name field should be jdcloud-cdn-ops"


def test_skill_md_cli_first_strategy() -> None:
    """This skill uses CLI-first with SDK fallback (not SDK-only)."""
    text = SKILL_MD.read_text()
    assert "cli_applicability: jdc-first-with-fallback" in text, (
        "expected jdc-first-with-fallback cli_applicability"
    )


def test_skill_md_gcl_classification() -> None:
    text = SKILL_MD.read_text()
    assert "gcl_classification: recommended" in text
    assert "gcl_max_iter: 3" in text


def test_all_required_refs_exist() -> None:
    for ref in REQUIRED_REFS:
        path = REFS_DIR / ref
        assert path.is_file(), f"missing required ref: {path}"


def test_example_config_parses() -> None:
    cfg_path = ASSETS_DIR / "example-config.yaml"
    assert cfg_path.is_file()
    cfg = yaml.safe_load(cfg_path.read_text())
    assert "domain" in cfg
    assert "cache_rules" in cfg
    assert "safety_gates" in cfg
    assert cfg["domain"]["cdn_type"] in ("vod", "live")


def test_failure_patterns_exists_and_structured() -> None:
    fp = DOCS_DIR / "failure-patterns.md"
    assert fp.is_file()
    text = fp.read_text()
    # at least 3 sections
    sections = [line for line in text.splitlines() if line.startswith("## §")]
    assert len(sections) >= 3, "failure-patterns.md should have ≥3 sections"


def test_rubric_has_five_dimensions() -> None:
    rubric = (REFS_DIR / "rubric.md").read_text()
    for dim in ("Correctness", "Safety", "Idempotency", "Traceability", "Spec Compliance"):
        assert dim in rubric, f"rubric.md missing dimension: {dim}"
    assert "Safety = 0" in rubric, "rubric must state Safety=0 → ABORT rule"


def test_prompt_templates_have_generator_and_critic() -> None:
    pt = (REFS_DIR / "prompt-templates.md").read_text()
    assert "Generator Prompt Template" in pt
    assert "Critic Prompt Template" in pt
    assert "{{output.rubric}}" in pt or "{{output.generator_output}}" in pt


def test_integration_delegates_to_other_skills() -> None:
    """integration.md must mention key cross-skill delegations."""
    text = (REFS_DIR / "integration.md").read_text()
    for skill in (
        "jdcloud-oss-ops",
        "jdcloud-cert-ops",
        "jdcloud-waf-ops",
        "jdcloud-cloudmonitor-ops",
    ):
        assert skill in text, f"integration.md missing delegation to {skill}"


def test_cli_usage_top_level_output_flag() -> None:
    """Document the CLI quirk: --output json must be top-level."""
    text = (REFS_DIR / "cli-usage.md").read_text()
    assert "top-level" in text.lower()


def test_fixtures_valid_json() -> None:
    for name in ("domain.json", "cache-rule.json"):
        path = TESTS_DIR / "fixtures" / name
        assert path.is_file()
        json.loads(path.read_text())  # raises if invalid
