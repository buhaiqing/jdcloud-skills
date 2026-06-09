# Integration — JD Cloud VPN

## Environment Setup (uv)

`jdc` CLI and JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

### Quick Start (Command-based)

**Bootstrap (idempotent — safe to re-run):**
```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

**Pin versions for reproducibility:**
```bash
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk==1.6.26
```

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-vpn-ops"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_cli>=1.2.0",
    "jdcloud_sdk>=1.6.0",
]

[tool.uv]
python-version = "3.10"
```

**2. Sync environment:**
```bash
uv sync
source .venv/bin/activate
```

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpn.client.VpnClient import VpnClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = VpnClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## Endpoint and Region

| Item | Value |
|------|-------|
| Service Endpoint | `vpn.jdcloud-api.com` |
| Scheme | `https` |
| Default Region | `cn-north-1` |

## Authentication

- **SDK**: Reads `JDC_ACCESS_KEY` and `JDC_SECRET_KEY` from environment variables.
- **CLI**: Reads credentials **only** from `~/.jdc/config` INI file.

## SDK-only Operations

As of `jdcloud_sdk>=1.6.26`, the VPN service module exposes:
- `jdcloud_sdk.services.vpn.client.VpnClient`
- All request/parameter classes under `jdcloud_sdk.services.vpn.apis`

Verify available classes:
```python
import jdcloud_sdk.services.vpn.apis as vpn_apis
print([x for x in dir(vpn_apis) if not x.startswith('_')])
```