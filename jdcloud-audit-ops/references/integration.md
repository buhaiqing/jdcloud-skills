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
# TODO: 确认官方 SDK 真实服务名（当前锁定 JD Cloud SDK 中未包含 services.audit 模块，API 调用需通过 REST API）
# from jdcloud_sdk.services.audit.client.AuditClient import AuditClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
# client = AuditClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))  # 当前模块不可用，需确认服务名
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

> **外部导出审批要求**：导出到 SIEM / Slack / Email / 对象存储前，必须完成安全审批，使用 TLS，限制收件人与索引访问权限，并设置保留期。字段展示策略参考 [Redaction Reference](redaction.md)。
>
> | 字段 | 外部导出策略 |
> |---|---|
> | `eventId` | 原样，作为证据锚点 |
> | `resourceId` | 部分 mask 或仅保留资源类型 + 后 6 位 |
> | `username` | mask/hash；仅 forensic_sealed 且审批后可关联原值 |
> | `sourceIpAddress` | `/24` mask 或 hash |
> | `userAgent` | truncate 到固定长度 |
> | `requestParameters` / `responseElements` | 必须 `mask_sensitive()` / `redact_sensitive_fields()` |

### Export to Elasticsearch

```python
from elasticsearch import Elasticsearch

def export_to_elasticsearch(events, es_host='localhost:9200'):
    """⚠️ 外部导出前必须完成脱敏，且必须经过安全审批。"""
    es = Elasticsearch([es_host])
    
    for event in events:
        # ⚠️ 脱敏：requestParameters / responseElements 中的敏感字段必须在导出前移除/替换
        # 必须脱敏字段：password, passwd, pwd, secret, secretKey, accessKeySecret, accessKey,
        # token, authorization, credential, privateKey, sessionKey, apiKey；手机号/邮箱等 PII 按策略 mask/hash
        # masked_default 会同时处理 username / sourceIpAddress / resourceId 等 PII/准标识符
        safe_event = mask_sensitive(event, mode='masked_default')
        doc = {
            'event_id': safe_event['eventId'],
            'timestamp': safe_event['eventTime'],
            'user': safe_event.get('username'),          # 外部导出：mask/hash
            'action': safe_event['eventName'],
            'resource_type': safe_event['resourceType'],
            'resource_id': safe_event.get('resourceId'), # 外部导出：部分 mask
            'source_ip': safe_event.get('sourceIpAddress'), # 外部导出：/24 mask 或 hash
            'user_agent': safe_event.get('userAgent', '')[:160],
            'request': safe_event.get('requestParameters', {}),
            'response': safe_event.get('responseElements', {})
        }
        
        es.index(index='jdcloud-audit', body=doc)
```

### Splunk Integration

```python
import requests

def export_to_splunk(events, splunk_hec_url, splunk_token):
    """⚠️ 外部导出前必须完成脱敏，且必须经过安全审批；splunk_token 只能从 Secret Manager/env 注入，禁止打印。"""
    headers = {
        'Authorization': f'Splunk {splunk_token}',
        'Content-Type': 'application/json'
    }
    
    for event in events:
        # ⚠️ 脱敏：整个 event 对象中可能含 requestParameters / responseElements、username、sourceIp、resourceId，导出前必须脱敏
        safe_event = redact_sensitive_fields(event, mode='masked_default')
        payload = {
            'event': safe_event,
            'sourcetype': 'jdcloud:audit',
            'index': 'security'
        }
        
        requests.post(splunk_hec_url, json=payload, headers=headers)
```

## Integration with Notification Systems

### Slack Notification

```python
import requests

def notify_slack(webhook_url, event_id, severity, masked_summary, evidence_link):
    """只发送 eventId / severity / masked summary / link；禁止发送完整事件或 raw message。

    webhook_url 必须来自 Secret Manager/env，发送前需确认频道 allowlist 与审批记录。
    """
    safe_message = mask_sensitive(
        f"*Audit Alert* severity={severity} eventId={event_id}\n{masked_summary}\nEvidence: {evidence_link}",
        mode='masked_default'
    )
    payload = {
        'text': safe_message,
        'blocks': [
            {'type': 'header', 'text': {'type': 'plain_text', 'text': 'Audit Alert'}},
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': safe_message}}
        ]
    }

    requests.post(webhook_url, json=payload, timeout=10)
```

### Email Notification

```python
import smtplib
from email.mime.text import MIMEText

def send_email_alert(smtp_server, from_addr, to_addrs, subject, body, allowed_recipients):
    """Email 只发送脱敏摘要；禁止发送 raw event / raw requestParameters / raw responseElements。

    要求：收件人 allowlist、TLS、审批记录、保留期策略。完整证据放受控系统，仅邮件发送链接。
    """
    unexpected = set(to_addrs) - set(allowed_recipients)
    if unexpected:
        raise ValueError(f"recipient not allowed: {sorted(unexpected)}")

    safe_body = mask_sensitive(body, mode='masked_default')
    msg = MIMEText(safe_body)
    msg['Subject'] = mask_sensitive(subject, mode='masked_default')
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)

    with smtplib.SMTP_SSL(smtp_server) as server:
        server.send_message(msg)
```

## Multi-Region Query

```python
def query_all_regions(start_time, end_time):
    """Query audit events across all regions"""
    regions = ['cn-north-1', 'cn-south-1', 'cn-east-1', 'cn-east-2']
    all_events = []
    
    for region in regions:
        # client = AuditClient(credential, region)  # 当前模块不可用，需确认服务名
        events = query_events(client, region, start_time, end_time)
        all_events.extend(events)
    
    return all_events
```

## Scheduled Audit Export

```python
import schedule
import time

def daily_audit_export():
    """Export yesterday's audit events.

    ⚠️ 展示件必须脱敏；如合规要求保存 raw archive，则必须加密、最小权限、限定保留期并记录审批。
    """
    yesterday = datetime.now() - timedelta(days=1)
    start_time = yesterday.strftime('%Y-%m-%dT00:00:00+08:00')
    end_time = yesterday.strftime('%Y-%m-%dT23:59:59+08:00')
    
    events = query_all_events(start_time, end_time)
    safe_events = redact_sensitive_fields(events, mode='masked_default')
    export_to_storage(safe_events, f'audit-{yesterday.strftime("%Y%m%d")}-masked.json')
    # 如必须保存 raw archive：export_encrypted_archive(events, kms_key_id, retention_days=30, approval_id='SEC-CHANGE-XXXX')

# Schedule daily at 1 AM
schedule.every().day.at("01:00").do(daily_audit_export)

while True:
    schedule.run_pending()
    time.sleep(60)
```
