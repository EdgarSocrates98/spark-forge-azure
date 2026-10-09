"""Managed manifests for the portable lifecycle (spec §17, §27–§30).

Two artifacts, both under ``.sparkforge-azure/`` (local state, gitignored —
paths are machine-local and must never be committed):

- ``project.yaml`` — the *portable project identity* (§38): a generated
  ``project_id`` that survives relocation, plus optional config overrides.
- ``workspace.yaml`` — the *ForgeWorkspace* (§22): a logical grouping of
  projects declared by id/path/role with explicit dependency edges.

Both are strict YAML, ``DATA_ONLY`` (§114): keys that smell like secrets are
refused at load and at write (§119), and unknown top-level keys fail closed
in strict mode (§47).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure import __version__
from sparkforge_azure.distribution.discovery import (
    PROJECT_MANIFEST_NAME,
    STATE_DIR_NAME,
    WORKSPACE_MANIFEST_NAME,
)
from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.durable import write_atomic

SCHEMA_VERSION = 1
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")

#: Spec §29 — advisory only, never required.
PROJECT_ROLES: frozenset[str] = frozenset(
    {"application", "data", "infra", "shared", "tests", "docs"}
)

#: Declared edge kinds (§30). ``transitive`` is *derived*, never written.
DEPENDENCY_KINDS: frozenset[str] = frozenset({"direct", "optional"})

_SECRET_KEYS = ("secret", "token", "password", "credential", "api_key", "private_key")

_PROJECT_KEYS = frozenset({"version", "project_id", "name", "created", "generator", "config"})
_WORKSPACE_KEYS = frozenset(
    {"version", "workspace_id", "name", "projects", "default_target", "config"}
)
_PROJECT_ENTRY_KEYS = frozenset({"id", "path", "role", "dependencies", "optional_dependencies"})


def new_project_id() -> str:
    """A generated, path-independent identity (§38–§39)."""
    return f"sfa-{uuid.uuid4().hex[:24]}"


def new_workspace_id() -> str:
    return f"sfw-{uuid.uuid4().hex[:24]}"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _refuse_secret_keys(data: Any, where: str) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if any(marker in str(key).lower() for marker in _SECRET_KEYS):
                raise PortableError(
                    "manifest_invalid",
                    f"{where}: secret-like key {key!r} is not allowed in a manifest",
                    unlock="keep credentials in env vars or a secret store",
                )
            _refuse_secret_keys(value, where)
    elif isinstance(data, list):
        for item in data:
            _refuse_secret_keys(item, where)


def _refuse_unknown_keys(data: dict[str, Any], allowed: frozenset[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise PortableError(
            "manifest_invalid",
            f"{where}: unknown keys {unknown}",
            unlock="remove the keys or extend the schema deliberately",
        )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise PortableError(
            "manifest_invalid", f"{path.name}: unreadable ({exc})",
            unlock="recreate the file or run `distribution detach`",
        ) from exc
    except yaml.YAMLError as exc:
        raise PortableError(
            "manifest_invalid", f"{path.name}: invalid YAML ({exc})",
            unlock="fix the YAML or re-run `distribution init --regen-id`",
        ) from exc
    if not isinstance(raw, dict):
        raise PortableError("manifest_invalid", f"{path.name}: expected a mapping")
    _refuse_secret_keys(raw, path.name)
    return raw


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    _refuse_secret_keys(data, path.name)
    write_atomic(path, yaml.safe_dump(data, sort_keys=True, allow_unicode=False))


# ---------------------------------------------------------------------------
# project.yaml — relocatable project identity
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    """`.sparkforge-azure/project.yaml` — identity independent of location."""

    project_id: str
    name: str
    created: str
    generator: str
    version: int = SCHEMA_VERSION
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def manifest_name(self) -> str:
        return PROJECT_MANIFEST_NAME

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "version": self.version,
            "project_id": self.project_id,
            "name": self.name,
            "created": self.created,
            "generator": self.generator,
        }
        if self.config:
            out["config"] = self.config
        return out


def write_project_identity(root: Path, identity: ProjectIdentity) -> Path:
    target = Path(root).resolve() / STATE_DIR_NAME / PROJECT_MANIFEST_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    _dump_yaml(target, identity.to_dict())
    return target


def load_project_identity(path: Path) -> ProjectIdentity:
    """Load and validate a project.yaml. Path is *location*, never identity."""
    target = Path(path)
    raw = _load_yaml(target)
    _refuse_unknown_keys(raw, _PROJECT_KEYS, target.name)
    if raw.get("version") != SCHEMA_VERSION:
        raise PortableError("manifest_invalid", f"{target.name}: version must be 1")
    project_id = raw.get("project_id")
    if not isinstance(project_id, str) or not project_id.startswith("sfa-"):
        raise PortableError("manifest_invalid", f"{target.name}: invalid project_id")
    name = raw.get("name")
    if not isinstance(name, str) or not _NAME.match(name.strip()):
        raise PortableError("manifest_invalid", f"{target.name}: invalid name")
    config = raw.get("config") or {}
    if not isinstance(config, dict):
        raise PortableError("manifest_invalid", f"{target.name}: config must be a mapping")
    return ProjectIdentity(
        project_id=project_id,
        name=name.strip(),
        created=str(raw.get("created") or ""),
        generator=str(raw.get("generator") or ""),
        version=SCHEMA_VERSION,
        config=dict(config),
    )


def init_project_identity(root: Path, *, name: str | None = None) -> ProjectIdentity:
    """Generate and persist a new identity for ``root``."""
    base = Path(root).resolve()
    identity = ProjectIdentity(
        project_id=new_project_id(),
        name=(name or base.name or "project").strip(),
        created=_utcnow(),
        generator=f"sparkforge-azure {__version__}",
    )
    write_project_identity(base, identity)
    return identity


# ---------------------------------------------------------------------------
# workspace.yaml — the ForgeWorkspace (§22)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProjectDecl:
    """One declared project inside a ForgeWorkspace."""

    id: str
    path: str
    role: str | None = None
    dependencies: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"id": self.id, "path": self.path}
        if self.role:
            out["role"] = self.role
        if self.dependencies:
            out["dependencies"] = list(self.dependencies)
        if self.optional_dependencies:
            out["optional_dependencies"] = list(self.optional_dependencies)
        return out


@dataclass(frozen=True, slots=True)
class WorkspaceDecl:
    """`.sparkforge-azure/workspace.yaml` — the ForgeWorkspace manifest."""

    workspace_id: str
    name: str
    projects: tuple[ProjectDecl, ...]
    default_target: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    version: int = SCHEMA_VERSION

    def project(self, ref: str) -> ProjectDecl | None:
        return next((p for p in self.projects if p.id == ref), None)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "version": self.version,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "projects": [p.to_dict() for p in self.projects],
        }
        if self.default_target:
            out["default_target"] = self.default_target
        if self.config:
            out["config"] = self.config
        return out


def _norm_declared_path(raw: str, workspace_root: Path) -> str:
    """Canonicalize a declared project path for storage (§36).

    Paths inside the workspace root are stored relative (relocatable with the
    workspace); external paths are stored absolute — declared, not discovered
    (§35/§118). Identity never comes from this string.
    """
    value = raw.strip().replace("\\", "/")
    if not value:
        raise PortableError("manifest_invalid", "project path cannot be empty")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = (workspace_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        return candidate.relative_to(workspace_root).as_posix()
    except ValueError:
        return candidate.as_posix()


def resolve_declared_path(declared: str, workspace_root: Path) -> Path:
    """Resolve a stored ``path`` against the *current* workspace root — this is
    what makes a moved workspace still resolve (§40, §145–§146)."""
    candidate = Path(declared).expanduser()
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    return candidate.resolve()


def _parse_projects(raw: Any, workspace_root: Path) -> tuple[ProjectDecl, ...]:
    if not isinstance(raw, list):
        raise PortableError("manifest_invalid", "workspace.yaml: projects must be a list")
    seen: set[str] = set()
    out: list[ProjectDecl] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise PortableError(
                "manifest_invalid", f"workspace.yaml: projects[{index}] must be a mapping"
            )
        _refuse_unknown_keys(entry, _PROJECT_ENTRY_KEYS, f"projects[{index}]")
        pid = entry.get("id")
        if not isinstance(pid, str) or not (
            _NAME.match(pid.strip()) or pid.strip().startswith("sfa-")
        ):
            raise PortableError(
                "manifest_invalid", f"workspace.yaml: projects[{index}].id invalid: {pid!r}"
            )
        if pid in seen:
            raise PortableError(
                "identity_collision",
                f"workspace.yaml: duplicate project id {pid!r}",
                unlock="each project id is unique; regen the copy's project.yaml",
            )
        seen.add(pid)
        path_raw = entry.get("path")
        if not isinstance(path_raw, str):
            raise PortableError(
                "manifest_invalid", f"workspace.yaml: projects[{index}].path missing"
            )
        role = entry.get("role")
        if role is not None and (not isinstance(role, str) or role not in PROJECT_ROLES):
            raise PortableError(
                "manifest_invalid",
                f"workspace.yaml: projects[{index}].role unknown: {role!r}",
                unlock=f"roles: {sorted(PROJECT_ROLES)}",
            )
        deps = _dep_list(entry.get("dependencies"), f"projects[{index}].dependencies")
        opt = _dep_list(
            entry.get("optional_dependencies"), f"projects[{index}].optional_dependencies"
        )
        out.append(
            ProjectDecl(
                id=pid.strip(),
                path=_norm_declared_path(path_raw, workspace_root),
                role=role,
                dependencies=deps,
                optional_dependencies=opt,
            )
        )
    return tuple(sorted(out, key=lambda item: item.id))


def _dep_list(raw: Any, where: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise PortableError("manifest_invalid", f"workspace.yaml: {where} must be a list of ids")
    return tuple(sorted(dict.fromkeys(raw)))


def _validate_edges(projects: tuple[ProjectDecl, ...]) -> None:
    ids = {p.id for p in projects}
    for project in projects:
        for dep in (*project.dependencies, *project.optional_dependencies):
            if dep not in ids:
                raise PortableError(
                    "manifest_invalid",
                    f"project {project.id!r} depends on undeclared project {dep!r}",
                    unlock=f"workspace add the repository for {dep!r} or remove the edge",
                )
            if dep == project.id:
                raise PortableError(
                    "dependency_cycle", f"project {project.id!r} depends on itself"
                )


def write_workspace_manifest(root: Path, manifest: WorkspaceDecl) -> Path:
    target = Path(root).resolve() / STATE_DIR_NAME / WORKSPACE_MANIFEST_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    _dump_yaml(target, manifest.to_dict())
    return target


def load_workspace_manifest(path: Path) -> WorkspaceDecl:
    target = Path(path)
    raw = _load_yaml(target)
    _refuse_unknown_keys(raw, _WORKSPACE_KEYS, target.name)
    if raw.get("version") != SCHEMA_VERSION:
        raise PortableError("manifest_invalid", f"{target.name}: version must be 1")
    workspace_id = raw.get("workspace_id")
    if not isinstance(workspace_id, str) or not workspace_id.startswith("sfw-"):
        raise PortableError("manifest_invalid", f"{target.name}: invalid workspace_id")
    name = raw.get("name")
    if not isinstance(name, str) or not _NAME.match(name.strip()):
        raise PortableError("manifest_invalid", f"{target.name}: invalid name")
    workspace_root = target.parent.parent.resolve()
    projects = _parse_projects(raw.get("projects") or [], workspace_root)
    _validate_edges(projects)
    default_target = raw.get("default_target")
    if default_target is not None:
        if not isinstance(default_target, str) or default_target not in {
            p.id for p in projects
        }:
            raise PortableError(
                "manifest_invalid",
                f"{target.name}: default_target {default_target!r} is not a declared project",
            )
    config = raw.get("config") or {}
    if not isinstance(config, dict):
        raise PortableError("manifest_invalid", f"{target.name}: config must be a mapping")
    return WorkspaceDecl(
        workspace_id=workspace_id,
        name=name.strip(),
        projects=projects,
        default_target=default_target,
        config=dict(config),
    )


def init_workspace_manifest(root: Path, *, name: str | None = None) -> WorkspaceDecl:
    base = Path(root).resolve()
    manifest = WorkspaceDecl(
        workspace_id=new_workspace_id(),
        name=(name or base.name or "workspace").strip(),
        projects=(),
    )
    write_workspace_manifest(base, manifest)
    return manifest


__all__ = [
    "DEPENDENCY_KINDS",
    "PROJECT_ROLES",
    "SCHEMA_VERSION",
    "ProjectDecl",
    "ProjectIdentity",
    "WorkspaceDecl",
    "init_project_identity",
    "init_workspace_manifest",
    "load_project_identity",
    "load_workspace_manifest",
    "new_project_id",
    "new_workspace_id",
    "resolve_declared_path",
    "write_project_identity",
    "write_workspace_manifest",
]
