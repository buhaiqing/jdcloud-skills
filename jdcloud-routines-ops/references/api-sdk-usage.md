# API & SDK Usage — `jdcloud-routines-ops`

> This skill is **CLI-first** (`jdc --output json …`) per the repository policy
> in `AGENTS.md` ("jdc-first with SDK fallback"). SDK is only invoked when:
>
> 1. The product is not exposed via `jdc` (e.g. Elasticsearch `describeInstances`),
>    **OR**
> 2. `jdc` has failed 3 consecutive times for the same query, **OR**
> 3. The CLI cannot return the required field shape (rare).

## 1. SDK Installation

```bash
uv pip install jdcloud_sdk
```

Version pinning is recommended for reproducibility:

```bash
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk>=1.6.26
```

## 2. Credential bootstrap

The Python SDK reads credentials from **`JDC_ACCESS_KEY` / `JDC_SECRET_KEY` env vars**,
**not** from `~/.jdc/config`. To use both CLI and SDK in the same process, you must
either:

1. Source both `.env` (SDK) and `~/.jdc/config` (CLI) from the same secret, or
2. Read the INI in Python and inject into env before instantiating the SDK.

```python
import configparser, os
from pathlib import Path

cfg = configparser.ConfigParser()
cfg.read(Path.home() / ".jdc" / "config")
os.environ["JDC_ACCESS_KEY"] = cfg.get("default", "access_key")
os.environ["JDC_SECRET_KEY"] = cfg.get("default", "secret_key")
```

> ⚠️ Never print `JDC_SECRET_KEY`. Existence checks (`test -n`) and length checks
> are OK; printing the value is not.

## 3. SDK Surface Used by `expiry_cruise.py`

### 3.1 Elasticsearch fallback

The `jdc` CLI does not expose `describeInstances` for Elasticsearch cleanly. The
script uses `jdcloud_sdk.services.es.client.EsClient` directly.

```python
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import (
    DescribeInstancesRequest,
    DescribeInstancesParameters,
)

credential = Credential(ak, sk)
config = Config(endpoint="es.jdcloud-api.com")
client = EsClient(credential, config)

param = DescribeInstancesParameters(region_id)
req = DescribeInstancesRequest(param)
resp = client.send(req)

for inst in (resp.result.instances or []):
    print(inst.instance_id, inst.charge.charge_expired_time)
```

### 3.2 Why this is wrapped in stdout capture

The SDK prints log lines to stdout. `JdcClient.describe_elasticsearch` redirects
stdout to `StringIO` during the call to avoid corrupting the cruise's JSON
report. This is intentional — do not remove it.

## 4. SDK Surface Planned (1.2.0 / 1.3.0)

| Product | SDK module | Purpose |
|---|---|---|
| Kubernetes | `jdcloud_sdk.services.kubernetes` | Cluster expiry / node-group rotation audit |
| WAF | `jdcloud_sdk.services.waf` | Domain expiry / cert chain audit |
| OSS | `jdcloud_sdk.services.oss` | Bucket lifecycle / object age audit |
| Bill | `jdcloud_sdk.services.bill` | Billing analysis (planned scenario) |

> The planned **billing analysis** script (`scripts/billing_cruise.py`) will use
> `bill.describeBillSummaryByInstance` (or equivalent) via SDK only — there is
> no `jdc bill …` subcommand today.

## 5. Fallback policy

```
for attempt in (1, 2, 3):
    result = run_jdc(...)
    if result.error is None and result.result is not None:
        return parse(result.result)
    log_warn(f"jdc attempt {attempt} failed: {result.error}")
    sleep(2 ** (attempt - 1))  # 0s, 2s, 4s
log_error("jdc exhausted after 3 attempts, falling back to SDK")
result = run_sdk(...)
return parse(result)
```

After 3 consecutive CLI failures, the script MUST fall back to SDK. It MUST NOT
mix CLI and SDK within the same resource list iteration — fall back per-resource,
not per-batch.

## 6. Mocking for unit tests

The `JdcClient` class is the seam. Tests should:

```python
from unittest.mock import patch, MagicMock

with patch("lib.jdc_client.JdcClient.describe_vms") as mock:
    mock.return_value = [{"instanceId": "i-1", "charge": {"chargeExpiredTime": "2026-07-01T00:00:00Z"}}]
    ...
```

Do not patch `subprocess.run` directly — patch the high-level method to keep tests
behavior-focused.

## 7. SDK error handling

```python
try:
    resp = client.send(req)
except Exception as e:
    log_error(f"SDK call failed: {type(e).__name__}: <masked>")
    return []
```

Catch broadly because the SDK uses a single exception type for many error
families (network, auth, throttling). Distinguish by inspecting `e.error` /
`e.message` fields if available.

## 8. Region coverage in SDK

| Product | Endpoint |
|---|---|
| Elasticsearch | `es.jdcloud-api.com` |
| Kubernetes | `kubernetes.jdcloud-api.com` |
| WAF | `waf.jdcloud-api.com` |
| Bill | `bill.jdcloud-api.com` |

All regions are multi-AZ. The SDK does not require per-region endpoints — pass
`regionId` as a request parameter.

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial api-sdk-usage for `jdcloud-routines-ops` (1.1.0 batch) |