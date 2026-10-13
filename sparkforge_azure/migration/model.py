"""Migration domain model — ADF/Synapse -> Fabric (SDDs MIGRATION_INVENTORY /
MIGRATION_COMPATIBILITY / ADF_FABRIC_DATA_FACTORY / SYNAPSE_FABRIC_SPARK /
DATA_ONELAKE / MIGRATION_PLANNER / POST_MIGRATION_VALIDATION).

Migration is not service mapping: "ADF = Fabric Data Factory" is a
*target candidate*, never a semantic equivalence.  Readiness is
provider-neutral; official Microsoft assessment statuses are *evidence*
(DATA_ONLY), mapped with provenance, never silently overridden.
"""
from __future__ import annotations

#: Provider-neutral internal readiness states (prompt §32).  UNRESOLVED is
#: the default when evidence is missing — absence is never READY (§29).
READINESS = (
    "READY",          # evidence supports migration
    "REVIEW",         # needs manual adjustment or official-vs-forge conflict
    "BLOCKED",        # hard blocker observed (unsupported capability)
    "MANUAL",         # manual migration path (no automatic/assisted route)
    "DEFERRED",       # known-but-deferred (coming soon / out of scope)
    "UNRESOLVED",     # insufficient evidence — never assumed
)
READY_ORDER = {s: i for i, s in enumerate(
    ("UNRESOLVED", "BLOCKED", "MANUAL", "REVIEW", "DEFERRED", "READY"))}

#: Official Microsoft readiness categories observed in assessment exports
#: (prompt §31) — modeled as source evidence, mapped with provenance.
OFFICIAL_STATES = frozenset({
    "ready", "needs review", "coming soon", "not compatible"})

#: Official -> internal mapping.  `coming soon` is DEFERRED (capability
#: announced, not usable today); unknown labels map to UNRESOLVED, never
#: silently upgraded.
OFFICIAL_TO_INTERNAL = {
    "ready": "READY",
    "needs review": "REVIEW",
    "coming soon": "DEFERRED",
    "not compatible": "BLOCKED",
}

#: Compatibility status vocabulary (prompt §38) — closed set.
COMPAT_STATUS = frozenset({
    "compatible",
    "compatible_with_change",
    "manual_refactor",
    "unsupported",
    "preview",
    "unknown",
})

#: Compatibility dimensions (prompt §37).
COMPAT_DIMENSIONS = (
    "pipeline_activity", "connector", "authentication",
    "integration_runtime", "network", "parameter", "trigger",
    "expression", "notebook", "spark_runtime", "library",
    "spark_config", "storage_path", "catalog_api", "git_integration",
    "deployment",
)

#: Migration edge status vocabulary (prompt §19).
MIGRATION_STATUS = frozenset({
    "automatic", "assisted", "manual", "refactor", "not_supported",
    "deferred",
})

#: Data-movement strategies (prompt §303).
DATA_STRATEGIES = frozenset({"retain", "shortcut", "copy", "hybrid"})

#: Post-migration validation dimensions (prompt §147).
VALIDATION_DIMENSIONS = (
    "functional", "data", "schema", "dq", "performance", "security",
    "lineage", "cost", "orchestration",
)

#: Asset types (prompt §14).
ASSET_TYPES = frozenset({
    "adf_factory", "synapse_workspace", "pipeline", "activity", "dataset",
    "linked_service", "trigger", "integration_runtime", "global_parameter",
    "synapse_notebook", "spark_pool", "spark_job", "lake_database",
    "table", "library", "spark_config", "adls_path", "storage_account",
    "fabric_workspace", "fabric_pipeline", "fabric_connection",
    "fabric_notebook", "fabric_environment", "fabric_lakehouse",
    "fabric_shortcut", "variable_library",
})

#: Dependency relations (prompt §16-17).
DEP_RELATIONS = frozenset({
    "contains", "uses", "reads", "writes", "invokes", "depends_on",
    "runs_on", "references", "default_lakehouse", "shortcut",
    "migrates_to",
})


def canonical_id(official_id: object, kind: str, name: object) -> str:
    """Identity = official/ARM id when present; name is an attribute."""
    if official_id:
        return str(official_id)
    return f"{kind}:{name or 'unknown'}"
