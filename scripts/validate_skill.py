#!/usr/bin/env python3
"""Repo-level skill validator.

Usage:
    python scripts/validate_skill.py <skill-dir>

Checks:
- SKILL.md exists and has YAML frontmatter with required fields
- Required reference files exist (8/8 standard refs)
- AIOps-specific structure when applicable
- Internal markdown links are valid
- SKILL.md size is within recommended limits
- Key sections are present in SKILL.md

Exit code 0 means pass; non-zero means fail.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml

    HAS_YAML = True
except Exception:  # pragma: no cover
    HAS_YAML = False

REQUIRED_FRONTMATTER_FIELDS = ["name", "metadata"]
# Special skills that only need minimal checks (meta/viz skills).
SPECIAL_SKILLS = {
    "jdcloud-skill-generator": "minimal",
    "jdcloud-topo-discovery": "minimal",
}
REQUIRED_REFERENCES = [
    "cli-usage.md",
    "core-concepts.md",
    "api-sdk-usage.md",
    "integration.md",
    "monitoring.md",
    "troubleshooting.md",
    "rubric.md",
    "prompt-templates.md",
]
MINIMAL_REFERENCES = ["rubric.md", "prompt-templates.md"]
# Each section is matched against a line starting with ##; regex supports
# both English titles and Chinese equivalents used in existing skills.
# "Safety" is considered satisfied if either a dedicated Safety section
# OR a Quality Gate (GCL) section exists, since GCL embeds safety rules.
REQUIRED_SECTIONS = [
    (r"## .*?(Trigger|Scope|触发范围)", "Trigger & Scope / 触发范围"),
    (r"## .*?(Variable|变量约定)", "Variable Convention / 变量约定"),
    (r"## .*?(Execution|工作流|执行流)", "Execution Flow / 工作流"),
]
OPTIONAL_SECTIONS = [
    (r"## .*?(Safety|安全)", "Safety Gates / 安全"),
    (r"## .*?Quality Gate", "Quality Gate (GCL)"),
]


def error(msg: str) -> None:
    print(f"[FAIL] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def ok(msg: str) -> None:
    print(f"[PASS] {msg}")


def extract_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_text, rest) or (None, text) if no frontmatter."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 4 :]


def check_frontmatter(skill_dir: Path) -> int:
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    fm_text, _ = extract_frontmatter(text)
    if fm_text is None:
        error("SKILL.md missing YAML frontmatter")
        return 1

    if not HAS_YAML:
        warn("PyYAML not installed; skipping frontmatter field parsing")
        return 0

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        error(f"SKILL.md frontmatter is invalid YAML: {exc}")
        return 1

    if not isinstance(fm, dict):
        error("SKILL.md frontmatter is not a mapping")
        return 1

    missing = [f for f in REQUIRED_FRONTMATTER_FIELDS if f not in fm]
    if missing:
        error(f"SKILL.md frontmatter missing fields: {missing}")
        return 1

    name = fm.get("name") or (fm.get("metadata") or {}).get("name")
    version = fm.get("version") or (fm.get("metadata") or {}).get("version")
    if not name:
        error("SKILL.md frontmatter missing name or metadata.name")
        return 1
    if not version:
        warn("SKILL.md frontmatter missing version or metadata.version")

    ok(f"SKILL.md frontmatter OK (name={name}, version={version})")
    return 0


def check_references(skill_dir: Path) -> int:
    profile = SPECIAL_SKILLS.get(skill_dir.name, "full")
    if profile == "minimal":
        required = MINIMAL_REFERENCES
    else:
        required = REQUIRED_REFERENCES

    refs_dir = skill_dir / "references"
    if not refs_dir.is_dir():
        error("missing references/ directory")
        return 1

    missing = [f for f in required if not (refs_dir / f).exists()]
    if missing:
        error(f"missing required references: {missing}")
        return 1

    label = "minimal" if profile == "minimal" else "required"
    ok(f"{label} references present")
    return 0


def check_aiops_structure(skill_dir: Path) -> int:
    """Extra checks for skills following the AIOps three-phase model."""
    perceive = skill_dir / "scripts" / "01-perceive"
    if not perceive.is_dir():
        return 0

    missing = []
    for sub in ("02-reason", "03-execute"):
        if not (skill_dir / "scripts" / sub).is_dir():
            missing.append(f"scripts/{sub}")
    if not (skill_dir / "runbooks").is_dir():
        missing.append("runbooks/")

    if missing:
        error(f"AIOps skill missing three-phase directories: {missing}")
        return 1

    ok("AIOps three-phase structure present")
    return 0


def extract_markdown_links(file_path: Path) -> list[tuple[str, Path]]:
    text = file_path.read_text(encoding="utf-8")
    links: list[tuple[str, Path]] = []
    in_code_block = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        for match in re.finditer(r"\[.*?\]\(([^)#]+)(?:#.*?)?\)", line):
            link = match.group(1).strip()
            if link.startswith(("http://", "https://")):
                continue
            if link in ("目标路径", "路径", "file.md", "path/to/file"):
                continue
            links.append((link, file_path))
    return links


def check_internal_links(skill_dir: Path) -> int:
    profile = SPECIAL_SKILLS.get(skill_dir.name, "full")
    broken: list[tuple[str, Path]] = []
    for md_file in skill_dir.rglob("*.md"):
        for link, source in extract_markdown_links(md_file):
            target = (source.parent / link).resolve()
            if not target.exists():
                target = (source.parent / link.rstrip("/")).resolve()
                if not target.exists():
                    broken.append((link, source))

    if broken:
        if profile == "minimal":
            warn(f"{len(broken)} broken internal link(s) (non-blocking for minimal-profile skill)")
            for link, source in broken[:5]:
                rel = source.relative_to(skill_dir)
                print(f"  - {rel}: {link}")
            if len(broken) > 5:
                print(f"  ... and {len(broken) - 5} more")
            return 0
        error(f"{len(broken)} broken internal link(s)")
        for link, source in broken:
            rel = source.relative_to(skill_dir)
            print(f"  - {rel}: {link}")
        return 1

    ok("all internal links valid")
    return 0


def check_skillmd_size(skill_dir: Path) -> int:
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    tokens = len(text) // 3

    issues = []
    if lines > 500:
        issues.append(f"{lines} lines (recommended <=500)")
    if tokens > 2000:
        issues.append(f"~{tokens} tokens (recommended <=2000)")

    if issues:
        warn("SKILL.md size: " + "; ".join(issues))
        return 0

    ok(f"SKILL.md size OK ({lines} lines, ~{tokens} tokens)")
    return 0


def check_sections(skill_dir: Path) -> int:
    profile = SPECIAL_SKILLS.get(skill_dir.name, "full")
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    lines = text.split("\n")
    rc = 0

    if profile == "minimal":
        ok("section checks skipped (minimal-profile skill)")
        return 0

    # Required sections: fail if missing
    missing = []
    for pattern, label in REQUIRED_SECTIONS:
        if not any(re.match(pattern, line) for line in lines):
            missing.append(label)
            rc = 1
    if missing:
        error(f"SKILL.md missing required sections: {missing}")

    # Optional sections: warn if missing
    missing_opt = []
    for pattern, label in OPTIONAL_SECTIONS:
        if not any(re.match(pattern, line) for line in lines):
            missing_opt.append(label)
    if missing_opt:
        warn(f"SKILL.md missing recommended sections: {missing_opt}")
    # Safety is satisfied if Quality Gate exists
    safety_pattern = OPTIONAL_SECTIONS[0][0]
    qg_pattern = OPTIONAL_SECTIONS[1][0]
    has_safety = any(re.match(safety_pattern, line) for line in lines)
    has_qg = any(re.match(qg_pattern, line) for line in lines)
    if has_qg and not has_safety:
        ok("Safety rules covered by Quality Gate (GCL)")

    if rc == 0 and not missing:
        ok("SKILL.md required sections present")
    return rc


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <skill-dir>", file=sys.stderr)
        print(f"       {sys.argv[0]} --all", file=sys.stderr)
        return 2

    if sys.argv[1] == "--all":
        repo_root = Path(__file__).resolve().parents[1]
        skills = sorted(
            d.name for d in repo_root.iterdir()
            if d.is_dir() and d.name.startswith("jdcloud-") and (d / "SKILL.md").exists()
        )
        if not skills:
            print("No skills found in repository root", file=sys.stderr)
            return 2
        total_rc = 0
        for skill_name in skills:
            rc = validate_one(repo_root / skill_name)
            if rc != 0:
                total_rc = 1
        return total_rc

    skill_dir = Path(sys.argv[1]).expanduser().resolve()
    return validate_one(skill_dir)


def validate_one(skill_dir: Path) -> int:
    if not skill_dir.is_dir():
        print(f"Not a directory: {skill_dir}", file=sys.stderr)
        return 2

    print(f"[VALIDATE] {skill_dir.name}")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        error("SKILL.md not found")
        return 1

    rcs = [
        check_frontmatter(skill_dir),
        check_references(skill_dir),
        check_aiops_structure(skill_dir),
        check_internal_links(skill_dir),
        check_skillmd_size(skill_dir),
        check_sections(skill_dir),
    ]
    total = sum(rcs)
    if total == 0:
        print(f"[OK] {skill_dir.name} passed all checks")
    else:
        print(f"[ERROR] {skill_dir.name} failed {total} check(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
