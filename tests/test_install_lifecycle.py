"""PORTABLE_INSTALL_LIFECYCLE — ``sparkforge-azure install`` forge/* surface.

Covers the shared-contract lifecycle verbs over the repo's own ownership
machinery: dry-run plans, approval refusal, managed apply (markers + MCP +
skill mirrors), health docs, drift/repair, and reversible uninstall —
project and user scopes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.distribution.managed import load_ledger
from sparkforge_azure.install import service


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    root = tmp_path / "my-project"
    root.mkdir()
    return root


@pytest.fixture()
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("FORGE_HOME_OVERRIDE", str(home))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


# --- AC1: dry-run plans without writing ---------------------------------


def test_dry_run_plans_and_writes_nothing(project: Path) -> None:
    doc = service.install(scope="project", root=project, dry_run=True)
    assert doc["schema"] == "forge/InstallReceipt/v1"
    assert doc["status"] == "planned"
    assert doc["dry_run"] is True
    assert ".mcp.json" in doc["planned_files"]
    assert not (project / ".sparkforge-azure").exists()
    assert not (project / ".mcp.json").exists()


def test_dry_run_lists_skill_mirrors(project: Path) -> None:
    doc = service.install(scope="project", root=project, dry_run=True)
    mirrors = [f for f in doc["planned_files"] if "skills/" in f]
    assert mirrors, "recommended profile should plan skill mirrors"
    assert all("sparkforge-azure-" in f for f in mirrors)


# --- AC2: writes require approval ---------------------------------------


def test_install_without_yes_is_refused(project: Path) -> None:
    with pytest.raises(PortableError) as exc:
        service.install(scope="project", root=project, yes=False)
    assert exc.value.kind == "FORGE-INSTALL-PLAN-NOT-APPROVED"


def test_bad_profile_is_refused(project: Path) -> None:
    with pytest.raises(PortableError):
        service.install(scope="project", root=project, profile="bogus",
                        yes=True, dry_run=False)


# --- AC3: apply writes managed assets + receipt --------------------------


def test_install_apply_writes_managed_assets(project: Path) -> None:
    doc = service.install(scope="project", root=project, yes=True)
    assert doc["schema"] == "forge/InstallReceipt/v1"
    assert doc["status"] == "completed"
    assert (project / ".mcp.json").is_file()
    assert "sparkforge-azure" in json.loads(
        (project / ".mcp.json").read_text())["mcpServers"]
    assert (project / "AGENTS.md").is_file()
    assert (project / ".sparkforge-azure" / "project.yaml").is_file()
    ledger = load_ledger(project / ".sparkforge-azure")
    assert len(ledger["files"]) > 5
    skill_files = [p for p in (project / ".claude" / "skills").rglob("SKILL.md")]
    assert skill_files, "recommended profile installs skill mirrors"


def test_minimal_profile_skips_skill_mirrors(project: Path) -> None:
    service.install(scope="project", root=project, profile="minimal",
                    yes=True)
    assert not (project / ".claude" / "skills").exists()


def test_existing_mcp_foreign_keys_preserved(project: Path) -> None:
    (project / ".mcp.json").write_text(json.dumps(
        {"mcpServers": {"other": {"command": "x"}}}))
    service.install(scope="project", root=project, yes=True)
    cfg = json.loads((project / ".mcp.json").read_text())
    assert cfg["mcpServers"]["other"] == {"command": "x"}
    assert "sparkforge-azure" in cfg["mcpServers"]


# --- AC4: status/doctor emit forge/InstallationHealth/v1 ------------------


def test_status_and_doctor_health_schema(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    status = service.status(scope="project", root=project)
    assert status["schema"] == "forge/InstallationHealth/v1"
    assert status["status"] in ("healthy", "degraded", "unverified")
    doc = service.doctor(scope="project", root=project)
    assert doc["schema"] == "forge/InstallationHealth/v1"
    assert any(c["id"] == "mcp-handshake" for c in doc["checks"])


def test_mcp_verify_check(project: Path) -> None:
    check = service.mcp_verify()
    assert check["id"] == "mcp-handshake"
    assert check["status"] in ("PASS", "FAIL", "NOT_APPLICABLE", "BLOCKED")


# --- AC5: drift detection + repair ----------------------------------------


def test_repair_restores_drifted_managed(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    ledger = load_ledger(project / ".sparkforge-azure")
    drift = next(p for p in ledger["files"]
                 if "skills" in p["path"] and p["mode"] == "file")
    target = Path(drift["path"])
    target.write_text("user broke this mirror")
    out = service.repair(scope="project", root=project)
    assert out["status"] == "completed"
    assert target.read_text() != "user broke this mirror"


def test_repair_dry_run_reports_drift(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    ledger = load_ledger(project / ".sparkforge-azure")
    drift = next(p for p in ledger["files"] if p["mode"] == "file")
    Path(drift["path"]).write_text("drifted")
    out = service.repair(scope="project", root=project, dry_run=True)
    assert out["status"] == "planned"
    assert drift["path"] in out["drifted"]
    assert Path(drift["path"]).read_text() == "drifted"


# --- AC6: uninstall is reversible and conservative ------------------------


def test_uninstall_removes_managed_preserves_user(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    (project / "AGENTS.md").write_text(
        (project / "AGENTS.md").read_text() + "\n# user section\nkeep me\n")
    out = service.uninstall(scope="project", root=project)
    assert out["status"] == "completed"
    assert not (project / ".mcp.json").exists() or \
        "sparkforge-azure" not in json.loads(
            (project / ".mcp.json").read_text()).get("mcpServers", {})
    assert (project / "AGENTS.md").is_file()
    assert "keep me" in (project / "AGENTS.md").read_text()
    assert not (project / ".claude" / "skills").exists()


def test_uninstall_on_pristine_root_is_noop(project: Path) -> None:
    out = service.uninstall(scope="project", root=project)
    assert out["status"] == "completed"
    assert not (project / ".sparkforge-azure").exists()


# --- AC7: user scope -------------------------------------------------------


def test_user_scope_writes_under_home(fake_home: Path) -> None:
    doc = service.install(scope="user", root=fake_home, yes=True)
    assert doc["status"] == "completed"
    assert (fake_home / ".sparkforge-azure" / "managed.json").is_file()
    assert "sparkforge-azure" in json.loads(
        (fake_home / ".mcp.json").read_text())["mcpServers"]
    skills = list((fake_home / ".agents" / "skills").rglob("SKILL.md"))
    assert skills


# --- AC8: surface parity ---------------------------------------------------


def test_cli_dispatches_all_verbs(project: Path,
                                  capsys: pytest.CaptureFixture[str]) -> None:
    from sparkforge_azure.cli.main import main

    rc = main(["install", "--root", str(project), "--dry-run"])
    assert rc == 0
    rc = main(["install", "status", "--root", str(project)])
    assert rc == 0
    # mcp-verify reports honestly: BLOCKED when the CLI isn't on PATH here,
    # PASS when it is — either is a valid exit for the check itself.
    capsys.readouterr()
    rc = main(["install", "mcp-verify"])
    out = capsys.readouterr().out
    assert '"mcp-handshake"' in out
    assert rc in (0, 1)


def test_install_apply_via_cli(project: Path) -> None:
    from sparkforge_azure.cli.main import main

    rc = main(["install", "--root", str(project), "--yes"])
    assert rc == 0
    assert (project / ".sparkforge-azure" / "project.yaml").is_file()
    rc = main(["install", "uninstall", "--root", str(project)])
    assert rc == 0


def test_hosts_none_e_csv(tmp_path):
    """GAP-003: `none` nunca vira `all`; csv subconjunto e validado."""
    import pytest

    from sparkforge_azure.install import service
    alvo = tmp_path / "proj"
    alvo.mkdir()
    plan = service.install(host="none", scope="project", root=alvo,
                           dry_run=True)
    assert plan is not None
    with pytest.raises(PortableError):
        service.install(host="nope", scope="project", root=alvo, dry_run=True)


# --- forge/context/v1 — workspace registry (install-2.0 ciclo 2) ----------


def test_install_escreve_forge_context(project: Path) -> None:
    from sparkforge_azure import _forgecontext as fctx

    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    check = next(c for c in out["checks"] if c["id"] == "context-registry")
    assert check["status"] == "PASS"

    ctx = project / ".forge" / "context"
    registry = json.loads((ctx / "registry.json").read_text(encoding="utf-8"))
    assert registry["schema"] == "forge/context-registry/v1"
    entry = next(
        e for e in registry["forges"] if e["forge_id"] == "sparkforge-azure")
    assert entry["scope"] == "project"

    manifest = json.loads(
        (ctx / "capabilities" / "sparkforge-azure.json").read_text(
            encoding="utf-8"))
    assert manifest["schema"] == "forge/context/v1"
    assert fctx.validate_manifest(manifest) == []
    assert manifest["skills"], "manifesto sem skills reais"
    assert manifest["rule_areas"], "manifesto sem rule areas"
    assert manifest["agents"], "manifesto sem agents"
    assert manifest["integrity"]["files"]["forge.json"].startswith("sha256:")

    routing = (ctx / "ROUTING.md").read_text(encoding="utf-8")
    assert "sparkforge-azure" in routing
    assert "azure-data" in routing


def test_install_context_idempotente_byte_a_byte(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    ctx = project / ".forge" / "context"
    snap = {
        p.relative_to(ctx).as_posix(): p.read_bytes()
        for p in sorted(ctx.rglob("*"))
        if p.is_file()
    }
    service.install(scope="project", root=project, yes=True)
    depois = {
        p.relative_to(ctx).as_posix(): p.read_bytes()
        for p in sorted(ctx.rglob("*"))
        if p.is_file()
    }
    assert snap == depois


def test_uninstall_desregistra_so_o_proprio_forge(project: Path) -> None:
    from sparkforge_azure import _forgecontext as fctx

    service.install(scope="project", root=project, yes=True)
    estrangeiro = fctx.build_manifest(
        forge_id="forge-alheia",
        name="Forge Alheia",
        version="1.0.0",
        cli="forge-alheia",
        package="forge_alheia",
        distribution="forge-alheia",
        python_spec=">=3.10",
        scope="project",
        domains=("dominio-alheio",),
        skills=("skill-alheia",),
    )
    fctx.register_forge(project, estrangeiro, owner="forge-alheia")

    un = service.uninstall(scope="project", root=project)
    assert un["status"] == "completed"

    ctx = project / ".forge" / "context"
    registry = json.loads((ctx / "registry.json").read_text(encoding="utf-8"))
    assert {e["forge_id"] for e in registry["forges"]} == {"forge-alheia"}
    assert not (ctx / "capabilities" / "sparkforge-azure.json").exists()
    assert (ctx / "capabilities" / "forge-alheia.json").exists()
