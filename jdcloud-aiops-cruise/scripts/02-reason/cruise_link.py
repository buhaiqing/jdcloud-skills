#!/usr/bin/env python3
"""Compatibility wrapper for historical docs/commands.

The Phase 2 implementation was renamed to cruise_analyze.py. Keep this wrapper
read-only and side-effect equivalent to invoking cruise_analyze.py directly.
"""

from cruise_analyze import main


if __name__ == "__main__":
    main()
