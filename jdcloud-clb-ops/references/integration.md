# Integration — JD Cloud Load Balancer (CLB)

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
uv pip install jdcloud_cli==1.2.30 jdcloud_sdk==1.6.26
```
> Replace version numbers with the latest stable releases verified against CLB OpenAPI.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-clb-ops"
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

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.lb.client.LbClient import LbClient

# Initialize credential
credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)

# Initialize client
client = LbClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## jdc CLI Setup

### Configuration File

Create `~/.jdc/config` (or in sandbox: `/tmp/jdc-home/.jdc/config`):

```ini
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = lb.jdcloud-api.com
scheme = https
timeout = 20
```

Create `~/.jdc/current`:
```bash
printf "%s" "default" > ~/.jdc/current
```

### Sandbox Setup Script

```bash
#!/bin/bash
# setup-jdc-sandbox.sh

export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc

cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = ${JDC_ACCESS_KEY}
secret_key = ${JDC_SECRET_KEY}
region_id = ${JDC_REGION:-cn-north-1}
endpoint = lb.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF

printf "%s" "default" > /tmp/jdc-home/.jdc/current

echo "jdc CLI configured for sandbox environment"
jdc --version
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| JDC_ACCESS_KEY | JD Cloud access key | ak-xxx |
| JDC_SECRET_KEY | JD Cloud secret key | sk-xxx |
| JDC_REGION | Default region | cn-north-1 |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| JDC_ENDPOINT | API endpoint | lb.jdcloud-api.com |
| JDC_SCHEME | Protocol | https |
| JDC_TIMEOUT | Request timeout (seconds) | 20 |

## Multi-Cloud Environment Setup

When working with multiple cloud providers, use prefixed environment variables:

```ini
# .env file
# JD Cloud
JDC_ACCESS_KEY=your_jdcloud_access_key
JDC_SECRET_KEY=your_jdcloud_secret_key
JDC_REGION=cn-north-1

# Aliyun
ALIYUN_ACCESS_KEY_ID=your_aliyun_access_key
ALIYUN_ACCESS_KEY_SECRET=your_aliyun_secret_key
ALIYUN_REGION=cn-hangzhou

# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: CLB Deployment

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
          uv pip install jdcloud_cli jdcloud_sdk
      
      - name: Configure jdc CLI
        env:
          JDC_ACCESS_KEY: ${{ secrets.JDC_ACCESS_KEY }}
          JDC_SECRET_KEY: ${{ secrets.JDC_SECRET_KEY }}
          JDC_REGION: cn-north-1
        run: |
          mkdir -p ~/.jdc
          cat > ~/.jdc/config << EOF
          [default]
          access_key = $JDC_ACCESS_KEY
          secret_key = $JDC_SECRET_KEY
          region_id = $JDC_REGION
          endpoint = lb.jdcloud-api.com
          scheme = https
          timeout = 20
          EOF
          printf "%s" "default" > ~/.jdc/current
      
      - name: Deploy CLB
        run: |
          source .venv/bin/activate
          jdc --output json lb describe-load-balancers --region-id cn-north-1
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        JDC_ACCESS_KEY = credentials('jdcloud-access-key')
        JDC_SECRET_KEY = credentials('jdcloud-secret-key')
        JDC_REGION = 'cn-north-1'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    uv venv --python 3.10
                    source .venv/bin/activate
                    uv pip install jdcloud_cli jdcloud_sdk
                '''
            }
        }
        
        stage('Configure') {
            steps {
                sh '''
                    mkdir -p ~/.jdc
                    cat > ~/.jdc/config << EOF
[default]
access_key = ${JDC_ACCESS_KEY}
secret_key = ${JDC_SECRET_KEY}
region_id = ${JDC_REGION}
endpoint = lb.jdcloud-api.com
scheme = https
timeout = 20
EOF
                    printf "%s" "default" > ~/.jdc/current
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                sh '''
                    source .venv/bin/activate
                    jdc --output json lb describe-load-balancers --region-id ${JDC_REGION}
                '''
            }
        }
    }
}
```

## MCP (Model Context Protocol) Integration

When using this skill in an MCP context:

1. **Environment variables** are loaded from the MCP runtime environment
2. **Credentials** should be configured in the MCP server configuration
3. **Region** can be specified per-request or use default

### MCP Server Configuration Example

```json
{
  "mcpServers": {
    "jdcloud-clb": {
      "command": "uv",
      "args": ["run", "--with", "jdcloud_sdk", "python", "-m", "mcp_clb_server"],
      "env": {
        "JDC_ACCESS_KEY": "${JDC_ACCESS_KEY}",
        "JDC_SECRET_KEY": "${JDC_SECRET_KEY}",
        "JDC_REGION": "cn-north-1"
      }
    }
  }
}
```

## Testing Your Setup

### Verify SDK Installation

```python
import jdcloud_sdk
print(f"SDK Version: {jdcloud_sdk.__version__}")

from jdcloud_sdk.services.lb.client.LbClient import LbClient
print("LB Client imported successfully")
```

### Verify CLI Installation

```bash
# Check version
jdc --version

# Test connectivity
jdc --output json lb describe-load-balancers --region-id cn-north-1 --page-number 1 --page-size 1
```

### Verify Credentials

```bash
# SDK credential test
python -c "
import os
from jdcloud_sdk.core.credential import Credential
cred = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
print('Credentials OK')
"

# CLI credential test
jdc --output json lb describe-load-balancers --region-id cn-north-1
```

## Troubleshooting Integration Issues

### uv Installation Fails

```bash
# Check Python version (3.10+ required)
python3 --version

# Alternative: use pip
pip install jdcloud_cli jdcloud_sdk
```

### SDK Import Errors

```bash
# Verify virtual environment is activated
which python
source .venv/bin/activate

# Reinstall SDK
uv pip install --force-reinstall jdcloud_sdk
```

### CLI Authentication Errors

```bash
# Check config file exists
cat ~/.jdc/config

# Check current profile
cat ~/.jdc/current

# For sandbox, verify HOME is set
echo $HOME
```
