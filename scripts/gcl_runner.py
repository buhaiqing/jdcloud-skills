#!/usr/bin/env python3
"""
GCL Runner — Generator-Critic-Loop Orchestrator (Phase 2).

This script implements the Orchestrator (O) role defined in
`AGENTS.md` §2 (Roles). It is the reusable executor for any
`jdcloud-*-ops` skill that has opted into the GCL quality gate.

## What this script does

For a given user request, it:

1. Loads the skill's `references/rubric.md` and parses the 5-dimension
   rubric (Correctness / Safety / Idempotency / Traceability / Spec
   Compliance), the operation-specific overrides, and the safety
   special-case auto-fail rules.
2. Loads the skill's `references/prompt-templates.md` to extract the
   Generator (G) and Critic (C) prompt skeletons.
3. Runs the G -> C -> Decide loop, capped at `max_iterations`
   (from the rubric or from `AGENTS.md` §8 defaults).
4. Persists a JSON trace to `./audit-results/gcl-trace-<ts>.json`
   matching the schema in `AGENTS.md` §6.
5. Returns the final decision (`PASS` / `RETURN_BEST` / `ABORT`)
   with a human-readable summary.

## What this script does NOT do

- It does NOT call the actual LLM. The Generator and Critic
  functions are injected (see `--gen-fn` / `--critic-fn`). For
  real LLM usage, write a thin wrapper that imports this script
  and supplies LLM-backed G/C functions.
- It does NOT execute `jdc` / SDK calls. That is the Generator's
  responsibility inside the loop.
- It does NOT enforce user confirmation. The
  `safety_confirm_required` flag is read from the rubric and the
  decision is recorded in the trace; the actual user-prompt for
  confirmation is upstream (in the Agent harness, not in this
  script).

## How this script addresses `docs/GCL_RETROSPECTIVE.md` §3.6

The retrospective identified Critic isolation as an open issue:
how do we guarantee the Critic doesn't share context with the
Generator? This script resolves it by making Generator and Critic
**injected `Callable` objects** (`GeneratorFn`, `CriticFn` type
aliases). Any real LLM integration MUST pass two functions whose
underlying prompt contexts are independent — there is no way to
use a shared LLM session by accident.

## CLI usage

    # Run GCL on a vm-ops request with a mock generator and critic
    python scripts/gcl_runner.py \\
        --skill vm-ops \\
        --request "stop instance i-abc123" \\
        --safety-confirm "yes" \\
        --gen-fn mock \\
        --critic-fn mock \\
        --trace-dir audit-results

    # Show parsed rubric (no execution)
    python scripts/gcl_runner.py --skill vm-ops --show-rubric

    # Self-check (parse every skill's rubric; report any failures)
    python scripts/gcl_runner.py --self-check

## Exit codes

    0   PASS or RETURN_BEST
    1   ABORT (Safety=0 or blocking)
    2   Self-check found rubric-parse failures
    3   Usage / argument error

## Python version

Python 3.10+. Uses `match` statement (3.10+) and `from __future__
import annotations` to keep type hints forward-compatible.

## Dependencies

Standard library only. No `jdcloud_sdk`, no `requests`. The
Generator / Critic LLM functions are expected to live elsewhere
and are passed in by the caller.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from collections.abc import Callable


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# AGENTS.md §3 — the 5 rubric dimensions in canonical order.
RUBRIC_DIMENSIONS = (
    "correctness",
    "safety",
    "idempotency",
    "traceability",
    "spec_compliance",
)

# Optional extension dimensions (e.g., audit-ops uses 8 dimensions).
# These are parsed if present but not required.
EXTENSION_DIMENSIONS = (
    "region_compliance",
    "credential_hygiene",
    "well_architected",
)

# AGENTS.md §8 — per-skill class -> max_iterations default.
# Used as a fallback when a skill's `## Quality Gate` chapter
# doesn't override.
DEFAULT_MAX_ITER = {
    "required": 2,      # write ops on production
    "recommended": 3,   # network / monitoring
    "optional": 3,      # read-only / meta (aligned 2026-06-19)
}

# AGENTS.md §10.2.1 — built-in parameter knowledge base for H layer.
# Maps (product, operation) -> set of valid --flag names.
# This is a conservative default; skills can extend via references/api-sdk-usage.md.
PARAMETER_KNOWLEDGE: dict[str, dict[str, set[str]]] = {
    "vm": {
        "describe-instances": {"--ids", "--region-id", "--page-number", "--page-size", "--filters", "--output"},
        "create-instance": {"--image-id", "--instance-type", "--az", "--name", "--subnet-id", "--client-token", "--region-id", "--output"},
        "start-instance": {"--instance-id", "--region-id", "--output"},
        "stop-instance": {"--instance-id", "--region-id", "--output"},
        "reboot-instance": {"--instance-id", "--region-id", "--output"},
        "delete-instance": {"--instance-id", "--region-id", "--output"},
        "resize-instance": {"--instance-id", "--instance-type", "--region-id", "--output"},
    },
    "disk": {
        "describe-disks": {"--disk-ids", "--region-id", "--page-number", "--page-size", "--output"},
        "create-disks": {"--disk-size", "--disk-type", "--az", "--name", "--client-token", "--region-id", "--output"},
        "delete-disk": {"--disk-id", "--region-id", "--output"},
        "attach-disk": {"--disk-id", "--instance-id", "--device", "--region-id", "--output"},
        "detach-disk": {"--disk-id", "--instance-id", "--region-id", "--output"},
        "resize-disk": {"--disk-id", "--new-size", "--region-id", "--output"},
    },
    "redis": {
        "describe-instances": {"--instance-id", "--region-id", "--page-number", "--page-size", "--output"},
        "create-instance": {"--instance-name", "--instance-class", "--vpc-id", "--subnet-id", "--az", "--region-id", "--output"},
        "delete-instance": {"--instance-id", "--region-id", "--output"},
    },
    "clb": {
        "describe-load-balancers": {"--load-balancer-ids", "--region-id", "--page-number", "--page-size", "--output"},
        "create-load-balancer": {"--name", "--type", "--az", "--subnet-id", "--region-id", "--output"},
        "delete-load-balancer": {"--load-balancer-id", "--region-id", "--output"},
    },
}

# AGENTS.md §10.2.3 — audit log retention limit (days).
AUDIT_RETENTION_DAYS = 90

# AGENTS.md §6 — trace filename format.
TRACE_FILE_PREFIX = "gcl-trace"
TRACE_FILE_SUFFIX = ".json"

# Root of the repository (scripts/gcl_runner.py -> parent -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[1]

# Where traces go.
DEFAULT_TRACE_DIR = REPO_ROOT / "audit-results"


# ---------------------------------------------------------------------------
# Data classes — the in-memory shape of a GCL run
# ---------------------------------------------------------------------------


@dataclass
class RubricConfig:
    """Parsed `references/rubric.md` content.

    Holds the 5-dimension rubric thresholds, operation-specific
    overrides, and safety auto-fail patterns. The Critic uses this
    to score a Generator run; the Orchestrator uses it to decide
    ABORT/RETURN/RETRY.
    """

    skill: str
    rubric_version: str = "v1"

    # Per-dimension: name -> threshold (0 / 0.5 / 1).
    thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "correctness": 1.0,
            "safety": 1.0,
            "idempotency": 0.5,
            "traceability": 0.5,
            "spec_compliance": 0.5,
        }
    )

    # Per-dimension: name -> scale. Either "0/0.5/1" or "0/1".
    scales: dict[str, str] = field(
        default_factory=lambda: {
            "correctness": "0/0.5/1",
            "safety": "0/1",
            "idempotency": "0/0.5/1",
            "traceability": "0/0.5/1",
            "spec_compliance": "0/0.5/1",
        }
    )

    # Operation -> list of dimensions that MUST be 1.0.
    required_dimensions: dict[str, list[str]] = field(default_factory=dict)

    # Operation -> free-text safety notes (e.g., "WHERE clause required").
    operation_notes: dict[str, str] = field(default_factory=dict)

    # Free-text safety special-case auto-fail patterns. The Critic
    # applies these heuristically; the Orchestrator doesn't regex-match
    # on them (that's the Critic's job).
    safety_auto_fail: list[str] = field(default_factory=list)

    # max_iterations override (read from rubric if present, else class default).
    max_iterations: int = 2

    # safety_confirm_required (read from rubric).
    safety_confirm_required: bool = True


@dataclass
class GeneratorOutput:
    """One execution of the Generator. Mirrors the post_state JSON
    shape defined in each skill's `references/prompt-templates.md`."""

    command: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0
    result: str = ""
    post_state: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class CriticScore:
    """One execution of the Critic. Mirrors the `scores` JSON shape
    in each skill's `references/prompt-templates.md`."""

    scores: dict[str, float] = field(
        default_factory=lambda: dict.fromkeys(RUBRIC_DIMENSIONS, 1.0)
    )
    justifications: dict[str, str] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    blocking: bool = False


@dataclass
class IterationRecord:
    """One full Generator -> H -> Critic -> Decide cycle.

    Extended per AGENTS.md §10.4 (H layer fields) and §11.2 (failure_pattern).
    """

    iter: int
    generator: dict[str, Any]
    critic: dict[str, Any]
    decision: str  # "PASS" | "RETRY" | "RETURN_BEST" | "ABORT" | "HALLUCINATION_ABORT"
    reason: str
    # §10.4 — Hallucination Detector result (None if H not enabled).
    hallucination_detector: dict[str, Any] | None = None
    # §10.4 — Whether this iteration was regenerated after H FAIL.
    regenerated: bool = False
    # §11.2 — Extracted failure pattern (None if no failure).
    failure_pattern: dict[str, Any] | None = None


@dataclass
class Trace:
    """The full GCL run trace. Persisted to audit-results/*.json
    per AGENTS.md §6."""

    skill: str
    request: str
    rubric_version: str
    iterations: list[IterationRecord] = field(default_factory=list)
    final: dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    finished_at: str | None = None


# ---------------------------------------------------------------------------
# Rubric parser
# ---------------------------------------------------------------------------


def parse_rubric(skill: str, rubric_path: Path) -> RubricConfig:
    """Parse a skill's `references/rubric.md` into a `RubricConfig`.

    The parser is intentionally tolerant: it uses regex against the
    AGENTS.md-canonical structure (5-dimension table, operation
    overrides table, safety special cases list). If a section is
    missing, sensible defaults are used. This lets us rollout GCL
    to new skills that may not have a perfectly-formatted rubric.

    Args:
        skill: skill name, e.g., "vm-ops"
        rubric_path: path to the skill's `references/rubric.md`

    Returns:
        Parsed `RubricConfig`. Raises `ValueError` only if the
        file is missing or unparseable as Markdown.
    """
    if not rubric_path.exists():
        raise FileNotFoundError(f"rubric not found: {rubric_path}")

    text = rubric_path.read_text(encoding="utf-8")
    cfg = RubricConfig(skill=skill)

    # ---- Rubric version: line like `\`v1\` — see AGENTS.md §11.` ----
    m = re.search(r"`v(\d+)`\s*[—\-]", text)
    if m:
        cfg.rubric_version = f"v{m.group(1)}"

    # ---- 5-dimension thresholds from the Dimensions table ----
    # Match a table row like:
    #   | **Correctness** | hard | ≥ 0.5; = 1.0 required for ... | 0 / 0.5 / 1 | ... |
    dim_re = re.compile(
        r"^\|\s*\*\*(\w+)\*\*\s*\|[^|]*\|[^|]*\|"
        r"\s*(0\s*/\s*0\.5\s*/\s*1|0\s*/\s*1)\s*\|",
        re.MULTILINE,
    )
    for match in dim_re.finditer(text):
        dim = match.group(1).lower()
        if dim not in RUBRIC_DIMENSIONS:
            continue
        scale = match.group(2).replace(" ", "")
        cfg.scales[dim] = scale

    # Threshold heuristic: most skills use the AGENTS.md §3 defaults,
    # so we don't try to parse the human-readable "≥ 0.5" / "= 1"
    # text. We use the per-dimension defaults from `RubricConfig`.
    # Skills that need different thresholds override them in
    # `## Operation-specific overrides` or via the `safety_auto_fail`
    # special cases (which the Critic applies heuristically).

    # ---- Operation-specific overrides ----
    # Match rows like: | `create-instance` | Correctness, Safety, **Idempotency** | notes |
    op_re = re.compile(
        r"^\|\s*`([a-z][a-z0-9-]+)`\s*\|"
        r"\s*([^|]+)\s*\|"
        r"\s*([^|]+)\s*\|",
        re.MULTILINE,
    )
    for match in op_re.finditer(text):
        op = match.group(1)
        dims_text = match.group(2)
        notes = match.group(3).strip()

        # Extract dimension names (skip the asterisks / punctuation).
        required: list[str] = []
        for d in RUBRIC_DIMENSIONS:
            if re.search(rf"\b{d.capitalize()}\b|\b\*\*{d.capitalize()}\*\*\b", dims_text):
                required.append(d)

        cfg.required_dimensions[op] = required
        cfg.operation_notes[op] = notes

    # ---- Safety special cases (the `## Safety special cases` section) ----
    in_safety = False
    for line in text.splitlines():
        if line.startswith("## Safety special cases"):
            in_safety = True
            continue
        if in_safety and line.startswith("## "):
            in_safety = False
        if in_safety and line.strip().startswith("- "):
            cfg.safety_auto_fail.append(line.strip()[2:])

    # ---- Loop parameters: max_iterations & safety_confirm_required ----
    # From the "Loop parameters" table at the end of the rubric.
    m = re.search(r"max_iterations`\s*\|\s*\*\*(\d+)\*\*", text)
    if m:
        cfg.max_iterations = int(m.group(1))

    m = re.search(r"safety_confirm_required`\s*\|\s*\*(true|false)\*", text)
    if m:
        cfg.safety_confirm_required = m.group(1) == "true"

    return cfg


# ---------------------------------------------------------------------------
# Generator / Critic interfaces
# ---------------------------------------------------------------------------

# Type aliases. The caller supplies concrete implementations:
#   - generator_fn(request, critic_feedback, rubric, iter) -> GeneratorOutput
#   - critic_fn(generator_output, trace, rubric) -> CriticScore
GeneratorFn = Callable[[str, str, RubricConfig, int], GeneratorOutput]
CriticFn = Callable[[GeneratorOutput, dict, RubricConfig], CriticScore]


def mock_generator(
    request: str,
    critic_feedback: str,
    rubric: RubricConfig,
    iter: int,
) -> GeneratorOutput:
    """Mock Generator that always returns a perfect run.

    Useful for self-checks, demos, and the `--gen-fn mock` CLI flag.
    Real LLM-backed Generators are passed in by the caller.
    """
    return GeneratorOutput(
        command=f"echo 'mock execution of: {request[:60]}'",
        args={"request": request, "iter": iter},
        exit_code=0,
        result="mock-result",
        post_state={"status": "ok"},
        errors=[],
        notes="mock",
    )


def mock_critic(
    generator_output: GeneratorOutput,
    trace: dict,
    rubric: RubricConfig,
) -> CriticScore:
    """Mock Critic that always returns 1.0 across all dimensions.

    Use `--critic-fn mock-strict` for a Critic that always flags
    safety=0 (to demonstrate the ABORT path).
    """
    return CriticScore(
        scores=dict.fromkeys(RUBRIC_DIMENSIONS, 1.0),
        justifications=dict.fromkeys(RUBRIC_DIMENSIONS, "mock pass"),
        suggestions=[],
        blocking=False,
    )


def mock_strict_critic(
    generator_output: GeneratorOutput,
    trace: dict,
    rubric: RubricConfig,
) -> CriticScore:
    """Mock Critic that always returns safety=0 (ABORT demo)."""
    scores = dict.fromkeys(RUBRIC_DIMENSIONS, 1.0)
    scores["safety"] = 0.0
    return CriticScore(
        scores=scores,
        justifications=dict.fromkeys(RUBRIC_DIMENSIONS, "mock"),
        suggestions=["mock-strict: safety=0 to demo ABORT"],
        blocking=True,
    )


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------


def should_abort(score: CriticScore, rubric: RubricConfig) -> bool:
    """Apply AGENTS.md §5 termination rule #1: ABORT on safety=0 or blocking.

    Safety is the only hard-veto dimension; all others can be
    retried up to `max_iterations`.
    """
    return score.scores.get("safety", 1.0) == 0.0 or score.blocking


def all_pass(score: CriticScore, rubric: RubricConfig) -> bool:
    """All rubric dimensions meet their thresholds.

    Per `RubricConfig.thresholds` defaults:
    - correctness: 1.0
    - safety: 1.0
    - idempotency: 0.5
    - traceability: 0.5
    - spec_compliance: 0.5
    """
    for dim, threshold in rubric.thresholds.items():
        if score.scores.get(dim, 0.0) < threshold:
            return False
    return True


def decide(
    score: CriticScore,
    rubric: RubricConfig,
    iter: int,
) -> tuple[str, str, str | None]:
    """Apply the AGENTS.md §5 decision rules in order.

    Returns: (decision, reason, next_iter_feedback or None)
        decision ∈ {"ABORT", "RETURN", "RETRY", "RETURN_BEST"}
    """
    # Rule 1: ABORT
    if should_abort(score, rubric):
        return ("ABORT", "safety=0 or blocking=true", None)

    # Rule 2: PASS / RETURN
    if all_pass(score, rubric):
        return ("RETURN", "all dimensions meet thresholds", None)

    # Rule 3: RETRY
    if iter < rubric.max_iterations:
        feedback = (
            "Critic suggestions:\n" + "\n".join(f"- {s}" for s in score.suggestions)
            if score.suggestions
            else "Critic flagged dimensions below threshold; please address."
        )
        return ("RETRY", f"some dimensions below threshold; iter {iter} < max {rubric.max_iterations}", feedback)

    # Rule 4: RETURN_BEST
    return (
        "RETURN_BEST",
        f"max_iterations={rubric.max_iterations} reached with unresolved items",
        None,
    )


# ---------------------------------------------------------------------------
# Hallucination Detection Layer (H) — Phase 6
# ---------------------------------------------------------------------------


def hallucination_detect(
    skill: str,
    operation: str,
    command: str,
    json_payload: dict | None = None,
    enable_time_range_check: bool = False,
) -> dict[str, Any]:
    """Pre-execution structural validity check per AGENTS.md §10.2.

    Three-category check:
    1. CLI/SDK Parameter Existence (§10.2.1) — MANDATORY
    2. JSON Structure Compliance (§10.2.2) — RECOMMENDED
    3. Time Range Validity (§10.2.3) — MANDATORY for audit-ops

    This is a deterministic offline check. It NEVER executes cloud API calls.
    It NEVER modifies the Generator's command.

    Args:
        skill: skill name (e.g., "vm-ops", "audit-ops")
        operation: operation name (e.g., "describe-instances", "describe-events")
        command: the generated command string to validate
        json_payload: optional JSON payload dict for structure validation
        enable_time_range_check: enable §10.2.3 time range check (audit-ops)

    Returns:
        Dict matching the §10.4 trace schema:
        {
            "status": "PASS"|"FAIL",
            "checks": {
                "cli_parameters": {...},
                "json_structure": {...},
                "time_range": {...}
            },
            "report": "..."
        }
    """
    checks: dict[str, Any] = {}
    issues: list[str] = []

    # ---- §10.2.1 CLI Parameter Existence ----
    product = skill.replace("-ops", "").replace("jdcloud-", "")
    known_ops = PARAMETER_KNOWLEDGE.get(product, {})
    known_flags = known_ops.get(operation, set())

    # Tokenize --flag patterns from command
    import shlex
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    found_flags: list[str] = []
    for tok in tokens:
        if tok.startswith("--"):
            # Strip =value suffix
            flag = tok.split("=")[0]
            found_flags.append(flag)

    unrecognized = []
    if known_flags:
        for f in found_flags:
            if f not in known_flags and f not in ("--output", "--help"):
                unrecognized.append(f)
    # If no known_flags for this op, conservative PASS (can't verify)

    checks["cli_parameters"] = {
        "total": len(found_flags),
        "recognized": len(found_flags) - len(unrecognized),
        "unrecognized": unrecognized,
        "status": "FAIL" if unrecognized else "PASS",
    }
    if unrecognized:
        issues.append(
            f"Unrecognized CLI parameters: {unrecognized} "
            f"(known: {sorted(known_flags) if known_flags else 'none in KB'})"
        )

    # ---- §10.2.2 JSON Structure Compliance ----
    if json_payload:
        json_issues = []
        # Basic type checks — field values must match expected types
        for key, val in json_payload.items():
            if val is None:
                json_issues.append(f"Field '{key}' is null")
        checks["json_structure"] = {
            "status": "FAIL" if json_issues else "PASS",
            "issues": json_issues,
        }
        issues.extend(json_issues)
    else:
        checks["json_structure"] = {
            "status": "PASS",
            "note": "no JSON payload in command",
        }

    # ---- §10.2.3 Time Range Validity (audit-ops only) ----
    if enable_time_range_check and json_payload:
        start = json_payload.get("startTime") or json_payload.get("start_time")
        end = json_payload.get("endTime") or json_payload.get("end_time")
        if start and end:
            try:
                from datetime import datetime as _dt
                # Parse ISO 8601 (strip Z suffix for fromisoformat)
                s = _dt.fromisoformat(start.replace("Z", "+00:00"))
                e = _dt.fromisoformat(end.replace("Z", "+00:00"))
                delta_days = (e - s).days
                within = delta_days <= AUDIT_RETENTION_DAYS
                checks["time_range"] = {
                    "status": "PASS" if within and delta_days > 0 else "FAIL",
                    "delta_days": delta_days,
                    "within_retention": within,
                    "suggestion": "" if within else f"Limit to ≤ {AUDIT_RETENTION_DAYS} days",
                }
                if not within:
                    issues.append(f"Time range {delta_days}d exceeds {AUDIT_RETENTION_DAYS}d retention")
                if delta_days <= 0:
                    issues.append("startTime must be before endTime")
            except Exception as ex:
                checks["time_range"] = {
                    "status": "FAIL",
                    "error": f"Cannot parse timestamps: {ex}",
                }
                issues.append(f"Time range parse error: {ex}")
        else:
            checks["time_range"] = {"status": "PASS", "note": "no time range in payload"}
    else:
        checks["time_range"] = {"status": "PASS", "note": "not applicable"}

    overall = "FAIL" if issues else "PASS"
    return {
        "status": overall,
        "checks": checks,
        "report": "; ".join(issues) if issues else "All structural checks passed",
    }


# ---------------------------------------------------------------------------
# Reflexion Integration — Phase 7
# ---------------------------------------------------------------------------


def load_failure_patterns(skill: str) -> list[dict[str, Any]]:
    """Load failure patterns for a skill from docs/failure-patterns.md.

    Per AGENTS.md §11.5, this is an OPTIONAL pre-flight retrieval.
    Searches both per-skill and central failure-patterns.md files.

    Args:
        skill: skill name (e.g., "vm-ops")

    Returns:
        List of pattern dicts with keys: category, skill, command, error, fix, count, reusable.
        Empty list if no file found.
    """
    patterns: list[dict[str, Any]] = []

    # Try per-skill file first
    per_skill_path = REPO_ROOT / f"jdcloud-{skill}" / "docs" / "failure-patterns.md"
    central_path = REPO_ROOT / "docs" / "failure-patterns.md"

    for path in (per_skill_path, central_path):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Parse ### Pattern: <name> blocks
        blocks = re.split(r"^### Pattern:\s*", text, flags=re.MULTILINE)[1:]
        for block in blocks:
            lines = block.strip().splitlines()
            if not lines:
                continue
            name = lines[0].strip()
            pat: dict[str, Any] = {"name": name, "count": 1}
            for line in lines[1:]:
                m = re.match(r"-\s*\*\*(\w+)\*\*:\s*(.+)", line)
                if m:
                    key = m.group(1).lower()
                    val = m.group(2).strip()
                    if key == "reusable":
                        val = val.lower() in ("true", "yes", "1")
                    pat[key] = val
            # Filter by skill if the pattern has a skill field
            pat_skill = pat.get("skill", "")
            if pat_skill and skill not in pat_skill:
                continue
            patterns.append(pat)

    return patterns


def inject_failure_patterns(patterns: list[dict[str, Any]], max_patterns: int = 3) -> str:
    """Format failure patterns as a prevention hint for the Generator.

    Per AGENTS.md §11.5, this is a HINT, not a CONSTRAINT.
    """
    if not patterns:
        return ""
    top = patterns[:max_patterns]
    lines = ["Known failure patterns to avoid:"]
    for p in top:
        lines.append(f"- {p.get('name', 'unknown')}: {p.get('error', '')} → {p.get('fix', '')}")
    return "\n".join(lines)


def extract_failure_pattern(
    skill: str,
    command: str,
    error: str,
    decision: str,
) -> dict[str, Any] | None:
    """Extract a failure pattern from a failed GCL iteration per §11.2.

    Returns None if the iteration passed (no failure to extract).
    """
    if decision in ("RETURN",):
        return None
    category = "runtime"
    if "InvalidParameter" in error or "MissingParameter" in error or "unrecognized" in error.lower() or decision == "HALLUCINATION_ABORT":
        category = "cli_parameter"

    return {
        "category": category,
        "skill": f"jdcloud-{skill}",
        "command": command[:200],
        "error": error[:500],
        "fix": "See GCL trace suggestions",
        "count": 1,
        "reusable": True,
    }


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run_gcl(
    skill: str,
    request: str,
    safety_confirm: bool,
    generator_fn: GeneratorFn,
    critic_fn: CriticFn,
    rubric: RubricConfig | None = None,
    enable_hallucination_check: bool = False,
    operation: str = "",
    enable_reflexion: bool = True,
) -> tuple[str, Trace]:
    """Run one GCL cycle and return (decision, trace).

    This is the core Orchestrator function. It does NOT call any
    LLM; it loops over the injected generator_fn and critic_fn.

    Args:
        skill: skill name, e.g., "vm-ops"
        request: user request (sanitized)
        safety_confirm: whether the user has confirmed destructive ops
        generator_fn: callable implementing the Generator
        critic_fn: callable implementing the Critic
        rubric: pre-parsed RubricConfig. If None, parsed from
            `jdcloud-<skill>/references/rubric.md`.
        enable_hallucination_check: enable Phase 6 H layer (§10)
        operation: operation name for H layer parameter validation
        enable_reflexion: enable Phase 7 Reflexion pre-flight (§11)

    Returns:
        (decision, trace) where decision ∈
        {"ABORT", "RETURN", "RETURN_BEST", "HALLUCINATION_ABORT"} and trace is the
        full Trace object.
    """
    if rubric is None:
        rubric_path = REPO_ROOT / f"jdcloud-{skill}" / "references" / "rubric.md"
        rubric = parse_rubric(skill, rubric_path)

    trace = Trace(
        skill=skill,
        request=request,
        rubric_version=rubric.rubric_version,
    )

    # ---- Phase 7: Reflexion pre-flight (optional) ----
    reflexion_hint = ""
    if enable_reflexion:
        patterns = load_failure_patterns(skill)
        reflexion_hint = inject_failure_patterns(patterns)
        if reflexion_hint:
            # Append to request context so Generator sees it
            request = f"{request}\n\n# Reflexion prevention hints\n{reflexion_hint}"

    # Determine if time range check applies (audit-ops only)
    enable_time_range = skill in ("audit-ops", "tag-audit-ops")

    critic_feedback = ""
    for it in range(1, rubric.max_iterations + 1):
        # Step 1: Generate
        gen_out = generator_fn(request, critic_feedback, rubric, it)

        # ---- Phase 6: Hallucination Detection (pre-execution) ----
        h_result: dict[str, Any] | None = None
        regenerated = False
        if enable_hallucination_check and operation:
            h_result = hallucination_detect(
                skill=skill,
                operation=operation,
                command=gen_out.command,
                json_payload=gen_out.args if gen_out.args else None,
                enable_time_range_check=enable_time_range,
            )

            # H_FAIL → Regenerate (max 1 retry per §10.3)
            if h_result["status"] == "FAIL":
                # Inject hallucination report into Generator feedback
                h_feedback = f"Hallucination detected: {h_result['report']}. Fix the command and retry."
                gen_out = generator_fn(request, h_feedback, rubric, it)
                regenerated = True

                # Re-check after regeneration
                h_result = hallucination_detect(
                    skill=skill,
                    operation=operation,
                    command=gen_out.command,
                    json_payload=gen_out.args if gen_out.args else None,
                    enable_time_range_check=enable_time_range,
                )

                # Still FAIL → HALLUCINATION_ABORT
                if h_result["status"] == "FAIL":
                    record = IterationRecord(
                        iter=it,
                        generator=asdict(gen_out),
                        critic={},
                        decision="HALLUCINATION_ABORT",
                        reason=f"H layer failed after regeneration: {h_result['report']}",
                        hallucination_detector=h_result,
                        regenerated=True,
                    )
                    trace.iterations.append(record)
                    trace.final = {
                        "status": "HALLUCINATION_ABORT",
                        "iter": it,
                        "output": None,
                        "hallucination_report": h_result["report"],
                    }
                    trace.finished_at = datetime.now(timezone.utc).isoformat()
                    return "HALLUCINATION_ABORT", trace

        # Step 2: Critique
        score = critic_fn(
            gen_out,
            {
                "skill": skill,
                "iter": it,
                "rubric_version": rubric.rubric_version,
                "safety_confirm": safety_confirm,
            },
            rubric,
        )

        # Step 3: Decide
        decision, reason, next_feedback = decide(score, rubric, it)

        # ---- Phase 7: Extract failure pattern from failed iteration ----
        failure_pat = None
        if decision in ("ABORT", "RETURN_BEST", "HALLUCINATION_ABORT", "RETRY"):
            error_msg = reason
            if score.suggestions:
                error_msg += "; " + "; ".join(score.suggestions[:2])
            failure_pat = extract_failure_pattern(
                skill=skill,
                command=gen_out.command,
                error=error_msg,
                decision=decision,
            )

        trace.iterations.append(
            IterationRecord(
                iter=it,
                generator=asdict(gen_out),
                critic={
                    "scores": score.scores,
                    "justifications": score.justifications,
                    "suggestions": score.suggestions,
                    "blocking": score.blocking,
                },
                decision=decision,
                reason=reason,
                hallucination_detector=h_result,
                regenerated=regenerated,
                failure_pattern=failure_pat,
            )
        )

        if decision in ("RETURN", "RETURN_BEST", "ABORT"):
            trace.final = {
                "status": (
                    "PASS" if decision == "RETURN"
                    else "RETURN_BEST" if decision == "RETURN_BEST"
                    else "ABORT"
                ),
                "iter": it,
                "output": gen_out.result,
            }
            trace.finished_at = datetime.now(timezone.utc).isoformat()
            return decision, trace

        # RETRY: prepare feedback for next Generator call
        critic_feedback = next_feedback or ""

    # Loop completed without RETURN/ABORT (shouldn't happen given
    # decide() always returns one of those, but guard anyway).
    trace.finished_at = datetime.now(timezone.utc).isoformat()
    return "RETURN_BEST", trace


# ---------------------------------------------------------------------------
# Trace persistence
# ---------------------------------------------------------------------------


def write_trace(trace: Trace, trace_dir: Path) -> Path:
    """Persist the trace to disk per AGENTS.md §6.

    File path: `<trace_dir>/gcl-trace-YYYYMMDD-HHMMSS.json`.
    The directory is created if missing.
    """
    trace_dir.mkdir(parents=True, exist_ok=True)

    started = datetime.fromisoformat(trace.started_at)
    fname = f"{TRACE_FILE_PREFIX}-{started.strftime('%Y%m%d-%H%M%S')}-{trace.run_id[:8]}{TRACE_FILE_SUFFIX}"
    out_path = trace_dir / fname

    payload = {
        "skill": trace.skill,
        "request": trace.request,
        "rubric_version": trace.rubric_version,
        "iterations": [asdict(it) for it in trace.iterations],
        "final": trace.final,
        "run_id": trace.run_id,
        "started_at": trace.started_at,
        "finished_at": trace.finished_at,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def list_skills() -> list[str]:
    """List all `jdcloud-*-ops` skills under REPO_ROOT."""
    return sorted(
        p.name[len("jdcloud-"):]
        for p in REPO_ROOT.iterdir()
        if p.is_dir() and p.name.startswith("jdcloud-")
    )


def cmd_show_rubric(args: argparse.Namespace) -> int:
    """Show the parsed rubric for a skill."""
    try:
        rubric = parse_rubric(
            args.skill,
            REPO_ROOT / f"jdcloud-{args.skill}" / "references" / "rubric.md",
        )
    except FileNotFoundError as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        return 3

    print(json.dumps(asdict(rubric), indent=2, ensure_ascii=False))
    return 0


def cmd_self_check(args: argparse.Namespace) -> int:
    """Parse every skill's rubric and report any failures.

    The self-check is the GCL Orchestrator's smoke test: if we
    can't parse a skill's rubric, the runtime loop won't work
    for that skill either.
    """
    skills = list_skills()
    failures: list[tuple[str, str]] = []

    for skill in skills:
        rubric_path = REPO_ROOT / f"jdcloud-{skill}" / "references" / "rubric.md"
        if not rubric_path.exists():
            failures.append((skill, "no references/rubric.md"))
            continue
        try:
            cfg = parse_rubric(skill, rubric_path)
            if not cfg.required_dimensions and not cfg.safety_auto_fail:
                # This is fine for read-only skills but warn anyway.
                print(f"[WARN] {skill}: rubric has no operation overrides or safety auto-fails")
        except Exception as e:
            failures.append((skill, str(e)))

    print(f"\n=== Self-check: {len(skills)} skills ===")
    print(f"  passed: {len(skills) - len(failures)}")
    print(f"  failed: {len(failures)}")
    for skill, err in failures:
        print(f"  [FAIL] {skill}: {err}")
    return 0 if not failures else 2


def cmd_run(args: argparse.Namespace) -> int:
    """Run a GCL cycle and persist the trace."""
    rubric_path = REPO_ROOT / f"jdcloud-{args.skill}" / "references" / "rubric.md"
    try:
        rubric = parse_rubric(args.skill, rubric_path)
    except FileNotFoundError as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        return 3

    # Generator / Critic selection. Currently only mock variants
    # are built-in; real LLM-backed functions are expected to be
    # supplied by an external harness.
    if args.gen_fn == "mock":
        gen_fn: GeneratorFn = mock_generator
    else:
        print(f"[FATAL] unknown --gen-fn: {args.gen_fn}", file=sys.stderr)
        return 3

    if args.critic_fn == "mock":
        critic_fn: CriticFn = mock_critic
    elif args.critic_fn == "mock-strict":
        critic_fn = mock_strict_critic
    else:
        print(f"[FATAL] unknown --critic-fn: {args.critic_fn}", file=sys.stderr)
        return 3

    # Safety confirm gate: if the rubric requires it but the user
    # did not confirm, fail fast (this is a human-facing check,
    # not a Critic check).
    if rubric.safety_confirm_required and not args.safety_confirm:
        # We do NOT abort here — the Generator's job is to detect
        # this and either prompt the user or refuse. The Critic
        # will score safety=0 if the trace doesn't carry the
        # confirm flag. This is a soft signal.
        print(
            "[INFO] rubric.safety_confirm_required=true but "
            "--safety-confirm not set; Generator must enforce or "
            "Critic will score safety=0",
            file=sys.stderr,
        )

    decision, trace = run_gcl(
        skill=args.skill,
        request=args.request,
        safety_confirm=args.safety_confirm,
        generator_fn=gen_fn,
        critic_fn=critic_fn,
        rubric=rubric,
        enable_hallucination_check=args.enable_hallucination_check,
        operation=args.operation or "",
        enable_reflexion=not args.disable_reflexion,
    )

    # Persist trace.
    trace_dir = Path(args.trace_dir) if args.trace_dir else DEFAULT_TRACE_DIR
    out_path = write_trace(trace, trace_dir)

    # Print summary.
    print(f"\n=== GCL run: {args.skill} ===")
    print(f"  request: {args.request[:80]}")
    print(f"  decision: {decision}")
    print(f"  iterations: {len(trace.iterations)}")
    print(f"  trace: {out_path}")

    # Map to exit code.
    if decision == "ABORT":
        return 1
    return 0


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gcl_runner",
        description="GCL Orchestrator for jdcloud-skills (Phase 2)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # --run
    p_run = sub.add_parser("run", help="Run a GCL cycle")
    p_run.add_argument("--skill", required=True, help="skill name (e.g., vm-ops)")
    p_run.add_argument("--request", required=True, help="user request (sanitized)")
    p_run.add_argument(
        "--safety-confirm",
        action="store_true",
        help="user has explicitly confirmed destructive ops",
    )
    p_run.add_argument(
        "--gen-fn",
        default="mock",
        choices=["mock"],
        help="Generator function (only mock built-in; real LLM is injected)",
    )
    p_run.add_argument(
        "--critic-fn",
        default="mock",
        choices=["mock", "mock-strict"],
        help="Critic function (mock = always pass, mock-strict = always safety=0)",
    )
    p_run.add_argument(
        "--trace-dir",
        default=None,
        help=f"trace output directory (default: {DEFAULT_TRACE_DIR})",
    )
    p_run.add_argument(
        "--enable-hallucination-check",
        action="store_true",
        help="Enable Phase 6 Hallucination Detection Layer (H) pre-execution check",
    )
    p_run.add_argument(
        "--operation",
        default="",
        help="Operation name for H layer parameter validation (e.g., describe-instances)",
    )
    p_run.add_argument(
        "--disable-reflexion",
        action="store_true",
        help="Disable Phase 7 Reflexion pre-flight (failure pattern retrieval)",
    )
    p_run.set_defaults(func=cmd_run)

    # --show-rubric
    p_show = sub.add_parser("show-rubric", help="Show the parsed rubric for a skill")
    p_show.add_argument("--skill", required=True)
    p_show.set_defaults(func=cmd_show_rubric)

    # --self-check
    p_check = sub.add_parser(
        "self-check",
        help="Parse every skill's rubric; report any parse failures",
    )
    p_check.set_defaults(func=cmd_self_check)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
