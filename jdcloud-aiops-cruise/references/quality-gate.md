# Quality Gate (GCL) for jdcloud-aiops-cruise

> Concrete quality-gate guide for this skill.
> Repository-wide GCL spec: [`AGENTS.md` §Quality Gate](../../AGENTS.md#generator-critic-loop-gcl--adversarial-quality-gate).
> The quality gate is **optional** for this read-only skill (per `AGENTS.md` §8).

## Parameters (override `AGENTS.md` §8 defaults)

| Parameter | Value | Reason |
|---|---|---|
| `max_iterations` | **3** | `AGENTS.md` §8 default for optional skills |
| `rubric_version` | `v2` | see [rubric.md](./rubric.md) |
| `trace_path` | `./audit-results/gcl-trace-YYYYMMDD-HHMMSS.json` | unified trace path |
| `safety_confirm_required` | **false** | read-only cruise; no mutations |
| `hallucination_check` | **optional** | Phase 6 H layer; optional for this read-only skill |
| `reflexion_integration` | **enabled** | Phase 7 lightweight Reflexion; loads `../docs/failure-patterns.md` |

## Loop overview

```
User request
   │
   ▼
[0] Orchestrator pre-flight  ──► load rubric, classify operation
   │                              optionally load failure-patterns.md
   ▼
[1] Generator (G)            ──► Python scripts (Phase 1 sniff + Phase 2 analyze)
   │                              generate cruise commands (DO NOT execute mutations)
   ▼
[1.5] Hallucination Detection (H) ──► pre-execution structural validity check
   │   (optional for aiops-cruise)    - CLI parameter existence
   │                                   - JSON structure compliance
   │                                   - script import path validity
   │
   ├── PASS → [1a] Execute (run the script/command)
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
   ├─ iter<3 & not all pass   → RETRY (inject suggestions)
   └─ iter=3 & not all pass   → RETURN_BEST
```

## Hallucination Detection Layer (H) — Optional

> Catch LLM-generated cruise commands that contain structurally invalid elements
> **before** they reach the JD Cloud API.

| Category | Check | Method |
|---|---|---|
| **CLI Parameter Existence** | Verify every `--flag` in `jdc <product>` commands exists | Compare against [api-sdk-usage.md](./api-sdk-usage.md) operation tables |
| **JSON Structure Compliance** | For script input/output JSON payloads | Validate field names match API spec |
| **Script Import Path Validity** | Verify `sys.path` imports follow three-phase directory structure | Check `_project_dir` pattern per `AGENTS.md` |

**Termination:**

| Condition | Action |
|---|---|
| **H_PASS** | Continue to Execute |
| **H_FAIL → Regenerate** | Inject hallucination report into G; max 1 retry |
| **HALLUCINATION_ABORT** | HALT — structural hallucinations persist after regeneration |

## Reflexion Integration

> Cross-session failure memory. See `AGENTS.md` §11 and [../docs/failure-patterns.md](../docs/failure-patterns.md).

The Orchestrator MAY lazy-load `../docs/failure-patterns.md`, filter by
`jdcloud-aiops-cruise`, and inject the top-3 relevant patterns into the
Generator context as **hints** (not constraints).

When a GCL iteration fails, the Orchestrator SHOULD extract a structured failure
pattern and append it to the trace:

```json
{
  "failure_pattern": {
    "category": "cli_parameter|runtime|cross_skill",
    "skill": "jdcloud-aiops-cruise",
    "command": "python scripts/01-perceive/cruise_sniff.py ...",
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

## Operation-specific behavior

- **Phase 1: 嗅探 (Perceive)** — Resource discovery via `cruise_sniff.py`. MUST use customer tag filter. H layer validates CLI parameters for all `jdc` discovery commands. MUST NOT return/persist full-account resource lists.
- **Phase 2: 深度巡检 (Reason)** — Analysis via `cruise_link.py` + analyzers. MUST follow three-phase import path convention. MUST NOT execute any mutation.
- **Phase 3: 执行建议 (Execute)** — Read-only suggestions only. MUST delegate all mutations to corresponding ops skills. H layer validates no mutation commands are generated.
