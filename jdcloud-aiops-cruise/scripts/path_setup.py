"""
path_setup.py — Central path setup for jdcloud-aiops-cruise.

Usage in any script under scripts/:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adjust parent count
    import path_setup  # adds scripts/ to sys.path

    from lib.jdc_client import JdcClient
    from analyzers import create_all

Parent count from __file__ to scripts/:
  - 01-perceive/*.py:              parent.parent  (depth=2)
  - 02-reason/*.py:                parent.parent  (depth=2)
  - 02-reason/analyzers/*.py:      parent.parent.parent  (depth=3)
"""

import sys
from pathlib import Path

_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
