"""Pytest fixtures for jdcloud-kms-ops tests."""
import json
import sys
from pathlib import Path
import pytest

SKILL_DIR = Path(__file__).parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def skill_dir():
    """Return the skill root directory."""
    return SKILL_DIR


@pytest.fixture
def fixtures_dir():
    """Return the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def load_fixture():
    """Load a JSON fixture by name."""

    def _load(name: str) -> dict:
        path = FIXTURES_DIR / f"{name}.json"
        with open(path) as f:
            return json.load(f)

    return _load


@pytest.fixture
def rubric_template():
    """Return the expected rubric dimensions and thresholds for destructive ops."""
    return {
        "dimensions": [
            "correctness",
            "safety",
            "idempotency",
            "traceability",
            "spec_compliance",
        ],
        "levels": [0, 0.5, 1],
        "safety_abort_on_zero": True,
        "thresholds": {
            "correctness": 0.5,
            "safety": 1.0,
            "idempotency": 0.5,
            "traceability": 0.5,
            "spec_compliance": 0.5,
        },
        "max_iterations": 2,
        "gcl_level": "required",
    }
