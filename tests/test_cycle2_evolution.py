"""Evolucao pos-merge: paridade MCP, overhead por estagio, unresolved com
artefato esperado, e doctor do vertical de acesso."""
from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "access"


def test_mcp_output_schema_matches_run_case_report() -> None:
    """Toda chave top-level do report deve estar declarada no output schema.

    O schema e o contrato do cliente MCP -- campos emitidos mas nao declarados
    sao superficie invisivel para validacao downstream."""
    from sparkforge_azure.azure.pipeline import run_case
    from sparkforge_azure.mcp import access_tools

    report = run_case(FIXTURES / "s02_rbac_control_plane_only")
    declared = set(access_tools._OUTPUT_SCHEMA["properties"])
    emitted = {k for k in report if not k.startswith("_")}
    missing = emitted - declared
    assert not missing, f"report keys undeclared in MCP output schema: {missing}"


def test_overhead_reports_per_stage_ms() -> None:
    """overhead.stages torna o custo de cada estagio inspecionavel sem abrir
    o traces.db -- economia medida no report, nao so no ledger."""
    from sparkforge_azure.azure.pipeline import run_case

    report = run_case(FIXTURES / "s02_rbac_control_plane_only")
    stages = report["overhead"]["stages"]
    for name in ("load_bundle", "extract", "notebook_scan", "diagnose",
                 "rules", "graph", "evidence_trust"):
        assert name in stages, f"stage {name} missing from overhead.stages"
        assert isinstance(stages[name]["ms"], (int, float))
        assert stages[name]["ms"] >= 0


def test_unresolved_entries_name_expected_artifact() -> None:
    """Um layer UNKNOWN deve dizer qual artefato o alimentaria e se ele
    estava presente no bundle -- acao direta, nao adivinhacao."""
    from sparkforge_azure.azure.pipeline import run_case

    report = run_case(FIXTURES / "s10_missing_evidence")
    unresolved = report["unresolved"]
    assert unresolved, "s10 must produce unresolved layers"
    for entry in unresolved:
        assert "layer" in entry and "reason" in entry
        if "artifact" in entry:
            assert "artifact_present" in entry
            assert isinstance(entry["artifact_present"], bool)


def test_doctor_access_vertical_check() -> None:
    """Doctor cobre a integridade do vertical: catalogo SF-ACC carrega,
    ids unicos, fixtures presentes, fronteira de redacao importavel."""
    from sparkforge_azure import doctor

    result = doctor.run(areas=["access_vertical"])
    check = result["checks"][0]
    assert check["area"] == "access_vertical"
    assert check["status"] == "ok", check
    data = check["data"]
    # 001-004 live in the catalog; 010-013 are pipeline-emitted findings.
    assert data["rules"] >= 4
    assert data["fixtures"] == 10
    assert data["duplicate_rule_ids"] == []
    assert data["redact_boundary"] == "available"


def test_state_dir_env_override(tmp_path, monkeypatch) -> None:
    """SPARKFORGE_AZURE_STATE_DIR redireciona o traces.db -- proofs e scripts
    com cwd=repo nao sujam o worktree."""
    from sparkforge_azure.observability.store import SQLiteTraceStore

    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    store = SQLiteTraceStore()
    assert store.db_path == tmp_path / "state" / "traces.db"


def test_doctor_access_vertical_detects_duplicate_ids(monkeypatch) -> None:
    """Id duplicado no catalogo e defeito estrutural -- o check reprova."""
    from sparkforge_azure import doctor

    real = doctor.load_access_rules
    def dup():
        rules = real()
        return [*rules, dict(rules[0])]
    monkeypatch.setattr(doctor, "load_access_rules", dup)
    result = doctor.run(areas=["access_vertical"])
    assert result["checks"][0]["status"] == "fail"
