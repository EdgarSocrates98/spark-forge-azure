"""Fabric domain model — contracts, fact kinds, deterministic IDs (SDD FABRIC_CORE).

Fabric is a SaaS platform, not a set of ARM resources: Tenant → Capacity →
Workspace → Item → (Lakehouse → OneLake tables/files/shortcuts).  Azure
subscription and Fabric workspace are different axes — never merged.

Fact kinds are versioned by contract, never by display name.  ``fabric_item_id``
is the canonical identity for graph nodes and fact subjects; a missing GUID is
modeled as the path/type tuple, never as a name coincidence.
"""
from __future__ import annotations

#: Public failure-layer vocabulary for the Fabric vertical (prompt #49,
#: reviewed per #50 — each layer is a distinct diagnosable cause with its
#: own evidence and remediation).
FABRIC_LAYERS = (
    "fabric_workspace",
    "item_permission",
    "onelake_security",
    "lakehouse",
    "shortcut",
    "shortcut_auth",
    "source_access",
    "spark_runtime",
    "spark_job",
    "capacity",
    "data_factory",
    "cross_environment",
    "unresolved",
)

#: Fabric item types modeled explicitly (REST ``Item.type`` values).
ITEM_TYPES = frozenset({
    "Lakehouse", "Notebook", "SparkJobDefinition", "Environment",
    "DataPipeline", "SemanticModel", "Warehouse", "SQLEndpoint",
    "MirroredDatabase", "Eventhouse", "Report", "Dashboard",
})

#: Workspace roles (control plane).  Per current docs, members of
#: Admin/Member/Contributor already have data-plane access — OneLake security
#: roles mainly constrain Viewer/Read-permission principals.
WORKSPACE_ROLES = ("Admin", "Member", "Contributor", "Viewer")
DATA_PLANE_BYPASS_ROLES = frozenset({"Admin", "Member", "Contributor"})

#: OneLake security role permissions (grant-only model — no Deny role type).
ONELAKE_PERMISSIONS = frozenset({"Read", "ReadWrite"})

#: Shortcut auth models (current docs).
SHORTCUT_AUTH_PASSTHROUGH = "passthrough"
SHORTCUT_AUTH_DELEGATED = "delegated"

#: Shortcut target kinds.
SHORTCUT_TARGET_KINDS = frozenset({"onelake", "adls_gen2", "external"})


def fabric_item_id(item_id: str | None, item_type: str | None,
                   workspace_id: str | None) -> str:
    """Deterministic item identity: official GUID when present."""
    if item_id:
        return str(item_id)
    # Sem GUID oficial o sujeito usa type+workspace — nunca display name.
    return f"{workspace_id or 'workspace-unknown'}:{item_type or 'Item'}:unknown"
