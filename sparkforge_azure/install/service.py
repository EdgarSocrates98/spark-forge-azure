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

from sparkforge_azure import __version__
from sparkforge_azure import _installkit as kit

FORGE_ID = "sparkforge-azure"
PROFILES: tuple[str, ...] = ("minimal", "recommended", "full")
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


def _install_skill_mirrors(
    root: Path, ledger: dict[str, Any], hosts: tuple[str, ...],
) -> tuple[dict[str, Any], list[str]]:
    """Write ``sparkforge-azure-<name>/SKILL.md`` mirrors into the selected
    host roots, ledgered like every other managed asset."""
    from sparkforge_azure.distribution.managed import record_file
    from sparkforge_azure.durable import write_atomic
    from sparkforge_azure.skills.mirrors import mirror_name, render_mirror

    written: list[str] = []
    for skill_name, text in _skill_sources():
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
        out.append(".sparkforge-azure/project.yaml")
    if "claude" in hosts or (target / "CLAUDE.md").exists():
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
            components: tuple[str, ...] | None = None) -> dict[str, Any]:
    """``sparkforge-azure install`` — governed apply over ``initialize``."""
    from sparkforge_azure.distribution import service as dist
    from sparkforge_azure.distribution.errors import PortableError

    if profile not in PROFILES:
        raise PortableError(
            kit.E_PROFILE, f"profile {profile!r}; expected {PROFILES}")
    hosts = HOSTS if host == "all" else (host,)
    if host != "all" and host not in HOSTS:
        raise PortableError(kit.E_HOST, f"host {host!r}; expected {HOSTS} + all")
    target = _resolve(scope, root)
    state = _state_dir(scope, target)
    opts = kit.component_options("recommended", components)

    if dry_run:
        return _receipt(
            "install", scope, target, status="planned",
            checks=[{"id": "plan", "status": "UNVERIFIED",
                     "detail": "dry-run — nothing written"}],
            managed_files=[],
            extra={"dry_run": True,
                   "components": opts or None,
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
            doc = dist.initialize(target, with_mirrors=(profile == "full"))
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
    return _receipt(
        "install", scope, target,
        status="completed" if ok else "failed",
        checks=[{"id": "apply", "status": "PASS" if ok else "FAIL",
                 "detail": f"{len(doc.get('managed_files', []))} managed files"}],
        managed_files=doc.get("managed_files", []),
        extra={"components": opts or None,
               "distribution": {k: v for k, v in doc.items()
                                if k not in ("managed_files",)}})


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
            dist.initialize(target, with_mirrors=False)
            from sparkforge_azure.distribution.managed import (
                load_ledger,
                save_ledger,
            )
            ledger = load_ledger(state)
            ledger, _w = _install_skill_mirrors(target, ledger, HOSTS)
            save_ledger(state, ledger)
        after = [a for a in assess_ledger(state) if a["state"] != "present"]
    return _receipt(
        "repair", scope, target,
        status="completed" if not after else "failed",
        checks=[{"id": "repair",
                 "status": "PASS" if not after else "FAIL",
                 "detail": f"{len(before)} drifted, {len(after)} remaining"}],
        extra={"repaired": [a["path"] for a in before
                            if a["path"] not in {b["path"] for b in after}]})


def uninstall(*, scope: str = "project", root: Path | None = None,
              purge: bool = False, dry_run: bool = False) -> dict[str, Any]:
    from sparkforge_azure.distribution import detach as detach_service

    target = _resolve(scope, root)
    if not _state_dir(scope, target).exists() and not dry_run:
        return _receipt(
            "uninstall", scope, target, status="completed",
            checks=[{"id": "uninstall", "status": "PASS",
                     "detail": "0 removed, 0 kept — nothing installed"}],
            extra={"removed": [], "kept": []})
    out = detach_service.detach(
        target, dry_run=dry_run, purge_state=purge, purge_cache=False)
    removed = [d["path"] for d in out.get("detached", [])
               if d.get("action") not in ("preserved_state", "absent")]
    if not dry_run:
        kit._prune_empty_dirs(target, removed)
    return _receipt(
        "uninstall", scope, target,
        status="planned" if dry_run else "completed",
        checks=[{"id": "uninstall", "status": "PASS",
                 "detail": f"{len(removed)} removed, "
                           f"{len(out.get('preserved', []))} preserved"}],
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
