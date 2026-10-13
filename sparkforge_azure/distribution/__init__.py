"""Portable distribution layer (prompt_evo_portable.md §9–§19).

The product layer that makes the Forge portable by installation: managed
manifests under ``.sparkforge-azure/``, a single path service with recorded
sources, packaged-asset inventory, host detection, a managed-asset ledger for
safe detach, and the application operations behind the ``distribution``,
``workspace`` and ``context`` verbs.

This package is deliberately additive (§208): it reuses ``paths``,
``durable``, ``doctor`` and ``agentmanifest`` instead of duplicating them.
"""

from sparkforge_azure.distribution.discovery import Discovery, discover
from sparkforge_azure.distribution.errors import (
    FAILURE_KINDS,
    PortableError,
    refused_document,
)
from sparkforge_azure.distribution.manifests import (
    ProjectDecl,
    ProjectIdentity,
    WorkspaceDecl,
)
from sparkforge_azure.distribution.paths import PortablePaths, resolve_paths

__all__ = [
    "FAILURE_KINDS",
    "Discovery",
    "PortableError",
    "PortablePaths",
    "ProjectDecl",
    "ProjectIdentity",
    "WorkspaceDecl",
    "discover",
    "refused_document",
    "resolve_paths",
]
