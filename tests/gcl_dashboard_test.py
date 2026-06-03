#!/usr/bin/env python3
"""
GCL Dashboard Test — verify dashboard against ground truth.

This is a closed-loop test: for each ground-truth record, we
generate a deterministic mock trace that **exactly matches** the
ground-truth label, then run the dashboard over all traces, and
verify the dashboard's aggregated output is consistent with the
labels.

## What this test checks

For each record in `gcl_ground_truth.jsonl`:

1. **Trace creation**: we can construct a mock trace whose
   `final.status` equals the record's `expected_status`.
2. **Per-record Q1 (skill-level abort rate)**: the count of
   records with status=ABORT for each skill is correctly
   reflected in the dashboard's `by_skill` aggregate.
3. **Per-record Q2 (dimension score-0 rate)**: the score=0
   events are reflected in the dashboard's
   `dimension_score_zero_rate` per-skill view.
4. **Per-record Q3 (iteration histogram)**: the
   `expected_iterations` is reflected in the dashboard's
   `iter_histogram` for PASS / RETURN_BEST records.
5. **Per-record Q4 (safety=0 count)**: the safety=0 events
   are reflected in `by_skill_safety_zero`.
6. **Per-record Q5 (auto-fail reasons)**: the score=0
   dimensions are reflected in `safety_auto_fail_reasons`.

## What this test does NOT check

- The dashboard's *rendered text*. JSON output is asserted;
  text rendering is a thin wrapper.
- The exact threshold logic. The dashboard's alert thresholds
  (5% / 2%) are tested in `gcl_dashboard.py`'s own unit
  checks; this test verifies the *aggregated counts*.
- Cross-record interaction. Each record is checked in
  isolation (only its own contribution to the dashboard).

## Usage

    # Run the test
    python3 tests/gcl_dashboard_test.py

    # With a different corpus
    python3 tests/gcl_dashboard_test.py --ground-truth tests/gcl_ground_truth.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gcl_runner import (  # noqa: E402
    GeneratorOutput,
    CriticScore,
    RUBRIC_DIMENSIONS,
    parse_rubric,
    run_gcl,
    write_trace,
)

sys.path.insert(0, str(REPO_ROOT / "tests"))
from gcl_dashboard import load_traces, DashboardData, parse_iso  # noqa: E402


# ---------------------------------------------------------------------------
# Test fixture builders
# ---------------------------------------------------------------------------


def make_critic_for_record(record: dict[str, Any]) -> callable:
    """Build a critic that produces the score pattern the record
    expects. We need to encode both `expected_status` and
    `expected_score_0_dims` (across all iterations).

    For status=PASS without score_0_dims: all dims = 1.0, 1 iter
    For status=PASS with score_0_dims (RETRY→PASS pattern):
      - iter 1: dims in score_0_dims are 0.0, others 1.0
      - iter 2: all dims 1.0
    For status=ABORT: dims in score_0_dims are 0.0 (incl. safety)
      1 iter only
    For status=RETURN_BEST: dims in score_0_dims are 0.0 (NOT safety),
      max_iterations iters with no fix
    """
    score_0 = set(record.get("expected_score_0_dims", []))
    status = record.get("expected_status")
    n_iter = record.get("expected_iterations", 1)

    iter_counter = {"n": 0}

    def critic(gen_out, trace, rubric):
        iter_counter["n"] += 1
        it = iter_counter["n"]
        scores = {}
        for d in RUBRIC_DIMENSIONS:
            # For RETRY→PASS: iter 1 has score_0, iter 2 has 1.0
            if status == "PASS" and it == 1 and d in score_0:
                scores[d] = 0.0
            elif status == "ABORT" and d in score_0:
                scores[d] = 0.0
            elif status == "RETURN_BEST" and d in score_0:
                scores[d] = 0.0
            else:
                scores[d] = 1.0
        blocking = scores.get("safety", 1.0) == 0.0
        return CriticScore(
            scores=scores,
            justifications={d: f"test fixture for {record['id']}" for d in RUBRIC_DIMENSIONS},
            suggestions=[
                f"address {d}" for d in RUBRIC_DIMENSIONS
                if scores.get(d, 1.0) == 0.0
            ],
            blocking=blocking,
        )

    return critic


def make_generator_for_record(record: dict[str, Any]) -> callable:
    """Build a generator that records the run id and adapts to
    the number of iterations."""
    def generator(request, feedback, rubric, iter):
        return GeneratorOutput(
            command=f"jdc {record['skill']} mock-op (iter {iter})",
            args={"request": request[:40], "iter": iter, "feedback": feedback[:60] if feedback else ""},
            exit_code=0,
            result=f"mock result for {record['id']} iter {iter}",
            post_state={"status": "ok", "skill": record["skill"], "iter": iter},
        )
    return generator


# ---------------------------------------------------------------------------
# The test
# ---------------------------------------------------------------------------


def run_test(gt_path: Path, verbose: bool = False) -> int:
    """Run the dashboard test. Returns 0 on success, 1 on failure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        trace_dir = Path(tmp_dir) / "audit-results"
        trace_dir.mkdir()

        # Build a synthetic trace for each ground-truth record
        records = []
        with gt_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))

        for record in records:
            rubric = parse_rubric(
                record["skill"],
                REPO_ROOT / f"jdcloud-{record['skill']}" / "references" / "rubric.md",
            )
            decision, trace = run_gcl(
                skill=record["skill"],
                request=record.get("request_intent", "test"),
                safety_confirm=True,  # confirm is a separate check, not a fix
                generator_fn=make_generator_for_record(record),
                critic_fn=make_critic_for_record(record),
                rubric=rubric,
            )
            # Verify the synthetic trace matches the label
            actual_status = trace.final.get("status")
            if actual_status != record["expected_status"]:
                print(
                    f"  [FAIL] {record['id']}: trace ended with status={actual_status} "
                    f"but expected {record['expected_status']}"
                )
                return 1
            if len(trace.iterations) != record["expected_iterations"]:
                print(
                    f"  [FAIL] {record['id']}: trace had {len(trace.iterations)} iters "
                    f"but expected {record['expected_iterations']}"
                )
                return 1
            write_trace(trace, trace_dir)

        # Now load all traces via the dashboard loader
        traces, errors = load_traces(trace_dir)
        if errors:
            print(f"  [FAIL] dashboard loader reported {len(errors)} errors:")
            for path, err in errors:
                print(f"    {path}: {err}")
            return 1

        # Aggregate
        data = DashboardData()
        data.compute(traces)

        if verbose:
            print(f"  Built {len(traces)} traces; total={data.total_runs}")
            print(f"  by_skill: {dict(data.by_skill)}")
            print(f"  iter_histogram: {dict(data.iter_histogram)}")
            print(f"  by_skill_safety_zero: {data.by_skill_safety_zero}")
            print(f"  safety_auto_fail_reasons: {dict(data.safety_auto_fail_reasons)}")

        # ---- Q1 per-skill check: counts ----
        for record in records:
            skill = record["skill"]
            status = record["expected_status"]
            expected_count = sum(
                1 for r in records
                if r["skill"] == skill and r["expected_status"] == status
            )
            actual_count = data.by_skill.get(skill, {}).get(status, 0)
            if actual_count != expected_count:
                print(
                    f"  [FAIL] {record['id']}: Q1 by_skill[{skill!r}][{status!r}] "
                    f"expected {expected_count}, got {actual_count}"
                )
                return 1

        # ---- Q2 per-skill dimension rate ----
        # The dashboard's `dimension_score_zero_rate[skill][dim]` is
        # `events / total_iters`, where `events` is the count of
        # score-0 events for that (skill, dim) across all traces.
        # The number of events per record depends on the record's
        # status:
        #   - ABORT       : 1 event per dim in expected_score_0_dims
        #   - RETURN_BEST : expected_iterations events per dim
        #                   (all iters fail)
        #   - PASS+retry  : 1 event per dim in expected_score_0_dims
        #                   (only the first iter fails)
        def events_for(record: dict) -> dict[str, int]:
            score_0 = record.get("expected_score_0_dims", [])
            if not score_0:
                return {}
            status = record.get("expected_status")
            if status == "ABORT":
                return {d: 1 for d in score_0}
            if status == "RETURN_BEST":
                return {d: record["expected_iterations"] for d in score_0}
            if status == "PASS":
                # RETRY→PASS: only the first iter fails.
                return {d: 1 for d in score_0}
            return {d: 1 for d in score_0}

        for record in records:
            skill = record["skill"]
            score_0 = record.get("expected_score_0_dims", [])
            if not score_0:
                continue
            iters_for_skill = sum(
                r["expected_iterations"] for r in records if r["skill"] == skill
            )
            for dim in score_0:
                # Sum events across all records (status-dependent).
                events = sum(
                    events_for(r).get(dim, 0)
                    for r in records
                    if r["skill"] == skill
                )
                expected_rate = events / iters_for_skill if iters_for_skill else 0.0
                actual_rate = data.dimension_score_zero_rate.get(skill, {}).get(dim, 0.0)
                # Allow a small float tolerance
                if abs(actual_rate - expected_rate) > 0.01:
                    print(
                        f"  [FAIL] {record['id']}: Q2 dim_rate[{skill!r}][{dim!r}] "
                        f"expected {expected_rate:.3f}, got {actual_rate:.3f}"
                    )
                    return 1

        # ---- Q3 iter histogram: only PASS / RETURN_BEST contribute
        for record in records:
            if record["expected_status"] not in ("PASS", "RETURN_BEST"):
                continue
            iters = record["expected_iterations"]
            expected_count = sum(
                1 for r in records
                if r["expected_status"] in ("PASS", "RETURN_BEST")
                and r["expected_iterations"] == iters
            )
            actual_count = data.iter_histogram.get(iters, 0)
            if actual_count != expected_count:
                print(
                    f"  [FAIL] {record['id']}: Q3 iter_histogram[{iters}] "
                    f"expected {expected_count}, got {actual_count}"
                )
                return 1

        # ---- Q4 safety=0 count
        for record in records:
            if "safety" not in record.get("expected_score_0_dims", []):
                continue
            skill = record["skill"]
            expected = sum(
                1 for r in records
                if r["skill"] == skill and "safety" in r.get("expected_score_0_dims", [])
            )
            actual = data.by_skill_safety_zero.get(skill, 0)
            if actual != expected:
                print(
                    f"  [FAIL] {record['id']}: Q4 by_skill_safety_zero[{skill!r}] "
                    f"expected {expected}, got {actual}"
                )
                return 1

        # ---- Q5 safety_auto_fail_reasons ----
        # The dashboard parses the FINAL iteration's suggestions for
        # the `address <dim>` pattern. So:
        #   - ABORT (1 iter)        : final is iter 1, which has the
        #                              suggestion. 1 event per score_0 dim.
        #   - RETURN_BEST (n iters) : final is iter n, which still has
        #                              the suggestion. 1 event per dim.
        #   - PASS (retry, 2 iters) : final is iter 2 which passes,
        #                              so suggestions are empty. 0 events.
        for dim in RUBRIC_DIMENSIONS:
            expected_count = sum(
                1 for r in records
                if r["expected_status"] in ("ABORT", "RETURN_BEST")
                and dim in r.get("expected_score_0_dims", [])
            )
            actual_count = data.safety_auto_fail_reasons.get(dim, 0)
            if actual_count != expected_count:
                print(
                    f"  [FAIL] {dim}: Q5 safety_auto_fail_reasons[{dim!r}] "
                    f"expected {expected_count}, got {actual_count}"
                )
                return 1

        print(f"  ✅ All {len(records)} ground-truth records produce a")
        print(f"     dashboard aggregation that matches their labels.")
        return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="gcl_dashboard_test",
        description="Verify dashboard aggregation against ground truth",
    )
    p.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(__file__).parent / "gcl_ground_truth.jsonl",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="print aggregation details",
    )
    args = p.parse_args(argv)

    print(f"=== GCL Dashboard Test ===")
    print(f"  Ground truth: {args.ground_truth}")
    print()
    rc = run_test(args.ground_truth, verbose=args.verbose)
    if rc == 0:
        print()
        print(f"  Result: PASS")
    else:
        print()
        print(f"  Result: FAIL")
    return rc


if __name__ == "__main__":
    sys.exit(main())
