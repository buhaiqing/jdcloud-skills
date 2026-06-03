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
uv pip install jdcloud_cli==1.2.30 jdcloud_sdk==1.6.26
```
> Replace version numbers with the latest stable releases verified against the product's OpenAPI.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-audit-ops"
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
from jdcloud_sdk.services.audit.client.AuditClient import AuditClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = AuditClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Audit Log Compliance Check

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  audit-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup uv
        uses: astral-sh/setup-uv@v2
        with:
          python-version: "3.10"
      
      - name: Install dependencies
        run: uv pip install jdcloud_sdk
      
      - name: Run compliance check
        env:
          JDC_ACCESS_KEY: ${{ secrets.JDC_ACCESS_KEY }}
          JDC_SECRET_KEY: ${{ secrets.JDC_SECRET_KEY }}
          JDC_REGION: cn-north-1
        run: python scripts/audit_compliance_check.py
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        JDC_ACCESS_KEY = credentials('jdc-access-key')
        JDC_SECRET_KEY = credentials('jdc-secret-key')
        JDC_REGION = 'cn-north-1'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    uv venv --python 3.10
                    source .venv/bin/activate
                    uv pip install jdcloud_sdk
                '''
            }
        }
        
        stage('Audit Check') {
            steps {
                sh '''
                    source .venv/bin/activate
                    python scripts/audit_compliance_check.py
                '''
            }
        }
    }
}
```

## Integration with SIEM Systems

### Export to Elasticsearch

```python
from elasticsearch import Elasticsearch

def export_to_elasticsearch(events, es_host='localhost:9200'):
    es = Elasticsearch([es_host])
    
    for event in events:
        doc = {
            'event_id': event['eventId'],
            'timestamp': event['eventTime'],
            'user': event['username'],
            'action': event['eventName'],
            'resource_type': event['resourceType'],
            'resource_id': event['resourceId'],
            'source_ip': event['sourceIpAddress'],
            'request': event.get('requestParameters'),
            'response': event.get('responseElements')
        }
        
        es.index(index='jdcloud-audit', body=doc)
```

### Splunk Integration

```python
import requests

def export_to_splunk(events, splunk_hec_url, splunk_token):
    headers = {
        'Authorization': f'Splunk {splunk_token}',
        'Content-Type': 'application/json'
    }
    
    for event in events:
        payload = {
            'event': event,
            'sourcetype': 'jdcloud:audit',
            'index': 'security'
        }
        
        requests.post(splunk_hec_url, json=payload, headers=headers)
```

## Integration with Notification Systems

### Slack Notification

```python
import requests

def notify_slack(webhook_url, message):
    payload = {
        'text': message,
        'blocks': [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': 'Audit Alert'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': message
                }
            }
        ]
    }
    
    requests.post(webhook_url, json=payload)
```

### Email Notification

```python
import smtplib
from email.mime.text import MIMEText

def send_email_alert(smtp_server, from_addr, to_addrs, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)
    
    with smtplib.SMTP(smtp_server) as server:
        server.send_message(msg)
```

## Multi-Region Query

```python
def query_all_regions(start_time, end_time):
    """Query audit events across all regions"""
    regions = ['cn-north-1', 'cn-south-1', 'cn-east-1', 'cn-east-2']
    all_events = []
    
    for region in regions:
        client = AuditClient(credential, region)
        events = query_events(client, region, start_time, end_time)
        all_events.extend(events)
    
    return all_events
```

## Scheduled Audit Export

```python
import schedule
import time

def daily_audit_export():
    """Export yesterday's audit events"""
    yesterday = datetime.now() - timedelta(days=1)
    start_time = yesterday.strftime('%Y-%m-%dT00:00:00+08:00')
    end_time = yesterday.strftime('%Y-%m-%dT23:59:59+08:00')
    
    events = query_all_events(start_time, end_time)
    export_to_storage(events, f'audit-{yesterday.strftime("%Y%m%d")}.json')

# Schedule daily at 1 AM
schedule.every().day.at("01:00").do(daily_audit_export)

while True:
    schedule.run_pending()
    time.sleep(60)
```
