"""
jdcloud-aiops-cruise / analyzers / __init__.py
=============================================
Analyzer registry. Auto-imports all registered analyzers.
"""

import sys, os

# Ensure scripts/ is in path for all analyzer submodules
# analyzers/ is at scripts/02-reason/analyzers/, so project root is two levels up
_scripts_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

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