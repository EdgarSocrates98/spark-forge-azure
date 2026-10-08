"""SDD STREAMING_ECONOMY_OBSERVABILITY — CLI/MCP surface do vertical."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

FIXTURES = Path("tests/fixtures/stream")


def _env(tmp_path):
    env = dict(os.environ)
    env["SPARKFORGE_AZURE_STATE_DIR"] = str(tmp_path / "state")
    return env


def test_diagnose_stream_cli_json_contract(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", "diagnose",
         "stream", "--bundle", str(FIXTURES / "s04-eh-throttled")],
        capture_output=True, text=True, env=_env(tmp_path), cwd=Path.cwd())
    assert proc.returncode in (0, 1), proc.stderr[:800]
    out = json.loads(proc.stdout)
    for key in ("status", "failure_layer", "diagnosis", "delivery",
                "stream_graph", "receipt"):
        assert key in out, key
    assert out["failure_layer"] == "event_hubs_capacity"


def test_diagnose_stream_suite_cli(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", "diagnose",
         "stream", "--suite", str(FIXTURES)],
        capture_output=True, text=True, env=_env(tmp_path), cwd=Path.cwd())
    out = json.loads(proc.stdout)
    assert out["failed"] == 0


def test_mcp_sfa_diagnose_stream():
    from sparkforge_azure.mcp.tools import TOOLS, load_all
    load_all()
    assert "sfa_diagnose_stream" in TOOLS
    spec = TOOLS["sfa_diagnose_stream"]
    assert "read" in str(spec.risk).lower()
    result = spec.handler({"bundle": str(FIXTURES / "s04-eh-throttled")})
    assert result["failure_layer"] == "event_hubs_capacity"
    assert result["delivery"]["classification"]
