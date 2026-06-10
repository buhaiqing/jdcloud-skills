# Integration

## Environment Setup (uv)

JD Cloud Python SDK requires a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

### Quick Start (Command-based)

**Bootstrap (idempotent — safe to re-run):**
```bash
uv venv --python 3.10

# Activate: macOS/Linux
source .venv/bin/activate
# Activate: Windows
# .venv\Scripts\activate

uv pip install jdcloud_sdk
```

**Pin versions for reproducibility (optional):**
```bash
uv pip install jdcloud_sdk==1.6.26
```

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-billing-ops"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_sdk>=1.6.0",
]

[tool.uv]
python-version = "3.10"
```

**2. Sync environment (idempotent):**
```bash
uv sync
source .venv/bin/activate
```

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.asset.client.AssetClient import AssetClient
from jdcloud_sdk.services.asset.apis.DescribeAccountAmountRequest import (
    DescribeAccountAmountRequest,
    DescribeAccountAmountParameters,
)

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
region = os.environ.get("JDC_REGION", "cn-north-1")
client = AssetClient(credential)

# Test connection — query account balance
params = DescribeAccountAmountParameters(regionId=region)
req = DescribeAccountAmountRequest(parameters=params)
resp = client.send(req)
print(f"Account balance: {resp.result.totalAmount}")
```

## Integration with Other Skills

### With `jdcloud-routines-ops`

When `routines-ops` discovers expiring resources with `--with-price` flag:

```python
# routines-ops calls billing APIs for price inquiry
# This is handled internally by routines-ops using shared lib/

# For standalone billing analysis, use this skill directly
```

### With `jdcloud-arch-advisor`

Cost optimization recommendations from `arch-advisor` may trigger billing queries:

```python
# arch-advisor suggests: "Consider reserved instances for long-term VMs"
# billing-ops provides: "Current on-demand cost vs reserved cost comparison"
```

## Output Format

All billing queries produce standardized output:

```json
{
  "query_time": "2026-06-10T12:00:00Z",
  "query_type": "account_balance",
  "result": {
    "balance": "1234.56",
    "currency": "CNY"
  }
}
```
