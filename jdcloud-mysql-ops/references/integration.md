# Integration - JD Cloud RDS MySQL

## Environment Setup (uv)

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

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
> Replace version numbers with the latest stable releases verified against the product's OpenAPI.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-mysql-ops"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_cli>=1.2.0",
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

**Benefits:**
- **Fully idempotent**: `uv sync` always produces the same environment
- **Lock file**: `uv.lock` pins exact versions for reproducibility
- **Team consistency**: All developers use identical dependencies
- **CI/CD ready**: `uv sync` works identically in pipelines

## Python SDK bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.rds.client.RdsClient import RdsClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = RdsClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## Environment Variables

### Required
- `JDC_ACCESS_KEY`: JD Cloud access key
- `JDC_SECRET_KEY`: JD Cloud secret key

### Optional
- `JDC_REGION`: Default region (default: `cn-north-1`)

### Example `.env` file

```ini
# JD Cloud credentials
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```

> **Security:** Never commit `.env` files to version control. Add `.env` to `.gitignore`.

## Multi-cloud Configuration

When integrating with other cloud providers, use namespace prefixes:

```ini
# JD Cloud
JDC_ACCESS_KEY=...
JDC_SECRET_KEY=...
JDC_REGION=cn-north-1

# Aliyun
ALIYUN_ACCESS_KEY_ID=...
ALIYUN_ACCESS_KEY_SECRET=...
ALIYUN_REGION=cn-hangzhou

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: JD Cloud MySQL Ops

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        version: "latest"
    
    - name: Set up Python
      run: uv venv --python 3.10
    
    - name: Install dependencies
      run: |
        source .venv/bin/activate
        uv pip install jdcloud_cli jdcloud_sdk
    
    - name: Configure jdc credentials
      run: |
        export HOME=/tmp/jdc-home
        mkdir -p /tmp/jdc-home/.jdc
        cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
        [default]
        access_key = ${{ secrets.JDC_ACCESS_KEY }}
        secret_key = ${{ secrets.JDC_SECRET_KEY }}
        region_id = cn-north-1
        endpoint = rds.jdcloud-api.com
        scheme = https
        timeout = 20
        CONFIGEOF
        printf "%s" "default" > /tmp/jdc-home/.jdc/current
    
    - name: Run MySQL operations
      run: |
        export HOME=/tmp/jdc-home
        jdc --output json rds describe-instances --region-id cn-north-1
```

### GitLab CI Example

```yaml
stages:
  - deploy

deploy:
  stage: deploy
  image: python:3.10-slim
  before_script:
    - apt-get update && apt-get install -y curl
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - uv venv --python 3.10
    - source .venv/bin/activate
    - uv pip install jdcloud_cli jdcloud_sdk
    - export HOME=/tmp/jdc-home
    - mkdir -p /tmp/jdc-home/.jdc
    - echo "[default]" > /tmp/jdc-home/.jdc/config
    - echo "access_key = $JDC_ACCESS_KEY" >> /tmp/jdc-home/.jdc/config
    - echo "secret_key = $JDC_SECRET_KEY" >> /tmp/jdc-home/.jdc/config
    - echo "region_id = cn-north-1" >> /tmp/jdc-home/.jdc/config
    - echo "endpoint = rds.jdcloud-api.com" >> /tmp/jdc-home/.jdc/config
    - echo "scheme = https" >> /tmp/jdc-home/.jdc/config
    - echo "timeout = 20" >> /tmp/jdc-home/.jdc/config
    - printf "%s" "default" > /tmp/jdc-home/.jdc/current
  script:
    - jdc --output json rds describe-instances --region-id cn-north-1
  variables:
    JDC_ACCESS_KEY: $JDC_ACCESS_KEY
    JDC_SECRET_KEY: $JDC_SECRET_KEY
```