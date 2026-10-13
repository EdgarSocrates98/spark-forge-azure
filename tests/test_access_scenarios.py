"""Os 10 cenários determinísticos do vertical UC/ADLS (AC4)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sparkforge_azure.azure import pipeline

FIXTURES = Path(__file__).parent / "fixtures" / "access"


def _scenarios() -> list[Path]:
    return sorted(p.parent for p in FIXTURES.glob("*/case.yaml"))


@pytest.mark.parametrize("bundle", _scenarios(), ids=lambda p: p.name)
def test_all_scenarios_fail_at_expected_layer(bundle: Path) -> None:
    case = yaml.safe_load((bundle / "case.yaml").read_text(encoding="utf-8"))
    expect = case["expect"]
    report = pipeline.run_case(bundle)
    assert report["status"] == expect["status"], report.get("unresolved")
    assert report["failure_layer"] == expect["failure_layer"]
