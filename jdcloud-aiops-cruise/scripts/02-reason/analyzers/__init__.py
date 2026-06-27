"""
jdcloud-aiops-cruise / analyzers / __init__.py
=============================================
Analyzer registry. Auto-imports all registered analyzers.
"""

import sys
from pathlib import Path

# analyzers/ is at scripts/02-reason/analyzers/, so scripts/ root is three levels up
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

_A = {}

def register(name: str, cls):
    _A[name] = cls

def get(name: str):
    return _A.get(name)

def list_available():
    return list(_A.keys())

def create_all() -> list:
    """Import all analyzer modules and create instances."""
    # Explicit imports to trigger register() calls
    # noqa: F401 — side-effect imports trigger register()
    from analyzers import vm_analyzer  # noqa: F401
    from analyzers import redis_analyzer  # noqa: F401
    from analyzers import rds_mysql_analyzer  # noqa: F401
    from analyzers import rds_postgresql_analyzer  # noqa: F401
    from analyzers import clb_analyzer  # noqa: F401
    from analyzers import eip_analyzer  # noqa: F401
    from analyzers import k8s_analyzer  # noqa: F401
    from analyzers import sg_analyzer  # noqa: F401
    from analyzers import nat_analyzer  # noqa: F401
    from analyzers import es_analyzer  # noqa: F401
    from analyzers import mongodb_analyzer  # noqa: F401
    return [cls() for cls in _A.values()]
