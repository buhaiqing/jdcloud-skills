"""Rubric compliance tests for jdcloud-vm-ops skill.

Tests that the skill follows the GCL rubric dimensions and thresholds.
"""
import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SKILL_NAME = "jdcloud-vm-ops"


class TestRubricDimensions:
    """Test that rubric dimensions are properly defined."""

    @pytest.fixture
    def rubric_md(self):
        """Load rubric.md content."""
        rubric_path = SKILL_DIR / "references" / "rubric.md"
        if not rubric_path.exists():
            pytest.skip("rubric.md not found")
        return rubric_path.read_text(encoding="utf-8")

    def test_rubric_has_correctness_dimension(self, rubric_md):
        """Rubric must define correctness dimension."""
        assert "correctness" in rubric_md.lower(), "Missing correctness dimension"

    def test_rubric_has_safety_dimension(self, rubric_md):
        """Rubric must define safety dimension."""
        assert "safety" in rubric_md.lower(), "Missing safety dimension"

    def test_rubric_has_idempotency_dimension(self, rubric_md):
        """Rubric must define idempotency dimension."""
        assert "idempotency" in rubric_md.lower(), "Missing idempotency dimension"

    def test_rubric_has_traceability_dimension(self, rubric_md):
        """Rubric must define traceability dimension."""
        assert "traceability" in rubric_md.lower(), "Missing traceability dimension"

    def test_rubric_has_spec_compliance_dimension(self, rubric_md):
        """Rubric must define spec_compliance dimension."""
        assert "spec" in rubric_md.lower(), "Missing spec_compliance dimension"

    def test_rubric_defines_thresholds(self, rubric_md):
        """Rubric must define thresholds for dimensions."""
        threshold_patterns = [r"≥\s*0\.5", r">=\s*0\.5", r"threshold", r"abort"]
        found = any(re.search(p, rubric_md.lower()) for p in threshold_patterns)
        assert found, "No threshold definitions found"


class TestSafetyRules:
    """Test safety-specific rules for destructive ops."""

    @pytest.fixture
    def skill_md(self):
        """Load SKILL.md content."""
        skill_path = SKILL_DIR / "SKILL.md"
        return skill_path.read_text(encoding="utf-8")

    def test_safety_abort_defined(self, skill_md):
        """Safety=0 must trigger abort, not downgrade."""
        # Look for safety abort indicators
        abort_patterns = [
            r"safety.*=.*0.*abort",
            r"safety.*zero.*abort",
            r"abort.*safety",
            r"safety.*fail.*abort",
        ]
        found = any(re.search(p, skill_md.lower()) for p in abort_patterns)
        # Also check if explicitly mentioned in rubric or prompt templates
        if not found:
            rubric_path = SKILL_DIR / "references" / "rubric.md"
            if rubric_path.exists():
                rubric_text = rubric_path.read_text(encoding="utf-8").lower()
                found = "safety" in rubric_text and ("abort" in rubric_text or "= 0" in rubric_text)
        assert found, "Safety abort rule not clearly defined"

    def test_destructive_ops_listed(self, skill_md):
        """Destructive operations should be explicitly listed."""
        destructive_ops = ["delete", "stop", "terminate", "销毁", "删除", "停止"]
        found = any(op in skill_md.lower() for op in destructive_ops)
        assert found, "No destructive operations identified"


class TestPromptTemplates:
    """Test prompt template structure."""

    @pytest.fixture
    def prompt_templates_md(self):
        """Load prompt-templates.md content."""
        pt_path = SKILL_DIR / "references" / "prompt-templates.md"
        if not pt_path.exists():
            pytest.skip("prompt-templates.md not found")
        return pt_path.read_text(encoding="utf-8")

    def test_has_generator_prompt(self, prompt_templates_md):
        """Must have Generator prompt template."""
        indicators = ["generator", "生成器", "执行"]
        found = any(ind in prompt_templates_md.lower() for ind in indicators)
        assert found, "No Generator prompt found"

    def test_has_critic_prompt(self, prompt_templates_md):
        """Must have Critic prompt template."""
        indicators = ["critic", "评审", "审计", "评分"]
        found = any(ind in prompt_templates_md.lower() for ind in indicators)
        assert found, "No Critic prompt found"

    def test_critic_isolated_context(self, prompt_templates_md):
        """Critic prompt should emphasize isolated context."""
        # Critic should not see user request
        isolation_indicators = [
            "isolated",
            "独立",
            "hide",
            "隐藏",
            "do not consider",
            "不考虑",
        ]
        found = any(ind in prompt_templates_md.lower() for ind in isolation_indicators)
        # This is a soft check - not all skills may explicitly state this
        if not found:
            pytest.skip("Isolation not explicitly documented (optional)")


class TestVersionAndMetadata:
    """Test version and metadata compliance."""

    def test_version_follows_semver(self):
        """Version should follow semantic versioning."""
        skill_md = SKILL_DIR / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")

        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not fm_match:
            pytest.skip("No frontmatter found")

        fm = fm_match.group(1)
        version_match = re.search(r'version:\s*["\']?([^"\'\s]+)["\']?', fm)
        if not version_match:
            pytest.skip("No version field found")

        version = version_match.group(1)
        # SemVer pattern: major.minor.patch
        semver_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(semver_pattern, version), f"Version {version} does not follow SemVer"
