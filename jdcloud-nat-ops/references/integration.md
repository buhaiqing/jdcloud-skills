# Integration — JD Cloud NAT Gateway

## Environment Setup (uv)

`jdc` CLI and JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

### Quick Start (Command-based)

**Bootstrap (idempotent — safe to re-run):**
```bash
uv venv --python 3.10

# Activate: macOS/Linux
source .venv/bin/activate
# Activate: Windows
# .venv\Scripts\activate

uv pip install jdcloud_cli jdcloud_sdk
```

**Pin versions for reproducibility (optional):**
```bash
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk==1.6.26
```

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-nat-ops"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_cli>=1.2.12",
    "jdcloud_sdk>=1.6.26",
]

[tool.uv]
python-version = "3.10"
```

**2. Sync environment (idempotent):**
```bash
# Creates .venv and installs all dependencies in one command
uv sync

# Activate
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

### Dependencies

| Package | Min Version | Notes |
|---------|-------------|-------|
| `jdcloud_cli` | 1.2.12 | CLI for `jdc` commands |
| `jdcloud_sdk` | 1.6.26 | Python SDK for API access |

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vpc.client.VpcClient import VpcClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = VpcClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## Cross-Skill Integration

| Skill | Integration Point |
|-------|------------------|
| `jdcloud-vpc-ops` | Verify VPC/subnet existence before NAT operations |
| `jdcloud-eip-ops` | Allocate, describe, verify Elastic IPs for NAT association |
| `jdcloud-vm-ops` | Verify backend VM existence for DNAT rules |
| `jdcloud-cloudmonitor-ops` | Monitor NAT bandwidth, connection metrics, set alarms |
| `jdcloud-iam-ops` | IAM policy configuration for NAT operations |

## Network Prerequisites

Before creating a NAT gateway:
1. **VPC**: Must exist and have at least one subnet
2. **Subnet**: For SNAT, target subnet must exist and belong to the same VPC
3. **Elastic IP**: At least one EIP must be allocated in the same region
4. **Route Table**: For SNAT, subnet route table needs a `0.0.0.0/0` route pointing to the NAT gateway (created automatically or manually)