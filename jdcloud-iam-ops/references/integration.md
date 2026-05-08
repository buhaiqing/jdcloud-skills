# IAM Integration Guide

## Environment Setup (uv)

Both `jdc` CLI and JD Cloud Python SDK require a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management.

### Install uv (System-Wide)

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **Note:** Installing uv itself is a one-time system setup. Commands below are idempotent and safe to re-run.

### Quick Start (Command-based)

**Bootstrap (idempotent — safe to re-run):**
```bash
# Create virtual environment
uv venv --python 3.10

# Activate
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
uv pip install jdcloud_cli jdcloud_sdk
```

**Verify:**
```bash
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

**Pin versions for reproducibility (optional):**
```bash
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk==1.6.293
```

> Replace version numbers with latest stable releases.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`.

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-iam-ops"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_cli>=1.2.12",
    "jdcloud_sdk>=1.6.293",
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
- **Fully idempotent:** `uv sync` always produces same environment
- **Lock file:** `uv.lock` pins exact versions for reproducibility
- **Team consistency:** All developers use identical dependencies
- **CI/CD ready:** `uv sync` works identically in pipelines

## Credential Configuration

### Method A: Configure for SDK (Environment Variables)

SDK reads credentials from environment variables — no config file needed.

```bash
export JDC_ACCESS_KEY="your_access_key_here"
export JDC_SECRET_KEY="your_secret_key_here"
export JDC_REGION="cn-north-1"  # IAM is global; region may not apply
```

**.env file support (optional):**
```ini
# .env file in project root
JDC_ACCESS_KEY=your_access_key_here
JDC_SECRET_KEY=your_secret_key_here
JDC_REGION=cn-north-1
```

Load `.env` in Python (if Agent Runtime supports):
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env into os.environ
```

> **Priority:** Shell environment variables override `.env` values.

### Method B: Configure for CLI (`~/.jdc/config` INI)

**CRITICAL:** CLI reads credentials exclusively from `~/.jdc/config` (INI format), NOT from environment variables.

#### Interactive Configuration

```bash
jdc configure add
# Follow prompts to enter AK/SK and other settings
```

#### Manual Configuration (Sandbox-Safe)

For sandboxed environments where `~` is not writable:

```bash
# 1. Set HOME to writable location
export HOME=/tmp/jdc-home

# 2. Create config directory
mkdir -p /tmp/jdc-home/.jdc

# 3. Write config file
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = your_access_key_here
secret_key = your_secret_key_here
region_id = cn-north-1
endpoint = iam.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

# 4. Write current profile WITHOUT trailing newline
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

#### Verify CLI Configuration

```bash
# Run a simple IAM command
jdc --output json iam describe-sub-users --page-number 1 --page-size 10
```

If successful, configuration is valid. If error: "Please use 'jdc configure add'", configuration file is missing or malformed.

## Python SDK Bootstrap

### IAM Client

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.iam.client.IamClient import IamClient

# Load credentials
credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)

# Initialize IAM client
client = IamClient(credential)
```

### STS Client

```python
from jdcloud_sdk.services.sts.client.StsClient import StsClient

sts_client = StsClient(credential)
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## Multi-Project Mixing (Cross-Cloud Skills)

JD Cloud IAM Skills can be mixed with other cloud provider skills (e.g., Aliyun, AWS) in the same project.

**Recommended namespace prefixes:**

```ini
# .env file
# JD Cloud
JDC_ACCESS_KEY=...
JDC_SECRET_KEY=...

# Aliyun
ALIYUN_ACCESS_KEY_ID=...
ALIYUN_ACCESS_KEY_SECRET=...
ALIYUN_REGION=cn-hangzhou

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

> **Best practice:** Place `.env` in the **working directory** (cwd) for cross-project mixing.

## Security Rules

1. **Never commit `.env` files** to version control (already in `.gitignore`)
2. **Never write real credentials** into generated Skill documents
3. **Use `{{env.*}}` placeholders** in Skill content
4. **Rotate AK/SK regularly** — create new, update applications, delete old
5. **Disable old keys immediately** if compromised

## Dependency Versioning

### jdcloud_cli

- **Latest:** Check PyPI for current version: https://pypi.org/project/jdcloud-cli/
- **Recommended:** >= 1.2.12 (supports IAM subcommands)

### jdcloud_sdk

- **Latest:** Check PyPI for current version: https://pypi.org/project/jdcloud-sdk/
- **Recommended:** >= 1.6.293 (supports IAM APIs)

**Pin strategy:**
- For production: Pin exact versions (e.g., `jdcloud_sdk==1.6.293`)
- For development: Use >= constraints (e.g., `jdcloud_sdk>=1.6.293`)
- Update pins when new features are required or security fixes released

## Troubleshooting Setup Issues

### Problem: uv not found

**Fix:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

### Problem: Python 3.10 not available

**Fix:**
```bash
# Install Python via Homebrew (macOS)
brew install python@3.10

# Or use uv to install Python
uv python install 3.10
```

### Problem: jdc command not found after pip install

**Diagnosis:** Virtual environment not activated

**Fix:**
```bash
source .venv/bin/activate
jdc --version
```

### Problem: SDK import fails

**Diagnosis:** SDK not installed or wrong module path

**Fix:**
```bash
# Reinstall SDK
uv pip install jdcloud_sdk

# Verify import
python -c "from jdcloud_sdk.services.iam.client.IamClient import IamClient; print('OK')"
```

### Problem: CLI fails with PermissionError on ~/.jdc/

**Diagnosis:** Home directory not writable (sandbox)

**Fix:** Use sandbox-safe config method (see above under "Manual Configuration")

## Testing Configuration

### Quick SDK Test

```python
from jdcloud_sdk.services.iam.apis.DescribeSubUsersRequest import (
    DescribeSubUsersRequest,
    DescribeSubUsersParameters
)

params = DescribeSubUsersParameters()
params.setPageNumber(1)
params.setPageSize(1)
req = DescribeSubUsersRequest(parameters=params)
resp = client.send(req)
print(f"Total sub-users: {resp.result['totalCount']}")
```

### Quick CLI Test

```bash
jdc --output json iam describe-sub-users --page-number 1 --page-size 1
```

If both tests succeed, configuration is valid.

## See Also

- [CLI Usage](cli-usage.md) — Primary execution path
- [API & SDK Usage](api-sdk-usage.md) — Fallback execution path
- [Troubleshooting](troubleshooting.md) — Error diagnosis