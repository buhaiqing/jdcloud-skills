# Smart Fallback Strategy

> This document is extracted from `SKILL.md`.
> Scope: All `jdc-first-with-fallback` execution paths.
> See [monitor-pitfalls.md](monitor-pitfalls.md) pitfall 7.

## Core Principle

**Not all CLI errors are worth retrying.** Deterministic errors (parameter parsing bugs, authentication failures)
retried 3 times are just wasting time — fall back to SDK immediately.

## Error Classification

| Error Type | Retriable? | Backoff Strategy | Example |
|------------|:--------:|------------------|---------|
| Network timeout | ✅ Yes | Exponential backoff 0s/2s/4s | `ConnectionError`, `Timeout` |
| API throttling | ✅ Yes | Exponential backoff 2s/4s/8s | `Throttling`, `429` |
| Server error | ✅ Yes | Fixed 2s | `InternalError`, `5xx` |
| **Parameter parsing error** | **❌ No** | **Fall back immediately** | `unrecognized arguments`, `ValueError` |
| **Authentication failure** | **❌ No** | **HALT** | `InvalidAccessKeyId`, `SignatureDoesNotMatch` |
| **Insufficient permissions** | **❌ No** | **HALT** | `Forbidden.RAM` |

## Execution Pseudocode

```python
def call_jdc_or_sdk(command, sdk_fn):
    result = run_jdc(command)
    if result.success:
        return result

    # Deterministic error → fall back immediately, no retry
    if is_deterministic_error(result.stderr):
        print(f"[INFO] CLI deterministic error, falling back to SDK")
        return sdk_fn()

    # Retriable error → retry 3 times
    for i in range(3):
        time.sleep(2 ** i)
        result = run_jdc(command)
        if result.success:
            return result

    # Final fallback
    print(f"[INFO] CLI failed after 3 retries, falling back to SDK")
    return sdk_fn()
```

## CLI Bug Workaround

`jdc_cli==1.2.12`'s `monitor` subcommand has a known parameter parsing bug.
Use `--input-json` to pass parameters as a workaround:

```bash
# ❌ Direct parameters (may trigger CLI bug)
jdc --output json monitor describe-metric-data \
  --service-code vm --resource-id i-xxx --metric cpu_util ...

# ✅ Use --input-json to work around
jdc --output json monitor describe-metric-data --input-json '{
  "serviceCode": "vm",
  "resourceId": "i-xxx",
  "metric": "vm.cpu_util",
  "startTime": "2026-06-09T00:00:00Z",
  "endTime": "2026-06-09T12:00:00Z",
  "timeInterval": "1h"
}'
```

## SDK Import Pitfall

`jdcloud_sdk`'s client module exports a module rather than a class:

```python
# ❌ Wrong
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient(cred, region)  # TypeError: not callable

# ✅ Correct
from jdcloud_sdk.services.monitor.client import MonitorClient
from jdcloud_sdk.core.config import Config
cfg = Config(endpoint='monitor.jdcloud-api.com', scheme='https', timeout=30)
client = MonitorClient.MonitorClient(cred, region, cfg)
```

## Silent Monitoring Data Failure

API returning `error: null` + `data: null` is a **silent failure** — it means the resource has no monitoring data
(usually because the cloud monitoring agent is not installed), not an API call failure.

**Always check the `data` field after each query**:

```python
items = resp.result.get('metricDatas', [])
for item in items:
    if item.get('data') is None:
        print(f"[WARN] {item['metric']['metric']}: no monitoring data (agent may not be installed)")
        continue
```

## Related Documents

| Document | Path | Description |
|----------|------|-------------|
| Monitoring Pitfalls | `monitor-pitfalls.md` | 7 known pitfalls + fix patterns |
| Template Safety Contract | `../../jdcloud-topo-discovery/SKILL.md` → Template Safety Contract | Cross-skill common constraints |