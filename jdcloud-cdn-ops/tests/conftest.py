"""conftest for jdcloud-cdn-ops tests.

Per AGENTS.md §3 "Test-driven" + skill-generator rule 4:
each skill must have conftest + smoke + rubric tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def domain_fixture() -> dict[str, Any]:
    with (FIXTURES / "domain.json").open() as f:
        return json.load(f)


@pytest.fixture
def cache_rule_fixture() -> dict[str, Any]:
    with (FIXTURES / "cache-rule.json").open() as f:
        return json.load(f)


@pytest.fixture
def example_config() -> str:
    """Path to assets/example-config.yaml — used by integration tests."""
    return str(Path(__file__).parent.parent / "assets" / "example-config.yaml")


@pytest.fixture
def mock_jdc_output(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture jdc invocations; default empty list."""
    captured: list[str] = []

    def fake_run(cmd: str, *args: str, **kwargs: Any) -> str:
        captured.append(cmd)
        return json.dumps({"result": {"ok": True}, "error": None})

    monkeypatch.setattr("subprocess.run", fake_run)
    return captured
