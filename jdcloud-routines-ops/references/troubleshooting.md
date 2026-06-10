# Troubleshooting — `jdcloud-routines-ops`

> Catalogues every failure mode observed (or anticipated) for `expiry_cruise.py`
> and the planned billing / inventory scripts. Use this as the runbook when the
> script returns a non-zero code or an empty `details` array.

## 1. Diagnostic flow

```
Script returns ?
├── exit 0 + non-empty details  → success, see report
├── exit 0 + empty details      → filter too tight (raise --warning-days)
├── exit 1 + report written     → no findings (clean) OR non-fatal error
├── exit 1 + no report          → fatal before reaching write step
└── other non-zero              → uncaught exception, see stderr
```

## 2. Failure catalogue

### 2.1 Credential

| Symptom | Cause | Fix |
|---|---|---|
| `Please use 'jdc configure add' …` | No `~/.jdc/config` | Create INI (see `cli-usage.md` §1.2) |
| `AccessKeyId does not exist` | Wrong / rotated AK | Update `~/.jdc/config` |
| `SignatureDoesNotMatch` | Wrong SK or clock skew | Check SK; check `date` on the box |
| `PermissionDenied` / `Forbidden` | AK/SK lacks `JDC ReadOnly` policy | Request IAM grant from admin |

> ⚠️ None of these should cause the script to print the secret. If you ever see
> a secret value in a log line, file a security incident immediately.

### 2.2 CLI

| Symptom | Cause | Fix |
|---|---|---|
| `unrecognized arguments: --output json` | Flag placed after subcommand | Move to top-level |
| `unrecognized arguments: --no-interactive` | Unsupported flag | Remove it (commands are non-interactive by default) |
| `RegionId not found` | Typo or unsupported region | See `regions.md` |
| `Throttling.User` | Too many calls | Add 1s sleep between types; reduce region count |
| Empty result list for an active resource | Pagination cap hit at page_size=100 | Tracked for 1.2.0; workaround: filter by customer or by date |
| `error: argument --customer: invalid value` (Py3.10 argparse quirk) | None — argparse encoding | Verify the script is run with `python` not `python3` on systems where the latter is 3.12+ |

### 2.3 SDK fallback (Elasticsearch)

| Symptom | Cause | Fix |
|---|---|---|
| Elasticsearch returns `[]` silently | SDK exception caught and swallowed | Re-run with `JDCS_DEBUG=1` (planned flag); check `~/.jdc/config` exists |
| `Endpoint not found` | Wrong endpoint constant | Verify `es.jdcloud-api.com` in `jdc_client.py` §`describe_elasticsearch` |
| Garbled stdout | SDK log lines leaked past `StringIO` capture | Do not edit the capture block; report as a regression |

### 2.4 Output

| Symptom | Cause | Fix |
|---|---|---|
| Report not written | `output_dir` not writable | Use `--output-dir` to a writable path |
| Report has `total_expiring: 0` but resources exist | `--warning-days` too low OR customer filter mismatch | Try `--warning-days 60 --customer ""` to confirm |
| Wrong region in report | `JDC_REGION` env / `region_id` in INI different from `--regions` | Align them |

### 2.5 Time / Date

| Symptom | Cause | Fix |
|---|---|---|
| `days_left` is `None` for all entries | `chargeExpiredTime` returned in non-ISO format | Check a single raw `jdc --output json vm describe-instances --region-id cn-north-1 --page-size 1` |
| `days_left` is negative for active resources | Host clock ahead of JD Cloud clock | Sync host with NTP; treat negative as "today" |
| `days_left` is one day off | Timezone mismatch (`chargeExpiredTime` is UTC) | Tracked for 1.2.0 — normalize to local before computing |

## 3. Common operator mistakes

### 3.1 Mixing `--no-interactive` and `jdc --output json`

```bash
# WRONG
jdc --no-interactive --output json vm describe-instances

# CORRECT (CLI is non-interactive by default)
jdc --output json vm describe-instances --region-id cn-north-1
```

### 3.2 Running the wrong Python

```bash
# WRONG — `python3` may be 3.12+ on some systems
python3 scripts/expiry_cruise.py

# CORRECT — use the .venv which pins 3.10
.venv/bin/python scripts/expiry_cruise.py
```

### 3.3 Expecting exit 0 on "clean"

The exit code semantics are:

- `0` = findings (something needs attention)
- `1` = no findings OR non-fatal error

CI pipelines should treat `0` as "action needed" and `1` as "all clear or
investigate". This is by design (so the same code can drive alerts in both
directions), but trips up shells that assume `0 = success`.

### 3.4 Trying to filter server-side

`--customer` does **not** reduce the API call count. The script always lists
all resources in the requested regions/types, then filters in-memory. To reduce
cost, narrow `--regions` and `--types` instead.

## 4. When to escalate

| Signal | Action |
|---|---|
| `permissionDenied` for a resource | Check IAM; if AK/SK should have access, contact account admin |
| `InternalError` 3 times in a row | Likely JD Cloud backend issue; check status page |
| Script keeps returning `1` with empty `details` despite `warning_days=60` | Open an issue — likely a parser bug |
| Customer tag unexpectedly empty for known-billable resources | Audit tag pipeline via `jdcloud-tag-audit-ops` |

## 5. Recovery

After fixing the underlying issue:

```bash
# Re-run with conservative scope to verify
python scripts/expiry_cruise.py \
  --types vm --regions cn-north-1 --warning-days 60

# Then expand
python scripts/expiry_cruise.py
```

## 6. Known limitations (1.1.0)

Tracked for 1.2.0:

- [ ] Pagination not looped — page_size=100 hard cap
- [ ] No structured log file
- [ ] Exit code `1` is overloaded (clean / error)
- [ ] Elasticsearch fallback swallows errors silently
- [ ] No `--no-color` flag for non-TTY environments

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial troubleshooting for `jdcloud-routines-ops` (1.1.0 batch) |