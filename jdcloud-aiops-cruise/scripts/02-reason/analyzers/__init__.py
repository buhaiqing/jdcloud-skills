"""
jdcloud-aiops-cruise / analyzers / __init__.py
=============================================
Analyzer registry. Auto-imports all registered analyzers.
"""

import sys
from pathlib import Path

# Ensure scripts/ is in path for all analyzer submodules
# analyzers/ is at scripts/02-reason/analyzers/, so project root is two levels up
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import path_setup

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
    from analyzers import vm_analyzer
    from analyzers import redis_analyzer
    from analyzers import rds_mysql_analyzer
    from analyzers import rds_postgresql_analyzer
    from analyzers import clb_analyzer
    from analyzers import eip_analyzer
    from analyzers import k8s_analyzer
    from analyzers import sg_analyzer
    from analyzers import nat_analyzer
    from analyzers import es_analyzer
    from analyzers import mongodb_analyzer
    return [cls() for cls in _A.values()]
