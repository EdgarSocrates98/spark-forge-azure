"""Resolução de contexto com escopo de workspace (P0-D — §48–§64).

`context resolve` responde "qual contexto deste workspace é relevante para
este target?" em três camadas já existentes:

1. `workspace.reachable` decide *quais projetos* entram — só o que a
   declaração autoriza (§64: dependência declarada ou `all` explícito).
2. `scan_repository` enumera os arquivos de cada projeto com a política
   bounded do kernel (deny_names, max_file_bytes, sem symlinks).
3. `TokenSave.context` (quando `--task` é dado) anda a escada L0→L6 por
   projeto, confinado à raiz dele, com orçamento e ledger de bytes.

O recibo (§58) registra considered/selected, files/bytes materializados e o
`stop_reason` — e vive em `receipt-context.json` no state dir do chamador.
Nenhum projeto lê arquivo de outro: cada `TokenSave` é confinado por
`resolve_within` à própria raiz.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.distribution.discovery import discover
from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.distribution.identity import (
    codeintel_db,
    project_cache_dir,
    receipt_namespace,
)
from sparkforge_azure.distribution.manifests import (
    load_workspace_manifest,
    resolve_declared_path,
)
from sparkforge_azure.distribution.paths import resolve_paths
from sparkforge_azure.distribution.workspace import reachable
from sparkforge_azure.durable import write_atomic
from sparkforge_azure.paths import scan_repository
from sparkforge_azure.tokensave import TokenSave

SCOPES = ("target", "direct", "transitive", "all")
PROFILES = ("economy", "balanced", "deep")
RECEIPT_NAME = "receipt-context.json"


def _resolve_target(ws, ws_root: Path, ref: str | None) -> str:
    """--target aceita id ou path; default cai em default_target."""
    if ref is None:
        if ws.default_target:
            return ws.default_target
        raise PortableError(
            "project_not_initialized",
            "no --target and the workspace has no default_target",
            unlock="pass --target <id|path> or `workspace init` a host project",
        )
    if ws.project(ref) is not None:
        return ref
    candidate = Path(ref).expanduser()
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()
    for p in ws.projects:
        try:
            if resolve_declared_path(p.path, ws_root) == candidate:
                return p.id
        except PortableError:
            continue
    raise PortableError(
        "workspace_not_found",
        f"target {ref!r} is not a declared project (id or path)",
        unlock="`workspace add` the project or pick an id from `workspace status`",
    )


def context_resolve(
    root: Path | str | None = None,
    *,
    target: str | None = None,
    scope: str = "target",
    task: str = "",
    profile: str = "economy",
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve o contexto do target no escopo dado; emite recibo §58."""
    if scope not in SCOPES:
        raise PortableError(
            "config_invalid",
            f"unknown scope {scope!r}",
            unlock=f"scope: {'|'.join(SCOPES)}",
        )
    if profile not in PROFILES:
        raise PortableError(
            "config_invalid",
            f"unknown economy profile {profile!r}",
            unlock=f"profile: {'|'.join(PROFILES)}",
        )
    base = Path(root).expanduser().resolve() if root else Path.cwd().resolve()
    found = discover(base)
    if found.workspace_manifest is None:
        raise PortableError(
            "workspace_not_found",
            f"no .sparkforge-azure/workspace.yaml found at or above {base}",
            unlock="`sparkforge-azure workspace init` at the workspace root",
        )
    ws = load_workspace_manifest(found.workspace_manifest)
    ws_root = found.workspace_root
    assert ws_root is not None
    target_id = _resolve_target(ws, ws_root, target)
    selected = sorted(reachable(ws, target_id, scope=scope))
    considered = sorted(p.id for p in ws.projects)

    projects: list[dict[str, Any]] = []
    unresolved: list[str] = []
    files_considered = 0
    files_materialized: set[str] = set()
    bytes_read = 0
    bytes_scanned = 0
    stop_reasons: list[str] = []

    for pid in selected:
        decl = ws.project(pid)
        assert decl is not None  # reachable() só devolve ids declarados
        proj_root = resolve_declared_path(decl.path, ws_root)
        entry: dict[str, Any] = {
            "id": pid,
            "role": decl.role,
            "root": str(proj_root),
        }
        if not proj_root.is_dir():
            entry["status"] = "unresolved_path"
            unresolved.append(pid)
            projects.append(entry)
            continue

        # Raízes por-projeto: env-compartilhadas → namespace por id lógico
        # (W3); sem env → o .sparkforge-azure do próprio projeto (§62–§63).
        pp = resolve_paths(cwd=proj_root, env=env)
        scan = scan_repository(proj_root)
        entry["files_considered"] = len(scan.files)
        files_considered += len(scan.files)
        scanned_bytes = 0
        for f in scan.files:
            try:
                scanned_bytes += f.stat().st_size
            except OSError:
                pass
        bytes_scanned += scanned_bytes

        if task:
            ts = TokenSave(
                proj_root,
                profile_name=profile,
                index_db=codeintel_db(pp, pid),
                cache_dir=project_cache_dir(pp, pid, workspace_id=ws.workspace_id),
            )
            result = ts.context(task)
            items = [i if isinstance(i, dict) else {"item": i} for i in result.items]
            entry["items"] = items
            entry["stop_reason"] = result.stop_reason
            entry["levels"] = list(result.levels_used)
            entry["status"] = result.status
            stop_reasons.append(result.stop_reason)
            led = result.ledger
            entry["bytes_read"] = led.get("payload_bytes", 0)
            bytes_read += entry["bytes_read"]
            for i in items:
                if "path" in i:
                    files_materialized.add(f"{pid}:{i['path']}")
        else:
            entry["status"] = "resolved"

        projects.append(entry)

    overall_stop = (
        "scope_complete"
        if not stop_reasons
        else ("partial" if any(r != "STOP_SUFFICIENT" for r in stop_reasons) else "sufficient")
    )
    receipt = {
        "version": 1,
        **receipt_namespace(target_id, ws.workspace_id, scope=scope),
        "target": target_id,
        "scope": scope,
        "profile": profile,
        "task": task or None,
        "projects_considered": considered,
        "projects_selected": [p["id"] for p in projects],
        "files_considered": files_considered,
        "files_materialized": len(files_materialized),
        "bytes_read": bytes_read,
        "bytes_avoided": max(0, bytes_scanned - bytes_read),
        "stop_reason": overall_stop,
        "unresolved": unresolved,
    }
    caller_paths = resolve_paths(cwd=base, env=env)
    receipt_path = caller_paths.state_root / RECEIPT_NAME
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(
        receipt_path,
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
    )
    return {
        "status": "ok" if not unresolved else "partial",
        **receipt,
        "receipt": str(receipt_path),
        "projects": projects,
    }
