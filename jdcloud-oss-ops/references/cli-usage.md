# CLI Usage — JD Cloud Object Storage Service (OSS)

## CLI Applicability: NOT Available

**The `jdc` CLI does NOT support OSS operations.**

OSS (Object Storage Service) is managed via a dedicated REST API at `oss.jdcloud-api.com`.
The official `jdc` CLI (`jdcloud_cli==1.2.12`) does not include an `oss` product group.

### Evidence

Confirmed via:
```bash
# jdc CLI does not expose any OSS subcommand
$ jdc --help | grep -i oss
# (no output -- OSS is not listed)
```

### Alternative: Use SDK/API

All OSS operations MUST use the Python SDK (`jdcloud_sdk`) or direct HTTP API calls.
See [API & SDK Usage](api-sdk-usage.md) for the complete operations map.

### For Agent Runtimes

When asked to perform OSS operations, **do NOT attempt to run `jdc` commands** for OSS.
Use the SDK path exclusively:

```python
from jdcloud_sdk.services.oss.client.OssClient import OssClient
from jdcloud_sdk.core.credential import Credential
import os

credential = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = OssClient(credential, endpoint="oss.jdcloud-api.com")
```

### Why SDK-only?

JD Cloud OSS uses a different API architecture from products like VM, VPC, or CLB.
The OSS API follows the S3-compatible protocol pattern and is managed through
a dedicated OSS SDK module (`jdcloud_sdk.services.oss`), not the unified `jdc` CLI.