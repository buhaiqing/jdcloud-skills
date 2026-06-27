#!/usr/bin/env python3
"""Compatibility wrapper for historical docs/commands.

The Phase 2 implementation was renamed to cruise_analyze.py. Keep this wrapper
read-only and side-effect equivalent to invoking cruise_analyze.py directly.
Deprecated: use `python cruise_analyze.py` instead.
"""

import warnings

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cruise_analyze import main

warnings.warn(
    "cruise_link.py is deprecated; use cruise_analyze.py instead",
    DeprecationWarning,
    stacklevel=2,
)

if __name__ == "__main__":
    main()
