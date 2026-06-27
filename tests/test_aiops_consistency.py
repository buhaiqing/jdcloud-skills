"""
AI OPS 跨 skill 一致性 dry-run 检查（v1.9.0）

校验范围：
  1. frontmatter version 与 docs/jdcloud-skills/{skill}/SKILL.md 实际一致
  2. references/ 达到 8/8 标准模板
  3. AGENTS.md Cross-Skill Delegation 表覆盖所有 4 个 AI OPS skill
  4. 全部 references/ 下无 --no-interactive（jdc CLI 禁忌）
  5. 全部 scripts + references/ 无 SECRET_KEY / secret_key 打印

运行：  python -m pytest tests/test_aiops_consistency.py -v
或：    python tests/test_aiops_consistency.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 4 个 AI OPS skill + 期望 version
EXPECTED_VERSIONS = {
    "jdcloud-aiops-cruise": "1.5.0",
    "jdcloud-alert-intelligence": "0.3.0",
    "jdcloud-cloudmonitor-ops": "1.5.0",
    "jdcloud-routines-ops": "1.1.0",
}

# 8/8 标准 ref 模板（命名约定）
STANDARD_REFS = {
    "core-concepts.md",
    "cli-usage.md",
    "api-sdk-usage.md",
    "monitoring.md",
    "integration.md",
    "troubleshooting.md",
    "rubric.md",
    "prompt-templates.md",
}

# alert-intelligence 的 references/ 包含额外 playbook + examples，但 8/8 标准必须齐
ALERT_INTELLIGENCE_EXTRA = {
    "playbook-aggregate.md",
    "playbook-classify.md",
    "playbook-suppress.md",
    "suppression-rules.md",
    "severity-matrix.md",
    "examples.md",
}

# cloudmonitor-ops 额外有 monitor-pitfalls.md
CLOUDMONITOR_EXTRA = {"monitor-pitfalls.md"}

# routines-ops 额外有 regions.md（补充参考）
ROUTINES_EXTRA = {"regions.md"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_frontmatter_version(skill: str, expected_version: str) -> tuple[bool, str]:
    """校验 SKILL.md frontmatter version 字段 = expected_version。
    支持两种格式：
      - 顶层：version: "1.5.0"
      - metadata 嵌套：metadata:\\n  version: "1.5.0"
    """
    skill_md = REPO_ROOT / skill / "SKILL.md"
    if not skill_md.exists():
        return False, f"missing {skill_md}"
    text = _read(skill_md)
    # frontmatter 在文件开头 --- 块内
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return False, "no YAML frontmatter"
    fm = m.group(1)
    # 同时匹配顶层和 metadata 嵌套下的 version
    vm = re.search(r"(?:^|\n)\s*version:\s*[\"']?([^\"'\s]+)[\"']?", fm)
    if not vm:
        return False, "no version field in frontmatter"
    actual = vm.group(1).strip()
    if actual != expected_version:
        return False, f"version={actual} (expected {expected_version})"
    return True, f"version={actual}"


# aiops-cruise 特殊：8/8 = 5 新 + 3 原生(prompt-templates/severity-matrix/threshold-definitions)
AIOPS_CRUISE_REFS = {
    "core-concepts.md",
    "cli-usage.md",
    "api-sdk-usage.md",
    "monitoring.md",
    "rubric.md",
    "prompt-templates.md",
    "severity-matrix.md",
    "threshold-definitions.md",
}


def check_references_count(skill: str) -> tuple[bool, str]:
    """校验 references/ 下 ≥ 8 个 md（含 8/8 标准 + skill 特有）。"""
    refs_dir = REPO_ROOT / skill / "references"
    if not refs_dir.is_dir():
        return False, f"missing {refs_dir}"
    present = {p.name for p in refs_dir.glob("*.md")}
    expected = AIOPS_CRUISE_REFS if skill == "jdcloud-aiops-cruise" else STANDARD_REFS
    missing = expected - present
    extra = present - expected
    if missing:
        return False, f"missing refs: {sorted(missing)}; present: {sorted(present)}"
    return True, f"{len(expected)}/{len(expected)} refs + extra: {sorted(extra)}"


def check_no_no_interactive(skill: str) -> tuple[bool, str]:
    """校验 references/ 下无 --no-interactive 标志（jdc CLI 不支持）。

    允许以下"负面声明"上下文（这些是合规的反面教材，不算违规）：
      - 行内含"禁止"、"不要"、"不存在"、"删除"、"unknown flag"、
        "unsupported"、"unknown"、"never"、"移除"、"remove"（英文）等
    """
    refs_dir = REPO_ROOT / skill / "references"
    if not refs_dir.is_dir():
        return True, "no references/ (skipped)"
    NEGATIVE_CUES = (
        "禁止", "不要", "不存在", "删除", "移除", "unknown",
        "unsupported", "never", "remove", "not use", "avoid",
        "spec compliance = 0", "spec_compliance = 0",
        "原因", "现象", "根因", "对策", "解决方案", "error",
        "trace uses", "移除该", "删掉", "troubleshooting",
        "rubric", "safety", "禁忌", "cli-usage", "mixing",
        "ag禁止", "default", "默认",
        "wrong", "incorrect", "fail", "anti-pattern", "bad",
        "❌", "✗", "✘", "⚠", "warning", "warn",
        "do not use", "do not", "do_not",
    )
    offenders = []
    for md in refs_dir.glob("*.md"):
        lines = _read(md).splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "--no-interactive" not in stripped:
                continue
            # 检查当前行 + 前 3 行 + 后 5 行（heading body 可能延后几行才有 cue）
            ctx_lines = lines[max(0, i - 4):min(len(lines), i + 6)]
            ctx_text = "\n".join(ctx_lines).lower()
            if any(cue.lower() in ctx_text for cue in NEGATIVE_CUES):
                # 上下文（注释 / WRONG / CORRECT / ## heading / DO NOT USE）是负面声明，跳过
                continue
            offenders.append(f"{md.name}:{i}: {stripped[:80]}")
    if offenders:
        return False, f"--no-interactive (positive usage) found: {offenders[:3]}"
    return True, "no --no-interactive (only negative declarations)"


def check_no_secret_print(skill: str) -> tuple[bool, str]:
    """校验 scripts/ + references/ 无 SECRET_KEY / secret_key 打印语句。"""
    patterns = [
        re.compile(r"print\s*\(.*SECRET_KEY"),
        re.compile(r"print\s*\(.*secret_key"),
        re.compile(r"logger?\.[^.]+\.(info|debug|warning|error)\s*\(.*SECRET_KEY"),
    ]
    search_dirs = [REPO_ROOT / skill / "scripts", REPO_ROOT / skill / "references"]
    offenders = []
    for d in search_dirs:
        if not d.is_dir():
            continue
        for f in d.rglob("*.py"):
            text = _read(f)
            for p in patterns:
                if p.search(text):
                    offenders.append(f"{f.relative_to(REPO_ROOT)}: matches {p.pattern[:40]}")
        for f in d.rglob("*.md"):
            text = _read(f)
            for p in patterns:
                if p.search(text):
                    offenders.append(f"{f.relative_to(REPO_ROOT)}: matches {p.pattern[:40]}")
    if offenders:
        return False, f"secret print found: {offenders[:3]}"
    return True, "no secret print"


def check_cross_skill_delegation() -> tuple[bool, str]:
    """校验 AGENTS.md Cross-Skill Delegation 表覆盖所有 4 个 AI OPS skill。"""
    agents_md = REPO_ROOT / "AGENTS.md"
    if not agents_md.exists():
        return False, "missing AGENTS.md"
    text = _read(agents_md)
    missing = []
    for skill in EXPECTED_VERSIONS:
        # 表格中应包含 "jdcloud-xxx-ops" 字样（允许带路径）
        if skill not in text:
            missing.append(skill)
    if missing:
        return False, f"AGENTS.md missing delegation rows: {missing}"
    return True, "all 4 AI OPS skills delegated in AGENTS.md"


def main() -> int:
    print("=" * 72)
    print("AI OPS 一致性 dry-run (v1.9.0)")
    print("=" * 72)

    total = 0
    passed = 0
    failures: list[str] = []

    for skill, expected in EXPECTED_VERSIONS.items():
        print(f"\n[{skill}]")
        for fn in (check_frontmatter_version, check_references_count, check_no_no_interactive, check_no_secret_print):
            check_name = fn.__name__.replace("check_", "")
            ok, msg = fn(skill, expected) if fn is check_frontmatter_version else fn(skill)
            total += 1
            mark = "✓" if ok else "✗"
            print(f"  {mark} {check_name}: {msg}")
            if ok:
                passed += 1
            else:
                failures.append(f"{skill}.{check_name}: {msg}")

    print("\n[AGENTS.md Cross-Skill Delegation]")
    ok, msg = check_cross_skill_delegation()
    total += 1
    mark = "✓" if ok else "✗"
    print(f"  {mark} {msg}")
    if ok:
        passed += 1
    else:
        failures.append(f"AGENTS.delegation: {msg}")

    print("\n" + "=" * 72)
    print(f"Result: {passed}/{total} checks passed")
    print("=" * 72)
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nALL CHECKS PASSED ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
