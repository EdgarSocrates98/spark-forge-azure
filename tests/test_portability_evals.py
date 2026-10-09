"""W7 — portability matrix + gate smoke (prompt_evo_portable.md §96–§101).

Runs the scenario runner and the static gate in-process. The wheel gate
(T3) stays manual/CI — it builds a wheel; a focused marker test covers
its presence without paying the build cost in the suite.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "evals" / "portability" / "runner.py"
GATE = ROOT / "scripts" / "check_portability.py"


def test_portability_matrix_all_cases_ok() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "portability: ok" in proc.stdout
    report = (RUNNER.parent / "reports" / "portability-matrix.json")
    import json

    data = json.loads(report.read_text(encoding="utf-8"))
    assert len(data["results"]) == 10
    assert all(r["status"] == "ok" for r in data["results"])


def test_portability_gate_static_ok() -> None:
    proc = subprocess.run(
        [sys.executable, str(GATE)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "portability gate: ok" in proc.stdout


def test_wheel_gate_function_exists() -> None:
    # T3 is exercised via `check_portability.py --wheel` (slow, builds a
    # wheel) — the suite only guards that the gate is wired.
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_portability  # noqa: PLC0415

    assert callable(check_portability.wheel_gate)
