"""``forge/*``-contract install lifecycle for Spark Forge Azure.

Wraps the repository's own ownership machinery (``distribution.service``,
``distribution.managed``, ``skills.mirrors``) and the vendored shared
installkit (scope resolution, locks, MCP handshake, family registry) so the
CLI surface matches every sibling Forge — without duplicating the ledger.

Profiles: ``minimal`` = markers + MCP key; ``recommended`` = + skill
mirrors; ``full`` = + agent mirrors. Scopes: ``project`` / ``workspace``
(delegate to ``distribution.initialize``), ``user`` (host assets under
``~`` only, no project identity).
"""

from __future__ import annotations

import json
import subprocess  # noqa: S404 — bounded argv to the installed venv pip
import sys
from pathlib import Path
from typing import Any

from sparkforge_azure import __version__, discovery_ops
from sparkforge_azure import _forgecontext as fctx
from sparkforge_azure import _installkit as kit

FORGE_ID = "sparkforge-azure"
PROFILES: tuple[str, ...] = ("minimal", "recommended", "full")
GATEWAY_PROFILES: tuple[str, ...] = ("economy", "balanced", "deep")
SCOPES: tuple[str, ...] = ("project", "workspace", "user")
HOSTS: tuple[str, ...] = ("claude", "devin", "codex", "copilot")

# Which host-owned dirs receive skill mirrors per host. `.agents/skills`
# is shared by Devin/Codex/Copilot (deduplicated at write time).
_SKILL_ROOTS: dict[str, tuple[str, ...]] = {
    "claude": (".claude/skills",),
    "devin": (".devin/skills", ".agents/skills"),
    "codex": (".agents/skills",),
    "copilot": (".agents/skills", ".github/skills"),
}


def _spec() -> kit.ForgeSpec:
    return kit.ForgeSpec(
        forge_id=FORGE_ID,
        package="sparkforge_azure",
        distribution="sparkforge-azure",
        cli_name="sparkforge-azure",
        python_spec=">=3.10",
        state_dir=".sparkforge-azure",
        mcp_command=("sparkforge-azure", "mcp", "serve"),
        mcp_server_name="sparkforge-azure",
        mcp_verify_tool="sfa_version",
        version_cmd=("--version",),
        render_assets=None,
        marker_files=("AGENTS.md", "CLAUDE.md"),
        marker_body="",
        user_state_dir="~/.sparkforge-azure",
    )


def _resolve(scope: str, root: Path | None) -> Path:
    return kit.resolve_scope(
        _spec(), scope, Path.cwd(), root.resolve() if root else None)


def _state_dir(scope: str, target: Path) -> Path:
    if scope == "user":
        return Path.home() / ".sparkforge-azure"
    return target / ".sparkforge-azure"


def _skill_sources() -> list[tuple[str, str]]:
    """``(skill_name, SKILL.md text)`` from the canonical ``skills/`` group —
    source checkout or the ``_data/skills`` payload inside the wheel."""
    from sparkforge_azure.distribution.assets import _group_dir

    root = _group_dir("skills")
    out: list[tuple[str, str]] = []
    if not root.is_dir():
        return out
    for item in sorted(root.iterdir(), key=lambda e: e.name):
        skill_md = item / "SKILL.md"
        if item.is_dir() and skill_md.is_file():
            out.append((item.name, skill_md.read_text(encoding="utf-8")))
    return out


def _skill_roots(hosts: tuple[str, ...]) -> list[str]:
    seen: list[str] = []
    for h in hosts:
        for r in _SKILL_ROOTS.get(h, ()):
            if r not in seen:
                seen.append(r)
    return seen


_KNOWLEDGE_REF_RE = None  # compiled lazily in _referenced_knowledge_paths


def _referenced_knowledge_paths(text: str) -> set[str]:
    """Os caminhos `knowledge/<rel>` citados num SKILL.md — por link markdown
    resolvido contra `skills/<name>` e por mencao textual `` `knowledge/x` ``.
    Serve para emitir ponteiros exatamente nos docs referenciados (lf-0037)."""
    global _KNOWLEDGE_REF_RE
    if _KNOWLEDGE_REF_RE is None:
        import re

        _KNOWLEDGE_REF_RE = re.compile(
            r"knowledge/[A-Za-z0-9_./-]+")
    refs: set[str] = set()
    for match in _KNOWLEDGE_REF_RE.finditer(text):
        rel = match.group(0)[len("knowledge/"):].rstrip(".,);]")
        if rel:
            refs.add(rel)
    return refs


_KNOWLEDGE_STUB = """\
# Ponteiro de knowledge — sparkforge-azure

Este arquivo e um PONTEIRO gerado na instalacao: os links `knowledge/<rel>`
dos mirrors (.claude/skills, .agents/skills, ...) resolvem aqui, mas o
CONTEUDO real mora no pacote `sparkforge-azure` instalado — fora de qualquer
checkout, e propositalmente nao copiado para o workspace.

Recupere o documento real com os verbos nativos (offline, deterministicos):

    sparkforge-azure knowledge get {rel}
    sparkforge-azure knowledge search "<termo>" --domain {dominio}
    sparkforge-azure context pack --domain {dominio}

`knowledge get` devolve o caminho absoluto e o sha256 do documento dentro do
pacote (ou de `SPARKFORGE_AZURE_KNOWLEDGE`, quando apontada). Para ver TODOS
os documentos disponiveis: `sparkforge-azure knowledge list`.
"""


def _knowledge_stub(rel: str) -> str:
    partes = rel.split("/")
    dominio = partes[0] if len(partes) > 1 else Path(rel).stem
    return _KNOWLEDGE_STUB.format(rel=rel, dominio=dominio)


def _install_skill_mirrors(
    root: Path, ledger: dict[str, Any], hosts: tuple[str, ...],
) -> tuple[dict[str, Any], list[str]]:
    """Write ``sparkforge-azure-<name>/SKILL.md`` mirrors into the selected
    host roots, ledgered like every other managed asset. Tambem emite os
    ponteiros `knowledge/<rel>` referenciados pelas skills (lf-0037): no
    wheel o knowledge mora no pacote, entao o stub aponta para os verbos
    nativos em vez de deixar o link morto."""
    from sparkforge_azure.distribution.managed import record_file
    from sparkforge_azure.durable import write_atomic
    from sparkforge_azure.skills.mirrors import mirror_name, render_mirror

    written: list[str] = []
    knowledge_refs: set[str] = set()
    for skill_name, text in _skill_sources():
        knowledge_refs |= _referenced_knowledge_paths(text)
        rendered = render_mirror(text, skill_name)
        for mroot in _skill_roots(hosts):
            target = root / mroot / mirror_name(skill_name) / "SKILL.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            write_atomic(target, rendered)
            ledger = record_file(
                ledger, target, kind="skill_mirror", mode="file",
                host=mroot.split("/")[0].lstrip("."),
            )
            written.append(str(target))
    for rel in sorted(knowledge_refs):
        # Ref de diretorio (`knowledge/spark/`) vira stub `<dir>/README.md`;
        # ref de arquivo vira stub no proprio caminho.
        stub_rel = rel if Path(rel).suffix else f"{rel}/README.md"
        stub = root / "knowledge" / stub_rel
        stub.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(stub, _knowledge_stub(rel))
        ledger = record_file(
            ledger, stub, kind="knowledge_pointer", mode="file",
        )
        written.append(str(stub))
    return ledger, written


def _mcp_config(root: Path, ledger: dict[str, Any]) -> tuple[dict[str, Any], str]:
    from sparkforge_azure.distribution.hosts import MCP_SERVER_NAME, mcp_entry
    from sparkforge_azure.distribution.managed import apply_json_key

    ledger, outcome = apply_json_key(
        root / ".mcp.json", f"mcpServers.{MCP_SERVER_NAME}", mcp_entry(),
        ledger=ledger, kind="mcp_config",
    )
    return ledger, outcome


def _planned_files(target: Path, scope: str, hosts: tuple[str, ...],
                   profile: str) -> list[str]:
    from sparkforge_azure.skills.mirrors import mirror_name

    out = [".mcp.json", "AGENTS.md"]
    if scope != "user":
        # install_docs sempre escreve CLAUDE.md + AGENT_PROTOCOL.md (lf-0036)
        out += [".sparkforge-azure/project.yaml", "CLAUDE.md",
                "AGENT_PROTOCOL.md"]
    elif "claude" in hosts or (target / "CLAUDE.md").exists():
        out.append("CLAUDE.md")
    if profile in ("recommended", "full"):
        for skill_name, _ in _skill_sources():
            for mroot in _skill_roots(hosts):
                out.append(f"{mroot}/{mirror_name(skill_name)}/SKILL.md")
    if profile == "full":
        from sparkforge_azure.agentmanifest.mirrors import (
            AGENT_MIRROR_ROOTS,
        )
        from sparkforge_azure.agentmanifest.mirrors import (
            mirror_name as agent_mirror_name,
        )
        from sparkforge_azure.distribution.hostfiles import _agent_sources
        for agent_id, _src in _agent_sources():
            for mroot in AGENT_MIRROR_ROOTS:
                out.append(f"{mroot}/{agent_mirror_name(agent_id)}.md")
    return sorted(dict.fromkeys(out))


def _receipt(operation: str, scope: str, target: Path, *,
             status: str, checks: list[dict[str, Any]],
             managed_files: list[str] | None = None,
             extra: dict[str, Any] | None = None) -> dict[str, Any]:
    doc = {
        "schema": kit.SCHEMA_RECEIPT, "forge_id": FORGE_ID,
        "operation": operation, "scope": scope,
        "target_root": str(target), "managed_files": managed_files or [],
        "checks": checks,
        "verification": {"status": "PASS" if all(
            c["status"] in ("PASS", "NOT_APPLICABLE", "UNVERIFIED")
            for c in checks) else "FAIL"},
        "status": status, "created_at": kit._utc_now(),
        "created_by": f"sparkforge-azure/{__version__}",
    }
    if extra:
        doc.update(extra)
    return doc


def install(*, scope: str = "project", root: Path | None = None,
            host: str = "all", profile: str = "recommended",
            yes: bool = False, dry_run: bool = False,
            components: tuple[str, ...] | None = None,
            gateway_profile: str = "balanced") -> dict[str, Any]:
    """``sparkforge-azure install`` — governed apply over ``initialize``."""
    from sparkforge_azure.distribution import service as dist
    from sparkforge_azure.distribution.errors import PortableError

    if profile not in PROFILES:
        raise PortableError(
            kit.E_PROFILE, f"profile {profile!r}; expected {PROFILES}")
    if gateway_profile not in GATEWAY_PROFILES:
        raise PortableError(
            kit.E_PROFILE,
            f"gateway_profile {gateway_profile!r}; expected {GATEWAY_PROFILES}",
        )
    if host == "all":
        hosts = list(HOSTS)
    elif not host or host == "none":
        hosts = []  # opt-out explícito — zero hosts nunca vira "all" (GAP-003)
    else:
        nomes = [h.strip() for h in host.split(",") if h.strip()]
        desconhecidos = [h for h in nomes if h not in HOSTS]
        if desconhecidos:
            raise PortableError(
                kit.E_HOST, f"host {desconhecidos[0]!r}; expected {HOSTS} + all,none")
        hosts = list(dict.fromkeys(nomes))
    target = _resolve(scope, root)
    state = _state_dir(scope, target)
    opts = kit.component_options("recommended", components)
    opts["execution_profile"] = gateway_profile

    if dry_run:
        return _receipt(
            "install", scope, target, status="planned",
            checks=[{"id": "plan", "status": "UNVERIFIED",
                     "detail": "dry-run — nothing written"}],
            managed_files=[],
            extra={"dry_run": True,
                   "components": opts or None,
                   "gateway_profile": gateway_profile,
                   "planned_files": _planned_files(target, scope, hosts,
                                                   profile)})
    if not yes:
        raise PortableError(
            kit.E_NOTAPPROVED,
            "install requires --yes or --dry-run; the plan is the contract")

    with kit.acquire_lock(state):
        if scope == "user":
            doc = _install_user(target, hosts, profile)
        else:
            # include_markers=False: os consumer docs (blocos `forge:*` +
            # AGENT_PROTOCOL.md consolidado) sao escritos pela camada
            # forge_context em `_register_context`, nao pelo ledger de
            # markers legado (lf-0036).
            doc = dist.initialize(
                target, with_mirrors=(profile == "full"), include_markers=False
            )
            _drop_stale_doc_entries(state, target)
            if profile in ("recommended", "full"):
                from sparkforge_azure.distribution.managed import (
                    load_ledger,
                    save_ledger,
                )
                ledger = load_ledger(state)
                ledger, written = _install_skill_mirrors(
                    target, ledger, hosts)
                save_ledger(state, ledger)
                doc["skill_mirrors"] = written
                doc["managed_files"] = [f["path"] for f in ledger["files"]]
        # `initialize` may report a refusal doc instead of raising.
        ok = doc.get("status") == "ok"
    if opts:
        state.mkdir(parents=True, exist_ok=True)
        (state / "components.json").write_text(
            json.dumps(opts, indent=2), encoding="utf-8")
    receipt = _receipt(
        "install", scope, target,
        status="completed" if ok else "failed",
        checks=[{"id": "apply", "status": "PASS" if ok else "FAIL",
                 "detail": f"{len(doc.get('managed_files', []))} managed files"}],
        managed_files=doc.get("managed_files", []),
        extra={"components": opts or None,
               "gateway_profile": gateway_profile,
               "distribution": {k: v for k, v in doc.items()
                                if k not in ("managed_files",)}})
    if ok:
        _register_context(
            target, receipt, scope=scope, profile=profile,
            hosts=hosts, components=opts or None,
        )
    return receipt


def _install_user(home: Path, hosts: tuple[str, ...],
                  profile: str) -> dict[str, Any]:
    """User scope: host assets only — no project identity (that's per-repo)."""
    from sparkforge_azure.distribution.hostfiles import install_host_assets
    from sparkforge_azure.distribution.hosts import detect_hosts
    from sparkforge_azure.distribution.managed import load_ledger, save_ledger

    state = home / ".sparkforge-azure"
    ledger = load_ledger(state)
    ledger, outcome = _mcp_config(home, ledger)
    detected = tuple(h["name"] for h in detect_hosts()
                     if h["status"] == "available")
    ledger, report = install_host_assets(
        home, ledger, hosts=detected,
        with_mirrors=(profile == "full"))
    written: list[str] = []
    if profile in ("recommended", "full"):
        ledger, written = _install_skill_mirrors(home, ledger, hosts)
    save_ledger(state, ledger)
    return {"status": "ok", "managed_files": [f["path"] for f in ledger["files"]],
            "host_files": report, "skill_mirrors": written,
            "mcp": outcome}


def status(*, scope: str = "project", root: Path | None = None) -> dict[str, Any]:
    from sparkforge_azure.distribution import service as dist

    target = _resolve(scope, root)
    doc = dist.status(target)
    level = doc.get("status", "uninitialized")
    healthy = level == "initialized"
    drifted = level in ("drifted", "partial", "broken")
    return {
        "schema": kit.SCHEMA_HEALTH, "forge_id": FORGE_ID,
        "status": ("healthy" if healthy else
                   ("degraded" if drifted else "unverified")),
        "target_root": str(target),
        "checks": [{"id": "distribution.status",
                    "status": "PASS" if healthy else "FAIL",
                    "detail": str(level)}],
        "distribution": doc,
        "checked_at": kit._utc_now(),
        "repair_hint": ("sparkforge-azure install repair" if drifted
                        else doc.get("unlock")),
    }


def doctor(*, scope: str = "project", root: Path | None = None) -> dict[str, Any]:
    from sparkforge_azure.distribution import service as dist

    target = _resolve(scope, root)
    doc = dist.doctor(target)
    checks = [{"id": f"dist:{c.get('area', '?')}",
               "status": "PASS" if c.get("status") == "ok" else "FAIL",
               "detail": str(c.get("detail", ""))}
              for c in doc.get("checks", [])]
    if not checks:
        checks = [{"id": "doctor",
                   "status": "UNVERIFIED",
                   "detail": "no checks reported"}]
    checks.append(kit.mcp_verify(_spec()))
    failed = any(c["status"] == "FAIL" for c in checks)
    return {
        "schema": kit.SCHEMA_HEALTH, "forge_id": FORGE_ID,
        "status": "degraded" if failed else "healthy",
        "target_root": str(target), "checks": checks,
        "distribution": doc,
        "checked_at": kit._utc_now(),
        "repair_hint": "sparkforge-azure install repair" if failed else None,
    }


def repair(*, scope: str = "project", root: Path | None = None,
           dry_run: bool = False) -> dict[str, Any]:
    from sparkforge_azure.distribution import service as dist
    from sparkforge_azure.distribution.managed import assess_ledger

    target = _resolve(scope, root)
    state = _state_dir(scope, target)
    before = [a for a in assess_ledger(state) if a["state"] != "present"]
    if dry_run:
        return _receipt(
            "repair", scope, target, status="planned",
            checks=[{"id": "drift", "status": "UNVERIFIED",
                     "detail": f"{len(before)} drifted managed assets"}],
            extra={"dry_run": True,
                   "drifted": [a["path"] for a in before]})
    with kit.acquire_lock(state):
        if scope == "user":
            _install_user(target, HOSTS, "recommended")
        else:
            # include_markers=False: markers legados sao convergidos pela
            # camada forge_context (repair_docs abaixo); reescreve-los aqui
            # recriaria o drift que estamos removendo (lf-0036).
            dist.initialize(target, with_mirrors=False, include_markers=False)
            from sparkforge_azure.distribution.managed import (
                load_ledger,
                save_ledger,
            )
            _drop_stale_doc_entries(state, target)
            ledger = load_ledger(state)
            ledger, _w = _install_skill_mirrors(target, ledger, HOSTS)
            save_ledger(state, ledger)
        after = [a for a in assess_ledger(state) if a["state"] != "present"]
        # Consumer docs: re-assert dos blocos `forge:*` a partir dos
        # manifests em `.forge/context/`; recusa nomeada vira check.
        # Escopo user tem target=~ e nunca registra contexto — repair_docs
        # criaria `~/.forge/context/` à toa, então só roda em project e
        # quando há resíduo de contexto.
        docs_check: dict[str, Any] | None = None
        if scope != "user" and _docs_leftovers(target):
            try:
                out_docs = fctx.repair_docs(
                    target, legacy_tags=_LEGACY_DOC_TAGS)
                docs_check = {
                    "id": "consumer-docs",
                    "status": "PASS",
                    "detail": f"{out_docs['status']} "
                    f"({len(out_docs['written'])} writes)",
                }
            except fctx.ContextError as exc:
                docs_check = {
                    "id": "consumer-docs",
                    "status": "BLOCKED",
                    "detail": f"{exc.kind}: {exc.detail}",
                }
    checks = [{"id": "repair",
               "status": "PASS" if not after else "FAIL",
               "detail": f"{len(before)} drifted, {len(after)} remaining"}]
    if docs_check is not None:
        checks.append(docs_check)
    return _receipt(
        "repair", scope, target,
        status="completed" if not after else "failed",
        checks=checks,
        extra={"repaired": [a["path"] for a in before
                            if a["path"] not in {b["path"] for b in after}]})


def uninstall(*, scope: str = "project", root: Path | None = None,
              purge: bool = False, dry_run: bool = False) -> dict[str, Any]:
    from sparkforge_azure.distribution import detach as detach_service

    target = _resolve(scope, root)
    if not _state_dir(scope, target).exists() and not dry_run:
        # No-op idempotente que não escreve estado — a menos que restem
        # resíduos de contexto/docs (state dir sumiu mas a entry no
        # registry ou os blocos `forge:*` continuam). As duas ops adquirem
        # lock, então só rodam quando há resíduo.
        checks = [{"id": "uninstall", "status": "PASS",
                   "detail": "0 removed, 0 kept — nothing installed"}]
        if scope != "user" and _docs_leftovers(target):
            checks += [_unregister_context(target), _uninstall_docs(target)]
        return _receipt(
            "uninstall", scope, target, status="completed",
            checks=checks,
            extra={"removed": [], "kept": []})
    out = detach_service.detach(
        target, dry_run=dry_run, purge_state=purge, purge_cache=False)
    removed = [d["path"] for d in out.get("detached", [])
               if d.get("action") not in ("preserved_state", "absent")]
    context_checks: list[dict[str, Any]] = []
    if not dry_run:
        kit._prune_empty_dirs(target, removed)
        if scope != "user" and _docs_leftovers(target):
            context_checks = [
                _unregister_context(target), _uninstall_docs(target)]
    return _receipt(
        "uninstall", scope, target,
        status="planned" if dry_run else "completed",
        checks=[{"id": "uninstall", "status": "PASS",
                 "detail": f"{len(removed)} removed, "
                           f"{len(out.get('preserved', []))} preserved"}]
        + context_checks,
        extra={"dry_run": dry_run, "removed": removed,
               "kept": out.get("preserved", []),
               "warnings": out.get("warnings", [])})


def update(*, to: str | None = None, repo: Path | None = None,
           dry_run: bool = False) -> dict[str, Any]:
    if to == "latest":
        return _receipt("update", "user", Path.home(), status="failed",
                        checks=[{"id": "version", "status": "FAIL",
                                 "detail": "'latest' is never installable"}])
    manifest = kit._load_json(
        kit.installations_dir() / f"{FORGE_ID}.json", None) or {}
    src = repo or (Path(p) if (p := (manifest.get("source") or {}).get("path"))
                   else None)
    venv = manifest.get("venv")
    if src is None or not src.exists() or not venv:
        return _receipt(
            "update", "user", Path.home(), status="failed",
            checks=[{"id": "source", "status": "BLOCKED",
                     "detail": "no registered checkout/venv — run setup"}])
    venv_py = Path(venv) / ("Scripts/python.exe" if sys.platform == "win32"
                            else "bin/python")
    cmd = [str(venv_py), "-m", "pip", "install", "--upgrade", str(src)]
    if dry_run:
        return _receipt(
            "update", "user", Path.home(), status="planned",
            checks=[{"id": "pip", "status": "UNVERIFIED",
                     "detail": " ".join(cmd)}], extra={"dry_run": True})
    proc = subprocess.run(  # noqa: S603 — venv python + fixed pip argv
        cmd, capture_output=True, text=True, timeout=900, check=False)
    return _receipt(
        "update", "user", Path.home(),
        status="completed" if proc.returncode == 0 else "failed",
        checks=[{"id": "pip",
                 "status": "PASS" if proc.returncode == 0 else "FAIL",
                 "detail": (proc.stdout or proc.stderr)[-300:]}])


def mcp_verify() -> dict[str, Any]:
    return kit.mcp_verify(_spec())


__all__ = ["HOSTS", "PROFILES", "SCOPES", "doctor", "install", "mcp_verify",
           "repair", "status", "uninstall", "update"]


# --------------------------------------------------------------------------
# forge-context/v1 wiring (install-2.0 ciclo 2, the-forge ADR-0061)
# `.forge/context/` e o registry de workspace compartilhado entre forges.
# Este forge so registra e desregistra o proprio `forge_id`.
# --------------------------------------------------------------------------

_PKG_DIR = Path(__file__).resolve().parents[1]
_REPO_DIR = _PKG_DIR.parent

# Markers de geracoes anteriores (`distribution.managed` escrevia
# `<!-- sparkforge-azure:begin -->`); `install_docs` os remove ao
# convergir para o contrato `forge:<tag>` (lf-0036).
_LEGACY_DOC_TAGS: tuple[str, ...] = ("sparkforge-azure",)

_AZURE_DOMAINS: tuple[str, ...] = (
    "azure-data",
    "azure-databricks",
    "microsoft-fabric",
    "azure-synapse",
    "adf",
    "apache-iceberg",
    "spark-streaming",
    "terraform",
    "data-quality",
)


def _group(group: str) -> Path | None:
    """`skills`/`agents`/`rules`/`knowledge`/`evals` — raiz do clone ou
    `_data/<group>` dentro do wheel, resolvido pelo canal canonico."""
    from sparkforge_azure.distribution.assets import _group_dir

    try:
        root = _group_dir(group)
    except Exception:
        return None
    return root if root.is_dir() else None


def _mds(base: Path) -> list[str]:
    return sorted(p.stem for p in base.glob("*.md")) if base.is_dir() else []


def _context_manifest(
    *, scope: str, profile: str, hosts: list[str],
    components: dict[str, Any] | None,
) -> dict[str, Any]:
    """Manifesto forge/context/v1 montado das fontes reais: `forge.json` +
    `forge.agentic.json` + `manifest.json` no checkout e os grupos de
    assets que o install usou."""
    forge_json = kit._load_json(_REPO_DIR / "forge.json", None)
    forge_json = forge_json if isinstance(forge_json, dict) else None
    agentic = kit._load_json(_REPO_DIR / "forge.agentic.json", None)
    agentic = agentic if isinstance(agentic, dict) else None

    skills_root = _group("skills")
    skills = (
        sorted(
            d.name for d in skills_root.iterdir()
            if d.is_dir() and (d / "SKILL.md").is_file()
        )
        if skills_root is not None
        else []
    )
    agents_root = _group("agents")
    agent_ids = _mds(agents_root) if agents_root is not None else []
    rules_root = _group("rules")
    catalog = rules_root / "catalog" if rules_root is not None else None
    rule_areas = (
        sorted(p.stem for p in catalog.glob("*.yaml"))
        if catalog is not None and catalog.is_dir()
        else []
    )
    knowledge_root = _group("knowledge")
    providers = (
        [{"id": "knowledge-base", "interface": "bundled"}]
        if knowledge_root is not None
        else []
    )
    evals_root = _group("evals")
    eval_suites = (
        [
            {"id": p.name, "kind": "output-verification"}
            for p in sorted(evals_root.iterdir())
            if p.is_dir()
        ]
        if evals_root is not None
        else []
    )

    checks: list[dict[str, Any]] = [
        {
            "id": "skills-bundle",
            "status": "PASS" if skills else "UNVERIFIED",
            "detail": f"{len(skills)} skills",
        },
        {
            "id": "agent-specs",
            "status": "PASS" if agent_ids else "UNVERIFIED",
            "detail": f"{len(agent_ids)} agent docs",
        },
        {
            "id": "rules-catalog",
            "status": "PASS" if rule_areas else "UNVERIFIED",
            "detail": f"{len(rule_areas)} rule files",
        },
    ]
    return fctx.build_manifest(
        forge_id=FORGE_ID,
        name="Spark Forge Azure",
        version=__version__,
        cli="sparkforge-azure",
        package="sparkforge_azure",
        distribution="sparkforge-azure",
        python_spec=">=3.10",
        scope=scope,
        profile=profile,
        hosts=hosts,
        forge_json=forge_json,
        agentic=agentic,
        domains=_AZURE_DOMAINS,
        skills=skills,
        coordinators=("coordinator",) if "coordinator" in agent_ids else (),
        agents=agent_ids,
        rule_areas=rule_areas,
        knowledge_providers=providers,
        eval_suites=eval_suites,
        protocols=(
            {"id": "forge/v1", "version": "1"},
            {"id": "forge/context/v1", "version": "1"},
            {"id": "forge/context-registry/v1", "version": "1"},
        ),
        discovery_ops=discovery_ops.ops(),
        discovery_commands=(
            *(
                c
                for c in discovery_ops.commands()
                if c["id"] != "doctor"  # `doctor` entra abaixo, ja declarado
            ),
            {
                "id": "analyze",
                "argv": ["sparkforge-azure", "analyze", "{target}"],
                "mode": "direct-capability",
                "read_only": True,
                "description": "analyze Azure data artifacts",
            },
            {
                "id": "next-step",
                "argv": ["sparkforge-azure", "next-step"],
                "mode": "specialist-workflow",
                "read_only": True,
                "description": "routing-driven specialist recommendation",
            },
            {
                "id": "doctor",
                "argv": ["sparkforge-azure", "doctor"],
                "mode": "diagnostic-only",
                "read_only": True,
                "description": "environment + installation health",
            },
        ),
        mcp={
            "server_name": "sparkforge-azure",
            "command": ["sparkforge-azure", "mcp", "serve"],
            "verify_tool": "sfa_version",
        },
        resources={
            "skills-bundle": {
                "kind": "bundled",
                "location": "sparkforge_azure/_data/skills",
                "optional": False,
            },
            "agents-bundle": {
                "kind": "bundled",
                "location": "sparkforge_azure/_data/agents",
                "optional": False,
            },
            "rules-catalog": {
                "kind": "bundled",
                "location": "sparkforge_azure/_data/rules",
                "optional": False,
            },
            "knowledge-base": {
                "kind": "bundled",
                "location": "sparkforge_azure/_data/knowledge",
                "optional": True,
            },
            "install-state": {
                "kind": "referenced",
                "location": ".sparkforge-azure",
                "optional": True,
            },
        },
        mutating_verbs=(
            "install",
            "uninstall",
            "repair",
            "integrate",
            "detach",
            "collect",
            "case update",
        ),
        requires_approval=("install", "uninstall", "integrate", "detach"),
        offline_available=True,
        health={
            "status": (
                "healthy" if skills and agent_ids and rule_areas else "degraded"
            ),
            "checks": checks,
        },
        components=components,
        recorded_by="sparkforge-azure",
    )


def _register_context(
    target: Path,
    receipt: dict[str, Any],
    *,
    scope: str,
    profile: str,
    hosts: list[str],
    components: dict[str, Any] | None,
) -> None:
    """Grava `.forge/context/` — manifesto + entrada no registry +
    ROUTING.md. Falha vira check BLOCKED nomeado no recibo."""
    try:
        manifest = _context_manifest(
            scope=scope, profile=profile, hosts=hosts, components=components
        )
        out = fctx.register_forge(target, manifest, owner=FORGE_ID)
        receipt.setdefault("checks", []).append(
            {
                "id": "context-registry",
                "status": "PASS",
                "detail": f".forge/context {out['status']} "
                f"({len(out['written'])} writes)",
            }
        )
    except fctx.ContextError as exc:
        receipt.setdefault("checks", []).append(
            {"id": "context-registry", "status": "BLOCKED",
             "detail": f"{exc.kind}: {exc.detail}"}
        )
        return
    # Consumer docs (AGENTS.md/CLAUDE.md/AGENT_PROTOCOL.md) so existem em
    # escopo de projeto/workspace — user-scope escreve assets sob ~ e ja
    # traz os markers legados via install_host_assets.
    if scope == "user":
        return
    try:
        docs = fctx.install_docs(
            target, manifest, owner=FORGE_ID, legacy_tags=_LEGACY_DOC_TAGS
        )
        receipt.setdefault("checks", []).append(
            {
                "id": "consumer-docs",
                "status": "PASS",
                "detail": (
                    f"{docs['status']}: {len(docs['written'])} written, "
                    f"{len(docs['kept'])} kept"
                ),
            }
        )
    except fctx.ContextError as exc:
        receipt.setdefault("checks", []).append(
            {"id": "consumer-docs", "status": "BLOCKED",
             "detail": f"{exc.kind}: {exc.detail}"}
        )


def _unregister_context(target: Path) -> dict[str, Any]:
    """Remove somente o manifesto/entry deste forge."""
    try:
        out = fctx.unregister_forge(target, FORGE_ID, owner=FORGE_ID)
        return {
            "id": "context-registry",
            "status": "PASS",
            "detail": f".forge/context {out['status']}",
        }
    except fctx.ContextError as exc:
        return {
            "id": "context-registry",
            "status": "BLOCKED",
            "detail": f"{exc.kind}: {exc.detail}",
        }


_CONSUMER_DOCS: tuple[str, ...] = (
    "AGENTS.md", "CLAUDE.md", "AGENT_PROTOCOL.md")


def _drop_stale_doc_entries(state: Path, target: Path) -> None:
    """Remove do ledger as entries dos consumer docs: eles agora sao
    managed pela camada forge_context (blocos `forge:*`), nao por hash de
    marker/bloco — uma entry `markers` antiga ficaria `modified` para
    sempre depois da convergencia."""
    from sparkforge_azure.distribution.managed import (
        forget_file,
        load_ledger,
        save_ledger,
    )

    ledger = load_ledger(state)
    for name in _CONSUMER_DOCS:
        ledger = forget_file(ledger, (target / name).resolve())
        ledger = forget_file(ledger, target / name)
    save_ledger(state, ledger)


def _docs_leftovers(target: Path) -> bool:
    """True quando o target ainda carrega resíduo forge_context: dir de
    contexto, nosso bloco managed, o bloco shared do ecossistema, o
    sentinel do protocolo managed ou um marker legado. Leitura sem lock —
    só um hit justifica o caminho de escrita (nunca criamos
    `.forge/context/` num root pristino)."""
    if (target / fctx.CONTEXT_DIR).exists():
        return True
    needles = (
        f"forge:{FORGE_ID}:", f"{fctx.DOC_TAG_ECOSYSTEM}:",
        fctx.PROTOCOL_SENTINEL, *_LEGACY_DOC_TAGS,
    )
    for name in _CONSUMER_DOCS:
        path = target / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(n in text for n in needles):
            return True
    return False


def _uninstall_docs(target: Path) -> dict[str, Any]:
    """Retira os blocos `forge:sparkforge-azure` (+ markers legados) dos
    consumer docs. Depois do unregister, para o protocolo sair sem nos."""
    try:
        out = fctx.uninstall_docs(
            target, FORGE_ID, owner=FORGE_ID, legacy_tags=_LEGACY_DOC_TAGS
        )
        return {
            "id": "consumer-docs",
            "status": "PASS",
            "detail": f"{out['status']}: {len(out['written'])} changed",
        }
    except fctx.ContextError as exc:
        return {
            "id": "consumer-docs",
            "status": "BLOCKED",
            "detail": f"{exc.kind}: {exc.detail}",
        }
