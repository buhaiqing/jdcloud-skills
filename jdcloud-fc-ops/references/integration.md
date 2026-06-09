# Integration

## Environment Setup (uv)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
```

## Python SDK Bootstrap

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.function.client import FunctionClient

credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)
client = FunctionClient(credential, os.environ.get("JDC_REGION", "cn-north-1"))
```

## Integration with Other Skills

### With API Gateway (`jdcloud-apigateway-ops`)
```python
# 1. Create function (this skill)
# 2. Create HTTP trigger (this skill)
# 3. Configure API Gateway route to function URL (jdcloud-apigateway-ops)
```

### With OSS (`jdcloud-oss-ops`)
```python
# 1. Create OSS bucket notification (jdcloud-oss-ops)
# 2. Create OSS trigger on function (this skill)
# 3. Function processes uploaded files
```

### With CloudMonitor (`jdcloud-cloudmonitor-ops`)
```python
# Set up alarms on:
# - Function error rate
# - Average duration
# - Throttling count
# - Concurrent executions
```
