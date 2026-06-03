# Integration - JD Cloud EIP

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
uv pip install jdcloud_cli==1.2.30 jdcloud_sdk==1.6.26
```

> Replace version numbers with the latest stable releases verified against the product's OpenAPI.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-eip-ops"
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

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.eip.client.EipClient import EipClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = EipClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## Credential Management

### Environment Variables (SDK Mode)

```bash
export JDC_ACCESS_KEY="your-access-key"
export JDC_SECRET_KEY="your-secret-key"
export JDC_REGION="cn-north-1"
```

### CLI Configuration (jdc Mode)

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = your-access-key
secret_key = your-secret-key
region_id = cn-north-1
endpoint = eip.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### .env File Support

Create a `.env` file for local development:

```ini
# JD Cloud EIP credentials
JDC_ACCESS_KEY=your-access-key
JDC_SECRET_KEY=your-secret-key
JDC_REGION=cn-north-1
```

Load with Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: EIP Operations
on: [workflow_dispatch]

jobs:
  eip-operation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Setup Python environment
        run: |
          uv venv --python 3.10
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
          endpoint = eip.jdcloud-api.com
          scheme = https
          timeout = 20
          CONFIGEOF
          printf "%s" "default" > /tmp/jdc-home/.jdc/current
      
      - name: List EIPs
        run: |
          export HOME=/tmp/jdc-home
          jdc --output json eip describe-addresses --region-id cn-north-1
```

### GitLab CI Example

```yaml
eip-operation:
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
    - |
      cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
      [default]
      access_key = $JDC_ACCESS_KEY
      secret_key = $JDC_SECRET_KEY
      region_id = cn-north-1
      endpoint = eip.jdcloud-api.com
      scheme = https
      timeout = 20
      CONFIGEOF
    - printf "%s" "default" > /tmp/jdc-home/.jdc/current
  script:
    - jdc --output json eip describe-addresses --region-id cn-north-1
  only:
    - main
```

## Cross-Skill Integration

### With VM Ops

```python
# Example: Allocate EIP and associate with VM
from jdcloud_sdk.services.eip.client.EipClient import EipClient
from jdcloud_sdk.services.vm.client.VmClient import VmClient

# Allocate EIP
eip_client = EipClient(credential, region)
# ... allocate EIP ...

# Verify VM exists via jdcloud-vm-ops
vm_client = VmClient(credential, region)
# ... describe VM ...

# Associate EIP with VM
# ... associate address ...
```

### With CLB Ops

```python
# Example: Associate EIP with Load Balancer
from jdcloud_sdk.services.eip.client.EipClient import EipClient
from jdcloud_sdk.services.lb.client.LbClient import LbClient

# Verify CLB exists via jdcloud-clb-ops
lb_client = LbClient(credential, region)
# ... describe CLB ...

# Associate EIP with CLB
eip_client = EipClient(credential, region)
# ... associate address with instanceType="clb" ...
```

## Security Best Practices

1. **Least Privilege**: Use IAM policies with minimal required permissions
2. **Secret Management**: Use secure vaults (AWS Secrets Manager, HashiCorp Vault) for credentials
3. **Environment Variables**: Never hardcode credentials in code or configuration files
4. **Encryption**: Use HTTPS for all API communications (default)
5. **Audit Logs**: Enable JD Cloud CloudTrail equivalent for API activity tracking
6. **Access Rotation**: Regularly rotate access keys and secrets
7. **Network Isolation**: Use VPC security groups to restrict EIP access
