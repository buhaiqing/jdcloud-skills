"""Smoke tests for jdcloud-kms-ops skill."""
import re
from pathlib import Path


SKILL_DIR = Path(__file__).parent.parent
SKILL_NAME = "jdcloud-kms-ops"


class TestSkillStructure:
    """Test basic skill structure and files."""

    def test_skill_md_exists(self):
        """SKILL.md must exist."""
        skill_md = SKILL_DIR / "SKILL.md"
        assert skill_md.exists(), f"{SKILL_NAME}/SKILL.md not found"

    def test_skill_md_has_frontmatter(self):
        """SKILL.md must have YAML frontmatter with required fields."""
        skill_md = SKILL_DIR / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")

        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert fm_match, "No YAML frontmatter found"

        fm = fm_match.group(1)
        required_fields = ["name", "version", "metadata"]
        for field in required_fields:
            pattern = rf"(?:^|\n)\s*{field}:"
            assert re.search(pattern, fm), f"Missing required field: {field}"

    def test_references_dir_exists(self):
        """references/ directory must exist."""
        refs_dir = SKILL_DIR / "references"
        assert refs_dir.is_dir(), f"{SKILL_NAME}/references/ not found"

    def test_rubric_md_exists(self):
        """references/rubric.md must exist."""
        rubric_md = SKILL_DIR / "references" / "rubric.md"
        assert rubric_md.exists(), f"{SKILL_NAME}/references/rubric.md not found"

    def test_prompt_templates_md_exists(self):
        """references/prompt-templates.md must exist."""
        pt_md = SKILL_DIR / "references" / "prompt-templates.md"
        assert pt_md.exists(), f"{SKILL_NAME}/references/prompt-templates.md not found"

    def test_assets_dir_exists(self):
        """assets/ directory should exist."""
        assets_dir = SKILL_DIR / "assets"
        assert assets_dir.is_dir(), f"{SKILL_NAME}/assets/ not found"


class TestGCLCompliance:
    """Test GCL (Generator-Critic-Loop) compliance."""

    def test_gcl_level_in_frontmatter(self):
        """SKILL.md should indicate GCL level in metadata."""
        skill_md = SKILL_DIR / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")

        gcl_indicators = ["required", "GCL", "Quality Gate", "rubric"]
        found = any(ind.lower() in text.lower() for ind in gcl_indicators)
        assert found, "No GCL indicators found in SKILL.md"

    def test_safety_gate_documented(self):
        """Destructive operations must have safety gates."""
        skill_md = SKILL_DIR / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")

        safety_indicators = ["safety", "confirm", "用户确认", "destructive", "删除", "停止"]
        found = any(ind.lower() in text.lower() for ind in safety_indicators)
        assert found, "No safety gate indicators found"
