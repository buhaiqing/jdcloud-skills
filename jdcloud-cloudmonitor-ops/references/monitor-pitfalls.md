# Cloud Monitor Data Collection Pitfalls (Monitor Pitfalls)

> This document records real error patterns encountered when collecting monitoring data
> using the `jdc monitor` CLI and `jdcloud_sdk` SDK,
> serving as a reference for future development and code review.
>
> When adding a new error pattern, please append it using the template below.

---

## Pitfall Index

| # | Symptom Keyword | Root Cause Category | First Discovered |
|:-:|-----------------|---------------------|------------------|
| 1 | `jdc monitor --help` crash | CLI parameter parsing bug | 2026-06-09 |
| 2 | `--down-sample-type` unrecognized | CLI parameter name inconsistency | 2026-06-09 |
| 3 | `MonitorClient` not callable | SDK module/class confusion | 2026-06-09 |
| 4 | `Config` no attribute 'log' | SDK constructor signature | 2026-06-09 |
| 5 | `serviceCode and metric not match` | Metric name prefix rules | 2026-06-09 |
| 6 | All metrics return `data: null` | Monitor agent not installed | 2026-06-09 |
| 7 | Retry 3 times still fails | CLI bug is deterministic | 2026-06-09 |

---

## Pitfall 1: `jdc monitor` CLI Parameter Parsing Crash

### Symptom

```bash
$ jdc monitor --help
ValueError: unsupported format character 'B' (0x42) at index 87
```

### Root Cause

The help text of the `monitor` subcommand in `jdc_cli==1.2.12` contains a `%B` format string,
which Python's `argparse` `%` substitution logic misinterprets as a formatting placeholder.

### Impact

All `jdc monitor` subcommand `--help` output is affected. However, executing actual commands
via `--input-json` is not affected (does not trigger help text rendering).

### Fix

**Workaround**: Use `--input-json` to pass parameters, avoiding CLI parameter parsing:

```bash
# ❌ Direct parameter passing (may trigger the bug)
jdc --output json monitor describe-metric-data \
  --service-code vm --resource-id i-xxx --metric cpu_util ...

# ✅ Use --input-json to bypass
jdc --output json monitor describe-metric-data --input-json '{
  "serviceCode": "vm",
  "resourceId": "i-xxx",
  "metric": "vm.cpu_util",
  "startTime": "2026-06-09T00:00:00Z",
  "endTime": "2026-06-09T12:00:00Z",
  "timeInterval": "1h"
}'
```

### Related

- This bug is confirmed in `jdc_cli==1.2.12`
- Upgrading to a newer version may fix it (pending verification)

---

## Pitfall 2: `last-downsample` Parameter Name Inconsistency

### Symptom

```bash
$ jdc monitor last-downsample --down-sample-type last ...
jdc: error: unrecognized arguments: --down-sample-type last
```

### Root Cause

The actual parameter name for `jdc monitor last-downsample` is inconsistent with the name
documented in SKILL.md. And since `--help` cannot be viewed due to Pitfall 1,
this must be resolved through trial and error.

### Fix

**Option A**: Use `describe-metric-data` instead (recommended)
```bash
jdc --output json monitor describe-metric-data --input-json '{...}'
```

**Option B**: Fall back to SDK
```python
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient.MonitorClient(cred, region, config)
# Use DescribeMetricDataRequest
```

### Related

- `jdcloud-cloudmonitor-ops/SKILL.md` → Operation: Query Monitoring Data

---

## Pitfall 3: SDK `MonitorClient` is a Module, Not a Class

### Symptom

```python
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient(cred, region)
# TypeError: 'module' object is not callable
```

### Root Cause

`jdcloud_sdk`'s `monitor/client.py` exports a **module** that contains
the `MonitorClient` class. The correct reference path is `MonitorClient.MonitorClient`.

### Fix

```python
# ❌ Wrong
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient(cred, region)

# ✅ Correct
from jdcloud_sdk.services.monitor.client import MonitorClient
client = MonitorClient.MonitorClient(cred, region, config)
```

### General SDK Reference Pattern

| SDK Module | Correct Reference |
|------------|-------------------|
| `monitor.client` | `MonitorClient.MonitorClient(cred, region, config)` |
| `vm.client` | `VmClient.VmClient(cred, region, config)` |
| `vpc.client` | `VpcClient.VpcClient(cred, region, config)` |

---

## Pitfall 4: SDK `Config` Constructor Signature

### Symptom

```python
from jdcloud_sdk.core.config import Config
cfg = Config(scheme='https', endpoint='monitor.jdcloud-api.com', timeout=30)
# AttributeError: 'Config' object has no attribute 'log'
```

### Root Cause

The actual signature of `Config.__init__` is `(self, endpoint, scheme, timeout)`,
with the parameter order opposite to intuition (endpoint comes first).

### Fix

```python
# ❌ Wrong order
cfg = Config(scheme='https', endpoint='monitor.jdcloud-api.com', timeout=30)

# ✅ Correct order
cfg = Config(endpoint='monitor.jdcloud-api.com', scheme='https', timeout=30)
```

### Product Endpoints

| Product | endpoint |
|---------|----------|
| monitor | `monitor.jdcloud-api.com` |
| vm | `vm.jdcloud-api.com` |
| vpc | `vpc.jdcloud-api.com` |
| lb | `lb.jdcloud-api.com` |
| redis | `redis.jdcloud-api.com` |
| rds | `rds.jdcloud-api.com` |

---

## Pitfall 5: Metric Name Prefix Rules

### Symptom

```bash
$ jdc monitor describe-metric-data --input-json '{"metric":"cpu_util",...}'
# error: "serviceCode and metric not match"
```

### Root Cause

Different products have different prefix rules for metric names:

| Product | serviceCode | Metric Prefix | Example |
|---------|:----------:|:------------:|---------|
| VM | `vm` | `vm.` | `vm.cpu_util`, `vm.disk.bytes.read` |
| VM (old) | `vm` | No prefix | `cpu_util`, `memory.usage` |
| CLB | `lb` | `network.services.lb.` | `network.services.lb.active.connections` |
| Redis | `redis` | `jmiss.redis.cluster.` or `redis_` | `jmiss.redis.cluster.memory_usage` |

### Fix

**Always use `describe-metrics` first to query the available metric list**, confirming the correct metric name:

```bash
jdc --output json monitor describe-metrics --service-code vm 2>&1 | \
  python3 -c "import sys,json; [print(m['metric']) for m in json.load(sys.stdin)['result']['metrics']]"
```

### Related

- `jdcloud-cloudmonitor-ops/SKILL.md` → Operation: Query Monitoring Data

---

## Pitfall 6: Monitoring Data Silently Returns null

### Symptom

```json
{
  "result": {
    "metricDatas": [{
      "data": null,
      "metric": {"metric": "vm.cpu_util", "metricName": "CPU Usage"}
    }]
  }
}
```

### Root Cause

The API call succeeds (`error: null`), but the `data` field is `null`. Reasons:
- Cloud monitor agent not installed on the VM
- No data exists within the time range
- Resource was just created, data hasn't been reported yet

**API returning no error ≠ data exists**. This is the most common silent failure pattern.

### Fix

**Always check whether `data` is non-null after every query**:

```python
items = resp.result.get('metricDatas', [])
for item in items:
    data = item.get('data')
    if data is None:
        print(f"[WARN] {item['metric']['metric']}: No monitoring data (agent may not be installed)")
        continue
    # Process data...
```

### Related

- It is recommended to check the alarm rule list before querying; having alarm rules = higher probability of monitoring data

---

## Pitfall 7: Deterministic CLI Bugs Should Not Be Retried

### Symptom

```
jdc monitor --help → ValueError (retried 3 times, still fails)
jdc monitor last-downsample --down-sample-type last → unrecognized arguments (retried 3 times, still fails)
```

### Root Cause

The jdc-first-with-fallback strategy in SKILL.md specifies "retry 3 times then fall back to SDK".
But CLI parameter parsing bugs are **deterministic** (same input always produces the same error),
so retrying will not fix the issue — it only wastes time.

### Fix

**Distinguish between retryable and non-retryable errors**:

| Error Type | Retryable? | Example |
|------------|:--------:|---------|
| Network timeout | ✅ Yes | `ConnectionError`, `Timeout` |
| API throttling | ✅ Yes | `Throttling`, `429` |
| Server error | ✅ Yes | `InternalError`, `5xx` |
| Parameter parsing error | ❌ No | `unrecognized arguments`, `ValueError` |
| Authentication failure | ❌ No | `InvalidAccessKeyId`, `SignatureDoesNotMatch` |
| Insufficient permissions | ❌ No | `Forbidden.RAM` |

**Recommended fast-fallback strategy**:

```python
def call_jdc_or_sdk(command, sdk_fn):
    """jdc-first with smart fallback."""
    result = run_jdc(command)
    if result.success:
        return result
    
    # Deterministic error → fall back immediately, no retry
    if is_deterministic_error(result.stderr):
        print(f"[INFO] CLI deterministic error, falling back to SDK")
        return sdk_fn()
    
    # Retryable error → retry 3 times
    for i in range(3):
        time.sleep(2 ** i)
        result = run_jdc(command)
        if result.success:
            return result
    
    # Final fallback
    print(f"[INFO] CLI failed after 3 retries, falling back to SDK")
    return sdk_fn()
```

---

## General Fix Patterns

### Secure Monitoring Data Collection Flow

```
1. describe-metrics → confirm metric name
        |
2. describe-alarms → confirm whether alarm rules exist (indirect check if agent is installed)
        |
        ▼
3. describe-metric-data → fetch data
        |
        ▼
4. Check data != null → yes → process data
                      → no  → WARNING + mark as "no monitoring"
```

### Code Review Checklist

- [ ] Was `describe-metrics` used to confirm the metric name first?
- [ ] Was the `data` field checked for non-null?
- [ ] Were retryable and non-retryable CLI errors distinguished?
- [ ] Does the SDK reference use the correct `Module.Class` pattern?
- [ ] Is the `Config` parameter order correct (`endpoint, scheme, timeout`)?
- [ ] Was the "no monitoring data" silent failure handled?

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-06-09 | 1.0.0 | Initial version, covering 7 known pitfalls |