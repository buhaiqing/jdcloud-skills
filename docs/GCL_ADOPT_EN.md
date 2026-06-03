# Adopting the GCL Quality Gate in Your Skill

> **30-minute onboarding for Agent developers integrating a new
> skill into the JD Cloud Skills Farm.**

This document is the **ADOPT guide** for the Generator-Critic-Loop
(GCL) quality gate. It is intentionally a sibling to
`AGENTS.md` (the spec) and `docs/GCL_RETROSPECTIVE.md` (the
post-rollout lessons). You do NOT need to read those first;
read this, decide if GCL is right for your skill, then go deeper.

---

## Table of contents

1. [Why does this skill need GCL?](#1-why-does-this-skill-need-gcl)
2. [What is GCL in one paragraph?](#2-what-is-gcl-in-one-paragraph)
3. [The 30-minute onboarding checklist](#3-the-30-minute-onboarding-checklist)
4. [Step 1: Read the spec (5 min)](#step-1-read-the-spec-5-min)
5. [Step 2: Write `references/rubric.md` (10 min)](#step-2-write-referencesrubricmd-10-min)
6. [Step 3: Write `references/prompt-templates.md` (10 min)](#step-3-write-referencesprompt-templatesmd-10-min)
7. [Step 4: Add the Quality Gate chapter to `SKILL.md` (5 min)](#step-4-add-the-quality-gate-chapter-to-skillmd-5-min)
8. [A live, end-to-end example](#4-a-live-end-to-end-example)
9. [Verifying your rollout](#5-verifying-your-rollout)
10. [What NOT to do](#6-what-not-to-do)
11. [Where to get help](#7-where-to-get-help)

---

## 1. Why does this skill need GCL?

If your skill **only reads** cloud state (`describe-*`, `list-*`,
`get-*`), GCL is **optional**. You can stop reading this document.

If your skill **writes** cloud state — `create`, `update`,
`delete`, `start`, `stop`, `restore`, IAM/KMS, or any destructive
operation — GCL is **mandatory** in this repo. The reasons:

| Risk without GCL | What GCL gives you |
|------------------|-------------------|
| A "looks-correct" output is actually destructive | Critic scores the Generator's output against an explicit rubric |
| Silent failure: agent returns success but the operation didn't happen | Traceability dimension: trace must include the actual response excerpt |
| The model hallucinates a resource id | Correctness dimension: must be echoed back from a `describe-*` lookup |
| The agent loops forever refining a bad approach | `max_iterations` is bounded (2 for write-class) |
| Two agents audit each other into a shared bias | Generator and Critic run in **isolated prompt contexts** |
| The user is asked to confirm, but the agent proceeds anyway | Safety dimension: `safety=0` is a hard veto, always ABORT |

**Bottom line**: GCL is the harness-level enforcement of "are
you sure this is what the user wanted?" for irreversible
operations. Without it, the Agent has no second pair of eyes.

---

## 2. What is GCL in one paragraph?

**Generator-Critic-Loop (GCL)** is a three-role pattern:

- **Generator (G)**: takes a user request, performs the operation
  (via `jdc` CLI or SDK), records the trace.
- **Critic (C)**: takes the Generator's trace, scores it on a
  5-dimension rubric. **C does not see the original user request**
  to prevent answer-aligned rubber-stamping.
- **Orchestrator (O)**: runs the G → C → Decide loop, capped at
  `max_iterations`. Decision: `PASS` / `RETRY` / `RETURN_BEST` /
  `ABORT`.

The 5 dimensions (defined in `AGENTS.md` §3):

| Dimension | Meaning | Default threshold |
|---|---|---|
| **Correctness** | Resource id / state / config matches the request | ≥ 0.5; **= 1.0 required** for `delete`/`stop`/IAM/KMS/DDL |
| **Safety** | Destructive op was confirmed or guarded | **= 1** (hard veto) |
| **Idempotency** | Retry will not duplicate side-effects | ≥ 0.5 |
| **Traceability** | Trace has the command, args, response, post-state | ≥ 0.5 |
| **Spec Compliance** | Conforms to `core-concepts.md` (e.g., correct AZ codes) | ≥ 0.5 |

**Safety is the only hard veto.** If `safety=0`, the loop ABORTs
immediately. There is no retry on safety. This is by design.

---

## 3. The 30-minute onboarding checklist

For an existing `jdcloud-<product>-ops` skill:

- [ ] **(5 min)** Read `AGENTS.md` §1-3 (Purpose, Roles, Rubric).
      You do NOT need to read §5-11 right now; come back later.
- [ ] **(10 min)** Write `jdcloud-<product>-ops/references/rubric.md`.
      Use `jdcloud-vm-ops/references/rubric.md` as the template.
- [ ] **(10 min)** Write `jdcloud-<product>-ops/references/prompt-templates.md`.
      Use `jdcloud-vm-ops/references/prompt-templates.md` as the template.
- [ ] **(5 min)** Add a `## Quality Gate (GCL)` chapter to
      `SKILL.md`. Bump the frontmatter `version` field.
- [ ] **Run** `python3 scripts/gcl_runner.py --skill <your-skill> --request "test" --gen-fn mock --critic-fn mock`
      to verify the loop works end-to-end.

**That's it.** You're done. Don't read any other docs until you
have a failing test.

---

## Step 1: Read the spec (5 min)

Open `AGENTS.md` and read in this order:

1. **§1 Purpose** (5 lines) — the goal of GCL.
2. **§2 Roles** (~40 lines) — what G, C, and O do.
3. **§3 Rubric** (~30 lines) — the 5 dimensions and thresholds.
4. **§5 Termination** (~20 lines) — when the loop stops.
5. **§6 Trace** (~20 lines) — what's written to disk.

**Skip for now**: §7 (Prompt templates) — you'll write your own.
§8 (Per-skill defaults) — comes back to it. §9-11 — read once you
have a working skill.

---

## Step 2: Write `references/rubric.md` (10 min)

The rubric is the **single source of truth** for what the Critic
scores against. It is parsed automatically by
`scripts/gcl_runner.py` (see `parse_rubric`).

### Minimum structure

```markdown
# <Product> Ops Rubric (GCL)

> Concrete instantiation of the **Generator-Critic-Loop** rubric
> defined in `AGENTS.md` §3 for `jdcloud-<product>-ops`.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|-----------|--------|-----------|-------|-------|
| 1 | **Correctness** | hard | ≥ 0.5; **= 1.0 required** for `<list destructive ops>` | 0 / 0.5 / 1 | <one-sentence definition> |
| 2 | **Safety** | hard | = 1 | 0 / 1 | <one-sentence definition> |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | <one-sentence definition> |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | <one-sentence definition> |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | <one-sentence definition> |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|-----------|---------------------------|-------|
| `<op-1>` | Correctness, Safety, **<X>** | <short note> |
| `<op-2>` | Correctness, **Safety** | <short note> |

## Safety special cases

- <Pattern 1>: → **Safety = 0 → ABORT**
- <Pattern 2>: → **Safety = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| `max_iterations` | **2** | required-class (AGENTS.md §8) |
| `safety_confirm_required` | **true** | write-class |
```

### What to fill in for the 5 dimensions

| Dimension | What you should write |
|-----------|----------------------|
| **Correctness** | "Verifies `<key resource id>` matches user request; read back via `<describe-* command>` and compare" |
| **Safety** | "Destructive ops (`<list them>`) MUST have explicit user confirmation. Payloads MUST include `force=false` unless user opted in" |
| **Idempotency** | "`<create-like-op>` with same `<idempotency-key>` must use `<key>`; `<delete-like-op>` is naturally idempotent" |
| **Traceability** | "Trace MUST contain: full `jdc` command (or SDK call), args, exit code, raw response excerpt (≤ 2 KB), and final `<describe-*>` snapshot" |
| **Spec Compliance** | "Conforms to `core-concepts.md`: correct `<field>` for the region, `<field>` is a valid code, `<resource>` is in `<state>` before attach" |

### What to put in "Operation-specific overrides"

This is the place where you express "for this specific operation,
this specific dimension MUST be 1.0, no slack". Example:

```markdown
| `delete-instance` | Correctness, Safety, **Traceability** | Must include snapshot of pre-delete state |
| `create-instance` | Correctness, Safety, **Idempotency** | Must use `client-token` |
```

The Critic will treat the **bold** dimension as a hard floor.

### What to put in "Safety special cases"

This is the **most important section** of the rubric. It
captures product-specific patterns that should always ABORT,
no matter what the rest of the rubric says. Examples:

- `Delete on a resource tagged env=prod without explicit confirm=DELETE → ABORT`
- `Stop more than 5 resources in a single call without batch confirmation → ABORT`
- `Operation on a resource id not echoed back from a describe-* lookup → ABORT`
- `DDL without WHERE clause on UPDATE/DELETE → ABORT`
- `VACUUM FULL on a > 100GB table during business hours → ABORT`
- `delete-by-query with match_all → ABORT`
- `dropDatabase in production → ABORT`

**Tip**: copy these from existing skills if the product is
similar. `jdcloud-mysql-ops`, `jdcloud-postgresql-ops`, and
`jdcloud-mongodb-ops` have 8-12 each.

### Loop parameters: pick from this table

| Skill class | `max_iterations` | `safety_confirm_required` |
|---|---|---|
| `required` (write ops on prod) | **2** | **true** |
| `recommended` (network / monitoring) | **3** | **true** |
| `optional` (read-only / meta) | **5** | **false** |

---

## Step 3: Write `references/prompt-templates.md` (10 min)

This file is the **Generator and Critic prompt skeletons**. It's
not parsed automatically; it's read by humans and (in production)
by the LLM. Three sections:

### 3.1 Generator (G) prompt skeleton

A markdown skeleton the Generator LLM fills in. The four blocks:

1. **Role**: "You are a `<product>` operations agent ..."
2. **Inputs**: request text, rubric (link), `critic_feedback` (if retrying)
3. **Steps**: pre-flight → execute → capture trace → output
4. **Output format**: a JSON object the Orchestrator can parse

```markdown
## Generator (G) prompt skeleton

### Role

You are a `<product>` operations agent. Your job is to perform
the user's request on JD Cloud, using the `jdc` CLI (preferred)
or the SDK (fallback), and produce a structured trace.

### Inputs

- `{{user.request}}` — the user's request, sanitized
- `{{output.rubric_link}}` — link to `references/rubric.md`
- `{{output.previous_critic_feedback}}` — Critic's suggestions
  from the previous iteration (empty on iter 1)
- `{{output.iter}}` — current iteration number (1, 2, ...)

### Steps

1. **Pre-flight**: confirm credentials, validate resource ids
   via `<describe-* command>`.
2. **Execute**: run the operation via `jdc` (or SDK fallback).
3. **Capture trace**: record command, args, exit code, raw
   response excerpt (≤ 2 KB), and final `<describe-*>` snapshot.
4. **Output**: produce a JSON object matching the schema below.

### Output format

```json
{
  "command": "jdc <product> <op> <args>",
  "args": {"<key>": "<value>"},
  "exit_code": 0,
  "result": "<truncated response>",
  "post_state": {"<key>": "<value>"},
  "errors": [],
  "notes": "<one-line context>"
}
```
```

### 3.2 Critic (C) prompt skeleton

Same structure, but the **Critic does NOT see the original user
request** to prevent answer-aligned rubber-stamping. The Critic
sees only:

- The Generator's output
- The rubric

```markdown
## Critic (C) prompt skeleton

### Role

You are a `<product>` operations auditor. You will receive a
Generator's trace; you must score it on the 5-dimension rubric
in `{{output.rubric_link}}`.

**You will NOT receive the original user request.** This is
intentional: a request-aligned Critic rubber-stamps the
Generator. You must judge the trace on its merits alone.

### Inputs

- `{{output.generator_trace}}` — the Generator's full trace
- `{{output.rubric_link}}` — link to `references/rubric.md`
- `{{output.iter}}` — current iteration number

### Steps

1. For each of the 5 dimensions, examine the trace and decide
   a score of `0`, `0.5`, or `1`.
2. For each score, write a one-sentence justification.
3. If any dimension is `0`, write a suggestion for how the
   Generator should fix it.
4. Decide if the trace is `blocking` (yes if `safety=0`).

### Output format

```json
{
  "scores": {
    "correctness": 1.0,
    "safety": 1.0,
    "idempotency": 1.0,
    "traceability": 1.0,
    "spec_compliance": 1.0
  },
  "justifications": {
    "correctness": "<reason>",
    "safety": "<reason>",
    "idempotency": "<reason>",
    "traceability": "<reason>",
    "spec_compliance": "<reason>"
  },
  "suggestions": ["<fix-1>", "<fix-2>"],
  "blocking": false
}
```
```

### 3.3 Optional: per-operation overrides

If you have operations that need radically different prompts
(like ES `_delete_by_query` vs ES `POST _bulk`), add a third
section listing per-op variations.

---

## Step 4: Add the Quality Gate chapter to `SKILL.md` (5 min)

Add this chapter at the end of your `SKILL.md` (right before
the Changelog). Bump the frontmatter `version` field by `+0.1.0`
(minor version bump per the retrospective's `1.x.0` convention).

```markdown
## Quality Gate (GCL)

This skill participates in the **Generator-Critic-Loop** quality
gate defined in [`AGENTS.md`](../AGENTS.md#generator-critic-loop-gcl-adversarial-quality-gate).

### Rubric instance

See [`references/rubric.md`](references/rubric.md) for the
5-dimension rubric, operation-specific overrides, and safety
special cases for this skill.

### Prompt templates

See [`references/prompt-templates.md`](references/prompt-templates.md)
for the Generator (G) and Critic (C) prompt skeletons.

### Loop parameters

| Parameter | Value |
|-----------|-------|
| `max_iterations` | **<2 or 3 or 5>** |
| `safety_confirm_required` | **<true or false>** |
| `class` | **<required / recommended / optional>** |

### When the loop runs

The GCL Orchestrator (`scripts/gcl_runner.py`) is invoked on
every **mutating** operation (create, update, delete, start,
stop, restore, IAM, KMS, DDL). For read-only operations
(`describe-*`, `list-*`, `get-*`), the loop is **not** invoked
unless the skill is `read-only-mandate` class (like
`jdcloud-alert-intelligence`).
```

---

## 4. A live, end-to-end example

This is the smallest possible adoption: a 5-line rubric for a
hypothetical `jdcloud-bucket-ops` skill (object storage).

### 4.1 The rubric

```markdown
# Bucket Ops Rubric (GCL)

> Concrete instantiation of the GCL rubric for `jdcloud-bucket-ops`.

## Rubric version

`v1` — see `AGENTS.md` §11.

## Dimensions

| # | Dimension | Weight | Threshold | Scale | Notes |
|---|-----------|--------|-----------|-------|-------|
| 1 | **Correctness** | hard | ≥ 0.5; = 1.0 for `delete-bucket` | 0 / 0.5 / 1 | Verifies bucket name + region match request; read back via `describe-bucket`. |
| 2 | **Safety** | hard | = 1 | 0 / 1 | Destructive ops (`delete-bucket`, `lifecycle-policy-apply`) MUST have explicit user confirmation. |
| 3 | **Idempotency** | soft | ≥ 0.5 | 0 / 0.5 / 1 | `create-bucket` must use `client-token`. |
| 4 | **Traceability** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Trace MUST contain: full `jdc` command, args, exit code, response excerpt. |
| 5 | **Spec Compliance** | soft | ≥ 0.5 | 0 / 0.5 / 1 | Bucket name is DNS-compliant (lowercase, no underscores), region is in supported list. |

## Operation-specific overrides

| Operation | Required dimensions = 1.0 | Notes |
|-----------|---------------------------|-------|
| `create-bucket` | Correctness, **Idempotency** | Must use `client-token` |
| `delete-bucket` | Correctness, Safety, **Traceability** | Pre-delete: bucket must be empty |
| `put-bucket-policy` | Correctness, Safety | Policy diff shown |

## Safety special cases

- `delete-bucket` on a bucket that has `>0` objects → **Safety = 0 → ABORT**
- `put-bucket-policy` with `Principal=*` and `Action=*` → **Safety = 0 → ABORT** (publicly open)
- `delete-bucket` without `confirm=DELETE_BUCKET` in the trace → **Safety = 0 → ABORT**

## Loop parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| `max_iterations` | **2** | required-class (AGENTS.md §8) |
| `safety_confirm_required` | **true** | write-class |
```

### 4.2 The end-to-end test

```bash
# 1. Verify the rubric is parseable
$ python3 scripts/gcl_runner.py show-rubric --skill bucket-ops | head
{
  "skill": "bucket-ops",
  "rubric_version": "v1",
  "thresholds": {...},
  ...
  "required_dimensions": {
    "create-bucket": ["correctness", "idempotency"],
    "delete-bucket": ["correctness", "safety", "traceability"],
    "put-bucket-policy": ["correctness", "safety"]
  },
  "safety_auto_fail": [
    "delete-bucket on a bucket that has >0 objects → Safety = 0 → ABORT",
    ...
  ],
  "max_iterations": 2,
  "safety_confirm_required": true
}

# 2. Run a mock GCL cycle
$ python3 scripts/gcl_runner.py run \
    --skill bucket-ops \
    --request "delete bucket 'prod-logs'" \
    --safety-confirm \
    --gen-fn mock \
    --critic-fn mock

=== GCL run: bucket-ops ===
  request: delete bucket 'prod-logs'
  decision: RETURN
  iterations: 1
  trace: /path/to/audit-results/gcl-trace-20260604-120000-abcd1234.json

# 3. Run the ABORT path (mock-strict critic)
$ python3 scripts/gcl_runner.py run \
    --skill bucket-ops \
    --request "delete bucket 'prod-logs'" \
    --gen-fn mock \
    --critic-fn mock-strict

=== GCL run: bucket-ops ===
  request: delete bucket 'prod-logs'
  decision: ABORT
  iterations: 1
  trace: /path/to/audit-results/gcl-trace-20260604-120005-efgh5678.json
```

---

## 5. Verifying your rollout

After you've written the rubric and prompt templates, run the
following in order. **Stop at the first failure** and fix it
before moving on.

| Step | Command | What it checks |
|------|---------|----------------|
| 1 | `python3 scripts/gcl_runner.py show-rubric --skill <your-skill>` | Rubric is parseable, all 5 dims present, safety auto-fail captured |
| 2 | `python3 scripts/gcl_runner.py run --skill <your-skill> --request "test" --gen-fn mock --critic-fn mock` | Loop runs end-to-end with mock G/C |
| 3 | `python3 scripts/gcl_runner.py run --skill <your-skill> --request "test" --gen-fn mock --critic-fn mock-strict` | ABORT path triggers |
| 4 | `python3 scripts/gcl_dashboard.py --format json` | Trace is consumable by the dashboard |
| 5 | `python3 tests/gcl_dashboard_test.py` | (Optional but recommended) Re-run the closed-loop test |

If step 2 or 3 fails, check:
- The rubric's dimension thresholds (use the defaults from `RubricConfig` if unsure)
- The `safety_confirm_required` flag (must be `true` for write-class skills)

If step 4 fails, check the trace JSON has the fields listed in
`AGENTS.md` §6 (`iterations`, `final.status`, `final.iter`,
`run_id`, `started_at`, `finished_at`).

---

## 6. What NOT to do

These are the most common mistakes from past rollouts
(see `docs/GCL_RETROSPECTIVE.md` §3.1-3.6 for the full list).

### 6.1 Don't make the rubric just "pass the test"

The rubric is a **defense against model drift**, not a checklist
of unit tests. If you write only dimensions that are easy for the
LLM to score, you've removed the quality gate.

**Bad**:
```markdown
| Correctness | hard | ≥ 0.5 | Did the model output a JSON? |
```

**Good**:
```markdown
| Correctness | hard | ≥ 0.5; = 1.0 for `delete` | Resource id matches `describe-*` lookup; AZ is a valid code; EIP is in `Available` state before attach. |
```

### 6.2 Don't share context between G and C

The Generator and Critic MUST run in **isolated prompt
contexts**. If the Critic sees the user's request, it will
rubber-stamp the Generator.

**Bad** (pseudo-GCL, see AGENTS.md §9):
```python
# same LLM session
context = user_request + generator_output
critic_score = same_llm(context + rubric)
```

**Good**:
```python
g_context = [user_request, rubric, feedback]
generator_output = g_llm(g_context)

# isolated critic context
c_context = [generator_output, rubric]  # NO user_request
critic_score = c_llm(c_context)
```

### 6.3 Don't retry on safety

Safety is a hard veto. If `safety=0`, ABORT. Do not "try again
with better confirm". The user is the one who needs to confirm,
not the loop.

### 6.4 Don't add a 6th dimension without evidence

The 5-dimension rubric was hard-won (see retrospective §3.3).
Before adding a 6th dimension, write up:
- What is it measuring?
- What failure mode does it prevent that the existing 5 don't catch?
- A test case in `tests/gcl_ground_truth.jsonl` that the
  current rubric would mis-score.

If you can't answer all three, don't add the dimension.

### 6.5 Don't leak the user's request to the Critic

This is a special case of §6.2 but worth calling out: the
Critic's prompt template MUST NOT include `{{user.request}}`.
The Critic sees only the Generator's output.

### 6.6 Don't score the Critic

The dashboard (`gcl_dashboard.py`) is read-only. It does not
score the Critic. "Auditing the auditor" is out of scope and
introduces bias. If the Critic is consistently wrong, the
rubric needs work, not the dashboard.

---

## 7. Where to get help

| Question | Where to look |
|----------|---------------|
| What is the 5-dimension rubric? | `AGENTS.md` §3 |
| When does the loop ABORT vs RETRY? | `AGENTS.md` §5 |
| What does the trace JSON look like? | `AGENTS.md` §6 |
| What's a per-skill default `max_iterations`? | `AGENTS.md` §8 |
| What's the most common rollout mistake? | `docs/GCL_RETROSPECTIVE.md` §3 |
| What's a good `references/rubric.md` example? | `jdcloud-vm-ops/references/rubric.md` |
| What's a good `references/prompt-templates.md` example? | `jdcloud-vm-ops/references/prompt-templates.md` |
| How do I run the GCL loop locally? | `scripts/gcl_runner.py --help` |
| How do I see the parsed rubric? | `python3 scripts/gcl_runner.py show-rubric --skill <name>` |
| How do I generate a closed-loop test? | `tests/gcl_dashboard_test.py` |
| Where can I ask a maintainer? | Open a GitHub issue with the `gcl-rollout` label |

---

## See also

- [`AGENTS.md`](../AGENTS.md) — the GCL spec (§1-12)
- [`docs/GCL_RETROSPECTIVE.md`](GCL_RETROSPECTIVE.md) — post-rollout lessons
- [`docs/SDK_VERSION_LOCKING.md`](SDK_VERSION_LOCKING.md) — how to pin SDK/CLI versions
- [`scripts/gcl_runner.py`](../scripts/gcl_runner.py) — the Orchestrator
- [`scripts/gcl_dashboard.py`](../scripts/gcl_dashboard.py) — the Phase 3 dashboard
- [`tests/gcl_ground_truth.jsonl`](../tests/gcl_ground_truth.jsonl) — expert-labeled test set
