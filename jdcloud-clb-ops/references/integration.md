# Integration — JD Cloud Load Balancer (CLB)

> **ponytail: trimmed — SDK init + env vars kept. Full setup in AGENTS.md pre-flight checks.**

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JDC_ACCESS_KEY` | Yes | — | JD Cloud Access Key |
| `JDC_SECRET_KEY` | Yes | — | JD Cloud Secret Key |
| `JDC_REGION` | No | `cn-north-1` | Default region |

> **Security**: NEVER log secret keys. Check existence only.

## SDK Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.lb.client.LbClient import LbClient

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = LbClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

## SDK Version Locking

| Package | Version |
|---------|---------|
| `jdcloud_cli` | `==1.2.12` |
| `jdcloud_sdk` | `>=1.6.26` |

```bash
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk>=1.6.26
```

## jdc CLI Config (Sandbox)

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{env.JDC_REGION}}
endpoint = lb.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```