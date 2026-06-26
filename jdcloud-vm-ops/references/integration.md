# JD Cloud VM Integration Reference

> **ponytail: trimmed — SKILL.md covers execution flows. Only SDK init pattern and env var reference kept.**

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JDC_ACCESS_KEY` | Yes | — | JD Cloud Access Key |
| `JDC_SECRET_KEY` | Yes | — | JD Cloud Secret Key |
| `JDC_REGION` | No | `cn-north-1` | Default region |

> **Security**: NEVER log secret keys. Check existence only: `test -n "$JDC_SECRET_KEY"`.

## SDK Initialization

### VM Client

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.vm.client import VmClient

credential = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
client = VmClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

### Disk Client (cross-skill)

```python
from jdcloud_sdk.services.disk.client import DiskClient
disk_client = DiskClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

### Cloud Assistant Client (SDK-only)

```python
from jdcloud_sdk.services.assistant.client import AssistantClient
assistant_client = AssistantClient(credential, os.environ.get('JDC_REGION', 'cn-north-1'))
```

## Error Handling Pattern

```python
from jdcloud_sdk.core.exception import ClientException, ServerException

try:
    response = client.some_operation(request)
    if response.error is not None:
        print(f"API Error: {response.error.code} - {response.error.message}")
except ClientException as e:
    print(f"Client error: {e.error_msg}")  # network / parameter issue
except ServerException as e:
    print(f"Server error: {e.error_code} - {e.error_msg}")  # retry with backoff
```

## SDK Version Locking

| Package | Version |
|---------|---------|
| `jdcloud_cli` | `==1.2.12` |
| `jdcloud_sdk` | `>=1.6.26` |

```bash
# via uv
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk>=1.6.26
```

> See [SDK Version Locking Guide](../../docs/SDK_VERSION_LOCKING.md) for detailed strategy.