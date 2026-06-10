# CLI Usage — `jdcloud-routines-ops`

> All scripts in `jdcloud-routines-ops/scripts/` follow the **jdc-first with
> SDK fallback** strategy defined in `AGENTS.md`. This file documents the CLI
> surface used by the expiry cruise and (planned) billing / inventory scripts.

## 1. Setup

### 1.1 Install (Python 3.10 — required)

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli==1.2.12 jdcloud_sdk
```

> **CRITICAL**: Python must be 3.10. `jdcloud_cli==1.2.12` imports
> `SafeConfigParser` from `configparser`, which was **removed in Python 3.12**.

### 1.2 Credentials

The `jdc` CLI reads credentials from **`~/.jdc/config` INI** — **NOT** from
environment variables. For sandboxed environments:

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id  = cn-north-1
endpoint   = vm.jdcloud-api.com
scheme     = https
timeout    = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

> ⚠️ The `~/.jdc/current` file MUST contain exactly `default` with **no trailing
> newline**. Use `printf "%s"` not `echo` to avoid the trailing newline.

The Python `jdcloud_sdk` reads `JDC_ACCESS_KEY` / `JDC_SECRET_KEY` env vars.

### 1.3 Verify

```bash
jdc --version
jdc --output json vm describe-instances --region-id cn-north-1 --page-size 1
```

## 2. CLI Conventions

### 2.1 `--output json` placement

`--output json` is a **top-level** argument, defined in `base_controller.py`.
It MUST be placed **before** the subcommand:

```bash
# CORRECT
jdc --output json vm describe-instances --region-id cn-north-1

# WRONG — fails with "unrecognized arguments"
jdc vm describe-instances --output json --region-id cn-north-1
```

### 2.2 `--no-interactive`

**DO NOT USE.** The `jdc` CLI does not support `--no-interactive`. All commands
are non-interactive by default if all required arguments are provided. Adding
`--no-interactive` will fail.

### 2.3 JSON output shape

Every `jdc` call returns:

```json
{
  "requestId": "abc-123",
  "error":     null,
  "result":    { ... }
}
```

Always read `error` first. If `error != null`, do not attempt to parse `result`.

### 2.4 Errors

| Error code | Meaning | Agent action |
|---|---|---|
| `InvalidParameter` | Bad arg | Fix args; do not retry |
| `Unauthorized` | Bad / expired AK/SK | Re-check `~/.jdc/config` |
| `Throttling` | Rate-limited | Sleep + retry (max 3) |
| `ResourceNotFound` | Resource gone | Skip silently |
| `5xx` | Server-side | Retry with backoff |

## 3. CLI Surface Used by `expiry_cruise.py`

| Resource | Subcommand | Required args | Optional args |
|---|---|---|---|
| VM | `vm describe-instances` | `--region-id` | `--page-number`, `--page-size`, `--filters` |
| Redis | `redis describe-cache-instances` | `--region-id` | `--cache-instance-id`, `--page-number`, `--page-size` |
| EIP | `vpc describe-eips` | `--region-id` | `--eip-ids`, `--page-number`, `--page-size` |
| Disk | `disk describe-disks` | `--region-id` | `--disk-ids`, `--page-number`, `--page-size` |
| RDS | `rds describe-instances` | `--region-id` | `--db-instance-id`, `--page-number`, `--page-size` |
| CLB | `lb describe-load-balancers` | `--region-id` | `--load-balancer-ids`, `--page-number`, `--page-size` |
| MongoDB | `mongodb describe-instances` | `--region-id` | `--db-instance-id` |
| SSL | `ssl describe-certs` | — (global) | `--page-number`, `--page-size` |

> Elasticsearch is **not** exposed via `jdc` for this purpose. The script falls
> back to `jdcloud_sdk.services.es.client.EsClient` directly. See
> `references/api-sdk-usage.md` §"Elasticsearch fallback".

### 3.1 Pagination

All `describe-*` calls paginate. `expiry_cruise.py` currently makes **single
page** calls (page 1, size 100). For accounts with > 100 resources of one type
per region, the cruise will silently miss resources.

> ⚠️ **Known limitation (1.1.0)**: pagination is not yet looped. Tracked in
> `references/troubleshooting.md` §"Missed resources". Fix planned for 1.2.0.

## 4. Script Invocation

### 4.1 Basic cruise (14-day threshold, all regions)

```bash
python jdcloud-routines-ops/scripts/expiry_cruise.py
```

### 4.2 Tighter threshold

```bash
python jdcloud-routines-ops/scripts/expiry_cruise.py --warning-days 7
```

### 4.3 Specific regions and types

```bash
python jdcloud-routines-ops/scripts/expiry_cruise.py \
  --regions cn-north-1,cn-south-1 \
  --types   vm,rds,ssl
```

### 4.4 Customer filter

```bash
python jdcloud-routines-ops/scripts/expiry_cruise.py --customer 烟台振华
```

> The filter is applied **after** all resources are listed — it does not reduce
> the API call count. Cost saving comes from filtering at scan time, not from
> a server-side query.

### 4.5 Custom output directory

```bash
python jdcloud-routines-ops/scripts/expiry_cruise.py \
  --output-dir /var/reports/jdcloud/routines
```

Default: `~/.jdcloud-routines-ops/outputs/expiry/`.

### 4.6 Exit codes

| Code | Meaning |
|---|---|
| `0` | At least one expiring resource was found (report written) |
| `1` | No expiring resources found OR a non-fatal error (report still written, possibly empty) |
| Other | Fatal (uncaught exception, credential missing) |

> ⚠️ **Quirk**: `1` is overloaded — both "clean" and "non-fatal error" return
> `1`. CI pipelines using `exit 0 == success` will interpret "clean" as failure.
> Document this in the consumer's automation. Tracked for refactor in 1.2.0.

## 5. Shell Examples

### 5.1 Dry-run with a single type

```bash
# See only what VMs are expiring
python jdcloud-routines-ops/scripts/expiry_cruise.py \
  --types vm --regions cn-north-1 --warning-days 30
```

### 5.2 Save the latest report path

```bash
LATEST=$(ls -t ~/.jdcloud-routines-ops/outputs/expiry/*.json | head -1)
echo "Latest report: $LATEST"
```

### 5.3 Cleanup old reports (cron-friendly)

```bash
# Keep only the last 7 days
find ~/.jdcloud-routines-ops/outputs -type f -mtime +7 -delete
```

`scripts/cleanup_outputs.sh` wraps this with a default of 7 days.

## 6. CLI Path Preference

| Use CLI when | Use SDK when |
|---|---|
| Routine cruise from cron / shell | `jdc` CLI is not exposed (Elasticsearch, some RDS engines) |
| One-shot operator runs | Need structured error handling around retries |
| Simple list + filter | Need pagination across > 100 results |
| Sandbox-friendly (no Python) | Need streaming output / partial decode |

## 7. Troubleshooting (CLI-specific)

| Symptom | Likely cause | Fix |
|---|---|---|
| `unrecognized arguments: --output json` | `--output` placed after subcommand | Move to top-level |
| `unrecognized arguments: --no-interactive` | Unsupported flag | Remove it |
| `Please use 'jdc configure add' …` | No `~/.jdc/config` | Create one (see §1.2) |
| `RegionId not found` | Bad region id | Use `cn-north-1` etc. — see `references/regions.md` |
| `AccessKeyId does not exist` | Wrong AK | Re-create `~/.jdc/config` |
| `Throttling` | Too many calls | Add `sleep 1` between resource types (planned) |
| Empty result list | Pagination cap hit | See `references/troubleshooting.md` §"Missed resources" |

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-10 | Initial cli-usage for `jdcloud-routines-ops` (1.1.0 batch) |