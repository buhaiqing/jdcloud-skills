#!/usr/bin/env python3
"""
GCL Ground-Truth Corpus Generator (testing utility).

This script generates a reproducible mock corpus of GCL traces
into `tests/gcl_mock_corpus.jsonl`. The mock corpus is for
**stress-testing** the GCL dashboard (`gcl_dashboard.py`); it
is NOT the ground truth.

The actual ground truth — the expert-labeled dataset that
defines "the right answer" — lives in `gcl_ground_truth.jsonl`
and is curated by hand.

## Why a corpus generator at all?

A real production trace dump is hard to reproduce, so
regression tests for the dashboard would be flaky. The corpus
generator produces deterministic traces (random seed fixed) so
that:

- Dashboard changes can be tested against a stable input
- Regression in dashboard rendering is caught by snapshot diff
- New dashboards can be compared to a baseline

## What this script does NOT do

- It does NOT create ground truth. The expert labels are human
  responsibility and live in `gcl_ground_truth.jsonl`.
- It does NOT test the GCL loop logic itself. That's
  `gcl_runner.py`'s self-check.

## Usage

    # Generate 100 traces into tests/gcl_mock_corpus.jsonl
    python3 tests/gcl_ground_truth_gen.py --count 100

    # Reproducible (fixed seed = 42)
    python3 tests/gcl_ground_truth_gen.py --count 100 --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Per-skill profile — the ground truth of "what we expect to see"
# ---------------------------------------------------------------------------

# These are the "intended" fail rates per dimension, per skill,
# captured from the rollout experience. Used for reproducible
# mock generation. The exact rates don't matter for testing the
# dashboard; what matters is that the generator is deterministic.

# Format: per (skill, dimension) -> probability that a single
# iteration scores 0 on that dimension. Safety is intentionally
# higher for write-class skills.

INTENDED_FAIL_RATES: dict[str, dict[str, float]] = {
    "vm-ops":              {"correctness": 0.01, "safety": 0.02, "idempotency": 0.05, "traceability": 0.02, "spec_compliance": 0.01},
    "redis-ops":           {"correctness": 0.00, "safety": 0.00, "idempotency": 0.02, "traceability": 0.01, "spec_compliance": 0.00},
    "mysql-ops":           {"correctness": 0.02, "safety": 0.01, "idempotency": 0.03, "traceability": 0.01, "spec_compliance": 0.01},
    "postgresql-ops":      {"correctness": 0.01, "safety": 0.01, "idempotency": 0.02, "traceability": 0.01, "spec_compliance": 0.01},
    "mongodb-ops":         {"correctness": 0.01, "safety": 0.01, "idempotency": 0.04, "traceability": 0.01, "spec_compliance": 0.02},
    "elasticsearch-ops":   {"correctness": 0.01, "safety": 0.02, "idempotency": 0.02, "traceability": 0.01, "spec_compliance": 0.01},
    "iam-ops":             {"correctness": 0.01, "safety": 0.03, "idempotency": 0.01, "traceability": 0.01, "spec_compliance": 0.02},
    "kms-ops":             {"correctness": 0.01, "safety": 0.02, "idempotency": 0.01, "traceability": 0.02, "spec_compliance": 0.01},
    "eip-ops":             {"correctness": 0.00, "safety": 0.01, "idempotency": 0.01, "traceability": 0.00, "spec_compliance": 0.00},
    "clb-ops":             {"correctness": 0.01, "safety": 0.01, "idempotency": 0.04, "traceability": 0.02, "spec_compliance": 0.02},
    "cloudmonitor-ops":    {"correctness": 0.01, "safety": 0.04, "idempotency": 0.01, "traceability": 0.01, "spec_compliance": 0.02},
    "alert-intelligence":  {"correctness": 0.02, "safety": 0.00, "idempotency": 0.01, "traceability": 0.02, "spec_compliance": 0.01},
    "audit-ops":           {"correctness": 0.01, "safety": 0.00, "idempotency": 0.01, "traceability": 0.01, "spec_compliance": 0.01},
    "tag-audit-ops":       {"correctness": 0.01, "safety": 0.00, "idempotency": 0.02, "traceability": 0.01, "spec_compliance": 0.01},
    "skill-generator":     {"correctness": 0.01, "safety": 0.01, "idempotency": 0.01, "traceability": 0.02, "spec_compliance": 0.01},
}


def make_critic(profile: dict[str, float]) -> callable:
    """Build a critic that scores per the given fail rates."""

    def critic(gen_out, trace, rubric):
        scores = {}
        for d in RUBRIC_DIMENSIONS:
            if random.random() < profile.get(d, 0.0):
                scores[d] = 0.0
            else:
                # Pass values: 1.0 for hard-required dims, 0.5/1.0
                # for soft dims (mimics real LLM noise).
                if d in ("correctness", "safety"):
                    scores[d] = 1.0
                else:
                    scores[d] = random.choice([0.5, 1.0])
        return CriticScore(
            scores=scores,
            justifications={d: f"profile {profile.get(d, 0):.2f}" for d in RUBRIC_DIMENSIONS},
            suggestions=[
                f"address {d}" for d in RUBRIC_DIMENSIONS
                if scores.get(d, 1.0) == 0.0
            ],
            blocking=scores.get("safety", 1.0) == 0.0,
        )

    return critic


def make_generator(skill: str) -> callable:
    """Build a generator that records a synthetic command."""

    def generator(request, feedback, rubric, iter):
        return GeneratorOutput(
            command=f"jdc {skill} mock-op",
            args={"request": request[:40], "iter": iter},
            exit_code=0,
            result=f"mock result for {skill}",
            post_state={"status": "ok", "skill": skill, "iter": iter},
        )

    return generator


def generate(
    count: int,
    seed: int,
    out_path: Path,
    skills: list[str],
) -> int:
    """Generate `count` mock traces, save to `out_path`.

    Each trace is also written to the repo-root `audit-results/`
    for dashboard consumption, and a metadata record is appended
    to `out_path` so the corpus is self-describing.
    """
    random.seed(seed)

    # Traces go to REPO_ROOT/audit-results/ so the dashboard
    # finds them by default. The corpus metadata lives in tests/.
    trace_dir = REPO_ROOT / "audit-results"
    trace_dir.mkdir(parents=True, exist_ok=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = []

    for i in range(count):
        skill = random.choice(skills)
        profile = INTENDED_FAIL_RATES[skill]
        rubric = parse_rubric(
            skill,
            REPO_ROOT / f"jdcloud-{skill}" / "references" / "rubric.md",
        )

        decision, trace = run_gcl(
            skill=skill,
            request=f"corpus-gen test #{i} for {skill}",
            safety_confirm=random.random() > 0.1,
            generator_fn=make_generator(skill),
            critic_fn=make_critic(profile),
            rubric=rubric,
        )

        # Backdate so --since filtering is testable
        backdate = datetime.now(timezone.utc) - timedelta(days=random.uniform(0, 30))
        trace.started_at = backdate.isoformat()
        if trace.finished_at:
            trace.finished_at = (backdate + timedelta(seconds=random.uniform(0.5, 5))).isoformat()

        trace_path = write_trace(trace, trace_dir)

        records.append({
            "corpus_index": i,
            "skill": skill,
            "final_status": trace.final["status"],
            "iterations": len(trace.iterations),
            "trace_path": str(trace_path.relative_to(REPO_ROOT)),
            "run_id": trace.run_id,
            "started_at": trace.started_at,
        })

    # Write JSONL corpus
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return len(records)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="gcl_ground_truth_gen",
        description="Generate a reproducible mock corpus for GCL dashboard tests",
    )
    p.add_argument(
        "--count",
        type=int,
        default=100,
        help="number of mock traces to generate (default: 100)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed for reproducibility (default: 42)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent / "gcl_mock_corpus.jsonl",
        help="output JSONL path",
    )
    p.add_argument(
        "--skills",
        nargs="*",
        default=list(INTENDED_FAIL_RATES.keys()),
        help="restrict to specific skills",
    )
    args = p.parse_args(argv)

    n = generate(args.count, args.seed, args.out, args.skills)
    print(f"Generated {n} mock traces; corpus written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
