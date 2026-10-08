"""Contrato do `sparkforge-azure diagnose`: um JSON, exit codes 0/1/2."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "access"


def _run(
    *argv: str, cwd: Path | None = None, state_dir: Path | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if state_dir is not None:
        env["SPARKFORGE_AZURE_STATE_DIR"] = str(state_dir)
    return subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", *argv],
        capture_output=True, text=True, cwd=cwd or FIXTURES, env=env)


def test_diagnose_cli_json_contract(tmp_path: Path) -> None:
    denied = _run("diagnose", "--bundle",
                  str(FIXTURES / "s01_uc_privilege_denied"), state_dir=tmp_path)
    doc = json.loads(denied.stdout)  # exatamente um documento JSON
    assert denied.returncode == 1
    assert doc["failure_layer"] == "unity_catalog"
    assert doc["diagnosis"]["status"] == "denied"

    allowed = _run("diagnose", "--bundle",
                   str(FIXTURES / "s07_governance_bypass"), state_dir=tmp_path)
    doc = json.loads(allowed.stdout)
    assert allowed.returncode == 1  # findings presentes -> exit 1
    assert doc["diagnosis"]["status"] == "allowed"
    assert doc["failure_layer"] == "governance_bypass"

    refused = _run("diagnose", "--bundle", str(tmp_path / "nonexistent"), state_dir=tmp_path)
    doc = json.loads(refused.stdout)
    assert refused.returncode == 2
    assert doc["status"] == "refused"


def test_diagnose_cli_clean_pass(tmp_path: Path) -> None:
    """Bundle sadio -> exit 0."""
    bundle = tmp_path / "ok"
    bundle.mkdir()
    (bundle / "case.yaml").write_text(
        "name: ok\n"
        "principal: {id: spn-1, type: service_principal}\n"
        "operation: read\n"
        "target: {kind: table, table: prod.s.t}\n"
        "compute: {type: classic_vnet}\n",
        encoding="utf-8")
    (bundle / "unity_catalog.json").write_text(json.dumps({
        "catalogs": {"prod": {"isolation_mode": "OPEN"}},
        "grants": [{"securable": s, "principal": "spn-1",
                    "privileges": ["ALL PRIVILEGES"]}
                   for s in ("prod", "prod.s", "prod.s.t")],
    }), encoding="utf-8")
    (bundle / "network.json").write_text(json.dumps({"default_action": "Allow"}),
                                        encoding="utf-8")
    (bundle / "entra.json").write_text(json.dumps(
        {"principals": {"spn-1": {"enabled": True}}}), encoding="utf-8")
    proc = _run("diagnose", "--bundle", str(bundle), state_dir=tmp_path)
    doc = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert doc["status"] == "pass"


def test_diagnose_access_mcp_tool(tmp_path: Path) -> None:
    """`sfa_diagnose_access` roda o mesmo pipeline via dispatch (offline, read-only)."""
    pytest.importorskip("mcp", reason="extra [mcp] nao instalado")

    from sparkforge_azure.mcp import access_tools  # noqa: F401 - registra a tool
    from sparkforge_azure.mcp.dispatch import call_tool

    result = call_tool("sfa_diagnose_access",
                       {"bundle": str(FIXTURES / "s01_uc_privilege_denied")})
    assert result.is_error is False
    doc = result.structured_content
    assert doc["failure_layer"] == "unity_catalog"
    assert doc["diagnosis"]["status"] == "denied"
    assert doc["_trust"]["taint"] in {"external", "suspicious"}
    # default-deny: sem cloud opt-in nada muda; tool é read_only
    assert access_tools._diagnose_access is not None
