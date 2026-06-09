# Integration

## Environment Setup (uv)

The JD Cloud Python SDK requires a Python runtime. Use **`uv`** for local, isolated, and **idempotent** environment management:

### Quick Start (Command-based)

**Bootstrap (idempotent — safe to re-run):**
```bash
uv venv --python 3.10

# Activate: macOS/Linux
source .venv/bin/activate
# Activate: Windows
# .venv\Scripts\activate

uv pip install jdcloud_sdk>=1.6.26
```

**Pin versions for reproducibility (optional):**
```bash
uv pip install jdcloud_sdk==1.6.26
```
> Replace version numbers with the latest stable releases verified against JCQ's OpenAPI.

### Advanced: Project-based Setup (Recommended for Teams)

For reproducible, version-locked environments, use `pyproject.toml` with `uv sync`:

**1. Create `pyproject.toml`:**
```toml
[project]
name = "jdcloud-jcq-ops"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "jdcloud_sdk>=1.6.0",
]

[tool.uv]
python-version = "3.10"
```

**2. Sync environment (idempotent):**
```bash
uv sync
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.jcq.client.JcqClient import JcqClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"],
)
client = JcqClient(credential, endpoint="jcq.jdcloud-api.com")
```

> Use `os.environ['KEY']` for secrets (fail-fast). Use `.get` only for optional non-secret config.

## Endpoint Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Endpoint | `jcq.jdcloud-api.com` | JCQ API endpoint |
| Scheme | `https` | Always use HTTPS |
| Timeout | `20` seconds | Default; increase for large message operations |
| Region | `cn-north-1` | Default region; adjust per deployment |

## Authentication

JCQ SDK uses the same credential system as all JD Cloud services:

- **Access Key:** `JDC_ACCESS_KEY` environment variable
- **Secret Key:** `JDC_SECRET_KEY` environment variable
- **Region:** `JDC_REGION` environment variable (optional, can be passed per-request)

Credentials are resolved at runtime — never hardcode in source files.

## IAM Permissions for JCQ

Minimum IAM policy for JCQ operations:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "jcq:CreateTopic",
        "jcq:DescribeTopics",
        "jcq:DeleteTopic",
        "jcq:CreateConsumerGroup",
        "jcq:DescribeConsumerGroups",
        "jcq:DeleteConsumerGroup",
        "jcq:SendMessage",
        "jcq:ReceiveMessage",
        "jcq:DescribeMessages"
      ],
      "Resource": "*"
    }
  ]
}
```

For production, scope `Resource` to specific topics and consumer groups instead of `*`.

## Network Requirements

- Outbound HTTPS (port 443) to `jcq.jdcloud-api.com`
- No inbound requirements
- VPC endpoints are not required but can be used for private network access

## SDK Version Compatibility

| SDK Version | JCQ API Version | Notes |
|-------------|-----------------|-------|
| >= 1.6.26 | v1 | Recommended minimum |

Always verify the latest SDK version against the official JD Cloud documentation.

## No CLI Support

JCQ is **NOT** supported by the `jdc` CLI. All operations must use:

1. Python SDK (`jdcloud_sdk.services.jcq`)
2. Direct HTTP API calls (fallback after 3 SDK failures)

Do not attempt `jdc jcq ...` commands — they will fail with "unknown product group".
