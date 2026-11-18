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

from sparkforge_azure import _installkit as kit
from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.distribution.managed import load_ledger
from sparkforge_azure.install import service


@pytest.fixture(autouse=True)
def _forge_home_isolado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isola `~/.forge/` — install-2.1 re-asserta o manifesto de conta em
    `~/.forge/installations/`; sem isto a suite escreveria no HOME real."""
    casa = tmp_path / "forge-home"
    casa.mkdir()
    monkeypatch.setenv("FORGE_HOME_OVERRIDE", str(casa))


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
    mirrors = [
        f for f in doc["planned_files"]
        if "skills/" in f and "_shared/" not in f
    ]
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


# --- install-2.1: ownership — foreign files preserved, never adopted -----


def test_install_preserva_arquivo_estrangeiro_no_mirror(project: Path) -> None:
    """Um arquivo do usuario num caminho de mirror NAO e clobbered nem
    adotado: fica intacto, fora do ledger, e o recibo recusa honestamente."""
    plan = service.install(scope="project", root=project, dry_run=True)
    alvo_rel = next(f for f in plan["planned_files"]
                    if f.startswith(".agents/skills/")
                    and f.endswith("SKILL.md"))
    alvo = project / alvo_rel
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("conteudo do usuario", encoding="utf-8")

    out = service.install(scope="project", root=project, yes=True)
    assert alvo.read_text(encoding="utf-8") == "conteudo do usuario"
    assert out["status"] == "failed"
    check = next(c for c in out["checks"] if c["id"] == "foreign-files")
    assert check["status"] == "FAIL"
    assert str(alvo) in (out.get("preserved_foreign") or [])

    from sparkforge_azure.distribution.managed import load_ledger

    ledger = load_ledger(project / ".sparkforge-azure")
    assert all(f["path"] != alvo.as_posix() for f in ledger["files"])


def test_install_preserva_stub_estrangeiro(project: Path) -> None:
    """O mesmo guarda-chuva cobre os ponteiros de knowledge/rules/evals:
    stub estrangeiro sob `knowledge/sparkforge-azure/` e preservado e
    reportado."""
    foreign = (project / "knowledge" / "sparkforge-azure"
               / "spark" / "README.md")
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("doc do usuario", encoding="utf-8")
    out = service.install(scope="project", root=project, yes=True)
    assert foreign.read_text(encoding="utf-8") == "doc do usuario"
    assert out["status"] == "failed"
    assert str(foreign) in (out.get("preserved_foreign") or [])


def test_install_preserva_agent_mirror_estrangeiro(project: Path) -> None:
    """Profile full: `.agents/agents/sparkforge-azure-*.md` estrangeiro e
    preservado e recusado — `with_mirrors` tambem passa pelo guard."""
    alvo = project / ".agents" / "agents" / "sparkforge-azure-coordinator.md"
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("meu agent", encoding="utf-8")
    out = service.install(scope="project", root=project, profile="full",
                          yes=True)
    assert alvo.read_text(encoding="utf-8") == "meu agent"
    assert out["status"] == "failed"
    assert str(alvo) in (out.get("preserved_foreign") or [])


def test_install_arquivo_identico_preexistente_nao_adota(project: Path) -> None:
    """Byte-identical pre-existing file at a managed path: the mirror is
    effectively installed, but the file is never ledgered — `uninstall`
    must not delete a file we never wrote."""
    from sparkforge_azure.distribution.managed import load_ledger
    from sparkforge_azure.install.service import _skill_sources
    from sparkforge_azure.skills.mirrors import (
        mirror_name,
        namespace_knowledge_refs,
        render_mirror,
    )

    skill_name, text = next(iter(_skill_sources()))
    alvo = (project / ".agents" / "skills" / mirror_name(skill_name)
            / "SKILL.md")
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(
        namespace_knowledge_refs(render_mirror(text, skill_name)),
        encoding="utf-8")

    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    ledger = load_ledger(project / ".sparkforge-azure")
    assert all(f["path"] != alvo.as_posix() for f in ledger["files"])

    service.uninstall(scope="project", root=project)
    assert alvo.is_file()


# --- install-2.1: knowledge namespace + migracao honesta -----------------


def test_install_namespaceia_ponteiros_knowledge(project: Path) -> None:
    """Stubs land em `knowledge/sparkforge-azure/<rel>` — nada direto na
    raiz compartilhada `knowledge/`; o indice e o espelho apontam para o
    subdir proprio (install-2.1)."""
    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    kns = project / "knowledge" / "sparkforge-azure"
    assert kns.is_dir()
    assert (kns / "README.md").is_file()
    diretos = [
        p.name for p in (project / "knowledge").iterdir()
        if p.name != "sparkforge-azure"
    ]
    assert diretos == []
    espelhos = list((project / ".claude" / "skills").rglob("SKILL.md"))
    assert espelhos
    corpo = "\n".join(e.read_text(encoding="utf-8") for e in espelhos)
    assert "knowledge/sparkforge-azure/" in corpo


def test_install_namespace_rewrite_e_idempotente(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    corpo = "\n".join(
        e.read_text(encoding="utf-8")
        for e in (project / ".claude" / "skills").rglob("*.md")
    )
    assert "sparkforge-azure/sparkforge-azure" not in corpo


def test_install_migra_stub_legado_proprio(project: Path) -> None:
    """Stub legado `knowledge/<rel>` ledgered e integro = nosso: some e o
    equivalente namespaced assume o lugar (moved, nao duplicado)."""
    from sparkforge_azure.distribution.managed import (
        load_ledger,
        record_file,
        save_ledger,
    )

    service.install(scope="project", root=project, yes=True)
    legacy = project / "knowledge" / "spark" / "README.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("ponteiro antigo", encoding="utf-8")
    state = project / ".sparkforge-azure"
    ledger = record_file(
        load_ledger(state), legacy, kind="knowledge_pointer")
    save_ledger(state, ledger)

    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    assert not legacy.exists()
    assert out["distribution"].get("knowledge_migrated")


def test_install_preserva_stub_legado_editado(project: Path) -> None:
    """Stub legado ledgered mas EDITADO pelo usuario: arquivo preservado,
    claim removido do ledger — detach semantics, nunca clobber."""
    from sparkforge_azure.distribution.managed import (
        load_ledger,
        record_file,
        save_ledger,
    )

    service.install(scope="project", root=project, yes=True)
    legacy = project / "knowledge" / "spark" / "README.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("ponteiro antigo", encoding="utf-8")
    state = project / ".sparkforge-azure"
    ledger = record_file(
        load_ledger(state), legacy, kind="knowledge_pointer")
    save_ledger(state, ledger)
    legacy.write_text("usuario editou", encoding="utf-8")

    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    assert legacy.read_text(encoding="utf-8") == "usuario editou"
    assert out["distribution"].get("knowledge_detached")
    ledger = load_ledger(state)
    assert all(f["path"] != legacy.as_posix() for f in ledger["files"])


def test_install_preserva_stub_legado_estrangeiro(project: Path) -> None:
    """Stub legado NAO-ledgered em `knowledge/<rel>`: nunca foi nosso —
    fica intacto e fora do ledger."""
    legacy = project / "knowledge" / "spark" / "README.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("doc do usuario", encoding="utf-8")
    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    assert legacy.read_text(encoding="utf-8") == "doc do usuario"


# --- install-2.1: workspace scope nao cunha identidade de projeto --------


def test_install_workspace_sem_project_yaml(tmp_path: Path) -> None:
    """`install --scope workspace` escreve estado e assets sem mintar
    `.sparkforge-azure/project.yaml` — a raiz de workspace nao se finge
    de projeto, entao member installs nao tropecam em
    `path_outside_root` (install-2.1)."""
    ws = tmp_path / "ws"
    ws.mkdir()
    out = service.install(scope="workspace", root=ws, yes=True)
    assert out["status"] == "completed"
    assert not (ws / ".sparkforge-azure" / "project.yaml").exists()

    member = ws / "member-a"
    member.mkdir()
    out2 = service.install(scope="project", root=member, yes=True)
    assert out2["status"] == "completed"
    assert (member / ".sparkforge-azure" / "project.yaml").is_file()


def test_discover_projects_membro_sem_git(tmp_path: Path) -> None:
    """installkit 1.0.6: membros de workspace sao descobertos por
    `MEMBER_MARKERS` — `.git` OU manifesto de projeto; um dir gitless
    com `pyproject.toml` e membro de primeira classe."""
    ws = tmp_path / "ws"
    member = ws / "member-gitless"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text(
        "[project]\nname = 'x'\n", encoding="utf-8")
    found = kit.discover_projects(ws)
    assert member.resolve() in found


# --- install-2.1: --host / --components / --gateway-profile --------------


def test_install_host_narrowing(project: Path) -> None:
    out = service.install(scope="project", root=project, host="codex",
                          yes=True)
    assert out["status"] == "completed"
    assert (project / ".agents" / "skills").is_dir()
    assert not (project / ".claude").exists()
    assert not (project / ".github").exists()


def test_install_host_csv(project: Path) -> None:
    out = service.install(scope="project", root=project,
                          host="claude,devin", yes=True)
    assert out["status"] == "completed"
    assert (project / ".claude" / "skills").is_dir()
    assert (project / ".agents" / "skills").is_dir()
    assert not (project / ".github").exists()  # .github/skills e copilot-only


def test_install_host_none_sem_writes_de_host(project: Path) -> None:
    out = service.install(scope="project", root=project, host="none",
                          yes=True)
    assert out["status"] == "completed"
    assert not (project / ".mcp.json").exists()
    assert not (project / ".agents").exists()
    assert not (project / ".claude").exists()


def test_install_host_invalido_recusa_nomeada(project: Path) -> None:
    from sparkforge_azure.distribution.errors import PortableError

    with pytest.raises(PortableError) as exc:
        service.install(scope="project", root=project, host="emacs",
                        yes=True)
    assert "HOST" in str(exc.value.kind)


def test_install_host_scope_espelhos_de_agent(project: Path) -> None:
    """profile=full + --host claude: mirrors de agent so em
    `.claude/agents/custom` — `.agents/agents` e de devin/codex/copilot."""
    out = service.install(scope="project", root=project, host="claude",
                          profile="full", yes=True)
    assert out["status"] == "completed"
    assert (project / ".claude" / "agents" / "custom").is_dir()
    assert not (project / ".agents" / "agents").exists()


def test_install_components_narrowing(project: Path) -> None:
    """`--components skills` instala so a camada de skills: sem
    `.mcp.json`, sem ponteiros de knowledge, sem agent mirrors."""
    out = service.install(scope="project", root=project,
                          components=("skills",), yes=True)
    assert out["status"] == "completed"
    assert (project / ".claude" / "skills").is_dir()
    assert not (project / ".mcp.json").exists()
    assert not (project / "knowledge").exists()


def test_install_components_skills_knowledge(project: Path) -> None:
    out = service.install(scope="project", root=project,
                          components=("skills", "knowledge"), yes=True)
    assert out["status"] == "completed"
    assert (project / "knowledge" / "sparkforge-azure").is_dir()
    assert not (project / ".mcp.json").exists()


def test_install_gateway_profile_compact_argv(project: Path) -> None:
    """economy/balanced → `mcp serve --compact`; deep → argv completo."""
    import json as _json

    for gw in ("economy", "balanced"):
        p = project / f"gw-{gw}"
        p.mkdir()
        service.install(scope="project", root=p, gateway_profile=gw,
                        yes=True)
        mcp = _json.loads((p / ".mcp.json").read_text(encoding="utf-8"))
        assert mcp["mcpServers"]["sparkforge-azure"]["args"] == [
            "mcp", "serve", "--compact"]

    p = project / "gw-deep"
    p.mkdir()
    service.install(scope="project", root=p, gateway_profile="deep",
                    yes=True)
    mcp = _json.loads((p / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["sparkforge-azure"]["args"] == ["mcp", "serve"]


def test_install_execution_profile_persistido(project: Path) -> None:
    service.install(scope="project", root=project,
                    gateway_profile="deep", yes=True)
    import json as _json

    opts = _json.loads(
        (project / ".sparkforge-azure" / "components.json").read_text(
            encoding="utf-8"))
    assert opts["execution_profile"] == "deep"


# --- install-2.1: mirror asset dirs completos ----------------------------


def test_install_envia_dirs_de_assets(project: Path) -> None:
    """sdd-* skills citam `references/` e `scripts/` — o mirror instala o
    diretorio completo, nao so SKILL.md; `_shared/` chega sem prefixo."""
    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    mdir = project / ".claude" / "skills" / "sparkforge-azure-sdd-build"
    assert (mdir / "SKILL.md").is_file()
    assert (mdir / "references").is_dir()
    assert (mdir / "references" / "README.md").is_file()
    assert (mdir / "scripts" / "validate_evidence.py").is_file()
    # `../_shared/` relativo ao mirror resolve contra `<mroot>/_shared/`
    assert (project / ".claude" / "skills" / "_shared").is_dir()


def test_install_asset_refs_nao_ficam_mortos(project: Path) -> None:
    """Todo `references/`/`scripts/` citado num SKILL.md mirrorado
    existe no mirror — a checagem de dead-link do install-2.1."""
    service.install(scope="project", root=project, yes=True)
    mortos: list[str] = []
    for skill_name, sdir in service._skill_source_dirs():
        mdir = (project / ".claude" / "skills"
                / f"sparkforge-azure-{skill_name}")
        if not mdir.is_dir():
            continue
        for sub in ("references", "scripts"):
            base = sdir / sub
            if not base.is_dir():
                continue
            for f in base.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(sdir)
                    if not (mdir / rel).is_file():
                        mortos.append(f"{skill_name}/{rel}")
    assert mortos == []


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
        e for e in registry["forges"] if e["forge_id"] == "spark-forge-azure")
    assert entry["scope"] == "project"

    manifest = json.loads(
        (ctx / "capabilities" / "spark-forge-azure.json").read_text(
            encoding="utf-8"))
    assert manifest["schema"] == "forge/context/v1"
    assert fctx.validate_manifest(manifest) == []
    assert manifest["skills"], "manifesto sem skills reais"
    assert manifest["rule_areas"], "manifesto sem rule areas"
    assert manifest["agents"], "manifesto sem agents"
    assert manifest["integrity"]["files"]["forge.json"].startswith("sha256:")

    routing = (ctx / "ROUTING.md").read_text(encoding="utf-8")
    assert "spark-forge-azure" in routing
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
    assert not (ctx / "capabilities" / "spark-forge-azure.json").exists()
    assert (ctx / "capabilities" / "forge-alheia.json").exists()


# --- consumer docs — install-2.0 ciclo 3 (lf-0036) ------------------------


def test_install_escreve_consumer_docs(project: Path) -> None:
    out = service.install(scope="project", root=project, yes=True)
    assert out["status"] == "completed"
    check = next(c for c in out["checks"] if c["id"] == "consumer-docs")
    assert check["status"] == "PASS"

    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    claude = (project / "CLAUDE.md").read_text(encoding="utf-8")
    proto = (project / "AGENT_PROTOCOL.md").read_text(encoding="utf-8")
    assert "<!-- forge:ecosystem:begin -->" in agents
    assert "<!-- forge:spark-forge-azure:begin -->" in agents
    assert "<!-- sparkforge-azure:begin -->" not in agents  # legado convergiu
    assert "@AGENTS.md" in claude
    for sec in (
        "1. Discovery", "2. Classification", "3. Routing",
        "4. Context Retrieval", "5. Planning", "6. Execution",
        "7. Evaluation", "8. Verification", "9. Reporting",
    ):
        assert sec in proto
    assert proto.startswith("<!-- forge:agent-protocol:v1 -->")


def test_install_converge_marker_legado(project: Path) -> None:
    """Um AGENTS.md com o marker `sparkforge-azure` antigo converge para
    `forge:*` sem duplicar blocos nem perder conteudo do usuario."""
    (project / "AGENTS.md").write_text(
        "# minhas regras\n\n"
        "<!-- sparkforge-azure:begin -->\nold managed\n"
        "<!-- sparkforge-azure:end -->\n",
        encoding="utf-8")
    service.install(scope="project", root=project, yes=True)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.startswith("# minhas regras\n")
    assert "old managed" not in agents
    assert "<!-- sparkforge-azure:begin -->" not in agents
    assert "<!-- forge:spark-forge-azure:begin -->" in agents


def test_install_docs_idempotente(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    nomes = ("AGENTS.md", "CLAUDE.md", "AGENT_PROTOCOL.md")
    snap = {n: (project / n).read_bytes() for n in nomes}
    service.install(scope="project", root=project, yes=True)
    assert {n: (project / n).read_bytes() for n in nomes} == snap


def test_uninstall_seletivo_entre_forges(project: Path) -> None:
    from sparkforge_azure import _forgecontext as fctx

    service.install(scope="project", root=project, yes=True)
    alheio = fctx.build_manifest(
        forge_id="forge-alheia", name="Forge Alheia", version="1.0.0",
        cli="forge-alheia", package="forge_alheia", distribution="forge-alheia",
        python_spec=">=3.10", scope="project", domains=("dominio-alheio",),
        skills=("skill-alheia",),
    )
    fctx.register_forge(project, alheio, owner="forge-alheia")
    fctx.install_docs(project, alheio, owner="forge-alheia")

    service.uninstall(scope="project", root=project)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "forge:spark-forge-azure" not in agents
    assert "forge:forge-alheia:begin" in agents
    proto = (project / "AGENT_PROTOCOL.md").read_text(encoding="utf-8")
    assert "forge:forge-alheia" in proto and "spark-forge-azure" not in proto


def test_install_recusa_marcador_ambiguo(project: Path) -> None:
    (project / "AGENTS.md").write_text(
        "# x\n<!-- forge:sparkforge-azure:begin -->\na\n"
        "<!-- forge:sparkforge-azure:begin -->\nb\n"
        "<!-- forge:sparkforge-azure:end -->\n",
        encoding="utf-8")
    out = service.install(scope="project", root=project, yes=True)
    check = next(
        (c for c in out["checks"] if c["id"] == "context-registry"), None)
    assert check is not None and check["status"] == "BLOCKED"
    assert "FORGE-CONTEXT-CONFLICT" in check["detail"]


def test_repair_reconstroi_bloco_danificado(project: Path) -> None:
    service.install(scope="project", root=project, yes=True)
    alvo = project / "AGENTS.md"
    alvo.write_text(
        alvo.read_text(encoding="utf-8").replace(
            "Spark Forge Azure", "ADULTERADO"),
        encoding="utf-8")
    out = service.repair(scope="project", root=project)
    check = next(
        (c for c in out["checks"] if c["id"] == "consumer-docs"), None)
    assert check is not None and check["status"] == "PASS"
    assert "ADULTERADO" not in alvo.read_text(encoding="utf-8")
