# JD Cloud CDN — Cross-Skill Integration

This skill is a leaf in the JD Cloud ops ecosystem. Most real workflows involve
2-3 other skills; here are the canonical patterns.

## 1. Static-site stack: OSS origin + CDN + SSL cert

Most common CDN use case. Three skills orchestrate:

```
1. jdcloud-oss-ops  — create bucket, upload files, set bucket public-read for static
2. jdcloud-cert-ops — upload SSL cert, get cert-id
3. jdcloud-cdn-ops  — create CDN domain with origin=oss-bucket, bind cert, enable HTTPS
4. jdcloud-dns-ops  — CNAME your domain to *.jcloud-cdn.com
```

### Execution

```bash
# Step 1: OSS (already done — assume bucket "static-prod" exists)
# jdcloud-oss-ops confirm bucket lifecycle / public-read

# Step 2: cert (already done — assume cert-id "cert-abc123")
# jdcloud-cert-ops list certs, get cert-id matching example.com

# Step 3: CDN (this skill)
jdc --output json cdn batch-create \
  --domain-list '["cdn.example.com"]' \
  --origin 'static-prod' \
  --cdn-type vod \
  --https-switch 1

jdc --output json cdn set-http-type \
  --domain cdn.example.com \
  --cert-id cert-abc123

jdc --output json cdn start-domain --domain cdn.example.com

# Step 4: DNS (delegate)
# jdcloud-dns-ops add CNAME: cdn.example.com → cdn.example.com.jcloud-cdn.com
```

## 2. WAF-PERF-048 (CDN 命中率) — arch-advisor 闭环

`jdcloud-arch-advisor` is the **read-only orchestrator** that evaluates WAF rules.
For `WAF-PERF-048` it delegates to this skill to compute hit rate.

### Flow

```
arch-advisor receives "evaluate WAF-PERF-048"
  → reads cdn-ops docs for hit-rate threshold (≥90% pass, 70-90% warn, <70% fail)
  → calls jdcloud-cdn-ops to query band + statistics over last 7 days
  → computes hit_rate from origin-traffic / total-traffic
  → emits verdict + remediation
```

### How arch-advisor invokes us

arch-advisor SKILL.md SHOULD NOT include the calculation logic — it calls our
public API surface:

```text
jdcloud-arch-advisor → jdcloud-cdn-ops.get_hit_rate(domain, days=7)
  → returns { hit_rate: 0.85, verdict: "warn", remediation: "review cache rules" }
```

`hit_rate` computation lives here, not in arch-advisor.

## 3. aiops-cruise 集成（巡检链路）

`jdcloud-aiops-cruise` (read-only) Phase 2 may invoke this skill for CDN
analysis. Pattern:

```
aiops-cruise Perceive (Phase 1)
  → discovers all CDN domains via jdcloud-cdn-ops.get-domain-list
  → cross-references with VM / OSS / DNS to map dependency graph

aiops-cruise Reason (Phase 2)
  → calls jdcloud-cdn-ops for each domain:
      - hit rate (last 7 days)
      - bandwidth trend
      - cache rule count
      - origin type (OSS vs ECS)
  → emits findings: "cdn.example.com hit_rate=62% (< 70% fail)"

aiops-cruise Execute (Phase 3)
  → does NOT modify (read-only)
  → emits recommendations: "add cache rule for /static/* with TTL=86400"
```

## 4. cloudmonitor 告警联动

For real-time hit-rate / bandwidth alerts, delegate to `jdcloud-cloudmonitor-ops`:

```text
User: "CDN 命中率低于 80% 告警"
  → jdcloud-cloudmonitor-ops:
      namespace=CDN
      metric=OriginTraffic / TotalTraffic (computed via expression)
      threshold=0.8
      period=5min
      action=notify
```

This skill does NOT create alarm rules directly — it provides the metric
namespace and field names.

## 5. waf-ops 联动（CC / WAF 防护）

CDN has built-in WAF glue commands (`enable-waf-black-rules` etc.), but full
rule semantics belong to `jdcloud-waf-ops`:

```
User: "在 cdn.example.com 上加一条 WAF 规则"
  → jdcloud-waf-ops: define rule semantics
  → jdcloud-cdn-ops: enable-waf-black-rules (just the binding step)
```

## 6. billing-ops 联动（流量费用）

CDN traffic cost analysis delegates to `jdcloud-billing-ops`:

```text
User: "上个月 CDN 流量费用"
  → jdcloud-billing-ops.query-bill → product=cdn, period=last-month
  → cross-reference with jdcloud-cdn-ops for per-domain breakdown
```

## Out-of-skill handoffs (deliberate non-features)

| User asks | We say | Delegate to |
|-----------|--------|-------------|
| "CDN 域名挂在 WAF 上" | "rule semantics are WAF-domain" | `jdcloud-waf-ops` |
| "CDN 域名对应的 ECS 出问题" | "investigate origin" | `jdcloud-vm-ops` |
| "CDN SSL 证书即将过期" | "manage cert" | `jdcloud-cert-ops` |
| "CDN 域名解析" | "DNS / CNAME" | `jdcloud-dns-ops` |
| "OSS 桶作为 CDN 回源" — bucket side | "OSS config" | `jdcloud-oss-ops` |

## Routing rules

When the user request is ambiguous, prefer:

1. **Pure CDN config** → this skill
2. **CDN + origin config** → if origin is OSS: oss-ops first, then this; if ECS: vm-ops first
3. **CDN + WAF** → waf-ops first (rules), then this (binding)
4. **CDN + cert** → cert-ops first, then this (bind)
5. **CDN + alarm** → cloudmonitor-ops only (this skill doesn't create alarms)

If unsure, ask: "Is this about CDN domain config, or about CDN-related
monitoring/alerts/origin?"