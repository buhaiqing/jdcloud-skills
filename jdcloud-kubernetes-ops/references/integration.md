# Integration — JD Cloud JCS for Kubernetes

> **⚠️ Security Warning:** **NEVER** log, print, or expose `JDC_SECRET_KEY` in console output, debug messages, or logs. When verification is needed, check existence only without printing the actual value. Use masked placeholders like `<masked>` or `***` for credential status logging.

## SDK Version Locking

### Recommended Versions

| Package | Version | Notes |
|---------|---------|-------|
| jdcloud_cli | 1.2.12 | CLI for Kubernetes operations (under `nc` subcommand) |
| jdcloud_sdk | >=1.6.26 | SDK fallback for CLI failures |

### Install Locked Versions

```bash
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk>=1.6.26
```

### Version Compatibility

| SDK Version | CLI Version | Python | K8s API | Status |
|-------------|-------------|--------|---------|--------|
| >=1.6.26 | 1.2.12 | 3.10+ | JCS K8s API v1 | ✅ Tested |

## Environment Setup (uv)

> **Python 3.10 is REQUIRED, NOT 3.12.** `jdcloud_cli==1.2.12` uses `SafeConfigParser` which was removed in Python 3.12. Always use `uv venv --python 3.10`. If Python 3.10 is unavailable, install it via `brew install python@3.10` (macOS) or `uv python install 3.10`.

### Quick Start (Command-based)

**Bootstrap (idempotent — safe to re-run):**
```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
```

### Project-based Setup

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-kubernetes-ops"
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
from jdcloud_sdk.services.nc.client.NcClient import NcClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = NcClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
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
endpoint = nc.jdcloud-api.com
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
endpoint = nc.jdcloud-api.com
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
| JDC_ENDPOINT | API endpoint | nc.jdcloud-api.com |
| JDC_SCHEME | Protocol | https |
| JDC_TIMEOUT | Request timeout (seconds) | 20 |

## CI/CD Integration

### GitHub Actions Example

```yaml
name: K8s Cluster Management

on:
  workflow_dispatch:
    inputs:
      cluster_name:
        description: 'Cluster name'
        required: true

jobs:
  manage-cluster:
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
          endpoint = nc.jdcloud-api.com
          scheme = https
          timeout = 20
          EOF
          printf "%s" "default" > ~/.jdc/current

      - name: Describe Cluster
        run: |
          jdc --output json nc describe-clusters --region-id cn-north-1
```

## jdcloud-aiops-cruise Integration

Before destructive operations (especially `delete-cluster`), this skill integrates with `jdcloud-aiops-cruise` for workload analysis via `k8s_analyzer.py`:

- `check_workloads(cluster_id)` — returns running deployments, services, and pods for a cluster
- `check_namespaces(cluster_id)` — returns active namespaces
- `analyze_delete_impact(cluster_id)` — analyzes blast radius of cluster deletion

**Pre-delete safety gate:** Before deleting any cluster, the Agent MUST invoke `k8s_analyzer.py` (if available) or use `jdc describe-cluster` / `kubectl get all` (via SSH to master or Cloud Shell) to verify the cluster has zero running workloads. If workloads exist, MUST warn the user and obtain explicit confirmation.

## Testing Your Setup

```bash
# SDK verification
python -c "
import jdcloud_sdk
print(f'SDK Version: {jdcloud_sdk.__version__}')
from jdcloud_sdk.services.nc.client.NcClient import NcClient
print('NC Client imported successfully')
"

# CLI verification
jdc --version
jdc --output json nc describe-clusters --region-id cn-north-1 --page-number 1 --page-size 1
```