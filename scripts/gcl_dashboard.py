#!/usr/bin/env python3
"""
GCL Dashboard — Quality Gate aggregator (Phase 3).

Consumes GCL trace JSON files produced by `gcl_runner.py` (per
`AGENTS.md` §6) and renders the 5-question dashboard designed in
`docs/GCL_RETROSPECTIVE.md` §5.

## What this script does

Answers the 5 questions in retrospective §5.2, in priority order:

  1. Are we ABORTing more than we should? (>5% over 7d is a signal)
  2. Which dimension is failing most? (per-skill, per-dimension rate)
  3. How many iterations does PASS take? (long tail = rubric/prompt drift)
  4. Are any skills below their `safety_confirm_required` bar?
  5. Which safety auto-fail is firing most? (top-N reasons)

## What this script does NOT do (per retrospective §5.3)

- It does NOT score the Critic. Auditing the auditor is out of scope.
- It does NOT auto-tighten rubrics. Recommendations only; humans act.
- It does NOT leak traces. The default output is aggregate counts
  only. Use `--show-trace-ids` to surface trace ids (still no
  command args, resource ids, or request text).

## CLI usage

    # Terminal dashboard (default)
    python3 scripts/gcl_dashboard.py

    # JSON summary (for downstream automation / Phase 4 alarms)
    python3 scripts/gcl_dashboard.py --format json --out dashboard.json

    # Last 24 hours only
    python3 scripts/gcl_dashboard.py --since 24h

    # Different trace dir
    python3 scripts/gcl_dashboard.py --trace-dir /var/log/gcl

    # Multi-tenant: filter to a single skill (e.g., for per-team dashboards)
    python3 scripts/gcl_dashboard.py --skill jdcloud-vm-ops

    # Retention policy: prune trace files older than 90 days
    python3 scripts/gcl_dashboard.py --retention-days 90

    # Combined: filter + retention + JSON output
    python3 scripts/gcl_dashboard.py --skill jdcloud-vm-ops --retention-days 90 --format json

## Exit codes

    0   Dashboard rendered (regardless of whether alerts fired)
    1   Self-check found a malformed trace (data-quality alert)
    2   Usage error

## Dependencies

Standard library only. Mirrors `gcl_runner.py` to keep Phase 2
and Phase 3 dependencies aligned.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Constants — mirror gcl_runner.py
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACE_DIR = REPO_ROOT / "audit-results"

RUBRIC_DIMENSIONS = (
    "correctness",
    "safety",
    "idempotency",
    "traceability",
    "spec_compliance",
)

# Per retrospective §5.2 Q1: > 5% ABORT rate over 7d is a signal.
ABORT_RATE_ALERT_THRESHOLD = 0.05

# Per retrospective §5.2 Q1: > 2% ABORT rate for a single skill is a signal.
PER_SKILL_ABORT_ALERT_THRESHOLD = 0.02

# Per retrospective §5.2 Q3: PASS taking more than max_iter is suspicious.
# (We don't enforce this here; we just surface the histogram.)


# ---------------------------------------------------------------------------
# Trace loading & validation
# ---------------------------------------------------------------------------


@dataclass
class TraceRecord:
    """In-memory view of one GCL trace. Only the fields the
    dashboard cares about are kept; raw request / command args
    are NOT loaded into the dashboard to avoid accidental leak.
    """

    path: Path
    run_id: str
    skill: str
    rubric_version: str
    started_at: datetime
    finished_at: Optional[datetime]
    final_status: str  # "PASS" | "RETURN_BEST" | "ABORT"
    final_iter: int
    iterations: int
    # Per-iteration: dimension -> score. The LAST iteration's
    # scores are the final verdict; earlier iterations are kept
    # for the iteration-histogram view.
    final_scores: dict[str, float]
    # All-iteration score-0 events: list of (iter, dimension).
    score_zero_events: list[tuple[int, str]]
    # Suggestions on the final iteration (used for Q5).
    final_suggestions: list[str]
    # Did the user pass --safety-confirm? (recorded by gcl_runner)
    safety_confirm_seen: bool

    @property
    def is_abort(self) -> bool:
        return self.final_status == "ABORT"

    @property
    def is_pass(self) -> bool:
        return self.final_status == "PASS"

    @property
    def is_return_best(self) -> bool:
        return self.final_status == "RETURN_BEST"


def parse_iso(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp. Tolerate `+00:00` and trailing Z."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def load_traces(
    trace_dir: Path,
    since: Optional[timedelta] = None,
    skill_filter: Optional[str] = None,
) -> tuple[list[TraceRecord], list[tuple[Path, str]]]:
    """Load all GCL trace JSON files from a directory.

    Returns:
        (traces, errors) where:
          - traces: list of successfully-parsed TraceRecord
          - errors: list of (path, error_message) for malformed traces

    Args:
        trace_dir: directory containing `gcl-trace-*.json` files.
        since: if set, only include traces whose `started_at` is newer than
            `now - since`. Useful for "last 24h" views.
        skill_filter: if set, only include traces whose `skill` field matches
            this value exactly. Enables multi-tenant per-skill dashboards.
    """
    traces: list[TraceRecord] = []
    errors: list[tuple[Path, str]] = []

    if not trace_dir.exists():
        return traces, errors

    cutoff: Optional[datetime] = None
    if since is not None:
        cutoff = datetime.now(timezone.utc) - since

    for path in sorted(trace_dir.glob("gcl-trace-*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append((path, f"json decode: {e}"))
            continue

        try:
            iterations = raw.get("iterations", [])
            if not iterations:
                errors.append((path, "no iterations"))
                continue

            # The final iteration's scores are the verdict.
            final_iteration = iterations[-1]
            final_scores = final_iteration.get("critic", {}).get("scores", {})

            # Collect all score-zero events across iterations.
            score_zero_events: list[tuple[int, str]] = []
            for it in iterations:
                it_scores = it.get("critic", {}).get("scores", {})
                for dim, score in it_scores.items():
                    if score == 0.0:
                        score_zero_events.append((it.get("iter", 0), dim))

            final_suggestions = final_iteration.get("critic", {}).get("suggestions", [])

            final = raw.get("final", {})
            record = TraceRecord(
                path=path,
                run_id=raw.get("run_id", "unknown"),
                skill=raw.get("skill", "unknown"),
                rubric_version=raw.get("rubric_version", "v?"),
                started_at=parse_iso(raw["started_at"]),
                finished_at=parse_iso(raw["finished_at"]) if raw.get("finished_at") else None,
                final_status=final.get("status", "UNKNOWN"),
                final_iter=final.get("iter", len(iterations)),
                iterations=len(iterations),
                final_scores=final_scores,
                score_zero_events=score_zero_events,
                final_suggestions=final_suggestions,
                # The trace doesn't always carry `safety_confirm` at
                # the top level; we recorded it in `iterations[].generator.args`
                # only in the v2 traces. Fall back to False.
                safety_confirm_seen=False,
            )

            if cutoff is not None and record.started_at < cutoff:
                continue

            # Multi-tenant filter: skip traces that don't match the requested skill.
            if skill_filter is not None and record.skill != skill_filter:
                continue

            traces.append(record)
        except (KeyError, ValueError) as e:
            errors.append((path, f"parse: {e}"))

    return traces, errors


def prune_old_traces(trace_dir: Path, retention_days: int) -> tuple[int, list[Path]]:
    """Delete trace files older than `retention_days` from `trace_dir`.

    Implements the trace retention policy (P2-1). Trace files are named
    `gcl-trace-YYYYMMDD-HHMMSS.json` and carry an ISO `started_at` inside;
    we use the file's mtime as the authoritative age to avoid parsing every
    file (which could fail on malformed traces).

    Args:
        trace_dir: directory containing `gcl-trace-*.json` files.
        retention_days: delete files whose mtime is older than this many days.

    Returns:
        (deleted_count, deleted_paths) — the caller may log these for audit.
    """
    if not trace_dir.exists() or retention_days <= 0:
        return 0, []

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_ts = cutoff.timestamp()

    deleted: list[Path] = []
    for path in sorted(trace_dir.glob("gcl-trace-*.json")):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff_ts:
            try:
                path.unlink()
                deleted.append(path)
            except OSError:
                # Best-effort prune; don't fail the dashboard run if one
                # file is locked or permission-denied.
                continue

    return len(deleted), deleted


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


@dataclass
class DashboardData:
    """Aggregated dashboard data. All percentages are 0.0-1.0."""

    total_runs: int = 0
    by_skill: dict[str, dict[str, int]] = field(default_factory=dict)
    by_skill_safety_zero: dict[str, int] = field(default_factory=dict)
    iter_histogram: Counter = field(default_factory=Counter)
    safety_auto_fail_reasons: Counter = field(default_factory=Counter)
    dimension_score_zero_rate: dict[str, dict[str, float]] = field(default_factory=dict)
    per_skill_abort_rate: dict[str, float] = field(default_factory=dict)
    overall_abort_rate: float = 0.0

    def compute(self, traces: list[TraceRecord]) -> None:
        if not traces:
            return

        self.total_runs = len(traces)

        # by_skill[skill][status] = count
        for t in traces:
            d = self.by_skill.setdefault(t.skill, Counter())
            d[t.final_status] += 1

        # iter_histogram: how many iterations did PASS / RETURN_BEST take?
        for t in traces:
            if t.final_status in ("PASS", "RETURN_BEST"):
                self.iter_histogram[t.iterations] += 1

        # safety_score=0 events grouped by skill
        for t in traces:
            score_zero_dims = {dim for (_, dim) in t.score_zero_events if dim == "safety"}
            if score_zero_dims:
                self.by_skill_safety_zero[t.skill] = self.by_skill_safety_zero.get(t.skill, 0) + 1

        # dimension_score_zero_rate[skill][dim] = rate
        # (rate = score_zero events for that dim / total iterations across
        #  ALL runs of that skill, not the count of zero-events summed
        #  across dimensions). This is per-dimension: each dimension's
        #  rate is the fraction of all iterations where it scored 0.
        per_skill_total_iters: dict[str, int] = defaultdict(int)
        per_skill_dim_zero: dict[str, Counter] = defaultdict(Counter)
        for t in traces:
            per_skill_total_iters[t.skill] += t.iterations
            for (_, dim) in t.score_zero_events:
                per_skill_dim_zero[t.skill][dim] += 1

        for skill, total_iters in per_skill_total_iters.items():
            self.dimension_score_zero_rate[skill] = {}
            for dim in RUBRIC_DIMENSIONS:
                if total_iters == 0:
                    self.dimension_score_zero_rate[skill][dim] = 0.0
                else:
                    # rate = (times this dim scored 0) / (total iters of this skill)
                    self.dimension_score_zero_rate[skill][dim] = (
                        per_skill_dim_zero[skill].get(dim, 0) / total_iters
                    )

        # per_skill_abort_rate
        abort_count = 0
        for skill, counts in self.by_skill.items():
            total = sum(counts.values())
            aborts = counts.get("ABORT", 0)
            self.per_skill_abort_rate[skill] = aborts / total if total else 0.0
            abort_count += aborts
        self.overall_abort_rate = abort_count / self.total_runs

        # safety auto-fail reasons: parse the suggestions to extract
        # the dimension that scored 0. We do NOT leak the suggestion
        # text — just the dimension that failed.
        for t in traces:
            for suggestion in t.final_suggestions:
                # Heuristic: the suggestion that says "address <dim>"
                # (the format from gcl_runner.py test fixtures) is a
                # dimension signature. Real suggestions from LLM-backed
                # Critics will be free text; we don't try to parse those.
                m = re.match(r"^address (\w+)$", suggestion.strip())
                if m and m.group(1) in RUBRIC_DIMENSIONS:
                    self.safety_auto_fail_reasons[m.group(1)] += 1
                else:
                    # Bucket unknown suggestions as "other"
                    self.safety_auto_fail_reasons["other"] += 1


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_terminal(
    d: DashboardData,
    errors: list[tuple[Path, str]],
    pruned_count: int = 0,
    skill_filter: Optional[str] = None,
) -> str:
    """Render the dashboard as ASCII art. Mirrors retrospective §5.4."""
    out: list[str] = []
    out.append("=" * 78)
    out.append("  GCL Quality Gate Dashboard — Phase 3 (read-only aggregator)".center(78))
    out.append("=" * 78)
    out.append("")

    # ---- Scope banner: show active filters ----
    scope_parts: list[str] = []
    if skill_filter is not None:
        scope_parts.append(f"skill={skill_filter}")
    if pruned_count > 0:
        scope_parts.append(f"pruned={pruned_count} old trace(s)")
    if scope_parts:
        out.append(f"  Scope: {' | '.join(scope_parts)}")
        out.append("")

    # ---- Top-level panel: GCL health ----
    out.append("[Q1] Top-level — GCL health")
    out.append("-" * 78)
    if d.total_runs == 0:
        out.append("  No GCL traces found. Run `gcl_runner.py` first.")
        return "\n".join(out)

    out.append(
        f"  Total runs: {d.total_runs}   "
        f"Overall ABORT rate: {d.overall_abort_rate * 100:.1f}%"
        + (
            "   *** ALERT (>5%) ***"
            if d.overall_abort_rate > ABORT_RATE_ALERT_THRESHOLD
            else ""
        )
    )
    out.append("")

    # Per-skill table
    header = (
        f"  {'Skill':<22} {'Runs':>5} {'PASS':>5} {'RETRY':>6} "
        f"{'R_BEST':>7} {'ABORT':>6}"
    )
    out.append(header)
    out.append("  " + "-" * (len(header) - 2))

    # Sort: by ABORT rate descending, then by name
    sorted_skills = sorted(
        d.by_skill.keys(),
        key=lambda s: (-d.per_skill_abort_rate.get(s, 0.0), s),
    )
    for skill in sorted_skills:
        counts = d.by_skill[skill]
        runs = sum(counts.values())
        n_pass = counts.get("PASS", 0)
        n_retry = counts.get("RETRY", 0)
        n_return_best = counts.get("RETURN_BEST", 0)
        n_abort = counts.get("ABORT", 0)
        abort_pct = d.per_skill_abort_rate[skill] * 100
        alert = " *" if abort_pct / 100 > PER_SKILL_ABORT_ALERT_THRESHOLD else ""
        out.append(
            f"  {skill:<22} {runs:>5} {n_pass:>5} {n_retry:>6} "
            f"{n_return_best:>7} {n_abort:>6}  {abort_pct:5.1f}%{alert}"
        )

    # Total row
    total_pass = sum(c.get("PASS", 0) for c in d.by_skill.values())
    total_retry = sum(c.get("RETRY", 0) for c in d.by_skill.values())
    total_return_best = sum(c.get("RETURN_BEST", 0) for c in d.by_skill.values())
    total_abort = sum(c.get("ABORT", 0) for c in d.by_skill.values())
    out.append("  " + "-" * (len(header) - 2))
    out.append(
        f"  {'TOTAL':<22} {d.total_runs:>5} {total_pass:>5} {total_retry:>6} "
        f"{total_return_best:>7} {total_abort:>6}  "
        f"{d.overall_abort_rate * 100:5.1f}%"
    )
    out.append("")
    out.append(
        f"  ({total_pass / d.total_runs * 100:.1f}% PASS, "
        f"{total_retry / d.total_runs * 100:.1f}% RETRY, "
        f"{total_return_best / d.total_runs * 100:.1f}% RETURN_BEST, "
        f"{total_abort / d.total_runs * 100:.1f}% ABORT)"
    )
    out.append("")

    # ---- Q2: Dimension score-0 rate per skill ----
    out.append("[Q2] Dimension score-0 rate per skill (lower is better)")
    out.append("-" * 78)
    if d.dimension_score_zero_rate:
        out.append(
            f"  {'Skill':<22} {'correct':>8} {'safety':>7} {'idem':>7} "
            f"{'trace':>7} {'spec':>7}"
        )
        out.append("  " + "-" * 64)
        for skill in sorted(d.dimension_score_zero_rate.keys()):
            rates = d.dimension_score_zero_rate[skill]
            out.append(
                f"  {skill:<22} "
                f"{rates.get('correctness', 0) * 100:>7.1f}% "
                f"{rates.get('safety', 0) * 100:>6.1f}% "
                f"{rates.get('idempotency', 0) * 100:>6.1f}% "
                f"{rates.get('traceability', 0) * 100:>6.1f}% "
                f"{rates.get('spec_compliance', 0) * 100:>6.1f}%"
            )
    else:
        out.append("  (no score-zero events)")
    out.append("")

    # ---- Q3: Iteration histogram for PASS / RETURN_BEST ----
    out.append("[Q3] Iteration count for PASS / RETURN_BEST")
    out.append("-" * 78)
    if d.iter_histogram:
        max_count = max(d.iter_histogram.values())
        for iters in sorted(d.iter_histogram.keys()):
            n = d.iter_histogram[iters]
            bar = "█" * int(40 * n / max_count) if max_count else ""
            out.append(f"  {iters} iter: {n:>4}  {bar}")
    else:
        out.append("  (no PASS / RETURN_BEST runs)")
    out.append("")

    # ---- Q4: Safety confirm bar check ----
    out.append("[Q4] Safety confirm — destructive ops without `safety_confirm` flag")
    out.append("-" * 78)
    if d.by_skill_safety_zero:
        out.append(
            f"  {'Skill':<22} {'safety=0 runs':>14}"
        )
        for skill, n in sorted(
            d.by_skill_safety_zero.items(), key=lambda kv: -kv[1]
        ):
            out.append(f"  {skill:<22} {n:>14}")
        out.append("")
        out.append("  Note: any non-zero count for a `required`-class skill is a P0 incident.")
    else:
        out.append("  (no safety=0 events in this window)")
    out.append("")

    # ---- Q5: Top safety auto-fail reasons ----
    out.append("[Q5] Top safety auto-fail reasons (from Critic suggestions)")
    out.append("-" * 78)
    if d.safety_auto_fail_reasons:
        out.append(
            f"  {'Reason (dimension / category)':<40} {'count':>7}"
        )
        for reason, n in d.safety_auto_fail_reasons.most_common(10):
            out.append(f"  {reason:<40} {n:>7}")
    else:
        out.append("  (no auto-fail reasons in this window)")
    out.append("")

    # ---- Data quality footer ----
    out.append("-" * 78)
    if errors:
        out.append(
            f"  [DATA-QUALITY] {len(errors)} malformed trace(s):"
        )
        for path, err in errors[:5]:
            out.append(f"    {path.name}: {err}")
        if len(errors) > 5:
            out.append(f"    ... and {len(errors) - 5} more")
    else:
        out.append("  [DATA-QUALITY] All traces parse cleanly.")
    out.append("=" * 78)
    return "\n".join(out)


def render_json(
    d: DashboardData,
    errors: list[tuple[Path, str]],
    pruned_count: int = 0,
    skill_filter: Optional[str] = None,
) -> str:
    """Render the dashboard as JSON. Suitable for downstream
    automation (Phase 4 alarms, Grafana, etc.)."""
    payload = {
        "scope": {
            "skill_filter": skill_filter,
            "pruned_count": pruned_count,
        },
        "total_runs": d.total_runs,
        "overall_abort_rate": d.overall_abort_rate,
        "by_skill": {
            skill: dict(counts) for skill, counts in d.by_skill.items()
        },
        "per_skill_abort_rate": d.per_skill_abort_rate,
        "iter_histogram": dict(d.iter_histogram),
        "by_skill_safety_zero": d.by_skill_safety_zero,
        "dimension_score_zero_rate": d.dimension_score_zero_rate,
        "safety_auto_fail_reasons": dict(d.safety_auto_fail_reasons),
        "data_quality_errors": [
            {"path": str(p), "error": e} for p, e in errors
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_since(s: str) -> timedelta:
    """Parse a duration string like '24h', '7d', '30m' into a timedelta."""
    m = re.match(r"^(\d+)([smhd])$", s.strip().lower())
    if not m:
        raise argparse.ArgumentTypeError(
            f"invalid duration: {s!r} (expected like '24h', '7d', '30m')"
        )
    n = int(m.group(1))
    unit = m.group(2)
    if unit == "s":
        return timedelta(seconds=n)
    if unit == "m":
        return timedelta(minutes=n)
    if unit == "h":
        return timedelta(hours=n)
    if unit == "d":
        return timedelta(days=n)
    raise argparse.ArgumentTypeError(f"unknown unit: {unit}")


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gcl_dashboard",
        description="GCL Quality Gate Dashboard (Phase 3 aggregator)",
    )
    p.add_argument(
        "--trace-dir",
        default=None,
        help=f"trace directory (default: {DEFAULT_TRACE_DIR})",
    )
    p.add_argument(
        "--since",
        type=parse_since,
        default=None,
        help="only include traces newer than this duration (e.g., 24h, 7d)",
    )
    p.add_argument(
        "--skill",
        default=None,
        help="multi-tenant filter: only include traces for this skill "
             "(e.g., jdcloud-vm-ops). Useful for per-team dashboards.",
    )
    p.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help="trace retention policy: delete trace files older than this "
             "many days (based on file mtime). Pruning runs BEFORE the "
             "dashboard is rendered, so pruned files won't appear in the "
             "current view. Set to 0 to disable (default: disabled).",
    )
    p.add_argument(
        "--format",
        choices=["terminal", "json"],
        default="terminal",
        help="output format (default: terminal)",
    )
    p.add_argument(
        "--out",
        default=None,
        help="write output to file instead of stdout",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_argparser().parse_args(argv)

    trace_dir = Path(args.trace_dir) if args.trace_dir else DEFAULT_TRACE_DIR

    # P2-1: Trace retention policy — prune BEFORE rendering so the
    # dashboard reflects the post-prune state. Best-effort: pruning
    # errors don't fail the dashboard run.
    pruned_count = 0
    if args.retention_days is not None and args.retention_days > 0:
        pruned_count, _ = prune_old_traces(trace_dir, args.retention_days)

    traces, errors = load_traces(trace_dir, since=args.since, skill_filter=args.skill)

    data = DashboardData()
    data.compute(traces)

    if args.format == "json":
        out = render_json(data, errors, pruned_count=pruned_count, skill_filter=args.skill)
    else:
        out = render_terminal(data, errors, pruned_count=pruned_count, skill_filter=args.skill)

    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    else:
        print(out)

    # Exit code: non-zero if any data-quality errors. Alerts
    # (e.g., >5% abort) are surfaced in the dashboard text, not
    # the exit code — we don't want CI to page on every alert.
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
