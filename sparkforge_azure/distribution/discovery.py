"""Bounded, deterministic, offline ancestor discovery (spec §24–§26).

Discovery walks the ancestor chain of a starting directory — current dir,
then parents, bounded by ``MAX_ANCESTORS`` — looking for the two managed
manifests. It never scans the home directory, never descends into siblings,
and never reads an undeclared path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#: Local state dir shared with `paths.state_dir()` — one directory name.
STATE_DIR_NAME = ".sparkforge-azure"
PROJECT_MANIFEST_NAME = "project.yaml"
WORKSPACE_MANIFEST_NAME = "workspace.yaml"

#: Hard bound on the ancestor walk (§26). 24 levels covers any realistic
#: checkout depth without approaching a home-wide scan.
MAX_ANCESTORS = 24


@dataclass(frozen=True, slots=True)
class Discovery:
    """What the bounded ancestor walk found, with evidence."""

    start: Path
    repository_root: Path | None
    project_manifest: Path | None
    workspace_manifest: Path | None
    evidence: tuple[str, ...]

    @property
    def project_root(self) -> Path | None:
        return (
            self.project_manifest.parent.parent.resolve()
            if self.project_manifest
            else None
        )

    @property
    def workspace_root(self) -> Path | None:
        return (
            self.workspace_manifest.parent.parent.resolve()
            if self.workspace_manifest
            else None
        )


def ancestors(start: Path) -> tuple[Path, ...]:
    current = Path(start).resolve()
    out: list[Path] = []
    for _ in range(MAX_ANCESTORS):
        out.append(current)
        if current.parent == current:
            break
        current = current.parent
    return tuple(out)


def find_repo_root(start: Path) -> Path | None:
    for candidate in ancestors(start):
        if (candidate / ".git").exists():
            return candidate
    return None


def find_project_manifest(start: Path) -> Path | None:
    for candidate in ancestors(start):
        path = candidate / STATE_DIR_NAME / PROJECT_MANIFEST_NAME
        if path.is_file():
            return path
    return None


def find_workspace_manifest(start: Path) -> Path | None:
    for candidate in ancestors(start):
        path = candidate / STATE_DIR_NAME / WORKSPACE_MANIFEST_NAME
        if path.is_file():
            return path
    return None


def discover(start: Path | None = None) -> Discovery:
    """Resolve repo, project and workspace roots from ``start`` upward."""
    base = Path(start or Path.cwd()).resolve()
    repository = find_repo_root(base)
    project = find_project_manifest(base)
    workspace = find_workspace_manifest(base)
    evidence = [
        f"start:{base}",
        f"repository:{repository}" if repository else "repository:unresolved",
        f"project:{project}" if project else "project:unresolved",
        f"workspace:{workspace}" if workspace else "workspace:unresolved",
    ]
    return Discovery(
        start=base,
        repository_root=repository,
        project_manifest=project,
        workspace_manifest=workspace,
        evidence=tuple(evidence),
    )


__all__ = [
    "MAX_ANCESTORS",
    "PROJECT_MANIFEST_NAME",
    "STATE_DIR_NAME",
    "WORKSPACE_MANIFEST_NAME",
    "Discovery",
    "ancestors",
    "discover",
    "find_project_manifest",
    "find_repo_root",
    "find_workspace_manifest",
]
