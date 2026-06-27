# JD Cloud CDN — Troubleshooting

Most CDN issues fall into 5 buckets: **DNS**, **origin**, **cache**, **HTTPS/cert**, **config drift**.

## 1. DNS issues — "domain not resolving via CDN"

### Symptom

```
$ curl -I https://cdn.example.com
curl: (6) Could not resolve host
```
or
```
$ dig cdn.example.com
;; ANSWER SECTION:
cdn.example.com.  600  IN  A  1.2.3.4    # points to origin, not CDN
```

### Diagnose

```bash
# 1. Check DNS resolution
dig cdn.example.com CNAME
# Should return: cdn.example.com.jcloud-cdn.com or similar

# 2. If A record, CNAME not set → fix in jdcloud-dns-ops
# 3. If CNAME but cached wrong → flush local DNS cache
```

### Fix

Delegate DNS config to `jdcloud-dns-ops`:

```bash
# Add CNAME: cdn.example.com → cdn.example.com.jcloud-cdn.com
# (CNAME value is shown in jdc cdn get-domain-detail)
```

CNAME propagation: 5-30 min globally, up to 24h for high TTL records.

## 2. Origin issues — "edge can't fetch origin"

### Symptom

- 5xx surge in `query-statistics-data`
- 502/503/504 in `query-domain-log`

### Diagnose

```bash
# 1. Check origin is reachable from outside
curl -I https://origin.example.com/foo.html

# 2. Check origin not blocking CDN IP ranges
# (CDN source IPs published in jdcloud-cdn-ops/references/integration.md)

# 3. Check origin security group (if ECS) allows CDN
# → delegate to jdcloud-vpc-ops for SG rules
```

### Fix

| Cause | Fix |
|-------|-----|
| Origin server down | Restart / check `vm-ops` |
| SG blocks CDN IPs | Whitelist CDN IP ranges in SG (`vpc-ops`) |
| Origin returns 404 | Source file missing — re-upload to OSS / fix path |
| Origin slow (timeout) | Increase CDN origin timeout (if available); add second origin |
| Cert mismatch (HTTPS origin) | Origin cert invalid → `cert-ops` for new cert |

## 3. Cache issues — "old content served" or "hit rate low"

### Old content served (purge not working)

```bash
# 1. Verify refresh task status
TASK_ID=... # from create-refresh-task
jdc --output json cdn query-refresh-task --task-id $TASK_ID

# 2. If task done but content still old:
#    - check URL list was correct
#    - check task-type (file vs dir)
#    - check refresh limit quota (default ~2000 URLs/day)
```

### Hit rate low (WAF-PERF-048)

See [monitoring.md §3](monitoring.md#3-improving-low-hit-rate) for the full
optimization checklist. Quick wins:

1. **Check TTL**: `jdc --output json cdn query-domain-config --domain X | jq '.result.cacheRules[]'`
2. **Check ignore-query-string**: `set-ignore-query-string 1` if query strings differ
3. **Check 404 cache**: `set-extra-cache-time --404 60` to prevent origin thrash

## 4. HTTPS / cert issues

### Symptom

```
curl: (60) SSL certificate problem: unable to get local issuer certificate
```
or browser shows "Your connection is not private"

### Diagnose

```bash
# 1. Check HTTPS enabled
jdc --output json cdn query-domain-config --domain cdn.example.com | jq '.result.httpsSwitch'
# Should be 1

# 2. Check cert bound
jdc --output json cdn get-domain-detail --domain cdn.example.com | jq '.result.certId'

# 3. Check cert validity
jdc --output json cdn get-ssl-cert-detail --cert-id <cert-id>
# Returns: $.result.{commonName, validBefore, validAfter, status}
```

### Fix

| Cause | Fix |
|-------|-----|
| HTTPS off | `set-http-type --https-switch 1` |
| No cert bound | `upload-cert` (or delegate to `cert-ops`) then `set-http-type --cert-id` |
| Cert expired | Upload new cert (`cert-ops`), update cert binding |
| Cert CN mismatch | Cert is for `*.example.com` but domain is `cdn.other.com` — re-issue |

## 5. Config drift — "skill says one thing, CDN does another"

### Symptom

Agent reports "cache rule exists with TTL=86400" but `query-band` shows high
origin traffic — meaning rule isn't actually applied.

### Diagnose

```bash
# 1. List ALL cache rules and verify priority
jdc --output json cdn query-domain-config --domain cdn.example.com \
  | jq '.result.cacheRules[] | {rulePath, cacheTtl, priority, cacheType}'

# 2. Check rule resolution order (lowest priority number = highest priority)
# Common bug: priority=99 default rule shadows priority=10 specific rule if priority set wrong

# 3. Check ignore-query-string
jdc --output json cdn query-domain-config --domain cdn.example.com \
  | jq '.result.ignoreQueryString'
```

### Fix

Re-order rules by priority, or update the wrong rule directly.

## 6. CLI-specific failures

### `jdc: command not found`

| Cause | Fix |
|-------|-----|
| Not in venv | `source .venv/bin/activate` |
| Wrong venv (Python 3.12+) | Recreate: `uv venv --python 3.10` |
| jdc not installed | `uv pip install jdcloud_cli==1.2.12` |

### `InvalidParameter` from CLI

| Cause | Fix |
|-------|-----|
| Wrong flag name | Check `jdc cdn <sub-command> --help` |
| Missing required flag | Same |
| Flag value wrong type | E.g. `--cache-ttl` expects int, not string |
| Enum value wrong | `--cdn-type vod` not `vod,` — no trailing punctuation |

### `PermissionDenied` / `CredentialInvalid`

```bash
# CLI ignores env vars — must use ~/.jdc/config
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

## 7. Quota errors

```bash
jdc --output json cdn query-cdn-user-quota
# Shows: domainQuota, refreshQuota, prefetchQuota, ...
```

| Quota | Default | Increase |
|-------|---------|----------|
| domain count | varies by plan | contact sales / upgrade |
| refresh URLs/day | 2000 | upgrade plan |
| prefetch URLs/day | 1000 | upgrade plan |

## 8. Outage / 5xx surge

```bash
# 1. Check status page (jcloud status)
# 2. Check origin (vm-ops / oss-ops)
# 3. Check recent config changes (git diff jdcloud-cdn-ops/) — agent or human?
# 4. Roll back if recent change: jdc cdn update-cache-rule --rule-id X --cache-ttl <old-ttl>
```

## 9. When to escalate

- Outage > 30 min with no clear cause
- Recurring 5xx from specific region (CDN regional issue)
- Quota / plan limitation blocking business growth
- Security incident (DDoS, WAF rule bypass)

Escalate to: JD Cloud support ticket, citing domain ID + status + recent config changes.