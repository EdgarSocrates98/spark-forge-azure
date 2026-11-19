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

import dataclasses
import json
import shutil
import subprocess  # noqa: S404 — bounded argv to the installed venv pip
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from sparkforge_azure import __version__, discovery_ops
from sparkforge_azure import _forgecontext as fctx
from sparkforge_azure import _installkit as kit

FORGE_ID = "spark-forge-azure"
# Registry identities this forge previously shipped under. Installs from
# pre-lf-0040 (merged in #79) registered `sparkforge-azure` — the canonical
# manifest id was always `spark-forge-azure` (forge.json). Install/uninstall
# sweep that stale identity: same forge, older name — reclaiming it is
# self-cleanup, never foreign deletion.
_LEGACY_FORGE_IDS: tuple[str, ...] = ("sparkforge-azure",)
PROFILES: tuple[str, ...] = ("minimal", "recommended", "full")
GATEWAY_PROFILES: tuple[str, ...] = ("economy", "balanced", "deep")
SCOPES: tuple[str, ...] = ("project", "workspace", "user")
HOSTS: tuple[str, ...] = ("claude", "devin", "codex", "copilot")

# Which host-owned dirs receive skill mirrors per host. `.agents/skills`
# is shared by Devin/Codex/Copilot (deduplicated at write time) — devin o
# le nativamente, entao `.devin/` fica so para confs host-specific.
_SKILL_ROOTS: dict[str, tuple[str, ...]] = {
    "claude": (".claude/skills",),
    "devin": (".agents/skills",),
    "codex": (".agents/skills",),
    "copilot": (".agents/skills", ".github/skills"),
}

#: Subdir proprio dentro de `knowledge/` do alvo (install-2.1) — canonical
#: em `skills/mirrors.py` (KNOWLEDGE_NAMESPACE), importado lazy onde usado.


def _resolved_mcp_command(spec: kit.ForgeSpec) -> tuple[str, ...] | None:
    """Resolve the managed server argv without depending on the host PATH."""
    if not spec.mcp_command:
        return None
    tail = spec.mcp_command[1:]
    shim = (_installation_manifest().get("cli") or {}).get("shim")
    if isinstance(shim, str) and shim and Path(shim).is_absolute():
        return (shim, *tail)
    return (sys.executable, "-m", spec.package, *tail)


def _resolve_mcp_command() -> tuple[str, ...]:
    command = shutil.which("sparkforge-azure")
    return (command or "sparkforge-azure", "mcp", "serve")


def _spec() -> kit.ForgeSpec:
    spec = kit.ForgeSpec(
        forge_id=FORGE_ID,
        package="sparkforge_azure",
        distribution="sparkforge-azure",
        cli_name="sparkforge-azure",
        python_spec=">=3.10",
        state_dir=".sparkforge-azure",
        mcp_command=_resolve_mcp_command(),
        mcp_server_name="sparkforge-azure",
        mcp_verify_tool="sfa_version",
        version_cmd=("--version",),
        render_assets=None,
        marker_files=("AGENTS.md", "CLAUDE.md"),
        marker_body="",
        user_state_dir="~/.sparkforge-azure",
    )
    resolved = _resolved_mcp_command(spec)
    return dataclasses.replace(spec, mcp_command=resolved) if resolved else spec


def _resolve(scope: str, root: Path | None) -> Path:
    return kit.resolve_scope(
        _spec(), scope, Path.cwd(), root.resolve() if root else None)


def _state_dir(scope: str, target: Path) -> Path:
    if scope == "user":
        return Path.home() / ".sparkforge-azure"
    return target / ".sparkforge-azure"


def _skill_source_dirs() -> list[tuple[str, Path]]:
    """``(skill_name, skill_dir)`` from the canonical ``skills/`` group —
    source checkout or the ``_data/skills`` payload inside the wheel. The
    dir is needed so asset files (``references/``, ``scripts/``) can ship
    alongside ``SKILL.md`` (install-2.1)."""
    from sparkforge_azure.distribution.assets import _group_dir

    root = _group_dir("skills")
    out: list[tuple[str, Path]] = []
    if not root.is_dir():
        return out
    for item in sorted(root.iterdir(), key=lambda e: e.name):
        if item.is_dir() and (item / "SKILL.md").is_file():
            out.append((item.name, item))
    return out


def _skill_sources() -> list[tuple[str, str]]:
    """``(skill_name, SKILL.md text)`` — convenience over
    ``_skill_source_dirs`` for callers that only need the document."""
    return [
        (name, (sdir / "SKILL.md").read_text(encoding="utf-8"))
        for name, sdir in _skill_source_dirs()
    ]


def _skill_roots(hosts: tuple[str, ...]) -> list[str]:
    seen: list[str] = []
    for h in hosts:
        for r in _SKILL_ROOTS.get(h, ()):
            if r not in seen:
                seen.append(r)
    return seen


_KNOWLEDGE_REF_RE = None  # compiled lazily in _referenced_knowledge_paths


def _rel_seguro(rel: str) -> bool:
    """Um `knowledge/<rel>` citado num doc vira path em disco no install —
    `..`, absoluto, drive ou barra invertida escreveriam FORA da raiz
    `knowledge/` (o `Path` nao normaliza `..` antes do syscall)."""
    if not rel or "\\" in rel or ":" in rel or "%" in rel:
        return False
    partes = PurePosixPath(rel)
    return not partes.is_absolute() and ".." not in partes.parts


def _referenced_knowledge_paths(text: str) -> set[str]:
    """Os caminhos `knowledge/<rel>` citados num SKILL.md — por link markdown
    resolvido contra `skills/<name>` e por mencao textual `` `knowledge/x` ``.
    Serve para emitir ponteiros exatamente nos docs referenciados (lf-0037).
    Refs que escapam a raiz (`..`, absoluto) sao descartadas — nunca viram
    path nem chave de ledger."""
    return {rel for root, rel in _referenced_asset_paths(text) if root == "knowledge"}


def _referenced_asset_paths(text: str) -> set[tuple[str, str]]:
    """Os caminhos `{knowledge,rules,evals}/<rel>` citados num SKILL.md —
    pares ``(root, rel)``; refs que escapam a raiz sao descartadas."""
    global _KNOWLEDGE_REF_RE
    if _KNOWLEDGE_REF_RE is None:
        import re

        _KNOWLEDGE_REF_RE = re.compile(
            r"(knowledge|rules|evals)/[A-Za-z0-9_./-]+")
    refs: set[tuple[str, str]] = set()
    for match in _KNOWLEDGE_REF_RE.finditer(text):
        root_kind = match.group(1)
        rel = match.group(0)[len(root_kind) + 1:].rstrip(".,);]")
        if rel and _rel_seguro(rel):
            refs.add((root_kind, rel))
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


_ASSET_STUB = """\
# Ponteiro de {kind}

Este arquivo e um PONTEIRO gerado na instalacao: os links `{kind}/<rel>`
dos mirrors (.agents/skills, .claude/skills, ...) resolvem aqui, mas o
CONTEUDO real mora no pacote do forge instalado — fora de qualquer
checkout, e propositalmente nao copiado para o workspace.

Num workspace federado a raiz `{kind}/` e compartilhada entre forges: o
forge dono deste ponteiro e os seus verbos nativos constam no registry
`.forge/context/registry.json` (workspace) e em
`~/.forge/installations/` (conta). O manifesto `forge/context/v1` em
`.forge/context/capabilities/<forge>.json` lista os comandos de
descoberta do forge — em geral `<cli> capabilities` devolve o mapa
completo ops -> verbos.
"""


def _asset_stub(root_kind: str, rel: str) -> str:
    if root_kind == "knowledge":
        return _knowledge_stub(rel)
    return _ASSET_STUB.format(kind=root_kind, rel=rel)


_KNOWLEDGE_INDEX = """\
# knowledge/sparkforge-azure/ — ponteiros do sparkforge-azure

Os arquivos neste diretorio sao PONTEIROS (um por documento referenciado
pelas skills/agents instalados). O knowledge real e versionado dentro do
pacote `sparkforge-azure` e se recupera offline pelos verbos:

    sparkforge-azure knowledge list
    sparkforge-azure knowledge get <doc>
    sparkforge-azure knowledge search "<termo>" [--domain <d>]
    sparkforge-azure context pack --domain <d>
    sparkforge-azure capabilities          # mapa completo ops -> verbos

Total referenciado nesta instalacao: {total} documento(s).
"""


def _knowledge_index_stub(total: int) -> str:
    """`knowledge/sparkforge-azure/README.md` do alvo: indice dos ponteiros
    + os verbos de retrieval (paridade com a wave-02 do sibling AWS)."""
    return _KNOWLEDGE_INDEX.format(total=total)


def _migrate_legacy_knowledge_stubs(
    root: Path, ledger: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[str]]:
    """install-2.0 wrote stubs at ``knowledge/<rel>`` (un-namespaced).

    Honest migration (install-2.1): a ledgered stub whose bytes still match
    the ledger is ours — it is unlinked and its entry dropped (the new
    namespaced stub takes over). A ledgered stub whose bytes drifted was
    edited by the user — the file is preserved and our claim is dropped
    (``detach`` semantics), and an unledgered file was never ours — it is
    left entirely alone. Returns ``(ledger, migrated, detached)``."""
    from sparkforge_azure.distribution.managed import forget_file
    from sparkforge_azure.skills.mirrors import KNOWLEDGE_NAMESPACE

    kroot = (root / "knowledge").as_posix() + "/"
    kns = (root / "knowledge" / KNOWLEDGE_NAMESPACE).as_posix() + "/"
    migrated: list[str] = []
    detached: list[str] = []
    for entry in list(ledger["files"]):
        path = str(entry.get("path") or "")
        if not path.startswith(kroot) or path.startswith(kns):
            continue
        if entry.get("kind") != "knowledge_pointer":
            continue
        legacy = Path(path)
        ledger = forget_file(ledger, legacy)
        if not legacy.is_file():
            migrated.append(path)  # already gone — just drop the claim
            continue
        import hashlib

        if hashlib.sha256(legacy.read_bytes()).hexdigest() == entry.get("sha256"):
            legacy.unlink()  # ours, unmodified — the namespaced stub replaces it
            migrated.append(path)
        else:
            detached.append(path)  # user-edited — preserved, claim dropped
    return ledger, migrated, detached


def _skill_mirror_plan(
    root: Path, hosts: tuple[str, ...],
    include_agent_refs: bool = False,
) -> list[tuple[Path, str, str]]:
    """The ``(path, text, kind)`` plan for skill-layer writes under ``root``.

    Covers ``SKILL.md`` + the ``references/``/``scripts/`` asset dirs each
    skill ships + the shared ``_shared/`` tree (mirroring the repo-local
    sync in ``skills/mirrors.py``, install-2.1) + the asset pointers
    (`knowledge/` namespaced, ``rules/``/``evals/`` at their roots).
    ``include_agent_refs`` folds agent-manifest `knowledge/` mentions into
    the pointer set — only when agent mirrors actually install (full)."""
    from sparkforge_azure.distribution.assets import _group_dir
    from sparkforge_azure.skills.mirrors import (
        ASSET_DIRS,
        KNOWLEDGE_NAMESPACE,
        SHARED_DIR,
        _walk_files,
        mirror_name,
        namespace_knowledge_refs,
        render_mirror,
    )

    def _asset_bytes(asset: Path) -> str | bytes:
        """Texto com rewrite de namespace para `.md`; bytes verbatim para
        o resto — assets binarios (fontes, imagens) sao copiados como sao."""
        data = asset.read_bytes()
        if asset.suffix != ".md":
            return data
        try:
            return namespace_knowledge_refs(data.decode("utf-8"))
        except UnicodeDecodeError:
            return data

    plan: list[tuple[Path, str | bytes, str]] = []
    asset_refs: set[tuple[str, str]] = set()
    mroots = _skill_roots(hosts)
    for skill_name, sdir in _skill_source_dirs():
        text = (sdir / "SKILL.md").read_text(encoding="utf-8")
        asset_refs |= _referenced_asset_paths(text)
        rendered = namespace_knowledge_refs(render_mirror(text, skill_name))
        for mroot in mroots:
            mdir = root / mroot / mirror_name(skill_name)
            plan.append((mdir / "SKILL.md", rendered, "skill"))
            for sub in ASSET_DIRS:
                base = sdir / sub
                if not base.is_dir():
                    continue
                for asset in _walk_files(base):
                    rel = asset.relative_to(sdir)
                    if asset.suffix == ".md":
                        try:
                            asset_refs |= _referenced_asset_paths(
                                asset.read_text(encoding="utf-8"))
                        except UnicodeDecodeError:
                            pass
                    plan.append((mdir / rel, _asset_bytes(asset), "skill"))
    shared = _group_dir("skills") / SHARED_DIR
    if shared.is_dir():
        for asset in _walk_files(shared):
            rel = asset.relative_to(shared)
            if asset.suffix == ".md":
                try:
                    asset_refs |= _referenced_asset_paths(
                        asset.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    pass
            for mroot in mroots:
                plan.append(
                    (root / mroot / SHARED_DIR / rel,
                     _asset_bytes(asset), "skill"))
    # Agent manifests citam `knowledge/<rel>` tambem — seus refs entram no
    # mesmo conjunto de ponteiros, mas so quando os mirrors de agent
    # instalam de fato (full + kind agent; o espelho e reescrito com o
    # namespace em `install_host_assets`).
    if include_agent_refs:
        from sparkforge_azure.distribution.hostfiles import _agent_sources
        for _agent_id, agent_text in _agent_sources():
            asset_refs |= _referenced_asset_paths(agent_text)
    knowledge_rels: set[str] = set()
    for root_kind, rel in sorted(asset_refs):
        # Defesa em profundidade: `rel` vem de texto de documento — um `..`
        # residiria fora de `root/<kind>/` no syscall e viraria path com
        # `..` no ledger (unlink fora da raiz no uninstall).
        if not _rel_seguro(rel):
            continue
        # Ref de diretorio (`knowledge/spark/`) vira stub `<dir>/README.md`;
        # ref de arquivo vira stub no proprio caminho.
        stub_rel = rel if Path(rel).suffix else f"{rel}/README.md"
        if root_kind == "knowledge":
            knowledge_rels.add(rel)
            stub = root / "knowledge" / KNOWLEDGE_NAMESPACE / stub_rel
        else:
            stub = root / root_kind / stub_rel
        plan.append((stub, _asset_stub(root_kind, rel), root_kind))
    if knowledge_rels:
        plan.append((
            root / "knowledge" / KNOWLEDGE_NAMESPACE / "README.md",
            _knowledge_index_stub(len(knowledge_rels)),
            "knowledge",
        ))
    return plan


def _install_skill_mirrors(
    root: Path, ledger: dict[str, Any], hosts: tuple[str, ...],
    enabled_kinds: set[str] | None = None,
    include_agent_refs: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Write the skill-layer plan into the selected host roots, ledgered
    like every other managed asset. Knowledge pointers land namespaced
    under ``knowledge/sparkforge-azure/`` (install-2.1); legacy
    un-namespaced stubs migrate honestly first.

    Toda escrita whole-file passa por ``write_managed_file``: um arquivo
    pre-existente nao-ledgered no caminho de um mirror/stub e ESTRANGEIRO —
    preservado, nunca adotado nem sobrescrito, e reportado em ``skipped``
    (install-2.1). ``enabled_kinds`` restringe o plano aos kinds
    selecionados por ``--components``/profile.

    Returns ``(ledger, report)`` — the report carries per-file
    ``entries`` in the ``forge/InstallReceipt/v1`` ``managed_files``
    shape (path/sha256/kind/action[+note]), ``kind_bytes`` measured on
    the rendered payloads (never tokens), ``present`` (plan paths now
    correct on disk), ``written_bytes`` and the migration lists
    (cycle 16.1 §7.4)."""
    import hashlib

    from sparkforge_azure.distribution.managed import (
        ledger_entry,
        write_managed_file,
    )

    ledger, migrated, detached = _migrate_legacy_knowledge_stubs(root, ledger)
    entries: list[dict[str, Any]] = []
    present: list[str] = []
    skipped: list[str] = []
    kind_bytes: dict[str, int] = {}
    written_bytes = 0
    for target, text, kind in _skill_mirror_plan(
            root, hosts, include_agent_refs):
        if enabled_kinds is not None and kind not in enabled_kinds:
            continue
        data = text.encode("utf-8") if isinstance(text, str) else bytes(text)
        kind_bytes[kind] = kind_bytes.get(kind, 0) + len(data)
        ledger_kind = "skill_mirror" if kind == "skill" else f"{kind}_pointer"
        rel_parts = target.relative_to(root).parts
        host = (
            rel_parts[0].lstrip(".")
            if "/skills/" in target.as_posix()
            else None
        )
        ledger, outcome = write_managed_file(
            ledger, target, text,
            kind=ledger_kind,
            host=host,
        )
        key = target.as_posix()
        if outcome == "preserved_foreign":
            skipped.append(str(target))
            try:
                sha = hashlib.sha256(target.read_bytes()).hexdigest()
            except OSError:
                sha = ""
            entries.append({
                "path": key, "sha256": sha, "kind": ledger_kind,
                "action": "unchanged",
                "note": "user-owned, not managed — skipped",
            })
            continue
        owned = ledger_entry(ledger, target) is not None
        entry: dict[str, Any] = {
            "path": key,
            "sha256": hashlib.sha256(data).hexdigest(),
            "kind": ledger_kind,
            "action": outcome,
        }
        if outcome == "unchanged" and not owned:
            # Byte-identical foreign file — never adopted (detach must not
            # delete what we never wrote); the receipt says so honestly.
            entry["note"] = "pre-existing identical — user-owned, not managed"
        if outcome in ("created", "updated", "restored"):
            written_bytes += len(data)
        entries.append(entry)
        present.append(str(target))
    return ledger, {
        "entries": entries,
        "present": present,
        "skipped": skipped,
        "migrated": migrated,
        "detached": detached,
        "kind_bytes": kind_bytes,
        "written_bytes": written_bytes,
    }


def _mcp_config(root: Path, ledger: dict[str, Any],
                profile: str | None = None) -> tuple[dict[str, Any], str]:
    from sparkforge_azure.distribution.hosts import MCP_SERVER_NAME, mcp_entry
    from sparkforge_azure.distribution.managed import apply_json_key

    ledger, outcome = apply_json_key(
        root / ".mcp.json", f"mcpServers.{MCP_SERVER_NAME}",
        mcp_entry(profile=profile),
        ledger=ledger, kind="mcp_config",
    )
    return ledger, outcome


def _planned_files(target: Path, scope: str, hosts: tuple[str, ...],
                   profile: str,
                   enabled_kinds: set[str] | None = None) -> list[str]:
    from sparkforge_azure.distribution.hostfiles import _AGENT_ROOT_HOSTS

    out = ["AGENTS.md"]
    # `.mcp.json` entra no plano quando ha host selecionado E o kind mcp
    # esta habilitado — `install` escreve a entrada nessa mesma condicao.
    if hosts and (enabled_kinds is None or "mcp" in enabled_kinds):
        out.append(".mcp.json")
    if scope == "project":
        # install_docs sempre escreve CLAUDE.md + AGENT_PROTOCOL.md (lf-0036)
        out += [".sparkforge-azure/project.yaml", "CLAUDE.md",
                "AGENT_PROTOCOL.md"]
    elif scope == "workspace":
        # install-2.1: workspace nao ganha project.yaml (membros precisam
        # poder instalar depois) — so os consumer docs.
        out += ["CLAUDE.md", "AGENT_PROTOCOL.md"]
    elif "claude" in hosts or (target / "CLAUDE.md").exists():
        out.append("CLAUDE.md")
    if profile in ("recommended", "full"):
        # O plano real da camada de skills — SKILL.md + references/ +
        # scripts/ + _shared/ + ponteiros namespaced (install-2.1) —
        # filtrado pelos kinds efetivos (--components/profile).
        out += [
            p.relative_to(target).as_posix()
            for p, _text, kind in _skill_mirror_plan(target, hosts)
            if enabled_kinds is None or kind in enabled_kinds
        ]
    if profile == "full" and (
        enabled_kinds is None or "agent" in enabled_kinds
    ):
        from sparkforge_azure.agentmanifest.mirrors import (
            AGENT_MIRROR_ROOTS,
        )
        from sparkforge_azure.agentmanifest.mirrors import (
            mirror_name as agent_mirror_name,
        )
        from sparkforge_azure.distribution.hostfiles import _agent_sources
        selected = set(hosts)
        roots = [
            r for r in AGENT_MIRROR_ROOTS
            if selected & set(_AGENT_ROOT_HOSTS.get(r, ()))
        ]
        for agent_id, _src in _agent_sources():
            for mroot in roots:
                out.append(f"{mroot}/{agent_mirror_name(agent_id)}.md")
    return sorted(dict.fromkeys(out))


def _receipt(operation: str, scope: str, target: Path, *,
             status: str, checks: list[dict[str, Any]],
             managed_files: list[dict[str, Any]] | None = None,
             extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """``forge/InstallReceipt/v1`` doc — ``managed_files`` items carry the
    contract shape ``{path, sha256, kind, action[, note]}`` measured by
    the writers, and every receipt leaves with its derived
    ``forge/InstallLifecycle/v1`` block (never a declared verdict)."""
    from sparkforge_azure.install import lifecycle

    seed = json.dumps(
        {"o": operation, "t": str(target), "ts": kit._utc_now()},
        sort_keys=True,
    ).encode()
    doc = {
        "schema": kit.SCHEMA_RECEIPT,
        "receipt_id": f"sha256:{kit._sha(seed)}",
        "forge_id": FORGE_ID,
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
    doc["lifecycle"] = lifecycle.receipt_block(doc)
    return doc


def _ledger_entries(
    state: Path,
    actions: dict[str, str],
    notes: dict[str, str],
    *,
    ledger: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """``managed_files`` entries for the state-layer files (mcp config,
    project manifest, distribution receipt, marker docs, agent mirrors):
    ``{path, sha256, kind, action[, note]}`` — sha/kind from the ledger
    when the file is ours, from disk when it is not (foreign)."""
    import hashlib

    from sparkforge_azure.distribution.managed import load_ledger

    files = (ledger if ledger is not None else load_ledger(state))["files"]
    by_path = {f["path"]: f for f in files}
    out: list[dict[str, Any]] = []
    for path in sorted(actions):
        owned = by_path.get(path)
        if owned is not None:
            sha, kind = owned.get("sha256") or "", owned.get("kind") or "asset"
        else:
            try:
                sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            except OSError:
                sha = ""
            kind = "foreign"
        entry: dict[str, Any] = {
            "path": path, "sha256": sha, "kind": kind,
            "action": actions[path],
        }
        if path in notes:
            entry["note"] = notes[path]
        out.append(entry)
    return out


def _refresh_distribution_receipt(state: Path) -> str | None:
    """Re-assert ``receipt-distribution.json``'s ``managed_files`` against
    the final ledger — the mirror layer ledgers its files *after*
    ``initialize``'s snapshot, so the doc converges only once refreshed
    (cycle 16.1 §7.4). Returns the real action or None."""
    from sparkforge_azure.distribution.managed import load_ledger
    from sparkforge_azure.durable import write_atomic_bytes

    path = state / "receipt-distribution.json"
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict):
        return None
    ledger = load_ledger(state)
    managed = sorted(
        {str(f["path"]) for f in ledger["files"]} | {path.as_posix()}
    )
    if doc.get("managed_files") == managed:
        return "unchanged"
    doc["managed_files"] = managed
    # bytes, not text — Windows `\r\n` would drift the ledger sha (§7.4).
    write_atomic_bytes(
        path, (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    # The ledger entry was recorded against the pre-refresh bytes — keep
    # the sha honest so the NEXT run's ledger compare is a fixpoint too.
    from sparkforge_azure.distribution.managed import record_file, save_ledger

    save_ledger(state, record_file(ledger, path, kind="receipt"))
    return "updated"


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
    opts = kit.component_options(profile, components)
    opts["execution_profile"] = gateway_profile
    # Kinds efetivos de asset: `--components` seleciona explicitamente;
    # senao o default do profile (paridade AWS wave-02 — PROFILE_COMPONENTS
    # / profile_asset_kinds). "config"/"marker"/"state" sao core.
    if components is None:
        enabled_kinds = set(kit.profile_asset_kinds(profile))
    else:
        enabled_kinds = set(opts.get("asset_kinds", ()))

    if dry_run:
        return _receipt(
            "install", scope, target, status="planned",
            checks=[{"id": "plan", "status": "UNVERIFIED",
                     "detail": "dry-run — nothing written"}],
            managed_files=[],
            extra={"dry_run": True,
                   "components": opts or None,
                   "gateway_profile": gateway_profile,
                   "planned_files": _planned_files(
                       target, scope, hosts, profile, enabled_kinds)})
    if not yes:
        raise PortableError(
            kit.E_NOTAPPROVED,
            "install requires --yes or --dry-run; the plan is the contract")

    # Incremental-install evidence (cycle 16.1 §7.4): every writer reports
    # the REAL per-path action; the receipt folds them into managed_files
    # entries + counts + measured context bytes (never tokens).
    file_actions: dict[str, str] = {}
    file_notes: dict[str, str] = {}
    entries: list[dict[str, Any]] = []
    kind_bytes: dict[str, int] = {}
    written_bytes = 0
    with kit.acquire_lock(state):
        if scope == "user":
            doc = _install_user(
                target, hosts, profile, enabled_kinds, gateway_profile)
        else:
            # include_markers=False: os consumer docs (blocos `forge:*` +
            # AGENT_PROTOCOL.md consolidado) sao escritos pela camada
            # forge_context em `_register_context`, nao pelo ledger de
            # markers legado (lf-0036).
            # mint_identity: workspace NAO e um projeto — sem project.yaml
            # na raiz do workspace, senao member installs recusam com
            # path_outside_root (install-2.1).
            doc = dist.initialize(
                target,
                with_mirrors=(profile == "full"),
                include_markers=False,
                hosts=tuple(hosts),
                execution_profile=gateway_profile,
                enabled_kinds=enabled_kinds,
                mint_identity=(scope == "project"),
            )
            _drop_stale_doc_entries(state, target)
            if profile in ("recommended", "full"):
                from sparkforge_azure.distribution.managed import (
                    load_ledger,
                    save_ledger,
                )
                ledger = load_ledger(state)
                with_agent_refs = (
                    profile == "full"
                    and (enabled_kinds is None or "agent" in enabled_kinds)
                )
                ledger, mirror_report = _install_skill_mirrors(
                    target, ledger, hosts, enabled_kinds,
                    with_agent_refs)
                save_ledger(state, ledger)
                doc["skill_mirrors"] = mirror_report["present"]
                if mirror_report["skipped"]:
                    doc["foreign_preserved"] = mirror_report["skipped"]
                if mirror_report["migrated"]:
                    doc["knowledge_migrated"] = mirror_report["migrated"]
                if mirror_report["detached"]:
                    doc["knowledge_detached"] = mirror_report["detached"]
                doc["skill_entries"] = mirror_report["entries"]
                merged_bytes = dict(doc.get("kind_bytes") or {})
                for _k, _n in mirror_report["kind_bytes"].items():
                    merged_bytes[_k] = merged_bytes.get(_k, 0) + _n
                doc["kind_bytes"] = merged_bytes
                doc["written_bytes"] = (
                    doc.get("written_bytes") or 0
                ) + mirror_report["written_bytes"]
                doc["managed_files"] = [f["path"] for f in ledger["files"]]
            # §7.4 fixpoint: `initialize` snapshots `managed_files` before
            # the mirror layer ledgers its files — re-assert the doc
            # against the final ledger so a second install sees identical
            # bytes (zero rewrites of unchanged assets).
            refreshed = _refresh_distribution_receipt(state)
            if refreshed:
                rkey = (state / dist.RECEIPT_NAME).as_posix()
                actions = doc.setdefault("file_actions", {})
                # don't downgrade `created` → `updated` within one run
                if actions.get(rkey) != "created":
                    actions[rkey] = refreshed
        # `initialize` may report a refusal doc instead of raising.
        ok = doc.get("status") == "ok"
    if opts:
        state.mkdir(parents=True, exist_ok=True)
        # Incremental (§7.4): components.json is state — identical bytes
        # are never re-touched on reinstall.
        components_path = state / "components.json"
        payload = json.dumps(opts, indent=2)
        if not (
            components_path.is_file()
            and components_path.read_text(encoding="utf-8") == payload
        ):
            components_path.write_text(payload, encoding="utf-8")
    preserved = list(doc.get("foreign_preserved") or [])
    preserved += list(
        (doc.get("host_files") or {}).get("preserved_foreign") or []
    )
    checks = [{"id": "apply", "status": "PASS" if ok else "FAIL",
               "detail": f"{len(doc.get('managed_files', []))} managed files"}]
    if preserved:
        # Um arquivo pre-existente nao-ledgered num caminho gerenciado e
        # estrangeiro: preservado, nao adotado — e o plano NAO foi aplicado
        # por inteiro, entao o recibo recusa honestamente (install-2.1).
        checks.append(
            {"id": "foreign-files", "status": "FAIL",
             "detail": f"{len(preserved)} foreign file(s) preserved at "
                       f"managed paths — not adopted"})
        ok = False
    file_actions.update(doc.get("file_actions") or {})
    file_notes.update(doc.get("file_notes") or {})
    entries.extend(_ledger_entries(state, file_actions, file_notes))
    entries.extend(doc.get("skill_entries") or [])
    entries.sort(key=lambda item: str(item.get("path") or ""))
    for kind, amount in (doc.get("kind_bytes") or {}).items():
        kind_bytes[kind] = kind_bytes.get(kind, 0) + amount
    written_bytes += doc.get("written_bytes") or 0
    counts: dict[str, int] = {}
    for item in entries:
        action = str(item.get("action", "?"))
        counts[action] = counts.get(action, 0) + 1
    counts["written"] = (
        counts.get("created", 0)
        + counts.get("updated", 0)
        + counts.get("restored", 0)
    )
    from sparkforge_azure.distribution.hosts import MCP_SERVER_NAME

    mcp_action = doc.get("mcp_action")
    receipt = _receipt(
        "install", scope, target,
        status="completed" if ok else "failed",
        checks=checks,
        managed_files=entries,
        extra={"components": opts or None,
               "profile": profile,
               "execution_profile": gateway_profile,
               "host": ",".join(hosts) or None,
               "dry_run": False,
               "counts": counts | {"written_bytes": written_bytes},
               # Context-budget metrics — only bytes MEASURED at write
               # time (§8.5/§13.2); tokens are never invented.
               "context": {
                   "profile": profile,
                   "skills_bytes": kind_bytes.get("skill") or None,
                   "agents_bytes": kind_bytes.get("agent") or None,
                   "knowledge_bytes": kind_bytes.get("knowledge") or None,
                   "rules_bytes": kind_bytes.get("rules") or None,
                   "evals_bytes": kind_bytes.get("evals") or None,
                   "managed_bytes": sum(kind_bytes.values()) or None,
                   "mcp_entries": 1 if mcp_action else None,
               },
               "mcp": ([{
                   "server": MCP_SERVER_NAME,
                   "file": ".mcp.json",
                   "action": mcp_action,
               }] if mcp_action else []),
               "gateway_profile": gateway_profile,
               "preserved_foreign": preserved or None,
               "distribution": {k: v for k, v in doc.items()
                                if k not in ("managed_files",)}})
    if ok:
        _register_context(
            target, receipt, scope=scope, profile=profile,
            hosts=hosts, components=opts or None,
        )
        # `_register_context` may append checks and downgrade `status`:
        # verification and lifecycle are re-derived from the FINAL
        # receipt, never declared by the writer.
        receipt["verification"]["status"] = (
            "PASS"
            if all(
                c["status"] in ("PASS", "NOT_APPLICABLE", "UNVERIFIED")
                for c in receipt["checks"]
            )
            else "FAIL"
        )
        from sparkforge_azure.install import lifecycle

        receipt["lifecycle"] = lifecycle.receipt_block(receipt)
        # O manifesto de conta (~/.forge/installations/) descreve o runtime
        # instalado — escopo user instala assets sob ~, nao o runtime; o
        # registro so e re-assertido nos escopos de projeto/workspace.
        if scope != "user":
            _register(target)
    # Canonical evidence trail: every real apply persists its final
    # receipt under `.sparkforge-azure/receipts/` (kit `_write_receipt`).
    kit._write_receipt(state, receipt)
    return receipt


def _install_user(home: Path, hosts: tuple[str, ...],
                  profile: str, enabled_kinds: set[str] | None = None,
                  gateway_profile: str | None = None) -> dict[str, Any]:
    """User scope: host assets only — no project identity (that's per-repo).

    install-2.1: `hosts` escopa mirrors/configs (`--host`), `enabled_kinds`
    restringe kinds (`--components`), `gateway_profile` seleciona o argv
    MCP (economy/balanced → `--compact`)."""
    from sparkforge_azure.distribution.hostfiles import install_host_assets
    from sparkforge_azure.distribution.hosts import detect_hosts
    from sparkforge_azure.distribution.managed import load_ledger, save_ledger

    state = home / ".sparkforge-azure"
    ledger = load_ledger(state)
    file_actions: dict[str, str] = {}
    file_notes: dict[str, str] = {}
    mcp_wanted = enabled_kinds is None or "mcp" in enabled_kinds
    outcome = "skipped"
    if mcp_wanted and hosts:
        ledger, outcome = _mcp_config(
            home, ledger, profile=gateway_profile)
        mcp_key = (home / ".mcp.json").as_posix()
        if outcome in ("created", "updated", "unchanged"):
            file_actions[mcp_key] = outcome
        elif outcome == "conflict":
            file_actions[mcp_key] = "unchanged"
            file_notes[mcp_key] = "user-owned, not managed — skipped"
    detected = tuple(h["name"] for h in detect_hosts()
                     if h["status"] == "available")
    ledger, report = install_host_assets(
        home, ledger, hosts=detected,
        with_mirrors=(profile == "full"),
        write_markers=bool(hosts),
        enabled_kinds=enabled_kinds,
        mirror_hosts=hosts)
    file_actions.update(report.get("actions") or {})
    for foreign in report.get("preserved_foreign") or ():
        file_actions[Path(foreign).as_posix()] = "unchanged"
        file_notes[Path(foreign).as_posix()] = (
            "user-owned, not managed — skipped"
        )
    agent_bytes = int((report.get("mirrors") or {}).get("bytes") or 0)
    agent_written_bytes = int(
        (report.get("mirrors") or {}).get("written_bytes") or 0
    )
    written: list[str] = []
    skipped: list[str] = []
    migrated: list[str] = []
    detached: list[str] = []
    skill_entries: list[dict[str, Any]] = []
    kind_bytes: dict[str, int] = {}
    written_bytes = 0
    if profile in ("recommended", "full"):
        with_agent_refs = (
            profile == "full"
            and (enabled_kinds is None or "agent" in enabled_kinds)
        )
        ledger, mirror_report = _install_skill_mirrors(
            home, ledger, hosts, enabled_kinds, with_agent_refs)
        written = mirror_report["present"]
        skipped = mirror_report["skipped"]
        migrated = mirror_report["migrated"]
        detached = mirror_report["detached"]
        skill_entries = mirror_report["entries"]
        kind_bytes = mirror_report["kind_bytes"]
        written_bytes = mirror_report["written_bytes"]
    if agent_bytes:
        kind_bytes["agent"] = kind_bytes.get("agent", 0) + agent_bytes
    written_bytes += agent_written_bytes
    save_ledger(state, ledger)
    out = {"status": "ok",
           "managed_files": [f["path"] for f in ledger["files"]],
           "host_files": report, "skill_mirrors": written,
           "mcp": outcome,
           "file_actions": file_actions,
           "file_notes": file_notes,
           "skill_entries": skill_entries,
           "kind_bytes": kind_bytes,
           "written_bytes": written_bytes}
    if outcome in ("created", "updated", "unchanged"):
        out["mcp_action"] = outcome
    if skipped:
        out["foreign_preserved"] = skipped
    if migrated:
        out["knowledge_migrated"] = migrated
    if detached:
        out["knowledge_detached"] = detached
    return out


def status(*, scope: str = "project", root: Path | None = None) -> dict[str, Any]:
    from sparkforge_azure.distribution import service as dist
    from sparkforge_azure.install import lifecycle

    target = _resolve(scope, root)
    doc = dist.status(target)
    level = doc.get("status", "uninitialized")
    healthy = level == "initialized"
    drifted = level in ("drifted", "partial", "broken")
    out = {
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
    out["lifecycle"] = lifecycle.health_block(out)
    return out


def doctor(*, scope: str = "project", root: Path | None = None) -> dict[str, Any]:
    from sparkforge_azure.distribution import service as dist
    from sparkforge_azure.install import lifecycle

    target = _resolve(scope, root)
    doc = dist.doctor(target)
    # Advisory findings stay honest UNVERIFIED, never FAIL: host detection
    # is local/advisory (absence never fails a lifecycle verb), and the
    # identity-manifest areas are discovery-optional — a project install
    # never ships `workspace.yaml`, so its absence is not drift. Real
    # `warn`s (managed-asset drift, unwritable state, broken runtime)
    # still degrade health.
    _ADVISORY = ("host:", "workspace", "project_identity")

    def _dist_status(c: dict[str, Any]) -> str:
        st = str(c.get("status"))
        if st == "ok":
            return "PASS"
        area = str(c.get("area", ""))
        if st == "unresolved" or any(
            area == a or area.startswith(a)
            for a in _ADVISORY
        ):
            return "UNVERIFIED"
        return "FAIL"

    checks = [{"id": f"dist:{c.get('area', '?')}",
               "status": _dist_status(c),
               "detail": str(c.get("detail", ""))}
              for c in doc.get("checks", [])]
    if not checks:
        checks = [{"id": "doctor",
                   "status": "UNVERIFIED",
                   "detail": "no checks reported"}]
    checks.append(kit.mcp_verify(_spec()))
    failed = any(c["status"] == "FAIL" for c in checks)
    # Honest state (forge/InstallLifecycle/v1): with no managed-asset
    # evidence at this scope there is nothing to verify — `unverified`,
    # never a fabricated `degraded`/`healthy` verdict.
    from sparkforge_azure.distribution.managed import load_ledger

    installed = bool(
        load_ledger(_state_dir(scope, target)).get("files")
    )
    out = {
        "schema": kit.SCHEMA_HEALTH, "forge_id": FORGE_ID,
        "status": ("unverified" if not installed
                   else "degraded" if failed else "healthy"),
        "target_root": str(target), "checks": checks,
        "distribution": doc,
        "checked_at": kit._utc_now(),
        "repair_hint": "sparkforge-azure install repair" if failed else None,
    }
    out["lifecycle"] = lifecycle.health_block(out)
    return out


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
    # Converge para a selecao persistida (components.json) quando existe —
    # um install com `--components skills` nao deve ganhar agents/knowledge
    # no repair; sem o arquivo o plano e o default recommended.
    saved_opts: dict[str, Any] = {}
    cj = kit.components_path(state)
    if cj.is_file():
        try:
            loaded = json.loads(cj.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                saved_opts = loaded
        except (OSError, ValueError):
            saved_opts = {}
    saved_kinds = (
        set(saved_opts["asset_kinds"]) if saved_opts.get("asset_kinds")
        else None
    )
    saved_gw = saved_opts.get("execution_profile")
    with kit.acquire_lock(state):
        if scope == "user":
            _install_user(
                target, HOSTS, "recommended", saved_kinds, saved_gw)
        else:
            # include_markers=False: markers legados sao convergidos pela
            # camada forge_context (repair_docs abaixo); reescreve-los aqui
            # recriaria o drift que estamos removendo (lf-0036). Repair e
            # convergencia da instalacao existente: mantem a identidade e
            # nao restringe hosts — o alvo e o plano persistido.
            dist.initialize(
                target,
                with_mirrors=False,
                include_markers=False,
                execution_profile=saved_gw,
                enabled_kinds=saved_kinds,
                mint_identity=(scope == "project"),
            )
            from sparkforge_azure.distribution.managed import (
                load_ledger,
                save_ledger,
            )
            _drop_stale_doc_entries(state, target)
            ledger = load_ledger(state)
            ledger, _mirror_report = _install_skill_mirrors(
                target, ledger, HOSTS, saved_kinds,
                include_agent_refs=(
                    saved_kinds is not None and "agent" in saved_kinds))
            save_ledger(state, ledger)
            # same §7.4 fixpoint as install(): the dist receipt snapshots
            # `managed_files` before the mirror layer ledgers its files.
            _refresh_distribution_receipt(state)
        after = [a for a in assess_ledger(state) if a["state"] != "present"]
        # Registry de contexto + consumer docs: re-assert dos blocos
        # `forge:*` a partir dos manifests em `.forge/context/`; recusa
        # nomeada vira check. Escopo user tem target=~ e nunca registra
        # contexto — as ops criariam `~/.forge/context/` à toa, então só
        # rodam em project e quando há resíduo de contexto.
        docs_check: dict[str, Any] | None = None
        ctx_check: dict[str, Any] | None = None
        if scope != "user" and _docs_leftovers(target):
            try:
                out_ctx = fctx.repair_context(target)
                rec = out_ctx.get("recovered")
                ctx_check = {
                    "id": "context-registry",
                    "status": "PASS",
                    "detail": (
                        f"{out_ctx['status']} "
                        f"({len(out_ctx['written'])} writes)"
                        + (f"; recovered {rec['op']}:{rec['forge_id']}" if rec else "")
                        + ("; stale lock reclaimed" if out_ctx.get("lock_recovered") else "")
                    ),
                }
            except fctx.ContextError as exc:
                ctx_check = {
                    "id": "context-registry",
                    "status": "BLOCKED",
                    "detail": f"{exc.kind}: {exc.detail}",
                }
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
    if ctx_check is not None:
        checks.append(ctx_check)
    if docs_check is not None:
        checks.append(docs_check)
    receipt = _receipt(
        "repair", scope, target,
        status="completed" if not after else "failed",
        checks=checks,
        extra={"repaired": [a["path"] for a in before
                            if a["path"] not in {b["path"] for b in after}]})
    kit._write_receipt(state, receipt)
    return receipt


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
            checks += _unregister_context(target)
        return _receipt(
            "uninstall", scope, target,
            status="failed" if any(c.get("status") == "BLOCKED" for c in checks) else "completed",
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
            context_checks = _unregister_context(target)
    ctx_blocked = any(c.get("status") == "BLOCKED" for c in context_checks)
    receipt = _receipt(
        "uninstall", scope, target,
        status="planned" if dry_run else "failed" if ctx_blocked else "completed",
        checks=[{"id": "uninstall", "status": "PASS",
                 "detail": f"{len(removed)} removed, "
                           f"{len(out.get('preserved', []))} preserved"}]
        + context_checks,
        extra={"dry_run": dry_run, "removed": removed,
               "kept": out.get("preserved", []),
               "warnings": out.get("warnings", [])})
    # Canonical parity: detach receipts persist only when state is not
    # purged — writing one under a purged `.sparkforge-azure/` would
    # resurrect the state dir uninstall just removed.
    state = _state_dir(scope, target)
    if not dry_run and not purge and state.exists():
        kit._write_receipt(state, receipt)
    return receipt


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
# `<!-- sparkforge-azure:begin -->`; os ciclos lf-0035–0039 escreviam
# `<!-- forge:sparkforge-azure:begin -->` sob o id sem hifen);
# `install_docs` os remove ao convergir para o contrato `forge:<tag>`.
_LEGACY_DOC_TAGS: tuple[str, ...] = (
    "sparkforge-azure",
    "forge:sparkforge-azure",
)

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


def _bundled_json(name: str) -> dict[str, Any] | None:
    """Manifesto JSON do pacote/checkout — ordem: `_data/` do wheel e a
    raiz do repo (checkout/editable)."""
    for cand in (_PKG_DIR / "_data" / name, _REPO_DIR / name):
        data = kit._load_json(cand, None)
        if isinstance(data, dict):
            return data
    return None


def _context_manifest(
    *, scope: str, profile: str, hosts: list[str],
    components: dict[str, Any] | None,
) -> dict[str, Any]:
    """Manifesto forge/context/v1 montado das fontes reais: `forge.json` +
    `forge.agentic.json` + `manifest.json` no checkout e os grupos de
    assets que o install usou."""
    forge_json = _bundled_json("forge.json")
    agentic = _bundled_json("forge.agentic.json")

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
    # §7.1 (lf-0038): a classificacao NAO vem do varrimento de `evals/` —
    # ela e a tabela declarada de `sparkforge_azure.evals.taxonomy`, que
    # cobre as 4 categorias do enum EVAL_KINDS e marca as suites seladas.
    # Suites novas entram na tabela; `evals describe <id>` e o command que
    # o manifesto publica para cada uma.
    import importlib

    _evals_taxonomy = importlib.import_module("sparkforge_azure.evals.taxonomy")

    eval_suites = _evals_taxonomy.manifest_suites("sparkforge-azure")

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
        kind="specialist",
        agentic=agentic,
        domains=_AZURE_DOMAINS,
        skills=skills,
        coordinators=("coordinator",) if "coordinator" in agent_ids else (),
        agents=agent_ids,
        rule_areas=rule_areas,
        knowledge_providers=providers,
        eval_suites=eval_suites,
        # As mesmas seis capabilities que `build_manifest` montaria por
        # default — declaradas aqui porque `evals` ganha `detail`: o resumo
        # §7.1 das categorias + a postura §7.3 (gabarito selado, prova
        # deterministica != ambiente real).
        capabilities={
            "skills": fctx._capability_doc(
                bool(skills), discovery="workspace-file", count=len(skills)
            ),
            "agents": fctx._capability_doc(
                bool(agent_ids),
                discovery="workspace-file",
                # mesmo default de build_manifest: agents + coordinators
                count=len(agent_ids) + (1 if "coordinator" in agent_ids else 0),
            ),
            "knowledge": fctx._capability_doc(
                bool(providers), discovery="native-runtime", count=len(providers)
            ),
            "rules": fctx._capability_doc(
                bool(rule_areas), discovery="native-runtime", count=len(rule_areas)
            ),
            "evals": fctx._capability_doc(
                bool(eval_suites),
                discovery="cli",
                count=len(eval_suites),
                detail=_evals_taxonomy.capability_detail(),
            ),
            "protocols": fctx._capability_doc(True, discovery="bundled", count=3),
        },
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
            # §7.2 (lf-0038): evals.list/describe/run/result +
            # verification.plan/run. `discovery.ops` e vocabulario fechado
            # do §6.2 — os ops do §7.2 entram como commands nomeados.
            *discovery_ops.eval_commands(),
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
        recorded_by=FORGE_ID,
    )


def _sweep_legacy_forge_ids(target: Path) -> list[str]:
    """Unregister registry identities this forge shipped under before the
    canonical id landed (see ``_LEGACY_FORGE_IDS``). Returns swept ids.

    Runs BEFORE the install/uninstall transaction so the sweep and the
    real op never share a lock — each ``unregister_forge`` is its own
    journaled unit. Absent entries are a no-op; a stale capability file
    without a registry entry is reclaimed the same way.
    """
    reg = fctx.load_registry(target)
    present = {e.get("forge_id") for e in (reg or {}).get("forges", [])}
    swept: list[str] = []
    for legacy in _LEGACY_FORGE_IDS:
        if legacy == FORGE_ID:
            continue
        if legacy in present or fctx.capability_path(target, legacy).exists():
            fctx.unregister_forge(target, legacy, owner=legacy)
            swept.append(legacy)
    return swept


def _installation_manifest() -> dict[str, Any]:
    path = kit.installations_dir() / f"{FORGE_ID}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _register(target: Path) -> None:
    """Atualiza `~/.forge/installations/spark-forge-azure.json` quando o
    bootstrap ja o escreveu (o runtime instalado e a autoridade); senao,
    grava um manifesto minimo apontando para o estado do projeto."""
    existing = _installation_manifest()
    doc = dict(existing) if existing else {}
    doc.update(
        {
            "schema": kit.SCHEMA_MANIFEST,
            "forge_id": FORGE_ID,
            "package": "sparkforge_azure",
            "distribution": "sparkforge-azure",
            "cli": {
                **(existing.get("cli") or {}),
                "name": "sparkforge-azure",
                "version_cmd": ["sparkforge-azure", "--version"],
            },
            "version": __version__,
            "updated_at": kit._utc_now(),
            "installed_at": doc.get("installed_at", kit._utc_now()),
            "installed_by": doc.get(
                "installed_by",
                {"agent": "sparkforge-azure-cli", "version": __version__},
            ),
            "source": doc.get(
                "source", {"kind": "project-install", "path": str(target)}
            ),
        }
    )
    doc.setdefault("install_root", str(kit.installs_root() / FORGE_ID))
    doc.setdefault(
        "mcp",
        {
            "server_name": "sparkforge-azure",
            "command": ["sparkforge-azure", "mcp", "serve"],
            "verify_tool": "sfa_version",
            "verified": False,
        },
    )
    doc.update(_declared_install_fields())
    kit.register_installation(doc)


def _declared_install_fields() -> dict[str, Any]:
    """As declaracoes install-2.1 do `forge.json` deste forge — copiadas
    verbatim para o manifesto registrado, nunca fabricadas (espelha o
    passo `register` do `forge_bootstrap`):

    - ``installation_kind``: ``content``|``service``|``control-tool`` —
      a classe que o plano consolidado usa na ordenacao estavel.
    - ``install``: a superficie declarada (operations/flags/hosts/scopes/
      profiles/approval) — o argv builder do orquestrador so envia o que
      esta declarado; ausente, o manifesto fica no default v1.
    - ``depends_on``: forge_ids que devem instalar antes — declarado
      mesmo quando vazio (``[]``): o plano consolidado le a presenca da
      chave como declaracao explicita, nao como ausencia de dado.
    """
    cfg = _bundled_json("forge.json")
    if not cfg:
        return {}
    from sparkforge_azure.distribution.errors import PortableError

    doc: dict[str, Any] = {}
    if cfg.get("installation_kind"):
        kind = str(cfg["installation_kind"])
        if kind not in kit.INSTALLATION_KINDS:
            raise PortableError(
                kit.E_UNSUPPORTED,
                f"forge.json installation_kind {kind!r} — expected "
                f"{kit.INSTALLATION_KINDS}",
            )
        doc["installation_kind"] = kind
    if cfg.get("install"):
        doc["install"] = dict(cfg["install"])
    if "depends_on" in cfg:
        doc["depends_on"] = [str(d) for d in cfg["depends_on"]]
    return doc


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
    ROUTING.md + consumer docs, numa UNICA transacao (install-2.0 §9.2:
    preflight → lock → conflicts → backup → write → verify → commit,
    rollback em falha). Falha vira check BLOCKED nomeado no recibo.
    Escopo user tem target=~: `~/.forge/` e nivel de conta; contexto de
    workspace nao se escreve la — senao o uninstall (que pul user-scope)
    orfa a entrada no registry."""
    if scope == "user":
        return
    try:
        manifest = _context_manifest(
            scope=scope, profile=profile, hosts=hosts, components=components
        )
        # Consumer docs (AGENTS.md/CLAUDE.md/AGENT_PROTOCOL.md) so existem
        # em escopo de projeto/workspace — user-scope escreve assets sob ~
        # e ja traz os markers legados via install_host_assets.
        swept = _sweep_legacy_forge_ids(target)
        out = fctx.install_transaction(
            target, manifest, owner=FORGE_ID,
            legacy_tags=_LEGACY_DOC_TAGS,
        )
        if swept:
            receipt.setdefault("checks", []).append(
                {
                    "id": "context-registry-legacy-sweep",
                    "status": "PASS",
                    "detail": f"stale registry ids reclaimed: {swept}",
                }
            )
        receipt.setdefault("checks", []).append(
            {
                "id": "context-registry",
                "status": "PASS",
                "detail": f".forge/context {out['status']} "
                f"({len(out['written'])} writes)",
            }
        )
        docs = out["docs"]
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
            {"id": "context-registry", "status": "BLOCKED",
             "detail": f"{exc.kind}: {exc.detail}"}
        )
        # BLOCKED num componente mandatório não sai exit 0 — os assets
        # foram escritos mas o contrato install-2.0 falhou.
        receipt["status"] = "failed"


def _unregister_context(target: Path) -> list[dict[str, Any]]:
    """Remove manifesto/entry/blocos `forge:*` deste forge numa UNICA
    transacao (§9.2) — só artifacts próprios: nosso capability file, nossa
    entrada no registry, nossos blocos; docs compartilhados regeneram
    para os sobreviventes."""
    try:
        _sweep_legacy_forge_ids(target)
        out = fctx.uninstall_transaction(
            target, FORGE_ID, owner=FORGE_ID, legacy_tags=_LEGACY_DOC_TAGS
        )
        docs = out["docs"]
        return [
            {
                "id": "context-registry",
                "status": "PASS",
                "detail": f".forge/context {out['status']}",
            },
            {
                "id": "consumer-docs",
                "status": "PASS",
                "detail": f"{docs['status']}: {len(docs['written'])} changed",
            },
        ]
    except fctx.ContextError as exc:
        return [
            {
                "id": "context-registry",
                "status": "BLOCKED",
                "detail": f"{exc.kind}: {exc.detail}",
            }
        ]


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

