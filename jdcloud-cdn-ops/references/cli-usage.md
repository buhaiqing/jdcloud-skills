# JD Cloud CDN — `jdc cdn` CLI Reference

> Verified against `jdcloud_cli==1.2.12`. Generated 2026-06-27.
> Total sub-commands: ~150 (most are query/operations; CRUD subset ~30).

## Path Preference

CLI-first with SDK fallback:

```bash
# Always
jdc --output json cdn <sub-command> [flags]

# Never
jdc cdn <sub-command> --output json    # FAILS — --output must be top-level
jdc --no-interactive cdn ...           # FAILS — flag does not exist
```

## Domain CRUD (the only safe entry points)

### `get-domain-list` — list all CDN domains

```bash
jdc --output json cdn get-domain-list --page-number 1 --page-size 50
# Response:
# $.result.domains[] = [{ domain, status, cdnType, origin, createTime, ... }]
# $.result.totalCount
```

| Flag | Required | Notes |
|------|:--------:|-------|
| `--page-number` | yes | 1-indexed |
| `--page-size`  | yes | ≤100 |
| `--domain`     | no  | filter by domain name (fuzzy) |

### `get-domain-detail` — single domain

```bash
jdc --output json cdn get-domain-detail --domain example.com
# Response: $.result.domain = { domain, status, cdnType, origin, httpsSwitch, ... }
```

### `batch-create` / `create-domain` — create (destructive in effect)

```bash
jdc --output json cdn batch-create \
  --domain-list '["cdn1.example.com","cdn2.example.com"]' \
  --origin 'https://origin.example.com' \
  --cdn-type vod
# After create, must `start-domain` to enable traffic
```

| Flag | Required | Notes |
|------|:--------:|-------|
| `--domain-list` (or `--domain`) | yes | domain(s) to add |
| `--origin` | yes | origin URL or OSS bucket |
| `--cdn-type` | yes | `vod` (点播) or `live` (直播, separate flow) |
| `--https-switch` | no | `0` / `1` |

### `start-domain` / `stop-domain` — traffic on/off

```bash
jdc --output json cdn start-domain --domain example.com
jdc --output json cdn stop-domain  --domain example.com
# Status transitions: running ↔ stopped, takes ~30s propagation
```

### `delete-domain` — **DESTRUCTIVE** (safety gate)

```bash
jdc --output json cdn delete-domain --domain example.com
# REMOVES: domain, all cache rules, all stats history. Cannot be undone.
```

## Cache Rules (WAF-PERF-048 / 命中率关键)

### `create-cache-rule`

```bash
jdc --output json cdn create-cache-rule \
  --domain example.com \
  --rule-path /static/* \
  --cache-ttl 3600 \
  --cache-type suffix \
  --priority 10
```

| Flag | Type | Notes |
|------|------|-------|
| `--domain` | string | required |
| `--rule-path` | string | URL pattern (`/static/*`, `*.jpg`, exact) |
| `--cache-ttl` | int | seconds (0 = no cache, max 365 days) |
| `--cache-type` | string | `exact` / `suffix` / `prefix` / `regex` |
| `--priority` | int | lower = higher priority, 1-100 |

### `update-cache-rule` / `delete-cache-rule`

```bash
jdc --output json cdn update-cache-rule --rule-id <id> --cache-ttl 7200
jdc --output json cdn delete-cache-rule --rule-id <id>
```

## Origin (回源) Configuration

### `set-source` — change origin server

```bash
jdc --output json cdn set-source \
  --domain example.com \
  --source '["https://origin1.example.com","https://origin2.example.com"]'
```

### `config-back-source-rule` — path rewrite

```bash
jdc --output json cdn config-back-source-rule \
  --domain example.com \
  --rule-pattern '/old/(.*)' \
  --replacement '/new/$1'
```

### `config-back-source-oss` — OSS bucket as origin

```bash
jdc --output json cdn config-back-source-oss \
  --domain example.com \
  --oss-bucket my-bucket \
  --oss-region cn-north-1
```

## Refresh / Prefetch (刷新 / 预热)

### `create-refresh-task` — purge URLs

```bash
jdc --output json cdn create-refresh-task \
  --domain example.com \
  --url-list '["https://example.com/a.html","https://example.com/b.css"]' \
  --task-type file
# Returns: $.result.taskId — poll via query-refresh-task
```

| `--task-type` | meaning |
|---------------|---------|
| `file` | URL list (refresh specific files) |
| `dir`  | directory (refresh entire path) |

### `bat-create-prefetch-task` — warm cache

```bash
jdc --output json cdn bat-create-prefetch-task \
  --domain example.com \
  --url-list '["https://example.com/popular-1.jpg","https://example.com/popular-2.jpg"]'
```

### `query-refresh-task` — poll status

```bash
jdc --output json cdn query-refresh-task --task-id <taskId>
# Response: $.result.status (pending/processing/done/failed)
```

## Statistics (bandwidth / traffic / hit-rate)

### `query-band` — bandwidth bps time series

```bash
jdc --output json cdn query-band \
  --domain example.com \
  --start-time '2026-06-26T00:00:00Z' \
  --end-time   '2026-06-27T00:00:00Z'
# Response: $.result.data[] = { time, bps }
```

### `query-statistics-data` — traffic / request volume

```bash
jdc --output json cdn query-statistics-data \
  --domain example.com \
  --start-time '2026-06-26T00:00:00Z' \
  --end-time   '2026-06-27T00:00:00Z'
# Response: $.result.data[] = { time, flow, pv, ... }
```

### Hit-rate calculation (no dedicated API — compute from above)

```text
hit_rate = 1 - (origin_traffic / total_traffic)

origin_traffic ≈ back-source flow (query-back-source-* if available, else estimate)
total_traffic  ≈ flow from query-statistics-data
```

For practical use, hit-rate is best estimated via:
- Cloud Monitor metrics (`jdcloud-cloudmonitor-ops`) — has `CDN` namespace with `OriginTraffic` / `TotalTraffic`
- Direct back-source query: `query-back-source-rule` / `query-back-source-rules`

## HTTP / HTTPS / Cache-Header

| Command | Purpose |
|---------|---------|
| `set-http-type` | http / https / follow / redirect protocol behavior |
| `config-http2` | enable/disable HTTP/2 |
| `set-cache-rules` | bulk cache rule replace |
| `set-extra-cache-time` | per-status-code (404/403/...) cache TTL |
| `set-gzip` | enable gzip |
| `set-http-header` | add custom HTTP response headers |
| `set-ignore-query-string` | ignore query string in cache key |

## Security / WAF (defer to `jdcloud-waf-ops` for rule definitions)

These commands exist but their rule semantics are WAF-domain; for full
WAF integration use `jdcloud-waf-ops`:

- `create-waf-black-rule` / `delete-waf-black-rules`
- `create-waf-white-rule` / `delete-waf-white-rules`
- `enable-waf-black-rules` / `disable-waf-black-rules`
- `set-waf-switch` / `query-waf-switch`

## Quota / Limits

```bash
jdc --output json cdn query-cdn-user-quota
# Response: $.result = { domainQuota, refreshQuota, ... }
```

## Pagination pattern

For any `*-list` command:

```bash
PAGE=1
while true; do
  RESP=$(jdc --output json cdn get-domain-list --page-number $PAGE --page-size 50)
  echo "$RESP" | jq '.result.domains[]'
  TOTAL=$(echo "$RESP" | jq '.result.totalCount')
  PAGE=$((PAGE+1))
  [ $((PAGE*50)) -ge $TOTAL ] && break
done
```

## Sandbox-Safe CLI Config

```bash
export HOME=/tmp/jdc-home
mkdir -p ~/.jdc
cat > ~/.jdc/config << EOF
[default]
access_key = $JDC_ACCESS_KEY
secret_key = $JDC_SECRET_KEY
region_id = ${JDC_REGION:-cn-north-1}
endpoint = cdn.jdcloud-api.com
scheme = https
timeout = 20
EOF
printf "%s" "default" > ~/.jdc/current
```