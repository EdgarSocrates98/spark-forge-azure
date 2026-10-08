"""Synapse Spark -> Fabric Spark assessment (SDD SYNAPSE_FABRIC_SPARK).

Notebook sources are scanned for the official refactor patterns published
by Microsoft Learn (synapse-migration-spark-workloads): every match becomes
a typed finding with file:line evidence.  Pools map to Fabric environments;
spark configs are classified, never force-mapped 1:1 (prompt §87); a
notebook is never auto-rewritten whole (§197).
"""
from __future__ import annotations

import re
from typing import Any

#: Official search patterns -> (category, action, status).  Source:
#: MS Learn fabric/data-engineering/synapse-migration-spark-workloads
#: (verified 2026-10).  Status from the closed COMPAT_STATUS vocabulary.
REFACTOR_PATTERNS: dict[str, tuple[str, str, str]] = {
    "mssparkutils": (
        "utility", "replace com notebookutils (APIs majoritariamente "
        "identicas)", "compatible_with_change"),
    "getSecretWithLS": (
        "credentials", "replace com getSecret(vaultUrl, secretName)",
        "manual_refactor"),
    "TokenLibrary": (
        "auth", "remover; usar OAuth direto ou notebookutils.credentials",
        "manual_refactor"),
    "LinkedServiceBasedTokenProvider": (
        "auth", "replace com ClientCredsTokenProvider",
        "manual_refactor"),
    "synapsesql": (
        "connector", "replace spark.read.synapsesql com leitura Delta",
        "manual_refactor"),
    "spark.synapse.linkedService": (
        "linked_service", "remover; endpoint direto ou Key Vault secrets",
        "manual_refactor"),
    "getPropertiesAsMap": (
        "linked_service", "remover; configurar storage diretamente",
        "manual_refactor"),
    "spark.storage.synapse": (
        "linked_service", "remover — nao suportado no Fabric",
        "unsupported"),
    "spark.catalog.listFunctions": (
        "catalog_api", "nao suportado no Fabric — remover",
        "unsupported"),
    "spark.catalog.registerFunction": (
        "catalog_api", "nao suportado — usar spark.udf.register()",
        "manual_refactor"),
    "spark.catalog.functionExists": (
        "catalog_api", "nao suportado no Fabric — remover",
        "unsupported"),
    "spark.catalog.listDatabases": (
        "catalog_api", 'replace com spark.sql("SHOW DATABASES")',
        "compatible_with_change"),
    "spark.catalog.currentDatabase": (
        "catalog_api", 'replace com spark.sql("SELECT CURRENT_DATABASE()")',
        "compatible_with_change"),
    "spark.catalog.getDatabase": (
        "catalog_api", 'replace com spark.sql("DESCRIBE DATABASE ...")',
        "compatible_with_change"),
    "/user/trusted-service-user/": (
        "storage_path", "replace com path OneLake ou shortcut",
        "compatible_with_change"),
    "cosmos.oltp": (
        "connector", "usar Key Vault para segredos em vez de linked service",
        "manual_refactor"),
    "kusto.spark.synapse": (
        "connector", "auth via accessToken getToken() em vez de linked "
        "service", "manual_refactor"),
}

#: Spark configs accepted verbatim in Fabric environments (subset — the
#: runtime matrix is the authority for pool-level claims).
SUPPORTED_CONFIG_PREFIXES = (
    "spark.sql.", "spark.databricks.delta", "spark.microsoft.delta",
    "spark.executor.", "spark.driver.", "spark.dynamicAllocation",
)


def scan_notebook_source(source: str, path: str) -> list[dict[str, Any]]:
    """Detect official refactor patterns; each match is one finding
    candidate with file:line evidence.  Never auto-rewrites (§197)."""
    findings: list[dict[str, Any]] = []
    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        for pattern, (cat, action, status) in REFACTOR_PATTERNS.items():
            if pattern in line:
                findings.append({
                    "pattern": pattern, "category": cat, "action": action,
                    "status": status, "file": path, "line": i})
    return findings


def notebook_dependency_graph(notebooks: list[dict[str, Any]],
                              sources: dict[str, str]) -> dict[str, Any]:
    """%run / notebook.run / mssparkutils.notebook.run edges between
    notebooks — feeds blast-radius queries (prompt §107-108)."""
    edges: list[dict[str, str]] = []
    name_of = {str(nb.get("path")): str(nb.get("name"))
               for nb in notebooks}
    for path, src in sorted(sources.items()):
        caller = name_of.get(path, path)
        for m in re.finditer(
                r"(?:%run|notebook\.run|notebooks\.run)\s*\(?\s*['\"]"
                r"([^'\"]+)['\"]", src):
            target = m.group(1).lstrip("/")
            dst = next(
                (name for p, name in name_of.items()
                 if p == target or p.endswith("/" + target)
                 or name == target or name == target.split("/")[-1]),
                target)
            edges.append({"src": caller, "dst": str(dst),
                          "relation": "invokes"})
    return {"edges": edges, "edge_count": len(edges)}


def classify_spark_config(key: str) -> str:
    """Config classification (prompt §105): supported / change / unknown."""
    k = str(key)
    if any(k.startswith(p) for p in SUPPORTED_CONFIG_PREFIXES):
        return "supported"
    if k.startswith(("spark.synapse.", "spark.sqlanalytics")):
        return "not_migratable"
    return "unknown"


def pool_to_environment(pool: Any) -> dict[str, Any]:
    """Spark pool -> Fabric environment candidate.  Never forces a 1:1
    compute mapping (prompt §87): runtime/library diffs are reported,
    sizes are advisory."""
    return {
        "kind": "fabric_environment_candidate",
        "source_pool": pool.subject.get("pool_id"),
        "name": pool.attrs.get("name"),
        "spark_version": pool.attrs.get("spark_version"),
        "node_size": pool.attrs.get("node_size"),
        "node_count": pool.attrs.get("node_count"),
        "libraries": pool.attrs.get("libraries"),
        "note": "Fabric environments gerenciam runtime+libs; node sizing "
                "e advisory, nao mapeamento 1:1",
    }


def assess_notebook(nb: Any, source: str | None,
                    path: str) -> dict[str, Any]:
    """Per-notebook refactor assessment."""
    findings = scan_notebook_source(source or "", path) if source else []
    statuses = {f["status"] for f in findings}
    if "unsupported" in statuses:
        readiness = "BLOCKED"
    elif "manual_refactor" in statuses:
        readiness = "MANUAL"
    elif "compatible_with_change" in statuses:
        readiness = "REVIEW"
    elif not findings and source is not None:
        readiness = "READY"
    else:
        readiness = "UNRESOLVED"
    return {"notebook_id": nb.subject.get("notebook_id"),
            "name": nb.attrs.get("name"), "readiness": readiness,
            "findings": findings}


def assess_libraries(facts: list[Any],
                     known_fabric: set[str] | None = None) -> list[dict[str, Any]]:
    """Custom libraries without proven Fabric compatibility are
    REVIEW/UNRESOLVED — never 'unsupported' unless proven (scenario 10)."""
    known = {k.lower() for k in (known_fabric or set())}
    out = []
    for lib in [f for f in facts if f.kind == "mig.library"]:
        name = str(lib.subject.get("library", ""))
        if name.lower() in known:
            status, readiness = "compatible", "READY"
        else:
            status, readiness = "unknown", "UNRESOLVED"
        out.append({"library": name, "kind": lib.attrs.get("kind"),
                    "version": lib.attrs.get("version"),
                    "status": status, "readiness": readiness,
                    "evidence": [lib.id]})
    return out


__all__ = [
    "REFACTOR_PATTERNS", "SUPPORTED_CONFIG_PREFIXES", "assess_libraries",
    "assess_notebook", "classify_spark_config", "notebook_dependency_graph",
    "pool_to_environment", "scan_notebook_source",
]
