"""``agentops`` CLI: runs/inspect/timeline/critical-path sobre traces.db."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from sparkforge_azure.observability.context_ledger import ContextLedger
from sparkforge_azure.observability.store import SQLiteTraceStore


def _seed_run(db: Path) -> str:
    ledger = ContextLedger(db_path=db, run_id="run_seed_test")
    t = time.time()
    ledger.record(name="diagnose.extract", resultado={"facts": 3},
                  detail_level="stage", outcome="ok", start_time=t)
    ledger.record(name="sfa_graph_query", resultado={"rows": 2},
                  detail_level="tool", outcome="ok", start_time=t)
    ledger.record(name="sfa_graph_query", resultado={"rows": 2},
                  detail_level="tool", outcome="ok", start_time=t)
    ledger.record(name="tokensave.search", resultado={"items": 2},
                  detail_level="L1", outcome="ok", start_time=t)
    ledger.record(name="tokensave.read_full", resultado={"items": 1},
                  detail_level="L6", outcome="ok", start_time=t)
    ledger.flush(final=True)
    return "run_seed_test"


def _cli(tmp_path: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", "agentops",
         "--db", str(tmp_path / "traces.db"), *argv],
        capture_output=True, text=True, cwd=tmp_path)


def test_list_runs(tmp_path: Path) -> None:
    db = tmp_path / "traces.db"
    run_id = _seed_run(db)
    runs = SQLiteTraceStore(db).list_runs()
    assert runs[0]["run_id"] == run_id
    assert runs[0]["spans"] == 5


def test_agentops_cli_end_to_end(tmp_path: Path) -> None:
    _seed_run(tmp_path / "traces.db")
    proc = _cli(tmp_path, "runs")
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["runs"][0]["run_id"] == "run_seed_test"

    proc = _cli(tmp_path, "inspect", "--run", "run_seed_test")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ok"
    waste = {w["pattern"] for w in payload["waste"]}
    assert "duplicate_tool_call" in waste  # sfa_graph_query repetido
    assert "full_read_after_index_hit" in waste  # L6 apos L1 ok

    proc = _cli(tmp_path, "timeline", "--run", "run_seed_test")
    assert json.loads(proc.stdout)["count"] == 5

    proc = _cli(tmp_path, "critical-path", "--run", "run_seed_test")
    assert json.loads(proc.stdout)["status"] == "ok"


def test_agentops_runs_requires_db(tmp_path: Path) -> None:
    proc = _cli(tmp_path, "runs")
    assert proc.returncode == 2
    assert "trace db not found" in proc.stdout + proc.stderr
