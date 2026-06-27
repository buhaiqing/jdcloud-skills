# Failure Patterns — jdcloud-cdn-ops

> Per AGENTS.md §11 (Lightweight Reflexion). Cross-session failure memory for
> this skill. Hard cap: 200 lines. Patterns come from GCL traces and self-review.

## §1 CLI Parameter Errors

| # | pattern | error | fix | count |
|---|---------|-------|-----|------:|
| 1 | `--output json` placed after sub-command | `unrecognized arguments: --output json` | Always: `jdc --output json cdn ...` | 3 |
| 2 | `--no-interactive` flag | `unrecognized arguments: --no-interactive` | Omit; the flag does not exist | 2 |
| 3 | `--cdnType vod,` (trailing comma) | `InvalidParameter: cdnType` | Use `vod` without punctuation | 1 |
| 4 | `--cacheType prefix` with `--rulePath /static/.*` (regex syntax) | `InvalidParameter: cacheType mismatch` | Match `cache-type` to pattern syntax (suffix/prefix/exact/regex) | 1 |
| 5 | Forgot `--start-time` for `query-band` | `MissingRequiredParameter` | All `query-*` data commands need start/end ISO 8601 | 2 |

## §2 Configuration Mistakes

| # | pattern | symptom | fix | count |
|---|---------|---------|-----|------:|
| 1 | Created domain but forgot `start-domain` | status=stopped, traffic=0 | `jdc cdn start-domain --domain X` | 4 |
| 2 | Added cache rule but priority=99 shadowed by existing priority=10 | rule never matches | Use `query-domain-config` to inspect, set priority correctly | 2 |
| 3 | Bound wrong cert (CN mismatch) | browser SSL warning | Re-issue cert with correct CN, re-bind | 1 |
| 4 | Origin set to OSS bucket but bucket not public-read | 403 on every miss | Set OSS bucket ACL via `jdcloud-oss-ops` | 1 |
| 5 | DNS CNAME not propagated yet | domain resolves to origin | Wait up to 24h, or lower DNS TTL before CNAME | 2 |

## §3 Cross-Skill Routing Mistakes

| # | pattern | symptom | correct routing | count |
|---|---------|---------|-----------------|------:|
| 1 | cdn-ops tried to create WAF rule | half-config: black rule created, no rule semantics | Delegate rule semantics to `jdcloud-waf-ops`; cdn-ops only enables binding | 1 |
| 2 | cdn-ops tried to upload SSL cert | cert uploaded but not bound to CDN | Use `jdcloud-cert-ops` for upload, return cert-id, then cdn-ops `set-http-type --cert-id` | 1 |
| 3 | cdn-ops tried to compute hit rate from `query-band` alone | hit rate = N/A (band has no origin data) | Use Cloud Monitor `OriginTraffic` / `TotalTraffic`, OR combine `query-statistics-data` + `query-back-source-*` | 2 |

## §4 Idempotency / Retry Pitfalls

| # | pattern | symptom | fix | count |
|---|---------|---------|-----|------:|
| 1 | `create-cache-rule` re-run | duplicate rules with same priority | Pre-check `query-domain-config`; skip create if equivalent rule exists | 1 |
| 2 | `create-refresh-task` re-run | duplicate refresh tasks | Idempotency-key via URL list dedup (already true if URL list identical) | 0 |
| 3 | `delete-domain` re-run | `Domain.NotFound` | Catch and treat as already-deleted success | 1 |
| 4 | `batch-create` re-run | `Domain.AlreadyExists` | List first; skip existing | 1 |

## §5 Quota / Limit Traps

| # | pattern | error | remediation | count |
|---|---------|-------|-------------|------:|
| 1 | Mass refresh > 2000 URLs/day | `Quota.Exceeded` | Batch across multiple days; or upgrade plan | 2 |
| 2 | Domain count exceeds plan | `Quota.Exceeded: domainQuota` | Upgrade plan or delete unused domains | 1 |
| 3 | Prefetch URL list > 1000 | `Quota.Exceeded` | Split into multiple tasks | 0 |

## Maintenance

- Add pattern only when count >= 1 (dedup existing first)
- Prune patterns with count < 3 when file exceeds 200 lines
- Patterns with count >= 10 → promote to GCL Hallucination Detector (§10 in AGENTS.md)
- Last reviewed: 2026-06-27