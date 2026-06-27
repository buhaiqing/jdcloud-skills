# JD Cloud CDN — Python SDK Fallback

> Use SDK **only** after 3 consecutive `jdc cdn` failures (per repository policy).
> SDK reads credentials from env vars (`JDC_ACCESS_KEY` / `JDC_SECRET_KEY`),
> NOT from `~/.jdc/config`.

## Client setup

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.cdn.client.CdnClient import CdnClient

cred = Credential(os.environ["JDC_ACCESS_KEY"], os.environ["JDC_SECRET_KEY"])
client = CdnClient(cred)
```

## Operation map (most-used subset)

| CLI sub-command | SDK method | Module path |
|-----------------|-----------|-------------|
| `get-domain-list` | `getDomainList(req)` | `jdcloud_sdk.services.cdn.apis.GetDomainListRequest` |
| `get-domain-detail` | `getDomainDetail(req)` | `...GetDomainDetailRequest` |
| `batch-create` | `batchCreate(req)` | `...BatchCreateRequest` |
| `start-domain` | `startDomain(req)` | `...StartDomainRequest` |
| `stop-domain` | `stopDomain(req)` | `...StopDomainRequest` |
| `delete-domain` | `deleteDomain(req)` | `...DeleteDomainRequest` |
| `create-cache-rule` | `createCacheRule(req)` | `...CreateCacheRuleRequest` |
| `query-band` | `queryBand(req)` | `...QueryBandRequest` |
| `query-statistics-data` | `queryStatisticsData(req)` | `...QueryStatisticsDataRequest` |
| `create-refresh-task` | `createRefreshTask(req)` | `...CreateRefreshTaskRequest` |

## Example: list domains

```python
from jdcloud_sdk.services.cdn.apis.GetDomainListRequest import GetDomainListRequest

req = GetDomainListRequest()
req.pageNumber = 1
req.pageSize = 50

resp = client.getDomainList(req)
print(resp.error)   # None if success
print(resp.result)  # { "domains": [...], "totalCount": N }
```

## Example: query hit rate (compute on top of SDK)

```python
from datetime import datetime, timedelta, timezone
from jdcloud_sdk.services.cdn.apis.QueryBandRequest import QueryBandRequest
from jdcloud_sdk.services.cdn.apis.QueryStatisticsDataRequest import QueryStatisticsDataRequest

end = datetime.now(timezone.utc)
start = end - timedelta(days=1)

req1 = QueryBandRequest()
req1.domain = "example.com"
req1.startTime = start.isoformat()
req1.endTime = end.isoformat()
band_resp = client.queryBand(req1)

req2 = QueryStatisticsDataRequest()
req2.domain = "example.com"
req2.startTime = start.isoformat()
req2.endTime = end.isoformat()
stat_resp = client.queryStatisticsData(req2)

# Note: hit-rate is computed from origin-traffic vs total-traffic, not from band.
# band_resp.result.data[].bps gives bytes/sec sampled.
# For accurate hit-rate, use Cloud Monitor metric OriginTraffic / TotalTraffic.
```

## Example: create cache rule

```python
from jdcloud_sdk.services.cdn.apis.CreateCacheRuleRequest import CreateCacheRuleRequest

req = CreateCacheRuleRequest()
req.domain = "example.com"
req.rulePath = "/static/*"
req.cacheTtl = 3600
req.cacheType = "suffix"
req.priority = 10

resp = client.createCacheRule(req)
print(resp.result.ruleId)
```

## Retry pattern

```python
import time

def call_with_retry(fn, *args, max_attempts=3, **kwargs):
    """0s → 2s → 4s backoff (per AGENTS.md policy)."""
    delays = [0, 2, 4]
    last_err = None
    for attempt in range(max_attempts):
        try:
            time.sleep(delays[attempt])
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            if attempt == max_attempts - 1:
                raise
    raise last_err  # unreachable
```

## Response envelope

All SDK responses follow:

```python
response.error    # None OR { "code": "...", "message": "..." }
response.result   # dict-shaped result, matches CLI $.result.*
response.requestId
```

## Common error codes (SDK)

| Code | Meaning | Action |
|------|---------|--------|
| `Domain.NotFound` | domain not in account | re-list domains |
| `Domain.AlreadyExists` | duplicate add | use existing |
| `CacheRule.InvalidPattern` | regex syntax error | validate regex client-side |
| `Quota.Exceeded` | plan limit hit | check `query-cdn-user-quota` |
| `Credential.Invalid` | AK/SK wrong | re-source `.env` |

## Pitfall: import path

The SDK uses **capitalized module path** that surprises newcomers:

```python
# WRONG (this is the jdcloud_cli style, not SDK)
from jdcloud_sdk.services.cdn import GetDomainListRequest

# CORRECT
from jdcloud_sdk.services.cdn.apis.GetDomainListRequest import GetDomainListRequest
```

If you see `ModuleNotFoundError: No module named 'jdcloud_sdk.services.cdn.apis.GetDomainListRequest'`,
verify the actual class lives at that path:

```bash
find .venv/lib/python3.10/site-packages/jdcloud_sdk/services/cdn -name "*.py" | head -20
```

## SDK version lock

`pyproject.toml` pins `jdcloud_sdk>=1.6.26`. Major CDN API refactors land in 1.7+;
always cross-check operation class names against installed package after upgrade.