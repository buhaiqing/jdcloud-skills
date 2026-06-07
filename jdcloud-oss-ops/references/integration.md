# Integration — JD Cloud Object Storage Service (OSS)

> **Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` in console output, debug messages, or logs. When verification is needed, check existence only without printing the actual value. Use masked placeholders like `<masked>` or `***` for credential status logging.

## SDK Version Locking

> **Recommended**: Use locked SDK versions for reproducible environments.

### Recommended Versions

| Package | Version | Notes |
|---------|---------|-------|
| jdcloud_sdk | >=1.6.26 | SDK for OSS operations (requires `oss` module) |

### Install Locked Versions

```bash
# Using uv (recommended)
uv pip install jdcloud_sdk>=1.6.26

# Or using pip
pip install jdcloud_sdk>=1.6.26
```

### Verify Installation

```bash
python -c "
import jdcloud_sdk
from jdcloud_sdk.services.oss.client.OssClient import OssClient
print(f'SDK version: {jdcloud_sdk.__version__}')
print('OSS client imported successfully')
"
```

## Environment Setup (uv)

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

The JD Cloud Python SDK requires a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

### Quick Start (Command-based)

**Bootstrap (idempotent -- safe to re-run):**
```bash
uv venv --python 3.10

# Activate: macOS/Linux
source .venv/bin/activate
# Activate: Windows
# .venv\Scripts\activate

uv pip install jdcloud_sdk
```

**Pin version for reproducibility (optional):**
```bash
uv pip install jdcloud_sdk==1.6.26
```

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-oss-ops"
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
# Creates .venv and installs all dependencies in one command
uv sync

# Activate
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.oss.client.OssClient import OssClient

# Initialize credential
credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)

# Initialize OSS client (SDK-only -- no jdc CLI for OSS)
client = OssClient(credential, endpoint="oss.jdcloud-api.com")
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| JDC_ACCESS_KEY | JD Cloud access key | ak-xxx |
| JDC_SECRET_KEY | JD Cloud secret key | sk-xxx |
| JDC_REGION | Default region | cn-north-1 |

## CI/CD Integration

### GitHub Actions Example

```yaml
name: OSS Deployment

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup uv
        uses: astral-sh/setup-uv@v1
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          uv pip install jdcloud_sdk

      - name: Configure credentials
        env:
          JDC_ACCESS_KEY: ${{ secrets.JDC_ACCESS_KEY }}
          JDC_SECRET_KEY: ${{ secrets.JDC_SECRET_KEY }}
          JDC_REGION: cn-north-1
        run: |
          python -c "
          import os
          from jdcloud_sdk.core.credential import Credential
          cred = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
          print('Credentials OK')
          "

      - name: Verify OSS setup
        run: |
          source .venv/bin/activate
          python -c "
          import os
          from jdcloud_sdk.core.credential import Credential
          from jdcloud_sdk.services.oss.client.OssClient import OssClient
          from jdcloud_sdk.services.oss.apis.ListBucketsRequest import ListBucketsRequest, ListBucketsParameters
          cred = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
          client = OssClient(cred, endpoint='oss.jdcloud-api.com')
          params = ListBucketsParameters()
          req = ListBucketsRequest(parameters=params)
          resp = client.send(req)
          print(f'Buckets: {len(resp.result.get(\"buckets\", []))}')
          "
```

## Testing Your Setup

### Verify SDK Installation

```python
import jdcloud_sdk
print(f"SDK Version: {jdcloud_sdk.__version__}")

from jdcloud_sdk.services.oss.client.OssClient import OssClient
print("OSS Client imported successfully")
```

### Verify Credentials

```bash
python -c "
import os
from jdcloud_sdk.core.credential import Credential
cred = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
print('Credentials OK')
"
```

## Troubleshooting Integration Issues

### uv Installation Fails

```bash
# Check Python version (3.10+ required)
python3 --version

# Alternative: use pip
pip install jdcloud_sdk
```

### SDK Import Errors

```bash
# Verify virtual environment is activated
which python
source .venv/bin/activate

# Reinstall SDK
uv pip install --force-reinstall jdcloud_sdk
```