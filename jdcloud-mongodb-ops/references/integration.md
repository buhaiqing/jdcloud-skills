# Integration

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
> Replace version numbers with the latest stable releases verified against the product's OpenAPI.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-mongodb-ops"
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
from jdcloud_sdk.services.mongodb.client.MongodbClient import MongodbClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = MongodbClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: MongoDB Operations

on:
  workflow_dispatch:
    inputs:
      operation:
        description: 'Operation to perform'
        required: true
        default: 'describe-instances'

jobs:
  mongodb-ops:
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
      
      - name: Configure credentials
        env:
          JDC_ACCESS_KEY: ${{ secrets.JDC_ACCESS_KEY }}
          JDC_SECRET_KEY: ${{ secrets.JDC_SECRET_KEY }}
        run: |
          export HOME=/tmp/jdc-home
          mkdir -p /tmp/jdc-home/.jdc
          cat > /tmp/jdc-home/.jdc/config << EOF
          [default]
          access_key = $JDC_ACCESS_KEY
          secret_key = $JDC_SECRET_KEY
          region_id = cn-north-1
          endpoint = mongodb.jdcloud-api.com
          scheme = https
          timeout = 20
          EOF
          printf "%s" "default" > /tmp/jdc-home/.jdc/current
      
      - name: Execute operation
        run: |
          source .venv/bin/activate
          export HOME=/tmp/jdc-home
          jdc --output json mongodb describe-instances --region-id cn-north-1
```

### GitLab CI Example

```yaml
mongodb-ops:
  image: python:3.10-slim
  variables:
    UV_CACHE_DIR: "$CI_PROJECT_DIR/.uv-cache"
  cache:
    paths:
      - .uv-cache/
  before_script:
    - pip install uv
    - uv venv --python 3.10
    - source .venv/bin/activate
    - uv pip install jdcloud_cli jdcloud_sdk
    - |
      export HOME=/tmp/jdc-home
      mkdir -p /tmp/jdc-home/.jdc
      cat > /tmp/jdc-home/.jdc/config << EOF
      [default]
      access_key = $JDC_ACCESS_KEY
      secret_key = $JDC_SECRET_KEY
      region_id = cn-north-1
      endpoint = mongodb.jdcloud-api.com
      scheme = https
      timeout = 20
      EOF
      printf "%s" "default" > /tmp/jdc-home/.jdc/current
  script:
    - export HOME=/tmp/jdc-home
    - jdc --output json mongodb describe-instances --region-id cn-north-1
```

## Terraform Integration

JD Cloud MongoDB can be managed via Terraform using the JD Cloud provider:

```hcl
terraform {
  required_providers {
    jdcloud = {
      source = "jdcloudlabs/jdcloud"
      version = "1.0.0"
    }
  }
}

provider "jdcloud" {
  access_key = var.jdc_access_key
  secret_key = var.jdc_secret_key
  region     = "cn-north-1"
}

resource "jdcloud_mongodb_instance" "example" {
  instance_name   = "my-mongodb"
  instance_class  = "mongodb.s1.small"
  engine_version  = "4.4"
  vpc_id          = jdcloud_vpc.example.id
  subnet_id       = jdcloud_subnet.example.id
  az_id           = "cn-north-1a"
  storage_type    = "local_ssd"
  storage_size    = 20
  username        = "admin"
  password        = var.db_password
}
```

## Ansible Integration

```yaml
---
- name: Manage JD Cloud MongoDB
  hosts: localhost
  gather_facts: false
  vars:
    jdc_access_key: "{{ lookup('env', 'JDC_ACCESS_KEY') }}"
    jdc_secret_key: "{{ lookup('env', 'JDC_SECRET_KEY') }}"
    region: "cn-north-1"
  
  tasks:
    - name: Describe MongoDB instances
      uri:
        url: "https://mongodb.jdcloud-api.com/v1/regions/{{ region }}/instances"
        method: GET
        headers:
          Authorization: "JDCLOUD2-HMAC-SHA256 ..."  # Use proper signature
        return_content: true
      register: mongodb_response
    
    - name: Debug response
      debug:
        var: mongodb_response.content
```

## SDK Error Handling Pattern

```python
from jdcloud_sdk.core.exception import ClientException, ServiceException

try:
    resp = client.send(req)
    print(f"Success: {resp.result}")
except ClientException as e:
    # Client-side error (network, config, etc.)
    print(f"Client error: {e.message}")
    raise
except ServiceException as e:
    # Service-side error (API error)
    print(f"Service error: {e.code} - {e.message}")
    if e.code == "QuotaExceeded":
        # Handle quota issue
        pass
    elif e.code == "InsufficientBalance":
        # Handle billing issue
        pass
    else:
        raise
```

## Multi-Region Deployment Pattern

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.mongodb.client.MongodbClient import MongodbClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)

# Create clients for multiple regions
regions = ["cn-north-1", "cn-south-1", "cn-east-1"]
clients = {r: MongodbClient(credential, r) for r in regions}

# List instances across all regions
for region, client in clients.items():
    print(f"\n=== Region: {region} ===")
    # ... make API calls
```
