"""Logical identity namespaces (spec §37–§43, §64).

Identity is a generated ``sfa-*``/``sfw-*`` id persisted in the manifest —
never the filesystem path. This module is where *logical* ids become
*physical* locations for state, cache and indexes:

- default case (state anchored at the project root): the state dir already
  IS project-scoped, so the namespace is the state root itself — fully
  compatible with the existing ``.sparkforge-azure/local/codeintel`` layout;
- shared root case (``SPARKFORGE_AZURE_STATE_DIR``/``SPARKFORGE_AZURE_CACHE``
  pointing elsewhere): the namespace is ``<root>/projects/<project_id>`` —
  two projects sharing an overridden root never collide.

Cache namespaces include ``workspace_id`` when one is known (§64). Agent
receipts carry ``project_id`` + ``workspace_id`` + scope via
``receipt_namespace`` — the tuple every W4+ receipt embeds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sparkforge_azure.distribution.paths import PortablePaths


def project_state_dir(paths: PortablePaths, project_id: str) -> Path:
    """Where project-scoped state lives for ``project_id``.

    Project-anchored roots are already the namespace; environment-anchored
    (shared) roots get ``projects/<id>`` so overrides never merge state.
    """
    sources = dict(paths.sources)
    if sources.get("state_root") == "environment":
        return paths.state_root / "projects" / project_id
    return paths.state_root


def project_cache_dir(
    paths: PortablePaths, project_id: str, *, workspace_id: str | None = None
) -> Path:
    """Where project-scoped cache lives — includes workspace_id when set."""
    sources = dict(paths.sources)
    if sources.get("cache_root") != "environment":
        return paths.cache_root
    base = paths.cache_root / workspace_id if workspace_id else paths.cache_root
    return base / "projects" / project_id


def codeintel_db(
    paths: PortablePaths, project_id: str, *, workspace_id: str | None = None
) -> Path:
    """The codeintel index path keyed by logical id, not by checkout path."""
    return project_state_dir(paths, project_id) / "local" / "codeintel" / "graph.sqlite3"


def receipt_namespace(
    project_id: str,
    workspace_id: str | None,
    *,
    scope: str | None = None,
) -> dict[str, Any]:
    """The identity tuple every portability-aware receipt embeds (§64)."""
    out: dict[str, Any] = {
        "project_id": project_id,
        "workspace_id": workspace_id,
    }
    if scope is not None:
        out["context_scope"] = scope
    return out


__all__ = [
    "codeintel_db",
    "project_cache_dir",
    "project_state_dir",
    "receipt_namespace",
]
