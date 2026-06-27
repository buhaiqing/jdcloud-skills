# JD Cloud CDN — Core Concepts

## 1. Domain (加速域名)

A CDN **domain** is the entry point — the URL your users actually request. JD Cloud CDN serves content at this domain by caching from a configured **origin**.

```
User request → CDN edge (closest POP) → if cached: respond → if miss: origin → cache + respond
```

| Property | Meaning |
|----------|---------|
| `domain` | The hostname (e.g. `cdn.example.com`) — must be DNS-resolvable and CNAME'd to JD CDN |
| `cdnType` | `vod` (点播 — static content) or `live` (直播 — stream media, separate flow) |
| `status` | `running` (serving traffic) / `stopped` (DNS resolves but returns 404) / `configuring` (brief) |
| `origin` | The source URL(s) — your real backend or OSS bucket |

A domain must be created, DNS-CNAME'd to JD CDN (e.g. `*.jcloud-cdn.com`), and then **started** before serving traffic.

## 2. Cache Rule (缓存规则)

Cache rules define **what** to cache and **for how long**.

| Field | Values |
|-------|--------|
| `rule-path` | URL pattern: exact `/foo.html`, suffix `*.jpg`, prefix `/static/*`, regex `^/api/.*$` |
| `cache-type` | `exact` / `suffix` / `prefix` / `regex` — must match pattern type |
| `cache-ttl` | seconds; 0 = no cache; max ~31,536,000 (365 days) |
| `priority` | 1-100; lower number = higher priority (evaluated first) |

### Resolution order

JD CDN evaluates rules **highest priority first** (lowest priority number); first match wins.

```
priority=1, exact, /api/health       → no cache (TTL=0)
priority=10, suffix, *.html          → 1h
priority=20, prefix, /static/*       → 7 days
priority=99, default                 → 1h
```

### Best-practice tiers

| Tier | TTL | Content type |
|------|-----|--------------|
| Versioned assets | 365 days | `app.v123.js`, `style.abcd.css` — filename-hashed, safe to cache forever |
| Images / media | 30 days | `/static/*.jpg`, `*.mp4` |
| HTML | 1 hour or less | `/`, `/*.html` — frequent updates |
| API | 0 (no cache) | `/api/*` — usually bypass |

## 3. Origin (回源)

The **origin** is where CDN fetches content on cache miss.

### Origin types

| Type | Config command | When to use |
|------|----------------|-------------|
| HTTPS / HTTP server | `set-source` | Your own origin (ECS / CLB) |
| OSS bucket | `config-back-source-oss` | Static files in OSS — fastest path |
| Multiple origins (failover) | `set-source` with array | Primary + backup |
| Path rewrite | `config-back-source-rule` | `/old/*` → `/new/*` (no redirect, internal) |

### Back-source protocol

- `set-follow-source-protocol`: edge uses http or https based on **client** request
- `set-protocol-convert`: edge always uses https to origin regardless of client

## 4. Refresh / Prefetch (刷新 / 预热)

| Action | Command | Use case |
|--------|---------|----------|
| **Refresh** (refresh cache) | `create-refresh-task --task-type file\|dir` | Source updated, purge CDN cache so next request re-fetches |
| **Prefetch** (warm cache) | `bat-create-prefetch-task` | Anticipated traffic spike, warm cache proactively |

Both are **async** — returns `taskId`, poll via `query-refresh-task`.

### When to refresh

- Source file updated (HTML / CSS / JS) → refresh file
- Whole directory changed → refresh dir
- Big sale / launch → prefetch popular URLs in advance

## 5. Hit Rate (命中率) — WAF-PERF-048

The WAF Performance rule `WAF-PERF-048` evaluates CDN cache hit rate:

```
hit_rate = 1 - (origin_traffic / total_traffic)
```

### How to compute

JD Cloud CDN does **not** expose a direct `hitRate` field. Compute from:

| Source | Field |
|--------|-------|
| `query-statistics-data` | `$.result.data[].flow` (total served) |
| `query-back-source-rule` / Cloud Monitor `OriginTraffic` | bytes pulled from origin |
| `query-band` | bandwidth only, not useful for hit rate directly |

### Threshold guidance

| Hit rate | WAF-PERF-048 verdict |
|----------|----------------------|
| ≥ 90% | pass — good |
| 70-90% | warn — review cache rules |
| < 70% | fail — needs rule optimization |

### Optimization levers (when hit rate is low)

1. **Extend TTL** on cacheable assets (HTML: 1h → 5min is fine; images: 30d → 365d if versioned)
2. **Tighten `ignore-query-string`** — `?utm_source=...` creates cache fragmentation
3. **Set `set-extra-cache-time`** for 404/403 — prevents origin thrash on missing assets
4. **Use `set-source` to OSS** for static — much faster than ECS origin
5. **Prefetch** popular URLs after rule changes to warm cache

## 6. HTTP/HTTPS / Security

| Concern | Command |
|---------|---------|
| HTTPS enable | `set-http-type` with `--https-switch 1` |
| HTTP/2 | `config-http2` |
| Custom cert (own key) | `upload-cert` + `set-http-type --cert-id <id>` (delegates to `jdcloud-cert-ops`) |
| Gzip | `set-gzip` |
| HTTP headers | `set-http-header` |
| WAF rules | Defer to `jdcloud-waf-ops` — `enable-waf-black-rules` etc. are CDN-glue only |
| CC protection | CDN has CC rules but full semantics are WAF-domain |

## 7. Domain Group (域名组)

A **domain group** groups multiple CDN domains for batch operations (e.g. unified refresh).

| Command | Purpose |
|---------|---------|
| `create-domain-group` | new group |
| `update-domain-group` | add/remove members |
| `query-domain-group-list` | list groups |
| `batch-delete-domain-group` | **DESTRUCTIVE** — deletes group + all member stats |

## 8. Limitations / Out of scope

- **Live streaming** (`cdnType=live`) — different sub-command family; live acceleration needs different analytics (bandwidth-only, no hit rate concept)
- **PCDN / jbox** — peer-assisted CDN; separate product
- **Cross-region replication** — not a CDN concept (use OSS CRR instead)
- **CDN-side encryption** — HTTPS terminates at edge; field-level encryption is the origin's job

## 9. State diagram

```
        create-domain (with cdnType=vod)
                   │
                   ▼
              configuring
                   │ (DNS CNAME not yet done)
                   ▼
              stopped  ──── start-domain ───► running
                  ▲                            │
                  └────── stop-domain ─────────┘
                                │
                          delete-domain
                                ▼
                            (deleted)
```

## 10. CLI ↔ SDK ↔ Console equivalence

| Intent | CLI | SDK | Console |
|--------|-----|-----|---------|
| List domains | `get-domain-list` | `CdnClient.getDomainList` | Domain list page |
| Add domain | `batch-create` | `CdnClient.batchCreate` | Add domain wizard |
| Set cache rule | `create-cache-rule` | `CdnClient.createCacheRule` | Cache config page |
| Refresh URL | `create-refresh-task` | `CdnClient.createRefreshTask` | Refresh submission |
| View bandwidth | `query-band` | `CdnClient.queryBand` | Statistics page |

For SDK fallback details see [api-sdk-usage.md](api-sdk-usage.md).