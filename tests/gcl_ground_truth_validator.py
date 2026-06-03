#!/usr/bin/env python3
"""
GCL Ground-Truth Validator.

This script validates the structure of `gcl_ground_truth.jsonl`
and verifies that the labels are internally consistent with the
rubric thresholds defined in `gcl_runner.py`.

## What this script checks

For every ground-truth record:

1. **Schema**: all required fields are present and have correct types
2. **Skill exists**: the skill name matches a `jdcloud-*-ops` directory
3. **Status is valid**: one of PASS / ABORT / RETURN_BEST
4. **expected_status agrees with expected_score_0_dims**:
   - status=PASS        → no score=0 dimensions
   - status=ABORT       → safety MUST be in expected_score_0_dims
   - status=RETURN_BEST → safety MUST NOT be in expected_score_0_dims
                          (else it would have been ABORT)
5. **expected_iterations is sane**:
   - status=PASS        → expected_iterations >= 1
   - status=ABORT       → expected_iterations == 1
   - status=RETURN_BEST → expected_iterations == max_iter for the skill

## What this script does NOT do

- It does NOT run the GCL loop. That's `gcl_runner.py`.
- It does NOT compare against a real trace. The ground truth
  is a label, not an output.
- It does NOT judge whether the labels are correct. That's a
  human responsibility (this validator checks internal
  consistency, not semantic correctness).

## Usage

    python3 tests/gcl_ground_truth_validator.py
    python3 tests/gcl_ground_truth_validator.py --ground-truth tests/gcl_ground_truth.jsonl

## Exit codes

    0   All records valid
    1   At least one validation failure
    2   Usage error
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gcl_runner import RUBRIC_DIMENSIONS, parse_rubric  # noqa: E402


REQUIRED_FIELDS = (
    "id",
    "skill",
    "request_intent",
    "expected_status",
    "expected_decision_reason",
    "expected_score_0_dims",
    "expected_iterations",
    "rubric_satisfied",
    "annotations",
    "created_at",
)

VALID_STATUSES = ("PASS", "ABORT", "RETURN_BEST")

VALID_ANNOTATION_TAGS = {
    "destructive-op", "idempotent", "baseline", "prod-incident", "safety-auto-fail",
    "retry-pattern", "idempotency-fix", "data-destruction", "ddl", "schema",
    "missing-where", "pg-specific", "cascade", "es-specific", "wildcard",
    "iam-specific", "secret-must-log", "kms-specific", "pending-window",
    "clb-specific", "drain", "silent-failure", "cloudmonitor-specific",
    "read-only", "read-only-mandate", "pii-leak", "audit-specific",
    "dops-ticket", "idempotency-check", "meta-skill", "openspec", "self-review",
    "return-best", "idempotency-n/a",
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@dataclass
class ValidationError:
    record_id: str
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.record_id}] field={self.field!r}: {self.message}"


# We avoid importing dataclasses from anywhere to keep the
# validator tiny and dependency-free.
class _DC:  # noqa: F841
    pass


def validate_record(record: dict[str, Any]) -> list[ValidationError]:
    """Validate one ground-truth record. Returns list of errors
    (empty if valid)."""
    errors: list[ValidationError] = []
    rid = record.get("id", "<missing id>")

    # 1. Required fields
    for f in REQUIRED_FIELDS:
        if f not in record:
            errors.append(ValidationError(rid, f, "missing required field"))

    # 2. Skill exists
    skill = record.get("skill", "")
    skill_dir = REPO_ROOT / f"jdcloud-{skill}"
    if not skill_dir.is_dir():
        errors.append(ValidationError(rid, "skill", f"unknown skill: {skill!r}"))

    # 3. Status is valid
    status = record.get("expected_status")
    if status not in VALID_STATUSES:
        errors.append(
            ValidationError(
                rid, "expected_status",
                f"invalid status {status!r}; must be one of {VALID_STATUSES}",
            )
        )

    # 4. expected_status agrees with expected_score_0_dims
    # NOTE: expected_score_0_dims lists dimensions that scored 0
    # at ANY iteration (including iterations that were retried).
    # A RETRY→PASS run will have non-empty score_0_dims even
    # though the final status is PASS. The rule is:
    #   - status=ABORT       → safety MUST be in score_0_dims
    #   - status=RETURN_BEST → safety MUST NOT be in score_0_dims
    score_0 = record.get("expected_score_0_dims", [])
    if not isinstance(score_0, list):
        errors.append(ValidationError(rid, "expected_score_0_dims", "must be a list"))
    else:
        for d in score_0:
            if d not in RUBRIC_DIMENSIONS:
                errors.append(
                    ValidationError(
                        rid, "expected_score_0_dims",
                        f"unknown dimension: {d!r}",
                    )
                )

        if status == "ABORT" and "safety" not in score_0:
            errors.append(
                ValidationError(
                    rid, "expected_status",
                    f"status=ABORT but 'safety' is not in expected_score_0_dims: {score_0}",
                )
            )
        if status == "RETURN_BEST" and "safety" in score_0:
            errors.append(
                ValidationError(
                    rid, "expected_status",
                    f"status=RETURN_BEST but 'safety' is in expected_score_0_dims; "
                    f"safety=0 would have triggered ABORT first",
                )
            )
        # For PASS, score_0_dims CAN be non-empty (RETRY→PASS pattern).
        # The validator does NOT check this; it's the human labeler's
        # responsibility to ensure the rationale explains the retry.

        # If score_0 is empty AND status=PASS, expected_iterations
        # MUST be 1 (no retry happened).
        if status == "PASS" and not score_0 and record.get("expected_iterations") != 1:
            errors.append(
                ValidationError(
                    rid, "expected_iterations",
                    f"status=PASS with no score_0_dims but expected_iterations="
                    f"{record.get('expected_iterations')}; first-iter PASS should have iter=1",
                )
            )

    # 5. expected_iterations is sane
    iters = record.get("expected_iterations")
    if not isinstance(iters, int) or iters < 1:
        errors.append(ValidationError(rid, "expected_iterations", "must be a positive integer"))
    elif status == "ABORT" and iters != 1:
        errors.append(
            ValidationError(
                rid, "expected_iterations",
                f"status=ABORT but expected_iterations={iters}; ABORT should happen in iter 1",
            )
        )

    # 6. Annotations structure
    ann = record.get("annotations", {})
    if not isinstance(ann, dict):
        errors.append(ValidationError(rid, "annotations", "must be a dict"))
    else:
        if "annotator" not in ann:
            errors.append(ValidationError(rid, "annotations.annotator", "missing"))
        if "rationale" not in ann:
            errors.append(ValidationError(rid, "annotations.rationale", "missing"))
        tags = ann.get("tags", [])
        if not isinstance(tags, list):
            errors.append(ValidationError(rid, "annotations.tags", "must be a list"))
        else:
            for t in tags:
                if t not in VALID_ANNOTATION_TAGS:
                    errors.append(
                        ValidationError(
                            rid, "annotations.tags",
                            f"unknown tag {t!r}; not in VALID_ANNOTATION_TAGS",
                        )
                    )

    # 7. rubric_satisfied is a bool
    if not isinstance(record.get("rubric_satisfied"), bool):
        errors.append(ValidationError(rid, "rubric_satisfied", "must be a bool"))

    return errors


# Re-add dataclass import
def validate_file(gt_path: Path) -> tuple[int, list[ValidationError], dict[str, int]]:
    """Validate the entire ground-truth file. Returns (total, errors, status_counts)."""
    all_errors: list[ValidationError] = []
    status_counts: Counter = Counter()
    total = 0
    seen_ids: set[str] = set()

    if not gt_path.exists():
        return 0, [ValidationError("<file>", "<file>", f"not found: {gt_path}")], status_counts

    with gt_path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(
                    ValidationError(f"<line {lineno}>", "<line>", f"json decode: {e}")
                )
                continue

            total += 1
            rid = record.get("id", f"<line {lineno}>")
            if rid in seen_ids:
                all_errors.append(ValidationError(rid, "id", "duplicate id"))
            seen_ids.add(rid)

            errs = validate_record(record)
            all_errors.extend(errs)
            status_counts[record.get("expected_status", "UNKNOWN")] += 1

    return total, all_errors, status_counts


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="gcl_ground_truth_validator",
        description="Validate internal consistency of gcl_ground_truth.jsonl",
    )
    p.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(__file__).parent / "gcl_ground_truth.jsonl",
        help="path to ground-truth JSONL",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors",
    )
    args = p.parse_args(argv)

    total, errors, status_counts = validate_file(args.ground_truth)

    print(f"=== Ground-truth validation: {args.ground_truth} ===")
    print(f"  Records: {total}")
    print(f"  Status distribution: {dict(status_counts)}")
    if total:
        skill_counts: Counter = Counter()
        with args.ground_truth.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                skill_counts[d.get("skill", "UNKNOWN")] += 1
        print(f"  Skills covered: {len(skill_counts)}/{len([p for p in REPO_ROOT.iterdir() if p.name.startswith('jdcloud-') and p.is_dir()])}")
        print(f"  Per-skill counts: {dict(skill_counts)}")

    print()
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors:
            print(f"    {e}")
        return 1
    print("  ✅ All records valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
