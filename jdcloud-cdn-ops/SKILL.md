---
name: jdcloud-cdn-ops
description: >-
  Use this skill to manage JD Cloud CDN (Content Delivery Network / CDNPlus):
  create, configure, monitor, or troubleshoot CDN domains via `jdc` CLI (CLI-first)
  or SDK fallback. Trigger for CDN, 内容分发, CDNPlus, 缓存加速, 命中率,
  or tasks involving CDN domain CRUD, cache rules, origin configuration,
  refresh/prefetch tasks, bandwidth monitoring, or cache hit rate analysis —
  even without explicit "CDN" mention.
license: MIT
compatibility: >-
  Official JD Cloud SDK (Python 3.10+), valid API credentials, network
  access to JD Cloud endpoints, and official JD Cloud CLI (`jdc`) when this
  product is supported by the CLI (jdc-first with SDK fallback).
metadata:
  author: buhaiqing
  version: "1.0.0"
  last_updated: "2026-06-27"
  runtime: Harness AI Agent
  api_profile: "JD Cloud CDN API v1 - https://cdn.jdcloud-api.com/v1"
  cli_applicability: jdc-first-with-fallback
  cli_version_locked: "1.2.12"
  sdk_version_locked: ">=1.6.26"
  cli_support_evidence: >-
    Confirmed via `jdc --help | grep cdn` showing `cdn` in product list and
    `jdc cdn --help` exposing ~150 sub-commands covering domain CRUD,
    cache rules, origin configuration, refresh/prefetch, and statistics.
    Official CLI documentation: https://docs.jdcloud.com/cn/cli/introduction
  gcl_classification: recommended
  gcl_max_iter: 3
  environment:
    - JDC_ACCESS_KEY
    - JDC_SECRET_KEY
    - JDC_REGION
---

> This skill follows the [Agent Skill OpenSpec](https://agentskills.io/specification).

# JD Cloud CDN Operations Skill

## Overview

JD Cloud CDN (CDNPlus) is a content delivery network that accelerates static
and dynamic content by caching it on edge nodes close to end users. This skill
is an operational runbook for agents: explicit scope, credential rules,
pre-flight checks, **jdc-first execution with SDK fallback**, response
validation, and failure recovery. Do not use the web console as the primary
execution path.

### Path Preference

1. `jdc` CLI first for every operation (`jdc --output json cdn <op>`).
2. Retry up to **3 times** with backoff (0s → 2s → 4s).
3. SDK fallback only after 3 consecutive `jdc` failures.
4. Prefer `jdc` output when both paths succeed.

### Critical jdc CLI Behavioral Notes

- `--output json` is **top-level**: `jdc --output json cdn ...` works; `jdc cdn ... --output json` fails.
- `--no-interactive` does **not exist** — omit it.
- CLI credentials come **only** from `~/.jdc/config` + `~/.jdc/current`; env vars are ignored by the CLI (SDK uses env vars).
- In sandboxed environments set `export HOME=/tmp/jdc-home` and pre-create `~/.jdc/config` to avoid `PermissionError`.

See [references/cli-usage.md](references/cli-usage.md) and [references/integration.md](references/integration.md) for full setup.

## Trigger & Scope (Agent-Readable)

### SHOULD Use This Skill When

- User explicitly mentions "JD Cloud CDN", "CDNPlus", "内容分发", "CDN加速", or "缓存加速"
- User wants to **create**, **configure**, **monitor**, or **troubleshoot** CDN domains via automation
- Task involves CRUD operations: create, describe, modify, delete, list, start, stop CDN domains
- Task involves cache rule management: create, modify, or delete cache rules / URL rules
- Task involves origin (回源) configuration: set-source, config-back-source-rule, config-back-source-oss
- Task involves refresh (刷新) / prefetch (预热) tasks
- Task involves bandwidth / traffic / hit-rate (命中率) statistics
- Keywords detected: createDomain, getDomainList, queryBand, queryStatisticsData, createCacheRule, createRefreshTask, setSource
- User describes CDN needs without naming "CDN" (e.g. "加速我的静态资源", "提高缓存命中率", "配置回源")

### SHOULD NOT Use This Skill When

- Task is purely billing / account management → delegate to: `jdcloud-billing-ops`
- Task is about CDN cost analysis → use `jdcloud-billing-ops` (流量账单)
- Task is about object storage origin (OSS bucket config) → delegate to: `jdcloud-oss-ops`
- Task is about SSL certificate upload → delegate to: `jdcloud-cert-ops` (then bind via `upload-cert` / `set-http-type`)
- Task is about monitoring metrics / alarms → delegate to: `jdcloud-cloudmonitor-ops` (for CDN告警规则)
- Task is about WAF protection rules attached to a CDN domain → delegate to: `jdcloud-waf-ops`
- Task is live-stream (直播) acceleration → live-domain sub-commands are out of scope; use CDN console or contact JD support
- User insists on **console-only** flows with no API → state limitation; do not invent undocumented HTTP steps

## Variable Convention

- `{{env.JDC_ACCESS_KEY}}` / `{{env.JDC_SECRET_KEY}}` / `{{env.JDC_REGION}}` — runtime env vars, **never prompt user**
- `{{user.domain}}` — CDN domain name (e.g. `cdn.example.com`); ask once, cache
- `{{user.origin}}` — origin server URL or OSS bucket (e.g. `https://origin.example.com` or `oss-bucket-name`)
- `{{output.*}}` — fields parsed from `jdc --output json` response

## Execution Flows

### Pre-flight

```bash
# 1. Activate virtual environment (always first)
source .venv/bin/activate

# 2. Verify Python + jdc
python --version          # MUST be 3.10.x
which jdc                 # MUST be .venv/bin/jdc
jdc --version             # MUST be 1.2.12

# 3. Verify credentials
test -n "$JDC_ACCESS_KEY" && test -n "$JDC_SECRET_KEY" || { echo "MISSING CREDS"; exit 1; }

# 4. Verify jdc config (sandbox-safe)
test -f ~/.jdc/config && test -f ~/.jdc/current || {
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
}

# 5. Smoke test
jdc --output json cdn get-domain-list --page-number 1 --page-size 1
```

### Execute (jdc primary)

```bash
# List domains (paginated)
jdc --output json cdn get-domain-list --page-number 1 --page-size 50

# Get domain detail
jdc --output json cdn get-domain-detail --domain example.com

# Start / stop domain
jdc --output json cdn start-domain --domain example.com
jdc --output json cdn stop-domain --domain example.com

# Create cache rule
jdc --output json cdn create-cache-rule \
  --domain example.com \
  --rule-path /static/* \
  --cache-ttl 3600 \
  --cache-type suffix

# Query bandwidth (last 24h)
jdc --output json cdn query-band \
  --domain example.com \
  --start-time "$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time   "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Refresh URL (purge cache)
jdc --output json cdn create-refresh-task \
  --domain example.com \
  --url-list '["https://example.com/foo.html","https://example.com/bar.html"]'

# Hit-rate calculation (WAF-PERF-048)
# Note: JD Cloud CDN does not expose hit-rate directly. Compute from:
#   hit_rate = 1 - (origin_traffic / total_traffic)
# Where:
#   total_traffic   = sum of $.result.data[].flow from query-statistics-data
#   origin_traffic  = Cloud Monitor metric "OriginTraffic" (or estimate from back-source logs)
#
# Example workflow:
# 1. Query total traffic
TOTAL=$(jdc --output json cdn query-statistics-data \
  --domain example.com --start-time 2026-06-20T00:00:00Z --end-time 2026-06-27T00:00:00Z \
  | jq '[.result.data[].flow] | add')
# 2. Query origin traffic via Cloud Monitor (delegate to jdcloud-cloudmonitor-ops)
# 3. Calculate: echo "scale=2; 1 - ($ORIGIN / $TOTAL)" | bc
```

### Validate

```bash
# Parse JSON path: $.result.* — domain list response
# 成功: result.domains 数组
# 失败: error.code + error.message
```

### Recover

| Pattern | Action |
|---------|--------|
| `jdc: command not found` | Verify `.venv/bin/jdc` exists; reinstall `jdcloud_cli==1.2.12` |
| `InvalidCredential` | Re-create `~/.jdc/config` per pre-flight step 4 |
| `DomainNotFound` | Re-list domains with `get-domain-list`; check spelling |
| `QuotaExceeded` | Check `query-cdn-user-quota`; upgrade plan or remove unused domains |
| SDK `ImportError: SafeConfigParser` | Python 3.12+ detected; recreate venv with `uv venv --python 3.10` |

## Output Parsing Rules

| Response path | Meaning |
|--------------|---------|
| `$.result.domains[]` | Domain list (get-domain-list) |
| `$.result.domain` | Domain detail (get-domain-detail) |
| `$.result.taskId` | Async task ID (refresh / prefetch / waf-rule) |
| `$.result.data[]` | Statistics data points (query-statistics-data) |
| `$.result.bps` | Bandwidth bps (query-band) |
| `$.error.code` + `$.error.message` | Error envelope |

State transitions for domain lifecycle:

| From → To | Operation | Notes |
|-----------|-----------|-------|
| (none) → `running` | `create-domain` + `start-domain` | New domain |
| `running` → `stopped` | `stop-domain` | Safe; traffic returns 404 |
| `stopped` → `running` | `start-domain` | Takes ~30s propagation |
| `running` → `deleted` | `delete-domain` | **DESTRUCTIVE — confirm required** |
| `*` → `configuring` | cache-rule / origin-rule changes | Brief; ~10s |

## Safety Gates

The following operations are **destructive** and REQUIRE explicit user confirmation
before execution. The agent must surface the resource ID and intent, then wait for
"yes" / "确认" / "proceed" before invoking:

| Operation | Command | Risk |
|-----------|---------|------|
| Delete CDN domain | `delete-domain` | Removes domain + all cache rules + all statistics history |
| Stop CDN domain (prod) | `stop-domain` | Traffic returns to origin or 404 |
| Batch delete domain group | `batch-delete-domain-group` | Removes all domains in group |
| WAF black/white rule enable | `enable-waf-black-rules` / `enable-waf-white-rules` | May block legitimate traffic |

**Confirmation template:**
```
About to: <operation> on <resource-id>
Risk: <one-line>
Continue? (yes/no)
```

## Quick Reference — Top 10 Commands

| Intent | Command |
|--------|---------|
| List domains | `jdc --output json cdn get-domain-list --page-number 1 --page-size 50` |
| Get domain detail | `jdc --output json cdn get-domain-detail --domain example.com` |
| Start / stop domain | `jdc --output json cdn start-domain --domain example.com` / `stop-domain` |
| Create cache rule | `jdc --output json cdn create-cache-rule --domain X --rule-path /static/* --cache-ttl 3600` |
| Query bandwidth | `jdc --output json cdn query-band --domain X --start-time ... --end-time ...` |
| Refresh URL (purge) | `jdc --output json cdn create-refresh-task --domain X --url-list '["..."]'` |
| Set origin | `jdc --output json cdn set-source --domain X --source '["https://origin.com"]'` |
| Check domain config | `jdc --output json cdn query-domain-config --domain example.com` |
| Query refresh task | `jdc --output json cdn query-refresh-task --task-id <id>` |
| Check quota | `jdc --output json cdn query-cdn-user-quota` |

See [cli-usage.md](references/cli-usage.md) for complete command reference (~150 sub-commands).

## Failure Recovery (Quick Reference)

| Error pattern | Retry? | Fallback |
|---------------|:------:|----------|
| `NetworkError` / timeout | yes (3×) | SDK |
| `InvalidParameter` (CLI flags) | no | Fix flag; check `references/cli-usage.md` |
| `DomainAlreadyExists` | no | Use existing domain |
| `QuotaExceeded` | no | User action: plan upgrade |
| `PermissionDenied` | no | Re-check IAM policy |
| `DomainInUse` (delete blocked) | no | Stop domain first, then retry delete |

## Cross-Skill Delegation

| User intent | Delegate to |
|-------------|-------------|
| "CDN 流量费用分析" | `jdcloud-billing-ops` (流量账单) |
| "OSS 桶作为 CDN 回源" | `jdcloud-oss-ops` (配置 bucket) → `jdcloud-cdn-ops` (set-source) |
| "上传 CDN 域名证书" | `jdcloud-cert-ops` → `jdcloud-cdn-ops` (`upload-cert`) |
| "CDN 带宽告警" | `jdcloud-cloudmonitor-ops` (告警规则) |
| "CDN 域名挂 WAF" | `jdcloud-waf-ops` (CC / WAF 规则) |
| "CDN 命中率评估 / WAF-PERF-048" | `jdcloud-arch-advisor` (集成入口) |
| "整体巡检（含 CDN）" | `jdcloud-aiops-cruise` (Perceive → Reason → Execute) |

## References

- [cli-usage.md](references/cli-usage.md) — `jdc cdn` full command reference
- [core-concepts.md](references/core-concepts.md) — domain / cache-rule / origin model
- [api-sdk-usage.md](references/api-sdk-usage.md) — SDK fallback patterns
- [integration.md](references/integration.md) — cross-skill workflows
- [monitoring.md](references/monitoring.md) — hit-rate / bandwidth alarms
- [troubleshooting.md](references/troubleshooting.md) — common errors
- [rubric.md](references/rubric.md) — GCL quality gate
- [prompt-templates.md](references/prompt-templates.md) — Generator / Critic templates