"""Root-level pytest configuration.

Adds each skill directory to sys.path so that tests using
  `from scripts.lib.<module> import ...`
can resolve imports correctly, regardless of --import-mode setting.
"""
import sys
from pathlib import Path

repo_root = Path(__file__).parent

for skill_dir in sorted(repo_root.glob("jdcloud-*")):
    if not skill_dir.is_dir():
        continue
    skill_path = str(skill_dir)
    if skill_path not in sys.path:
        sys.path.insert(0, skill_path)
