# Integration - JD Cloud Elasticsearch

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
name = "jdcloud-es-ops"
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

### Basic Setup

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = EsClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

### Advanced: Multi-Region Client

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient

class ElasticsearchMultiRegionClient:
    def __init__(self):
        self.credential = Credential(
            os.environ["JDC_ACCESS_KEY"],
            os.environ["JDC_SECRET_KEY"]
        )
        self.clients = {}
    
    def get_client(self, region):
        if region not in self.clients:
            self.clients[region] = EsClient(self.credential, region)
        return self.clients[region]

# Usage
mgr = ElasticsearchMultiRegionClient()
cn_north_client = mgr.get_client("cn-north-1")
cn_east_client = mgr.get_client("cn-east-2")
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Elasticsearch Operations

on:
  workflow_dispatch:
    inputs:
      region:
        description: 'Target region'
        required: true
        default: 'cn-north-1'

jobs:
  es-ops:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Setup Python
        run: |
          uv venv --python 3.10
          source .venv/bin/activate
          uv pip install jdcloud_sdk
      
      - name: Run ES Operations
        env:
          JDC_ACCESS_KEY: ${{ secrets.JDC_ACCESS_KEY }}
          JDC_SECRET_KEY: ${{ secrets.JDC_SECRET_KEY }}
        run: |
          source .venv/bin/activate
          python scripts/es_operations.py --region ${{ github.event.inputs.region }}
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        JDC_ACCESS_KEY = credentials('jdc-access-key')
        JDC_SECRET_KEY = credentials('jdc-secret-key')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.cargo/bin:$PATH"
                    uv venv --python 3.10
                    source .venv/bin/activate
                    uv pip install jdcloud_sdk
                '''
            }
        }
        
        stage('ES Operations') {
            steps {
                sh '''
                    source .venv/bin/activate
                    python scripts/es_operations.py
                '''
            }
        }
    }
}
```

## Application Integration

### Django Integration

```python
# settings.py
import os

JD_CLOUD_ES_CONFIG = {
    'access_key': os.environ['JDC_ACCESS_KEY'],
    'secret_key': os.environ['JDC_SECRET_KEY'],
    'region': os.environ.get('JDC_REGION', 'cn-north-1'),
    'instance_id': os.environ.get('ES_INSTANCE_ID'),
}

# es_client.py
from django.conf import settings
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient

def get_es_client():
    config = settings.JD_CLOUD_ES_CONFIG
    credential = Credential(config['access_key'], config['secret_key'])
    return EsClient(credential, config['region'])
```

### Flask Integration

```python
# extensions.py
from flask import current_app
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient

class ElasticsearchClient:
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        credential = Credential(
            app.config['JDC_ACCESS_KEY'],
            app.config['JDC_SECRET_KEY']
        )
        self.client = EsClient(
            credential,
            app.config.get('JDC_REGION', 'cn-north-1')
        )
    
    def __getattr__(self, name):
        return getattr(self.client, name)

es = ElasticsearchClient()

# app.py
from flask import Flask
from extensions import es

app = Flask(__name__)
app.config.from_envvar('APP_CONFIG')
es.init_app(app)
```

## Terraform Integration

```hcl
# main.tf
terraform {
  required_providers {
    jdcloud = {
      source  = "jdcloud/jdcloud"
      version = "~> 1.0"
    }
  }
}

provider "jdcloud" {
  access_key = var.jdc_access_key
  secret_key = var.jdc_secret_key
  region     = var.region
}

resource "jdcloud_elasticsearch_instance" "example" {
  instance_name = "tf-es-cluster"
  instance_class = "es.n1.small"
  version       = "7.10.0"
  vpc_id        = var.vpc_id
  subnet_id     = var.subnet_id
  az_id         = var.az_id
  
  data_node {
    node_amount  = 3
    node_class   = "es.n1.small"
    node_disk_type = "cloud_ssd"
    node_disk_size = 100
  }
  
  master_node {
    node_amount = 3
    node_class  = "es.n1.small"
  }
  
  kibana_node {
    node_class = "es.n1.small"
  }
}
```

## Monitoring Integration

### Prometheus Exporter

```python
from prometheus_client import Gauge, start_http_server
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import (
    DescribeInstancesRequest, DescribeInstancesParameters
)
import time
import os

# Metrics
cpu_gauge = Gauge('es_cpu_usage', 'CPU usage', ['instance_id', 'region'])
memory_gauge = Gauge('es_memory_usage', 'Memory usage', ['instance_id', 'region'])
disk_gauge = Gauge('es_disk_usage', 'Disk usage', ['instance_id', 'region'])

class ESMetricsExporter:
    def __init__(self):
        credential = Credential(
            os.environ["JDC_ACCESS_KEY"],
            os.environ["JDC_SECRET_KEY"]
        )
        self.client = EsClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
    
    def collect(self):
        params = DescribeInstancesParameters(regionId=os.environ.get("JDC_REGION", "cn-north-1"))
        params.setPageNumber(1)
        params.setPageSize(100)
        req = DescribeInstancesRequest(parameters=params)
        resp = self.client.send(req)
        
        for instance in resp.result.get("instances", []):
            labels = {
                'instance_id': instance['instanceId'],
                'region': os.environ.get("JDC_REGION", "cn-north-1")
            }
            # Update metrics (actual metric collection would use CloudMonitor API)
            cpu_gauge.labels(**labels).set(0)  # Placeholder

if __name__ == '__main__':
    start_http_server(8000)
    exporter = ESMetricsExporter()
    while True:
        exporter.collect()
        time.sleep(60)
```

## Log Integration

### Fluentd Configuration

```xml
<source>
  @type elasticsearch
  host ${ES_ENDPOINT}
  port 9200
  user ${ES_USERNAME}
  password ${ES_PASSWORD}
  index_name fluentd
  type_name _doc
</source>

<match **>
  @type elasticsearch
  host ${ES_ENDPOINT}
  port 9200
  user ${ES_USERNAME}
  password ${ES_PASSWORD}
  index_name logs-%Y.%m.%d
  type_name _doc
</match>
```

### Logstash Configuration

```ruby
output {
  elasticsearch {
    hosts => ["${ES_ENDPOINT}:9200"]
    user => "${ES_USERNAME}"
    password => "${ES_PASSWORD}"
    index => "logs-%{+YYYY.MM.dd}"
  }
}
```
