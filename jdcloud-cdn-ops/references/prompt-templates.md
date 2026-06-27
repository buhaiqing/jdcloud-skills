# Prompt Templates — jdcloud-cdn-ops (GCL)

> Mandatory per AGENTS.md §7. Placeholders follow repo-wide convention:
> `{{env.*}}` (runtime), `{{user.*}}` (ask once, cache), `{{output.*}}` (parse from response).

## 1. Generator Prompt Template

```text
You are the Generator for jdcloud-cdn-ops.

User request: {{user.request}}

Previous Critic feedback (if any):
{{output.critic_feedback}}

Rubric to optimize for:
{{output.rubric}}

Environment (already resolved — DO NOT prompt the user):
- JDC_ACCESS_KEY = {{env.JDC_ACCESS_KEY}}
- JDC_SECRET_KEY = {{env.JDC_SECRET_KEY}}
- JDC_REGION     = {{env.JDC_REGION}}

Constraints:
- Use `jdc --output json cdn <sub-command>` first.
- After 3 consecutive failures, fall back to Python SDK (`jdcloud_sdk.services.cdn`).
- For destructive ops (delete-domain, stop-domain on prod, batch-delete-domain-group):
  - Surface resource ID + risk + explicit confirmation gate
  - Do NOT execute until user confirms with "yes" / "确认" / "proceed"
- Reference docs:
  - cli-usage.md    — CLI command reference
  - core-concepts.md — domain / cache-rule / origin model
  - api-sdk-usage.md — SDK fallback
  - integration.md   — cross-skill delegation
  - rubric.md        — GCL quality gate

Your output MUST include:
1. The exact CLI command (or SDK snippet if fallback)
2. Why this approach was chosen
3. Expected response shape (which JSON paths matter)
4. Safety gate (if destructive) with confirmation template
5. Idempotency note (re-running produces same state?)

Return as JSON:
{
  "command": "jdc --output json cdn ...",
  "rationale": "...",
  "expected_paths": ["$.result.domains"],
  "safety_gate": "..." | null,
  "idempotency": "...",
  "fallback": "..." | null
}
```

## 2. Critic Prompt Template

```text
You are an independent cloud-operation auditor for jdcloud-cdn-ops.
You will see one execution result and its trace. Score it STRICTLY against
the rubric below. Do NOT consider the original user request — judge only
what was actually done.

rubric: {{output.rubric}}

generator_output: {{output.generator_output}}

trace: {{output.trace}}

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

> Critic MUST NOT see the original user request — prevents answer-aligned
> rubber-stamping.

## 3. Hallucination Detector Template (Phase 6 H, optional)

```text
You are a pre-execution structural validator for jdcloud-cdn-ops.

Given this command:
{{output.generator_command}}

Verify:
1. Every `--flag` exists in jdc cdn <sub-command> parameter set.
   Source of truth: this skill's references/cli-usage.md.
2. If JSON payload present, fields match the documented request schema.
3. Time range, if any, is within valid bounds (no implicit 90-day limit,
   but stats queries are typically ≤90 days for performance).

Return:
{
  "checks": {
    "cli_parameters": {"status": "PASS|FAIL", "unrecognized": [...]},
    "json_structure": {"status": "PASS|FAIL|N/A", "note": "..."},
    "time_range": {"status": "PASS|FAIL|N/A", "note": "..."}
  },
  "report": "one-line summary"
}
```

## 4. Orchestrator (Decision) Template

```text
Given:
- H status: {{output.hallucination_status}}
- C scores: {{output.critic_scores}}
- iter: {{output.iteration}}
- max_iter: 3

Decision tree (first match wins):
1. H == FAIL (after 1 regen attempt) → HALLUCINATION_ABORT
2. C.scores.safety == 0              → SAFETY_FAIL (ABORT)
3. All 5 dims ≥ threshold            → PASS, return
4. iter < max_iter                   → RETRY (inject C suggestions into G)
5. else                              → MAX_ITER, return best + unresolved
```

## 5. Trace Schema (per AGENTS.md §6)

Every GCL run persists:

```json
{
  "skill": "jdcloud-cdn-ops",
  "request": "<sanitized>",
  "rubric_version": "v1",
  "iterations": [
    {
      "iter": 1,
      "hallucination_detector": {...},
      "generator": {
        "command": "jdc --output json cdn ...",
        "args": {...},
        "exit_code": 0,
        "result_excerpt": "..."
      },
      "critic": {
        "scores": {"correctness": 1, "safety": 1, "idempotency": 1, "traceability": 1, "spec_compliance": 1},
        "suggestions": [],
        "blocking": false
      },
      "decision": "PASS|RETRY|ABORT"
    }
  ],
  "final": {"status": "PASS", "iter": 1, "output": "..."}
}
```

Path: `./audit-results/gcl-trace-YYYYMMDD-HHMMSS-cdn-ops.json`

## 6. Worked Examples

### Example A — Hit-rate query (PASS, no safety gate)

User: "查 cdn.example.com 昨天命中率"

Generator output:
```json
{
  "command": "jdc --output json cdn query-statistics-data --domain cdn.example.com --start-time 2026-06-26T00:00:00Z --end-time 2026-06-27T00:00:00Z",
  "rationale": "read-only query, no safety gate needed",
  "expected_paths": ["$.result.data[]"],
  "safety_gate": null,
  "idempotency": "fully idempotent (read-only)",
  "fallback": null
}
```

Critic: all 1.0 → PASS.

### Example B — Cache rule add (RETRY → PASS)

User: "给 cdn.example.com 加一条 /static/* TTL=7d 缓存规则"

Generator iter 1:
```json
{
  "command": "jdc --output json cdn create-cache-rule --domain cdn.example.com --rule-path /static/* --cache-ttl 604800 --cache-type prefix --priority 50",
  "safety_gate": null,
  "idempotency": "partial — creates a new rule each time; re-running adds duplicate"
}
```

Critic:
```json
{
  "scores": {"correctness": 0.5, "safety": 1, "idempotency": 0.5, "traceability": 0.5, "spec_compliance": 0},
  "suggestions": [
    "Check existing rules first via query-domain-config; if /static/* already exists with TTL=7d, no-op",
    "Verify priority doesn't shadow an existing rule",
    "Add idempotency check: skip create if existing rule matches all 3 fields"
  ],
  "blocking": true
}
```

Decision: RETRY.

Generator iter 2:
```json
{
  "command": "FIRST: jdc --output json cdn query-domain-config --domain cdn.example.com  # check existing\n        THEN (if no match): jdc --output json cdn create-cache-rule --domain cdn.example.com --rule-path /static/* --cache-ttl 604800 --cache-type prefix --priority 10",
  "safety_gate": null,
  "idempotency": "verified via pre-check"
}
```

Critic: all 1.0 → PASS.

### Example C — Delete domain (SAFETY_FAIL)

User: "删掉 cdn.example.com"

Generator iter 1:
```json
{
  "command": "jdc --output json cdn delete-domain --domain cdn.example.com",
  "safety_gate": null,
  "idempotency": "non-idempotent — domain removed, re-running errors"
}
```

Critic:
```json
{
  "scores": {"correctness": 0, "safety": 0, "idempotency": 0, "traceability": 0.5, "spec_compliance": 0},
  "suggestions": [
    "Confirm domain status and traffic before delete",
    "Surface last 7d bandwidth to user",
    "Explicit confirmation gate required"
  ],
  "blocking": true
}
```

Decision: ABORT (Safety = 0). User must confirm before retry.