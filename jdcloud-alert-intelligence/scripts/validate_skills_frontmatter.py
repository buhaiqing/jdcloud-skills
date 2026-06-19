#!/usr/bin/env python3
"""Local CI validator wrapper for jdcloud-alert-intelligence.

Invokes the repo-level skill validator against this skill directory.
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    repo_root = skill_dir.parent  # skill -> jdcloud-skills
    validator = repo_root / "scripts" / "validate_skill.py"
    if not validator.exists():
        print(f"Repo-level validator not found: {validator}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(validator), str(skill_dir)]).returncode


if __name__ == "__main__":
    sys.exit(main())
