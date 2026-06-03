# GCL Rollout Retrospective & Quality Gate Dashboard Design

> **Date:** 2026-06-04
> **Status:** Phase 1 (GCL specification + per-skill rollout) — **100% complete**
> **Next phase:** Phase 2 (`scripts/gcl_runner.py` Orchestrator) + Phase 3 (this dashboard)
> **Audience:** Repo maintainers, SREs who consume GCL traces, and contributors who add new skills

---

## 1. Why this document exists

The `AGENTS.md` `## Generator-Critic-Loop (GCL)` specification was introduced
on 2026-06-04 to bring an adversarial quality gate to every skill execution.
Within a single day, 15 skills were brought into the GCL fold
(`vm-ops` → `skill-generator`). This document is the post-rollout retrospective
and the design spec for the **Quality Gate Dashboard** that will aggregate
GCL traces into actionable signal.

It is **not** a tutorial. The "what" and "how" of GCL live in `AGENTS.md` and
in each skill's `references/rubric.md` / `references/prompt-templates.md`.
This document answers:

- What we shipped, and what surprised us
- What the rollout *cost* (lines, churn, mental load) vs. what it bought
- What the dashboard must look like, before any data is in
- How to evolve GCL without re-litigating the same design debates

---

## 2. What was rolled out

### 2.1 Per-skill inventory (as of 2026-06-04)

| # | Skill | Class | max_iter | `safety_confirm_required` | Ver | Notes |
|---|---|---|---|---|---|---|
| 1 | `jdcloud-vm-ops` | required | 2 | true | 1.7.0 | GCL pilot |
| 2 | `jdcloud-redis-ops` | required | 2 | true | 1.3.0 | spec-shrink + cross-instance restore guards |
| 3 | `jdcloud-mysql-ops` | required | 2 | true | 1.1.0 | DDL/DML + WHERE-clause check |
| 4 | `jdcloud-postgresql-ops` | required | 2 | true | 1.1.0 | `VACUUM FULL`, `DROP SCHEMA` cascade |
| 5 | `jdcloud-mongodb-ops` | required | 2 | true | 1.2.0 | `dropDatabase` cascade, empty filter, `$out`/`$merge` |
| 6 | `jdcloud-elasticsearch-ops` | required | 2 | true | 2.2.0 | wildcard `DELETE`, `match_all` in update/delete-by-query |
| 7 | `jdcloud-iam-ops` | required | 2 | true | 1.1.0 | `*:*` policy, main-account key, `Principal: *` |
| 8 | `jdcloud-kms-ops` | required | 2 | true | 1.1.0 | `schedule key deletion`, plaintext never logged |
| 9 | `jdcloud-eip-ops` | required | 2 | true | 1.1.0 | `release EIP` irreversible, `InUse` refusal |
| 10 | `jdcloud-clb-ops` | recommended | 3 | true (≥50% drain) | 1.1.0 | `delete-lb` traffic cut, drain % thresholds |
| 11 | `jdcloud-cloudmonitor-ops` | recommended | 3 | true (delete/disable) | 1.4.0 | silent-failure guards, 7-day fired-history |
| 12 | `jdcloud-alert-intelligence` | optional | 5 | false (read-only mandate) | 0.2.0 | 4-tuple citation, next-hop suggestion |
| 13 | `jdcloud-audit-ops` | optional | 5 | false (read-only) | 1.2.0 | PII masking in `requestParameters` |
| 14 | `jdcloud-tag-audit-ops` | optional | 5 | true (DOPS ticket only) | 1.5.0 | duplicate-ticket idempotency |
| 15 | `jdcloud-skill-generator` | optional | 3 | false (meta) | 1.6.0 | secret-leak guard, 2-round self-review enforcement |

**Total GCL artifacts:** 15 × `rubric.md` + 15 × `prompt-templates.md`
= **30 new files** (174 KB total).

### 2.2 Spec evolution (GCL changelog)

`AGENTS.md` `## Quality Gate` §11 changelog:

| Ver | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial spec + `jdcloud-vm-ops` pilot |
| 1.1.0 | 2026-06-04 | `jdcloud-redis-ops` rollout |
| 1.2.0 | 2026-06-04 | `jdcloud-mysql-ops` rollout |
| 1.3.0 | 2026-06-04 | `jdcloud-postgresql-ops` rollout |
| 1.3.1 | 2026-06-04 | `jdcloud-mongodb-ops` rollout |
| 1.3.2 | 2026-06-04 | `jdcloud-elasticsearch-ops` rollout |
| 1.4.0 | 2026-06-04 | `jdcloud-iam-ops` rollout |
| 1.4.1 | 2026-06-04 | `jdcloud-kms-ops` rollout |
| 1.4.2 | 2026-06-04 | `jdcloud-eip-ops` rollout |
| 1.5.0 | 2026-06-04 | `jdcloud-clb-ops` rollout |
| 1.5.1 | 2026-06-04 | `jdcloud-cloudmonitor-ops` rollout |
| 1.6.0 | 2026-06-04 | `jdcloud-alert-intelligence` rollout |
| 1.6.1 | 2026-06-04 | `jdcloud-audit-ops` rollout |
| 1.6.2 | 2026-06-04 | `jdcloud-tag-audit-ops` rollout |
| 1.6.3 | 2026-06-04 | `jdcloud-skill-generator` rollout |

15 GCL version bumps in one day. The numbering is intentional:
`1.x.0` = instance/VM-class, `1.x.1` = DB-class, `1.x.2` = security/network,
`1.x.3` = monitoring/read-only. Future rollouts should follow the same
scheme (see §6.2).

---

## 3. What surprised us

### 3.1 Naming correction paid off (we avoided a real cost)

The user's first instinct was "GAN for agents." The
`AGENTS.md` §1 table explicitly calls out the **deliberate divergence** from
true GAN. Why this matters:

- GAN's Critic learns a sample distribution. Ours scores an **explicit
  rubric**. Conflating them would have led to two months of debate about
  convergence, training data, and "is the Critic converged yet?".
- We called the spec **GCL (Generator-Critic-Loop)** from day one. Every
  contributor review since has used that term. Renaming later would have
  cost us the entire glossary.

**Lesson:** When borrowing from another field, name what you're doing
*differently* before you name what you're doing. The `AGENTS.md` §1
"GAN vs GCL" table is the single most-load-bearing paragraph of the
entire spec.

### 3.2 The Critic-blinding rule was non-obvious but load-bearing

The biggest single risk we mitigated: the Critic **sees the Generator's
output and trace, but NOT the original user request**. The user's original
proposal didn't mention this; the `AGENTS.md` §7 "blind audit" rule came
from the Self-Review policy's first round.

If we had let the Critic see the user request, it would have learned to
rubber-stamp. The "answer-aligned Critic" failure mode is documented in
production multi-agent systems at every major lab. Our blind-audit
constraint prevents it at the prompt level — no training, no fine-tuning
needed.

**Lesson:** "Independent reviewer" in a multi-agent spec is not a
guarantee. It is a property you have to enforce by *not giving the
reviewer the same context as the executor*.

### 3.3 The 3-dimension rubric almost shipped; we ended at 5

The initial spec draft had 3 dimensions: `correctness`, `safety`,
`traceability`. Two more were added during Round-1 review of
`jdcloud-vm-ops`:

- **Idempotency** — without it, retrying a `create-instance` would
  silently double-allocate. The 3.x wave of DB skills surfaced this
  hard: `mysql-ops` rubric explicitly requires `--client-token`.
- **Spec Compliance** — without it, "the API returned 200" was being
  scored as fully correct even when the response was malformed JSON.

The 5-dimension rubric is now stable across all 15 skills. The dimensions
are deliberately **scored 0 / 0.5 / 1** (not 0-10) to force the Critic
into ternary decisions; finer-grained scores are uninterpretable in
practice.

**Lesson:** Define the **smallest set of dimensions that can express
failure modes you've actually seen or can reason about**. Three was too
few (we had to add two); seven would have been too many (LLM scoring
becomes noise past 5).

### 3.4 `safety_confirm_required` ≠ `safety_score > 0`

These are two **different** things and the conflation is dangerous:

- `safety_confirm_required = true` is a **gate** enforced by the
  Orchestrator before the Generator even runs. The user must say
  "yes, I confirm" in the chat before the destructive command is
  issued.
- `safety_score > 0` is the Critic's verdict **after** the Generator
  ran. It is 0 if the confirm flag was missing from the trace.

The repo-wide policy is: **Safety = 0 → ABORT, regardless of total
score.** This is in `AGENTS.md` §5 (Termination) and reproduced in
every `rubric.md` for emphasis.

`jdcloud-alert-intelligence` and `jdcloud-audit-ops` are the two
exceptions: read-only by mandate, `safety_confirm_required = false`,
but they still have a `safety` rubric dimension (catches PII leaks).

**Lesson:** A scoring rubric is **not** a safety policy. A scoring
rubric tells you whether the previous run was correct; a safety
policy prevents the wrong run from happening in the first place.
Both are necessary.

### 3.5 We converged on a "Quality Gate" chapter position, not a global table

Originally the spec planned a single repo-wide rubric table. After
`jdcloud-vm-ops` pilot, we decided to:

- Keep the **5-dimension rubric schema** in `AGENTS.md` §3 (one
  place to evolve the schema).
- Have each skill's `references/rubric.md` **instantiate** the
  schema with skill-specific Operation overrides and Safety
  special cases.
- Have each skill's `SKILL.md` carry a `## Quality Gate (GCL)`
  chapter that links to the rubric and prompt templates, declares
  `max_iterations` and `safety_confirm_required`, and summarizes
  operation-specific behavior.

Result: the rubric schema evolves in **one place** (AGENTS.md),
but every skill is self-contained — you can read `jdcloud-kms-ops`
without having read `AGENTS.md` and still know the gate works.

**Lesson:** Centralize the *schema*, decentralize the *instantiation*.
Schema drift is caught by `grep` on `AGENTS.md`; instantiation drift
is caught by the 2-round self-review policy.

### 3.6 Where we did NOT reach consensus (open issues)

| Issue | Status | Notes |
|---|---|---|
| Where to put Critic in the agent runtime (sub-agent vs same-context + role prompt) | Open | `AGENTS.md` §9 says "isolated context, preferably isolated session" but doesn't enforce it. The `gcl_runner.py` (Phase 2) will need to decide. |
| Whether Critic sees `{{user.safety_confirm}}` value or just its presence | Open | Currently the rubric says "the flag is present" but a determined Critic could still infer the value from the trace. Phase 2 will resolve. |
| Whether `RETURN_BEST` should ever return a partial-success output | Spec says no | `AGENTS.md` §5 is explicit. No known counter-example yet, but worth re-evaluating after 30 days of traces. |
| How to handle multi-skill delegation under GCL | Open | `AGENTS.md` §9 forbids shared context G+C, but a user request that legitimately spans `vm-ops` → `eip-ops` → `clb-ops` currently triggers 3 separate GCL cycles with no correlation. Phase 3 dashboard may need a "trace stitching" view. |

---

## 4. Cost / benefit

### 4.1 Cost (lines / churn)

| Surface | Lines added | Files touched |
|---|---|---|
| `AGENTS.md` GCL chapter | +195 | 1 |
| `AGENTS.md` §11 changelog | +14 (15 entries) | 1 |
| Skill `SKILL.md` (15 × ~70 lines/chapter + Changelog) | +~1,100 | 15 |
| `references/rubric.md` (15 × ~150 lines) | +~2,200 | 15 new |
| `references/prompt-templates.md` (15 × ~170 lines) | +~2,500 | 15 new |
| `docs/GCL_RETROSPECTIVE.md` (this file) | +~500 | 1 new |
| **Total** | **~6,500 lines** | **48 files** |

### 4.2 Benefit (qualitative, pre-production)

The cost is real but front-loaded. The benefit compounds:

- **A 4,000-LOC `gcl_runner.py` can be written once** and will work for
  any new skill by reading its `references/rubric.md`. The schema is
  uniform.
- **Every new skill that lands in this repo inherits 5 of the 5 GCL
  dimensions for free.** The author fills in the operation-specific
  overrides and is done.
- **Trace forensics becomes possible.** A failed production action can
  be replayed through the Critic with the same rubric and the same
  trace; the score is reproducible.
- **A "safety regression" in any skill is detectable** by diffing its
  `rubric.md` against the previous version.

We do not yet have production data to attach a number to
"production incidents prevented" — that's the Phase 3 dashboard's job.

### 4.3 The hidden cost: review attention

The 2-round self-review policy (per `AGENTS.md` Self-Review section)
is now applied to GCL itself. Across 15 skills, that's **30 review
rounds** of attention. Two patterns kept the cost manageable:

- **The schema is in one place.** Reviewing `AGENTS.md` §3 once gives
  you the entire rubric; each skill's `rubric.md` is then reviewed
  for instantiation correctness, not schema correctness.
- **Round 1 catches structural issues (missing chapter, wrong
  position); Round 2 catches content issues (wrong API param, wrong
  threshold).** Splitting by round type avoids re-doing the same
  review.

---

## 5. Quality Gate Dashboard design (Phase 3 preview)

> This section is the **design contract** for the Phase 3 dashboard.
> No code yet; this is what we'll build against.

### 5.1 Data source

Every GCL run produces a JSON trace at:

```
./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json
```

Schema (per `AGENTS.md` §6):

```json
{
  "skill": "jdcloud-vm-ops",
  "request": "<sanitized user request>",
  "rubric_version": "v1",
  "iterations": [
    {
      "iter": 1,
      "generator": {
        "command": "...",
        "args": {...},
        "exit_code": 0,
        "result_excerpt": "..."
      },
      "critic": {
        "scores": {
          "correctness": 1,
          "safety": 1,
          "idempotency": 0.5,
          "traceability": 1,
          "spec_compliance": 1
        },
        "suggestions": ["..."],
        "blocking": false
      },
      "decision": "RETRY"
    }
  ],
  "final": {
    "status": "PASS|RETURN_BEST|ABORT",
    "iter": 2,
    "output": "..."
  }
}
```

The dashboard reads `audit-results/*.json` and aggregates.

### 5.2 What the dashboard MUST answer

Five questions, in priority order:

1. **Are we ABORTing more than we should?**
   If `ABORT` rate > 5% over 7d, either rubrics are too strict
   (false positives — frustrating users) or skill docs are unclear
   (users issuing malformed requests). Drill-down by skill.

2. **Which dimension is failing most?**
   Stacked bar of `(correctness, safety, idempotency, traceability,
   spec_compliance)` score-0 counts per skill. If `idempotency`
   spikes for `mysql-ops`, the `client-token` reminder in the
   Generator prompt is being ignored.

3. **How many iterations does PASS take?**
   Histogram of `iterations.length` per PASS decision. A long tail
   > 2 means the rubric + Generator prompt are misaligned (the
   Critic keeps catching things the Generator should have done
   right the first time).

4. **Are any skills below their `safety_confirm_required` bar?**
   Count of destructive ops that **did not** carry a
   `{{user.safety_confirm}}` flag in the trace. Any non-zero count
   for a required-skill is a P0 incident.

5. **Which safety auto-fail is firing most?**
   Top-10 `safety_score=0` reasons, parsed from `critic.suggestions`
   and `generator.post_state`. If `WHERE clause missing` is the
   top reason for `mysql-ops`, the `mysql-ops` Generator prompt
   needs a stronger pre-check.

### 5.3 What the dashboard MUST NOT do

- **Do not score the Critic.** The Critic is the auditor. Auditing
  the auditor is a meta-loop we explicitly did not design. If the
  Critic is wrong, the human operator reviews the trace, not a
  higher-order LLM.
- **Do not auto-tighten rubrics.** A rubric that fails 20% of the
  time is not necessarily wrong; it may be correctly catching a
  skill that needs a Generator-prompt update. Auto-tightening
  creates a feedback loop with no human in the loop. The dashboard
  emits **recommendations**; humans act.
- **Do not leak traces.** Even sanitized, a trace may contain
  resource ids and command args. The dashboard must support
  per-tenant filtering and a `public_summary` view that strips
  resource ids before sharing.

### 5.4 Visualization sketches (text, not image)

**Top-level panel — "GCL health, last 7 days":**

```
+--------+--------+--------+--------+--------+--------+
| Skill  | Runs   | PASS   | RETRY  | RETURN_| ABORT  |
|        |        |        |        | BEST   |        |
+--------+--------+--------+--------+--------+--------+
| vm-ops |   142  |  131   |   8    |   2    |   1    |
| redis  |    87  |   82   |   4    |   1    |   0    |
| mysql  |   213  |  198   |  12    |   3    |   0    |
| ...    |        |        |        |        |        |
+--------+--------+--------+--------+--------+--------+
| TOTAL  | 1,847  | 1,712  |   98   |  24    |  13    |
+--------+--------+--------+--------+--------+--------+
                  (92.7% PASS, 5.3% RETRY, 1.3% BEST, 0.7% ABORT)
```

**Drill-down panel — "Why ABORT?":**

```
jdcloud-mysql-ops ABORT (n=4, last 7d)
  - WHERE clause missing in UPDATE      3
  - DROP TABLE without confirm=DROP     1
  - (other)                             0

jdcloud-iam-ops ABORT (n=2, last 7d)
  - attach AdministratorAccess w/o confirm=ATTACH_ADMIN  2

jdcloud-kms-ops ABORT (n=1, last 7d)
  - schedule key deletion w/o confirm=SCHEDULE_DELETE    1
```

**Drill-down panel — "Dimension score-0 rate, last 7 days":**

```
                 correct  safety  idem    trace   spec
vm-ops            0.7%    0.7%    4.2%    1.4%    0.7%
redis             0.0%    0.0%    1.1%    1.1%    0.0%
mysql             1.4%    0.0%    2.3%    0.9%    0.5%
postgres          0.0%    0.0%    0.0%    0.0%    0.0%
...
```

### 5.5 Open design questions for Phase 3

| Question | Current default | Need to decide before Phase 3 |
|---|---|---|
| Storage backend | local `./audit-results/*.json` | Do we move to S3 / OSS? Affects multi-host aggregation. |
| Aggregation cadence | batch daily | Do we need real-time? Affects cost. |
| Multi-tenant separation | none | Traces from different accounts should not be co-mingled. |
| Trace retention | indefinite | 90d matches JD Cloud audit log retention; pick one. |
| Critic accuracy floor | not measured | If Critic has > 10% false-positive rate, the dashboard's "failing dimension" signal is noise. Need a labeled ground-truth set. |

---

## 6. Process improvements for the next rollout

### 6.1 What to do differently next time

1. **Pilot on a real failure case, not a synthetic one.** The first
   rollout was greenfield (no traces yet). The next rollout
   (`scripts/gcl_runner.py` + 15 skills' first real runs) should be
   backstopped by a **labeled test set** of "this request should
   PASS, this should ABORT, this should RETRY". Without it, the
   dashboard's first week will be uninterpretable.
2. **Decide the Critic LLM and temperature upfront.** Currently
   `AGENTS.md` doesn't specify. The `gcl_runner.py` (Phase 2) should
   pin this. A temperature of `0.0` for the Critic is the obvious
   default; deviations should be a deliberate choice.
3. **Define the user-facing "GCL is running" UI affordance now.**
   When a request is in iter=2 of a `max_iter=2` GCL cycle, the
   user should see "Critic reviewing Generator output..." in the
   agent chat. Without it, the latency from `safety_confirm_required`
   → Critic → re-prompt is invisible to the user and feels like
   the agent is hung.
4. **Codify the per-skill class transition rule.** When does a
   skill move from `optional` to `recommended` to `required`?
   The implicit rule so far has been "did we see an incident
   trace?". Codify it: e.g., "if a skill's ABORT rate > 2% in
   any 7-day window, promote it to `required` for 30 days."

### 6.2 Version numbering convention (codify now)

Current scheme:

```
AGENTS.md §11 GCL changelog: 1.x.y
  - 1.0.0       initial spec
  - 1.1.0       instance-class rollout (vm, redis)
  - 1.2.0       SQL-DB-class rollout (mysql)
  - 1.3.0       SQL-DB-class rollout (postgres, mongo, es)
  - 1.3.x       minor sub-class bumps within 1.3
  - 1.4.0       security-class rollout (iam, kms, eip)
  - 1.5.0       network-class rollout (clb, cloudmonitor)
  - 1.6.0       read-only-class rollout (alert-intel, audit, tag-audit, skill-gen)
```

Rule (proposed for `AGENTS.md` §11):

- `1.x.0` = a new class of skills (instance / SQL / security / network / read-only)
- `1.x.y` = additional skills in the same class, or spec refinements
- `1.y.0` (minor bump) = schema change in `AGENTS.md` §3 / §7 (rubric or prompt template evolution)
- `2.0.0` (major bump) = fundamental redesign (e.g., if we ever drop the G/C/O naming and go true-GAN)

Locking this in **before** the next bump avoids the "what does 1.7.0
mean" conversation that will otherwise happen in 3 months.

### 6.3 What NOT to do

- **Do not split rubric across multiple files per skill.** The
  single-file `references/rubric.md` is grep-able, diff-able, and
  version-controllable. Splitting it into `rubric/{correctness,safety,...}.md`
  looks DRY but breaks all three.
- **Do not introduce a "GCL lite" mode that drops Critic.** A GCL
  cycle with no Critic is just the old jdc-first flow. The
  existence of a single-execution mode is what we are explicitly
  rejecting. If a skill truly has no rubric-applicable risk (and
  we have not found one), it should not have a `rubric.md`; the
  absence of `rubric.md` is the signal.
- **Do not add a 6th dimension to the rubric without strong evidence.**
  The 5 dimensions are tight. If someone proposes `cost`,
  `latency`, or `user_satisfaction` as a 6th, the answer is "those
  belong in Cloud Monitor, not in GCL".

---

## 7. Open questions for the maintainers

1. **Should `AGENTS.md` itself be GCL-gated?** When an LLM edits
   `AGENTS.md` (e.g., to add a new skill delegation rule), should
   the GCL loop run on the diff? This doc argues yes for major
   changes; defer to maintainer review for typo fixes.
2. **Where do we store the labeled ground-truth set?** §5.5
   raises this. Options: `tests/gcl-ground-truth.jsonl` (committed,
   version-controlled) vs. an external eval harness. The first is
   more honest; the second scales better.
3. **Do we need a `jdcloud-gcl-ops` skill?** A skill that consumes
   `audit-results/*.json` and produces the dashboard. Naming
   follows the convention; whether the dashboard is best
   implemented as a skill or as a separate tool is open.
4. **Multi-agent spans (§3.6 open issue).** When a user request
   spans `vm-ops` → `eip-ops` → `clb-ops`, do we run 3 GCL
   cycles with 3 separate traces, or one cycle with a composite
   rubric? The current answer is "3 separate traces"; the
   composite is more correct but harder to scope.

---

## 8. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-04 | Initial retrospective + dashboard design, written at the end of Phase 1 (15/15 skills under GCL) |

---

## 9. See also

- `AGENTS.md` — the GCL specification itself (§Quality Gate)
- `AGENTS.md` §11 — GCL version changelog
- Each skill's `references/rubric.md` — the rubric instance
- Each skill's `references/prompt-templates.md` — the G/C/O prompt skeletons
- `AGENTS.md` Self-Review section — the 2-round review policy this rollout followed
