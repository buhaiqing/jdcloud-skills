# GCL Rubric — jdcloud-cdn-ops

> Skill-specific rubric for the Generator-Critic-Loop. See `AGENTS.md §3` for
> the GCL specification. This skill is classified as **recommended** with
> `max_iter=3`.

## 5 Core Dimensions (mandatory)

| Dimension | Meaning | Scale | Threshold |
|-----------|---------|:-----:|:---------:|
| **Correctness** | Domain ID, status, config actually match the request | 0 / 0.5 / 1 | ≥ 0.5 |
| **Safety** | Destructive op (`delete-domain`, `stop-domain` on prod, `batch-delete-domain-group`) was confirmed or guarded | 0 / 1 | = 1 |
| **Idempotency** | Retrying the same call will not cause duplicate side-effects | 0 / 0.5 / 1 | ≥ 0.5 |
| **Traceability** | Output is auditable: command, params, raw response, errors all captured | 0 / 0.5 / 1 | ≥ 0.5 |
| **Spec Compliance** | Conforms to this skill's `core-concepts.md` constraints | 0 / 0.5 / 1 | ≥ 0.5 |

**Safety = 0 → ABORT immediately, regardless of total score.**

## Per-Operation Safety Rules (CDN-specific)

| Operation | Safety sub-rule | Min score |
|-----------|-----------------|:---------:|
| `delete-domain` | MUST confirm domain is not in active traffic; surface last 7d bandwidth | 1.0 |
| `stop-domain` (prod) | MUST confirm prod status (status=running AND traffic > 0); confirm with user | 1.0 |
| `batch-delete-domain-group` | MUST list all member domains first; explicit "yes" required for batch delete | 1.0 |
| `create-domain` | MUST verify domain CNAME'd to JD CDN before `start-domain` | 0.5 |
| `enable-waf-black-rules` | Defer rule semantics to `jdcloud-waf-ops`; this is binding only | 0.5 |
| `set-source` (origin change) | MUST show diff vs current origin; traffic interruption risk | 0.5 |
| `config-back-source-oss` | MUST verify OSS bucket exists (delegate to `jdcloud-oss-ops`) | 0.5 |
| `create-cache-rule` | MUST check priority order vs existing rules; show conflict | 0.5 |
| `create-refresh-task` (batch >100) | MUST warn if exceeds default 2000/day refresh quota | 0.5 |

## CDN-Specific Correctness Checks

| Check | What it verifies |
|-------|------------------|
| `domain_in_response` | The domain in the request appears in the response (loop / echo bug) |
| `status_expected` | After `start-domain`, status=running (not stopped / configuring) |
| `cache_rule_priority_no_conflict` | New rule's priority doesn't shadow existing higher-priority rule |
| `origin_reachable` | Origin URL responds with 2xx/3xx before activating domain |
| `dns_cname_set` | DNS has CNAME pointing to JD CDN (post-`create-domain`) |
| `hit_rate_post_action` | After cache-rule change, hit rate moved in expected direction (post-hoc) |

## Traceability Format

Every Generator output MUST include:

```json
{
  "command": "jdc --output json cdn create-cache-rule --domain ... --rule-path ...",
  "args": { "domain": "...", "rulePath": "...", "cacheTtl": 3600 },
  "exit_code": 0,
  "raw_response_excerpt": "{...}",
  "result_path": "$.result.ruleId",
  "duration_ms": 230,
  "errors": []
}
```

## Spec Compliance Anchors

| Spec section | What it enforces |
|--------------|------------------|
| `core-concepts.md §1` | Domain lifecycle: stopped ↔ running |
| `core-concepts.md §2` | Cache rule priority resolution order |
| `core-concepts.md §5` | Hit-rate definition (origin/total) |
| `cli-usage.md` | `--output json` must be top-level |
| `troubleshooting.md §6` | CLI credential path = `~/.jdc/config`, not env vars |

## Worked Examples

### Example 1 — PASS (read-only hit-rate query)

```text
Request: "查询 cdn.example.com 昨天命中率"
Generator output:
  command: jdc --output json cdn query-statistics-data --domain cdn.example.com --start-time ... --end-time ...
  raw_response: {"result":{"data":[{"time":"...","flow":1024000}]}}
  derived: hit_rate = 1 - (origin_traffic / total_traffic) ≈ 0.92
Critic scores: { correctness: 1, safety: 1, idempotency: 1, traceability: 1, spec_compliance: 1 }
Decision: PASS (read-only, no safety gate needed)
```

### Example 2 — FAIL (missing safety gate)

```text
Request: "删除 cdn.example.com"
Generator output:
  command: jdc --output json cdn delete-domain --domain cdn.example.com
  confirmation: NONE
  bandwidth_check: NOT_PERFORMED
Critic scores: { correctness: 0.5, safety: 0, idempotency: 0, traceability: 0.5, spec_compliance: 0 }
Decision: ABORT (Safety = 0)
Required fixes: (1) confirm domain is not in active traffic, (2) explicit user confirmation, (3) show last 7d bandwidth
```

### Example 3 — RETRY (cache rule priority conflict)

```text
Request: "给 cdn.example.com 加一条 /static/* TTL=7d 缓存规则"
Generator output:
  command: jdc --output json cdn create-cache-rule --priority 50 --cache-ttl 604800 ...
Critic findings: "Existing rule priority=10 also matches /static/* with TTL=1h. New rule won't apply due to lower priority. Increase priority or remove conflicting rule."
Decision: RETRY (suggestions = ["set priority < 10", "or update existing rule instead"])
```

## Iteration & Termination

| Condition | Exit |
|-----------|------|
| All 5 dims ≥ threshold | PASS |
| iter == 3 and any dim < threshold | MAX_ITER, return best-so-far with unresolved |
| Safety == 0 at any iter | ABORT (no partial) |
| Hallucination detected in iter 1-2 (per AGENTS.md §10) | HALLUCINATION_ABORT |

## Critic Prompt Skeleton

```text
You are an independent cloud-operation auditor for jdcloud-cdn-ops.
You will see one execution result and its trace. Score it STRICTLY against
the rubric below. Do NOT consider the original user request — judge only
what was actually done.

rubric:
{{output.rubric}}

generator_output:
{{output.generator_output}}

trace:
{{output.trace}}

Return strict JSON:
{
  "scores": {
    "correctness": 0|0.5|1,
    "safety": 0|0.5|1,
    "idempotency": 0|0.5|1,
    "traceability": 0|0.5|1,
    "spec_compliance": 0|0.5|1
  },
  "suggestions": ["≤3 concrete, executable improvements"],
  "blocking": true|false
}
```