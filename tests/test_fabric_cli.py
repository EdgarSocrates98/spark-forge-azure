"""SDD FABRIC_CORE — CLI/MCP surface for the Fabric vertical."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

FIXTURES = Path("tests/fixtures/fabric")


def _env(tmp_path):
    env = dict(os.environ)
    env["SPARKFORGE_AZURE_STATE_DIR"] = str(tmp_path / "state")
    return env


def test_diagnose_fabric_cli_json_contract(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", "diagnose",
         "fabric", "--bundle", str(FIXTURES / "f02_onelake_denied")],
        capture_output=True, text=True, env=_env(tmp_path), cwd=Path.cwd())
    assert proc.returncode in (0, 1), proc.stderr[:800]
    out = json.loads(proc.stdout)
    for key in ("status", "failure_layer", "diagnosis", "fabric_graph",
                "receipt"):
        assert key in out, key
    assert out["failure_layer"] == "onelake_security"


def test_diagnose_fabric_suite_cli(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", "diagnose",
         "fabric", "--suite", str(FIXTURES)],
        capture_output=True, text=True, env=_env(tmp_path), cwd=Path.cwd())
    out = json.loads(proc.stdout)
    assert out["failed"] == 0


def test_mcp_sfa_diagnose_fabric():
    from sparkforge_azure.mcp.tools import TOOLS, load_all
    load_all()
    assert "sfa_diagnose_fabric" in TOOLS
    spec = TOOLS["sfa_diagnose_fabric"]
    assert "read" in str(spec.risk).lower()
    result = spec.handler({"bundle": str(FIXTURES / "f02_onelake_denied")})
    assert result["failure_layer"] == "onelake_security"
