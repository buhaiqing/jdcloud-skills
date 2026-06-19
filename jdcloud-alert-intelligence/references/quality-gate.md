# Quality Gate (GCL) for jdcloud-alert-intelligence

> Concrete quality-gate guide for this skill.
> Repository-wide GCL spec: [`AGENTS.md` §Quality Gate](../../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this read-only skill (per `AGENTS.md` §8).

## Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **5** | `AGENTS.md` §8 default for `jdcloud-alert-intelligence` (optional, read-only) |
| `rubric_version` | `v2` | see [rubric.md](./rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified with `jdcloud-audit-ops` |
| `safety_confirm_required` | **false** | read-only by mandate |
| `hallucination_check` | **optional** | Phase 6 H layer; optional for this read-only skill |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `../docs/failure-patterns.md` |

## Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify workflow step
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► jdc monitor (primary) → SDK (after 3 fails)
   │                              generate command/payload (DO NOT execute yet)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (optional for alert-intelligence)  - CLI parameter existence
   │                                      - JSON structure compliance
   │
   ├── PASS → [1a] Execute (run the jdc/SDK call)
   ├── FAIL → [1b] Regenerate (H retriggers G with hallucination report; max 1 retry)
   │         still FAIL → HALT with "HALLUCINATION_ABORT"
   ▼
[2] Critic (C)               ──► isolated context, blind to user request
   │                              score every rubric dimension
   │                              assess test accuracy + regression gate
   ▼
[3] Orchestrator decider
   ├─ HALLUCINATION_ABORT     → ABORT (no partial)
   ├─ Safety=0 / blocking     → ABORT
   ├─ all pass                → RETURN
   ├─ iter<5 & not all pass   → RETRY (inject suggestions)
   └─ iter=5 & not all pass   → RETURN_BEST
```

## Hallucination Detection Layer (H) — Optional

> Catch LLM-generated jdc/SDK calls that contain structurally invalid elements
> **before** they reach the JD Cloud Monitor API.

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` in `jdc monitor` commands exists | Compare against [api-sdk-usage.md](./api-sdk-usage.md) operation tables |
| **JSON Structure Compliance** | For alarm history query parameters | Validate field names match Monitor API spec |

**Termination:**

| Condition | Action |
|---|---|
| **H_PASS** | Continue to Execute |
| **H_FAIL → Regenerate** | Inject hallucination report into G; max 1 retry |
| **HALLUCINATION_ABORT** | HALT — structural hallucinations persist after regeneration |

## Reflexion Integration

> Cross-session failure memory. See `AGENTS.md` §11 and [../docs/failure-patterns.md](../docs/failure-patterns.md).

The Orchestrator MAY lazy-load `../docs/failure-patterns.md`, filter by
`jdcloud-alert-intelligence`, and inject the top-3 relevant patterns into the
Generator context as **hints** (not constraints).

When a GCL iteration fails, the Orchestrator SHOULD extract a structured failure
pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter|runtime|cross_skill",
    "skill": "jdcloud-alert-intelligence",
    "command": "jdc --output json monitor describe-alarm-history ...",
    "error": "...",
    "fix": "...",
    "reusable": true
  }
}
```

## Artifacts

- Rubric (concrete scoring rules): [rubric.md](./rubric.md)
- Prompt templates (G / C / O / H): [prompt-templates.md](./prompt-templates.md)
- Failure patterns (cross-session memory): [../docs/failure-patterns.md](../docs/failure-patterns.md)

## Workflow-step-specific behavior

- **Step 1. 加载时间窗告警** — Time window MUST be explicit; default 24h;
  max 15d. Time window > 15d → ABORT.
- **Step 2. 聚合** — Aggregation key `(service, resource, metric)` MUST be
  complete for every cluster. Dropped clusters MUST cite a suppression rule.
- **Step 3. 分级** — Each cluster gets P0-P3 per `severity-matrix.md` with
  the 4-tuple citation `(metric_value, threshold, time_window, jdc_query)`.
- **Step 4. 抑制** — Every suppression MUST cite the matching rule in
  `suppression-rules.md`.
- **Step 5. 报告输出** — Every P0/P1 cluster MUST have a 下一跳建议 pointing
  to a specific `jdcloud-*-ops` operation. The report MUST NOT recommend
  `delete` / `disable` / `modify` on an alert rule.
