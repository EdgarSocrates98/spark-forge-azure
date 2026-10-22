"""Canonical portable-distribution operations (spec §10–§19, §109–§113).

Each public function backs one CLI verb and returns a plain JSON-ready
mapping — one document per command (§180). The layer never touches the cloud
and never reads undeclared paths; every write goes through the managed
ledger so it can be reversed by ``detach``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sparkforge_azure import __version__
from sparkforge_azure.distribution.assets import asset_inventory, asset_summary
from sparkforge_azure.distribution.config import resolve_config
from sparkforge_azure.distribution.discovery import (
    STATE_DIR_NAME,
    discover,
)
from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.distribution.hostfiles import install_host_assets
from sparkforge_azure.distribution.hosts import (
    MCP_SERVER_NAME,
    detect_hosts,
    mcp_entry,
)
from sparkforge_azure.distribution.identity import (
    codeintel_db,
    project_cache_dir,
    project_state_dir,
)
from sparkforge_azure.distribution.managed import (
    apply_json_key,
    assess_ledger,
    load_ledger,
    record_file,
    save_ledger,
)
from sparkforge_azure.distribution.manifests import (
    ProjectIdentity,
    init_project_identity,
    load_project_identity,
    load_workspace_manifest,
    new_project_id,
    resolve_declared_path,
    write_project_identity,
)
from sparkforge_azure.distribution.paths import resolve_paths
from sparkforge_azure.durable import write_atomic

RECEIPT_NAME = "receipt-distribution.json"


def _writable(path: Path) -> bool:
    if path.exists():
        return os.access(path, os.W_OK)
    return os.access(path.parent if path.parent.exists() else path.parent.parent, os.W_OK)


def _project_or_none(root: Path) -> tuple[Path, ProjectIdentity] | None:
    found = discover(root)
    if found.project_manifest is None:
        return None
    try:
        return found.project_manifest.parent.parent.resolve(), load_project_identity(
            found.project_manifest
        )
    except PortableError:
        return None


def _workspace_or_none(root: Path) -> tuple[Path, Any] | None:
    found = discover(root)
    if found.workspace_manifest is None:
        return None
    try:
        return found.workspace_manifest.parent.parent.resolve(), load_workspace_manifest(
            found.workspace_manifest
        )
    except PortableError:
        return None


# ---------------------------------------------------------------------------
# inspect (§11) — everything, no mutation
# ---------------------------------------------------------------------------


def inspect(root: Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd()).resolve()
    found = discover(base)
    project = _project_or_none(base)
    workspace = _workspace_or_none(base)
    paths = resolve_paths(
        cwd=base,
        project_root=found.project_root,
        workspace_root=found.workspace_root,
    )
    effective = resolve_config(
        user_config_path=paths.config_path,
        workspace_config=workspace[1].config if workspace else None,
        project_config=project[1].config if project else None,
        strict=False,
    )
    return {
        "status": "ok",
        "version": __version__,
        "paths": paths.to_dict(),
        "discovery": {
            "repository_root": str(found.repository_root)
            if found.repository_root
            else None,
            "project_manifest": str(found.project_manifest)
            if found.project_manifest
            else None,
            "workspace_manifest": str(found.workspace_manifest)
            if found.workspace_manifest
            else None,
            "evidence": list(found.evidence),
        },
        "project": project[1].to_dict() if project else None,
        "workspace": workspace[1].to_dict() if workspace else None,
        "namespaces": {
            "state_dir": str(
                project_state_dir(paths, project[1].project_id)
            )
            if project
            else None,
            "cache_dir": str(
                project_cache_dir(
                    paths,
                    project[1].project_id,
                    workspace_id=workspace[1].workspace_id if workspace else None,
                )
            )
            if project
            else None,
            "codeintel_db": str(codeintel_db(paths, project[1].project_id))
            if project
            else None,
        },
        "config": {
            "effective": effective["config"],
            "sources": effective["sources"],
            "unknown_keys": effective["unknown_keys"],
        },
        "assets": asset_summary(),
        "hosts": list(detect_hosts()),
        "capabilities": _capabilities(project is not None, workspace is not None),
        "limitations": [
            "host detection observes PATH only; host behavior is not probed",
            "hashes are integrity markers, not signatures",
        ],
    }


def _capabilities(project: bool, workspace: bool) -> dict[str, bool]:
    """Public capability flags for Forger-style consumers (§170–§172)."""
    return {
        "portable_distribution": True,
        "forge_workspace": True,
        "context_resolution": True,
        "detach_safe": True,
        "project_initialized": project,
        "workspace_initialized": workspace,
    }


# ---------------------------------------------------------------------------
# init (§12–§13) — managed writes only, idempotent
# ---------------------------------------------------------------------------


def initialize(
    root: Path | None = None,
    *,
    name: str | None = None,
    regen_id: bool = False,
    with_mirrors: bool = False,
    include_markers: bool = True,
) -> dict[str, Any]:
    """Initialize portable identity + local integration for ``root``.

    Idempotent (§13): a second run keeps the same ``project_id`` and rewrites
    only managed assets. ``regen_id`` (§43) explicitly mints a new identity
    for a copied project — recorded in the receipt, never silent.
    """
    base = Path(root or Path.cwd()).resolve()
    found = discover(base)
    created: list[str] = []
    kept: list[str] = []
    warnings: list[str] = []

    if found.project_manifest is not None and found.project_root != base:
        raise PortableError(
            "path_outside_root",
            f"a project.yaml already exists at {found.project_root}; "
            "run init inside it or from its root",
            unlock=f"cd {found.project_root} or pass --root {found.project_root}",
        )

    existing = _project_or_none(base)
    if existing and not regen_id:
        identity = existing[1]
        kept.append("project_id")
    elif existing and regen_id:
        previous = existing[1]
        identity = ProjectIdentity(
            project_id=new_project_id(),
            name=previous.name,
            created=previous.created,
            generator=f"sparkforge-azure {__version__}",
            config=previous.config,
        )
        write_project_identity(base, identity)
        created.append("project_id_regenerated")
        warnings.append(f"previous project_id {previous.project_id} superseded")
    else:
        identity = init_project_identity(base, name=name)
        created.append("project.yaml")

    state = base / STATE_DIR_NAME
    ledger = load_ledger(state)

    # Local MCP integration for every MCP-capable declared host (§72–§75):
    # one shared .mcp.json at the project root, one owned key inside it.
    mcp_path = base / ".mcp.json"
    host_configs: list[dict[str, Any]] = []
    try:
        ledger, outcome = apply_json_key(
            mcp_path,
            f"mcpServers.{MCP_SERVER_NAME}",
            mcp_entry(),
            ledger=ledger,
            kind="mcp_config",
        )
        if outcome == "written":
            host_configs.append(
                {"file": str(mcp_path), "key": f"mcpServers.{MCP_SERVER_NAME}",
                 "state": "managed"}
            )
        else:
            host_configs.append(
                {"file": str(mcp_path), "key": f"mcpServers.{MCP_SERVER_NAME}",
                 "state": "conflict_preserved",
                 "detail": "existing mcpServers.sparkforge-azure entry kept; not ours"},
            )
            warnings.append(
                ".mcp.json has an unmanaged sparkforge-azure entry; left untouched"
            )
    except ValueError as exc:
        warnings.append(f".mcp.json not written: {exc}")

    # Host contracts (§65–§71): managed marker blocks in AGENTS.md always
    # and CLAUDE.md when the host is around; mirrors are opt-in bulk.
    # `include_markers=False` (install path): the forge_context docs layer
    # owns the `forge:*` blocks there — no double generation of markers.
    detected = tuple(
        h["name"] for h in detect_hosts() if h["status"] == "available"
    )
    ledger, host_files = install_host_assets(
        base,
        ledger,
        hosts=detected,
        with_mirrors=with_mirrors,
        write_markers=include_markers,
    )

    ledger = record_file(
        ledger,
        state / "project.yaml",
        kind="project_manifest",
    )
    workspace = _workspace_or_none(base)
    receipt = {
        "version": 1,
        "project_id": identity.project_id,
        "workspace_id": workspace[1].workspace_id if workspace else None,
        "package_version": __version__,
        "managed_files": [f["path"] for f in ledger["files"]],
        "host_configs": host_configs,
        "asset_count": asset_summary()["asset_count"],
    }
    receipt_path = state / RECEIPT_NAME
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(
        receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    ledger = record_file(ledger, receipt_path, kind="receipt")
    save_ledger(state, ledger)

    return {
        "status": "ok",
        "project_id": identity.project_id,
        "project_root": str(base),
        "created": created,
        "kept": kept,
        "receipt": str(receipt_path),
        "managed_files": [f["path"] for f in ledger["files"]],
        "host_configs": host_configs,
        "host_files": host_files,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# status (§14, §111–§112) — drift-aware, no mutation
# ---------------------------------------------------------------------------


def status(root: Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd()).resolve()
    found = discover(base)
    project = _project_or_none(base)
    workspace = _workspace_or_none(base)
    manifest_errors: list[str] = []
    if found.project_manifest and project is None:
        manifest_errors.append("project.yaml unreadable or invalid")
    if found.workspace_manifest and workspace is None:
        manifest_errors.append("workspace.yaml unreadable or invalid")

    if project is None and workspace is None and not manifest_errors:
        return {
            "status": "uninitialized",
            "project": None,
            "workspace": None,
            "drift": [],
            "unlock": "run `sparkforge-azure distribution init`",
        }

    project_root = project[0] if project else found.project_root
    state = (project_root or base) / STATE_DIR_NAME
    drift = list(assess_ledger(state))

    missing = [d for d in drift if d["state"] == "missing"]
    modified = [d for d in drift if d["state"] == "modified"]
    if manifest_errors:
        level = "broken"
    elif missing:
        level = "partial"
    elif modified:
        level = "drifted"
    else:
        level = "initialized"

    workspace_projects = None
    if workspace:
        ws_root, ws = workspace
        workspace_projects = [
            {
                "id": p.id,
                "role": p.role,
                "exists": resolve_declared_path(p.path, ws_root).is_dir(),
            }
            for p in ws.projects
        ]

    return {
        "status": level,
        "project": {
            "project_id": project[1].project_id,
            "name": project[1].name,
            "root": str(project[0]),
            "config": project[1].config or None,
        }
        if project
        else None,
        "workspace": {
            "workspace_id": workspace[1].workspace_id,
            "name": workspace[1].name,
            "root": str(workspace[0]),
            "projects": workspace_projects,
        }
        if workspace
        else None,
        "drift": drift,
        "manifest_errors": manifest_errors,
        "gaps": manifest_errors
        + [f"missing managed asset: {d['path']}" for d in missing]
        + [f"modified managed asset: {d['path']}" for d in modified],
    }


# ---------------------------------------------------------------------------
# doctor (§15–§16, §174) — offline, never fails on missing hosts/credentials
# ---------------------------------------------------------------------------


def doctor(root: Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd()).resolve()
    found = discover(base)
    paths = resolve_paths(
        cwd=base,
        project_root=found.project_root,
        workspace_root=found.workspace_root,
    )
    checks: list[dict[str, Any]] = []

    def check(area: str, ok: bool, detail: str, **extra: Any) -> None:
        checks.append(
            {"area": area, "status": "ok" if ok else "warn", "detail": detail, **extra}
        )

    try:
        assets = asset_inventory()
        check(
            "package_assets",
            bool(assets),
            f"{len(assets)} packaged assets under sparkforge_azure._data",
            count=len(assets),
        )
    except PortableError as exc:
        check("package_assets", False, exc.detail)

    check(
        "state_dir",
        _writable(paths.state_root),
        str(paths.state_root),
        source=dict(paths.sources).get("state_root", "default"),
    )
    check("cache_dir", _writable(paths.cache_root.parent), str(paths.cache_root))

    project = _project_or_none(base)
    check(
        "project_identity",
        project is not None,
        project[1].project_id if project else "no project.yaml discovered",
        source="discovery",
    )
    workspace = _workspace_or_none(base)
    check(
        "workspace",
        workspace is not None,
        workspace[1].workspace_id if workspace else "no workspace.yaml discovered",
    )

    drift = list(assess_ledger(paths.state_root))
    bad = [d for d in drift if d["state"] != "present"]
    check(
        "managed_assets",
        not bad,
        f"{len(drift)} managed assets, {len(bad)} drifted",
        drift=bad or None,
    )

    for host in detect_hosts():
        checks.append(
            {
                "area": f"host:{host['name']}",
                "status": "ok" if host["status"] == "available" else "unresolved",
                "detail": f"{host['status']} ({host['executable']})",
            }
        )

    mcp_ok = True
    try:
        import importlib.util as _ilu

        mcp_ok = _ilu.find_spec("sparkforge_azure.mcp.server") is not None
    except Exception:
        mcp_ok = False
    check("mcp_runtime", mcp_ok, "sparkforge-azure mcp serve entrypoint")

    worst = "ok"
    if any(c["status"] == "warn" for c in checks):
        worst = "warn"
    return {
        "status": worst,
        "checks": checks,
        "offline": True,
        "azure_auth_required": False,
        "paths": paths.to_dict(),
    }


__all__ = ["doctor", "initialize", "inspect", "status"]
