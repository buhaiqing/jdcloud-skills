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
from typing import Any, Callable, Optional


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

# AGENTS.md §8 — per-skill class -> max_iterations default.
# Used as a fallback when a skill's `## Quality Gate` chapter
# doesn't override.
DEFAULT_MAX_ITER = {
    "required": 2,      # write ops on production
    "recommended": 3,   # network / monitoring
    "optional": 5,      # read-only / meta
}

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
        default_factory=lambda: {d: 1.0 for d in RUBRIC_DIMENSIONS}
    )
    justifications: dict[str, str] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    blocking: bool = False


@dataclass
class IterationRecord:
    """One full Generator -> Critic -> Decide cycle."""

    iter: int
    generator: dict[str, Any]
    critic: dict[str, Any]
    decision: str  # "PASS" | "RETRY" | "RETURN_BEST" | "ABORT"
    reason: str


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
    finished_at: Optional[str] = None


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
        scores={d: 1.0 for d in RUBRIC_DIMENSIONS},
        justifications={d: "mock pass" for d in RUBRIC_DIMENSIONS},
        suggestions=[],
        blocking=False,
    )


def mock_strict_critic(
    generator_output: GeneratorOutput,
    trace: dict,
    rubric: RubricConfig,
) -> CriticScore:
    """Mock Critic that always returns safety=0 (ABORT demo)."""
    scores = {d: 1.0 for d in RUBRIC_DIMENSIONS}
    scores["safety"] = 0.0
    return CriticScore(
        scores=scores,
        justifications={d: "mock" for d in RUBRIC_DIMENSIONS},
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
) -> tuple[str, str, Optional[str]]:
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
# Main loop
# ---------------------------------------------------------------------------


def run_gcl(
    skill: str,
    request: str,
    safety_confirm: bool,
    generator_fn: GeneratorFn,
    critic_fn: CriticFn,
    rubric: Optional[RubricConfig] = None,
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

    Returns:
        (decision, trace) where decision ∈
        {"ABORT", "RETURN", "RETURN_BEST"} and trace is the
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

    critic_feedback = ""
    for it in range(1, rubric.max_iterations + 1):
        # Step 1: Generate
        gen_out = generator_fn(request, critic_feedback, rubric, it)

        # Pre-flight: safety_confirm_required gate.
        # AGENTS.md §2: Generator "MUST NOT proceed without explicit
        # user confirmation" for destructive ops. We model this as
        # if the Orchestrator blocks at the trace level — the
        # Generator itself is responsible for honoring the gate.
        # Here we record it; we don't actually abort, because the
        # safety_confirm is expected to be checked by the Generator
        # AND by the Critic (safety=0 if missing).

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
            f"[INFO] rubric.safety_confirm_required=true but "
            f"--safety-confirm not set; Generator must enforce or "
            f"Critic will score safety=0",
            file=sys.stderr,
        )

    decision, trace = run_gcl(
        skill=args.skill,
        request=args.request,
        safety_confirm=args.safety_confirm,
        generator_fn=gen_fn,
        critic_fn=critic_fn,
        rubric=rubric,
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


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
