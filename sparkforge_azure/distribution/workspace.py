"""ForgeWorkspace lifecycle (spec §20–§36): discover/init/add/remove/status.

A ForgeWorkspace is a *logical* grouping of projects (§21) — explicitly
distinct from Azure Workspace / Databricks Workspace / Fabric Workspace. It
is data-only (§114), bounded (§24–§26), deterministic (§34), and offline.

Semantics that matter:

- Projects inside the workspace root are stored as relative paths; projects
  outside are stored absolute — external repositories are *declared*, never
  discovered (§35). Nothing outside the root is touched unless declared.
- Dependencies are declared edges (`dependencies` = direct,
  `optional_dependencies` = optional). `transitive` is derived at read time,
  never written (§30). Business dependencies are never auto-inferred (§33).
- Cycles are detected and surface as `dependency_cycle` — an explicit review
  state, never an infinite recursion (§31–§32).
- `add` initializes a missing portable identity in the target (documented
  and reported via ``initialized_target``); `remove` drops only the
  declaration and the inbound edges — it never deletes a repository (§36).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sparkforge_azure.distribution.discovery import (
    PROJECT_MANIFEST_NAME,
    STATE_DIR_NAME,
    WORKSPACE_MANIFEST_NAME,
    ancestors,
    discover,
)
from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.distribution.managed import load_ledger, record_file, save_ledger
from sparkforge_azure.distribution.manifests import (
    PROJECT_ROLES,
    ProjectDecl,
    WorkspaceDecl,
    init_project_identity,
    init_workspace_manifest,
    load_project_identity,
    load_workspace_manifest,
    resolve_declared_path,
    write_workspace_manifest,
)
from sparkforge_azure.distribution.service import _workspace_or_none

_KEEP = object()  # sentinel: keep the current default_target

#: Breadth bound for candidate suggestion inside a root (§26).
MAX_SUGGESTIONS = 32
#: Depth bound: suggested children are looked at one level below the root.
MAX_CHILD_DEPTH = 2


# ---------------------------------------------------------------------------
# dependency graph — deterministic, finite
# ---------------------------------------------------------------------------


def dependency_edges(
    ws: WorkspaceDecl, *, include_optional: bool = True
) -> dict[str, tuple[str, ...]]:
    """id → declared dependency ids (direct; optional included by default)."""
    return {
        p.id: tuple(
            sorted((*p.dependencies, *(p.optional_dependencies if include_optional else ())))
        )
        for p in ws.projects
    }


def detect_cycles(ws: WorkspaceDecl) -> tuple[tuple[str, ...], ...]:
    """Every elementary cycle over declared edges, sorted for determinism.

    DFS with an explicit in-stack set — bounded by the number of declared
    projects; infinite recursion is impossible by construction (§31).
    """
    edges = dependency_edges(ws)
    cycles: set[tuple[str, ...]] = set()
    stack: list[str] = []
    in_stack: set[str] = set()
    done: set[str] = set()

    def visit(node: str) -> None:
        if node in done:
            return
        if node in in_stack:
            start = stack.index(node)
            cycles.add(tuple(stack[start:]))
            return
        stack.append(node)
        in_stack.add(node)
        for dep in edges.get(node, ()):
            visit(dep)
        stack.pop()
        in_stack.discard(node)
        done.add(node)

    for project in sorted(edges):
        visit(project)
    return tuple(sorted(cycles))


def reachable(
    ws: WorkspaceDecl, target: str, *, scope: str, include_optional: bool = True
) -> tuple[str, ...]:
    """The project set for a locality scope (§56–§60).

    ``target`` → just the target. ``direct`` → target + direct edges.
    ``transitive`` → full closure of declared edges. ``all`` → every
    declared project. Cycles make reachability refuse by name rather than
    loop (§31).
    """
    if ws.project(target) is None:
        raise PortableError(
            "workspace_not_found",
            f"target {target!r} is not a declared project",
            unlock="workspace add the project or check `workspace status`",
        )
    if scope not in {"target", "direct", "transitive", "all"}:
        raise PortableError(
            "config_invalid",
            f"unknown scope {scope!r}",
            unlock="scope: target|direct|transitive|all",
        )
    if scope == "all":
        cycles = detect_cycles(ws)  # still validated — an `all` over a cyclic
        if cycles:  # manifest reports the cycle instead of a silent set
            raise PortableError(
                "dependency_cycle",
                f"workspace has dependency cycles: {[list(c) for c in cycles]}",
                unlock="remove or rewire the edges and retry",
            )
        return tuple(sorted(p.id for p in ws.projects))
    if scope == "target":
        return (target,)
    cycles = detect_cycles(ws)
    if cycles:
        raise PortableError(
            "dependency_cycle",
            f"workspace has dependency cycles: {[list(c) for c in cycles]}",
            unlock="remove or rewire the edges and retry",
        )
    edges = dependency_edges(ws, include_optional=include_optional)
    seen: set[str] = {target}
    frontier = list(edges[target])
    while frontier:
        node = frontier.pop()
        if node in seen:
            continue
        seen.add(node)
        if scope == "transitive":
            frontier.extend(edges.get(node, ()))
        # scope == "direct": direct edges only — frontier never expands
    return tuple(sorted(seen))


# ---------------------------------------------------------------------------
# lifecycle operations
# ---------------------------------------------------------------------------


def _require_workspace(root: Path) -> tuple[Path, WorkspaceDecl]:
    found = _workspace_or_none(root)
    if found is None:
        raise PortableError(
            "workspace_not_found",
            "no .sparkforge-azure/workspace.yaml discovered",
            unlock="run `sparkforge-azure workspace init`",
        )
    return found


def _ensure_project_identity(project_root: Path) -> tuple[str, bool]:
    """Load or create the target's identity; returns (project_id, created)."""
    manifest = project_root / STATE_DIR_NAME / PROJECT_MANIFEST_NAME
    if manifest.is_file():
        try:
            return load_project_identity(manifest).project_id, False
        except PortableError:
            pass
    identity = init_project_identity(project_root)
    return identity.project_id, True


def workspace_init(root: Path | None = None, *, name: str | None = None) -> dict[str, Any]:
    """Create `workspace.yaml` in ``root`` and register the host project.

    Idempotent: a second run keeps the same ``workspace_id`` and reports
    ``kept``. The host project's portable identity is created if absent
    (reported via ``project_initialized``).
    """
    base = Path(root or Path.cwd()).resolve()
    found = discover(base)
    if found.workspace_manifest is not None and found.workspace_root != base:
        raise PortableError(
            "path_outside_root",
            f"a workspace.yaml already exists at {found.workspace_root}",
            unlock=f"cd {found.workspace_root} or pass --root {found.workspace_root}",
        )
    existing = _workspace_or_none(base)
    project_id, created_identity = _ensure_project_identity(base)
    if existing:
        ws_root, ws = existing
        if ws.project(project_id) is None:
            ws = _replace_projects(
                ws_root,
                ws,
                (*ws.projects, ProjectDecl(id=project_id, path=".", role="application")),
                default_target=ws.default_target or project_id,
            )
        return {
            "status": "ok",
            "workspace_id": ws.workspace_id,
            "workspace_root": str(ws_root),
            "kept": ["workspace_id"],
            "project_initialized": created_identity,
            "default_target": ws.default_target,
        }
    ws = init_workspace_manifest(base, name=name)
    ws = _replace_projects(
        base,
        ws,
        (ProjectDecl(id=project_id, path=".", role="application"),),
        default_target=project_id,
    )
    state = base / STATE_DIR_NAME
    ledger = load_ledger(state)
    ledger = record_file(
        ledger, state / WORKSPACE_MANIFEST_NAME, kind="workspace_manifest"
    )
    save_ledger(state, ledger)
    return {
        "status": "ok",
        "workspace_id": ws.workspace_id,
        "workspace_root": str(base),
        "created": [WORKSPACE_MANIFEST_NAME],
        "project_initialized": created_identity,
        "default_target": ws.default_target,
    }


def _replace_projects(
    root: Path,
    ws: WorkspaceDecl,
    projects: tuple[ProjectDecl, ...],
    *,
    default_target: str | None | object = _KEEP,
) -> WorkspaceDecl:
    """Write a new manifest with the given project set; returns reloaded decl."""
    new = WorkspaceDecl(
        workspace_id=ws.workspace_id,
        name=ws.name,
        projects=tuple(sorted(projects, key=lambda p: p.id)),
        default_target=(
            ws.default_target if default_target is _KEEP else default_target
        ),  # type: ignore[arg-type]
        config=ws.config,
        version=ws.version,
    )
    target = write_workspace_manifest(root, new)
    return load_workspace_manifest(target)


def workspace_add(
    root: Path | None,
    path: str,
    *,
    project_id: str | None = None,
    role: str | None = None,
    depends_on: tuple[str, ...] = (),
    optional: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Declare ``path`` as a workspace member. Deterministic and idempotent.

    The target's portable identity is created when absent — the only write
    outside the workspace root, and it is the explicit request of the
    command (reported via ``initialized_target``).
    """
    ws_root, ws = _require_workspace(root or Path.cwd())
    if role is not None and role not in PROJECT_ROLES:
        raise PortableError(
            "manifest_invalid",
            f"unknown role {role!r}",
            unlock=f"roles: {sorted(PROJECT_ROLES)}",
        )
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (ws_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.is_dir():
        raise PortableError(
            "path_outside_root",
            f"{candidate} is not a directory",
            unlock="workspace add takes an existing repository directory",
        )
    pid, initialized_target = _ensure_project_identity(candidate)
    if project_id and project_id != pid:
        raise PortableError(
            "identity_collision",
            f"target already has project_id {pid!r}; requested {project_id!r}",
            unlock="drop --id or regen the target's identity explicitly",
        )
    for dep in (*depends_on, *optional):
        if dep not in {p.id for p in ws.projects} and dep != pid:
            raise PortableError(
                "manifest_invalid",
                f"dependency {dep!r} is not a declared project",
                unlock="workspace add the dependency first",
            )
    same_path = [
        p for p in ws.projects
        if resolve_declared_path(p.path, ws_root) == candidate and p.id != pid
    ]
    if same_path:
        raise PortableError(
            "identity_collision",
            f"path already declared by {[p.id for p in same_path]}",
            unlock="remove the duplicate declaration first",
        )
    existing = ws.project(pid)
    decl = ProjectDecl(
        id=pid,
        path=str(candidate) if _is_external(candidate, ws_root) else _rel(candidate, ws_root),
        role=role or (existing.role if existing else None),
        dependencies=tuple(
            sorted(set(depends_on) | set(existing.dependencies if existing else ()))
        ),
        optional_dependencies=tuple(
            sorted(set(optional) | set(existing.optional_dependencies if existing else ()))
        ),
    )
    action = "kept" if existing and existing.to_dict() == decl.to_dict() else (
        "updated" if existing else "added"
    )
    projects = tuple(p for p in ws.projects if p.id != pid) + (decl,)
    ws = _replace_projects(ws_root, ws, projects)
    cycles = detect_cycles(ws)
    return {
        "status": "ok" if not cycles else "degraded",
        "action": action,
        "project": decl.to_dict(),
        "resolved_path": str(candidate),
        "external": _is_external(candidate, ws_root),
        "initialized_target": initialized_target,
        "workspace_id": ws.workspace_id,
        "dependency_cycles": [list(c) for c in cycles] or None,
    }


def _is_external(path: Path, ws_root: Path) -> bool:
    try:
        path.relative_to(ws_root)
        return False
    except ValueError:
        return True


def _rel(path: Path, ws_root: Path) -> str:
    return path.relative_to(ws_root).as_posix()


def workspace_remove(root: Path | None, project_id: str) -> dict[str, Any]:
    """Remove the *declaration* of a project — the repository is never
    deleted (§36). Inbound edges to it are dropped and reported."""
    ws_root, ws = _require_workspace(root or Path.cwd())
    target = ws.project(project_id)
    if target is None:
        raise PortableError(
            "workspace_not_found",
            f"project {project_id!r} is not declared",
            unlock="workspace status lists declared ids",
        )
    removed_edges: list[str] = []
    kept: list[ProjectDecl] = []
    for p in ws.projects:
        if p.id == project_id:
            continue
        deps = tuple(d for d in p.dependencies if d != project_id)
        opt = tuple(d for d in p.optional_dependencies if d != project_id)
        if len(deps) != len(p.dependencies) or len(opt) != len(p.optional_dependencies):
            removed_edges.append(p.id)
        kept.append(
            ProjectDecl(
                id=p.id, path=p.path, role=p.role,
                dependencies=deps, optional_dependencies=opt,
            )
        )
    default = ws.default_target if ws.default_target != project_id else None
    ws = _replace_projects(
        ws_root, ws, tuple(kept), default_target=default
    )
    return {
        "status": "ok",
        "removed": project_id,
        "inbound_edges_removed": removed_edges,
        "repository_deleted": False,
        "note": "declaration only — the repository on disk is untouched",
        "workspace_id": ws.workspace_id,
    }


def workspace_status(root: Path | None = None) -> dict[str, Any]:
    """Declared projects × resolution + cycles. An explicit review state,
    never silent failure."""
    base = Path(root or Path.cwd()).resolve()
    ws_root, ws = _require_workspace(base)
    projects = []
    missing: list[str] = []
    for p in ws.projects:
        resolved = resolve_declared_path(p.path, ws_root)
        exists = resolved.is_dir()
        if not exists:
            missing.append(p.id)
        projects.append(
            {
                "id": p.id,
                "path": p.path,
                "resolved_path": str(resolved),
                "external": _is_external(resolved, ws_root),
                "exists": exists,
                "role": p.role,
                "dependencies": list(p.dependencies),
                "optional_dependencies": list(p.optional_dependencies),
                "is_default_target": p.id == ws.default_target,
            }
        )
    cycles = detect_cycles(ws)
    if cycles:
        level = "dependency_cycle"
    elif missing:
        level = "degraded"
    else:
        level = "ok"
    return {
        "status": level,
        "workspace_id": ws.workspace_id,
        "name": ws.name,
        "workspace_root": str(ws_root),
        "default_target": ws.default_target,
        "projects": projects,
        "dependency_cycles": [list(c) for c in cycles],
        "missing_projects": missing,
        "project_count": len(projects),
    }


def workspace_discover(root: Path | None = None) -> dict[str, Any]:
    """Bounded suggestion pass — reads, never writes (§24–§27).

    Looks at: the current dir, bounded ancestors (existing manifests), and
    declared/one-level children of the workspace root. Everything else is a
    *suggestion* for `workspace add`, not a fact about dependencies.
    """
    base = Path(root or Path.cwd()).resolve()
    found = discover(base)
    candidates: list[dict[str, Any]] = []

    def marker_for(path: Path) -> str | None:
        if (path / STATE_DIR_NAME / PROJECT_MANIFEST_NAME).is_file():
            return "project_manifest"
        if (path / ".git").exists():
            return "git"
        if (path / "pyproject.toml").is_file():
            return "pyproject"
        return None

    def suggest(path: Path, via: str) -> None:
        marker = marker_for(path)
        if marker is None or len(candidates) >= MAX_SUGGESTIONS:
            return
        candidates.append(
            {"path": str(path.resolve()), "marker": marker, "via": via}
        )

    suggest(base, "cwd")
    for ancestor in ancestors(base)[1:]:
        if marker_for(ancestor):
            suggest(ancestor, "ancestor")
            break  # nearest project-like ancestor only — bounded

    ws_root = found.workspace_root
    declared: set[str] = set()
    ws_meta: dict[str, Any] | None = None
    if ws_root is not None:
        existing = _workspace_or_none(base)
        if existing is not None:
            _root, ws = existing
            ws_meta = {
                "workspace_id": ws.workspace_id,
                "workspace_root": str(ws_root),
            }
            declared = {
                str(resolve_declared_path(p.path, ws_root)) for p in ws.projects
            }
            for p in ws.projects:
                resolved = resolve_declared_path(p.path, ws_root)
                if resolved.is_dir():
                    for child in sorted(resolved.iterdir())[:MAX_SUGGESTIONS]:
                        if child.is_dir() and marker_for(child):
                            suggest(child, "declared_child")
        try:
            for child in sorted(ws_root.iterdir())[:MAX_SUGGESTIONS]:
                if child.is_dir() and child.name != STATE_DIR_NAME:
                    resolved = str(child.resolve())
                    if resolved not in declared:
                        suggest(child, "workspace_root_child")
        except OSError:
            pass

    return {
        "status": "ok",
        "start": str(base),
        "workspace": ws_meta,
        "candidates": candidates,
        "declared": sorted(declared),
        "bounded": {"max_ancestors": 24, "max_suggestions": MAX_SUGGESTIONS},
        "note": "suggestions only — `workspace add` confirms; nothing was written",
    }


__all__ = [
    "MAX_SUGGESTIONS",
    "dependency_edges",
    "detect_cycles",
    "reachable",
    "workspace_add",
    "workspace_discover",
    "workspace_init",
    "workspace_remove",
    "workspace_status",
]
