"""ADF / Synapse pipeline -> Fabric Data Factory assessment
(SDD ADF_FABRIC_DATA_FACTORY).

Per-pipeline dimensional verdicts over extracted facts.  Linked services
are *connection candidates*, never semantic equivalences; global
parameters are variable-library candidates; SHIR is manual network/IR
review — never auto-mapped (prompt §48-50).
"""
from __future__ import annotations

from typing import Any

#: Activity types with a supported Fabric pipeline equivalent today.
#: Everything else is evidence-driven: unknown types -> unknown, never
#: silently compatible (research: MS Learn upgrade assessment).
SUPPORTED_ACTIVITIES = frozenset({
    "Copy", "ForEach", "IfCondition", "WebActivity", "Wait",
    "SetVariable", "AppendVariable", "ExecutePipeline", "Lookup",
    "GetMetadata", "Filter", "Until", "Switch", "WebHook", "Delete",
    "Fail", "Script", "Notebook",
})

#: Activities with a Fabric path that is not lift-and-shift.
MANUAL_ACTIVITIES = {
    "DataFlow": "manual_refactor — data flows viram Dataflow Gen2 ou refactor",
    "SynapseNotebook": "manual_refactor — notebook exige análise de código",
    "SparkJob": "manual_refactor — SJD vira Fabric Spark job definition",
}

UNSUPPORTED_ACTIVITIES = {
    "ExecuteSSISPackage": "unsupported — SSIS fora do escopo do runtime Fabric",
    "Custom": "unsupported — .NET custom activity não tem equivalente",
    "HDInsightHive": "unsupported — HDInsight activity não migra",
    "HDInsightSpark": "unsupported — HDInsight activity não migra",
}

#: Linked-service auth kinds with a Fabric connection path.
SUPPORTED_AUTH = frozenset({
    "service_principal", "managed_identity", "oauth2", "entra_id",
    "account_key", "workspace_identity",
})
REVIEW_AUTH = frozenset({
    "key_vault_reference", "windows_auth", "sql_auth_legacy",
})


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def assess_pipeline(pipeline: Any, facts: list[Any]) -> dict[str, Any]:
    """Dimensional verdicts for one pipeline (prompt §42-62)."""
    pid = str(pipeline.subject.get("pipeline_id"))
    owner = str(pipeline.subject.get("owner"))
    dims: list[dict[str, Any]] = []
    recs: list[dict[str, Any]] = []
    activities = [f for f in _facts(facts, "mig.activity")
                  if f.subject.get("pipeline_id") == pid]
    ls_by_name = {str(f.attrs.get("name")): f
                  for f in _facts(facts, "mig.linked_service")
                  if f.subject.get("owner") == owner}
    irs = {str(f.attrs.get("name")): f
           for f in _facts(facts, "mig.integration_runtime")
           if f.subject.get("owner") == owner}

    # -- pipeline_activity -----------------------------------------------
    blocked = [a for a in activities
               if str(a.attrs.get("type")) in UNSUPPORTED_ACTIVITIES]
    manual = [a for a in activities
              if str(a.attrs.get("type")) in MANUAL_ACTIVITIES]
    unknown = [a for a in activities
               if str(a.attrs.get("type")) not in SUPPORTED_ACTIVITIES
               | set(MANUAL_ACTIVITIES) | set(UNSUPPORTED_ACTIVITIES)]
    if blocked:
        dims.append({"dimension": "pipeline_activity",
                     "status": "unsupported",
                     "evidence": [a.id for a in blocked],
                     "detail": "; ".join(
                         UNSUPPORTED_ACTIVITIES[str(a.attrs["type"])]
                         for a in blocked)})
    elif manual or unknown:
        status = "manual_refactor" if manual else "unknown"
        ev = [a.id for a in [*manual, *unknown]]
        dims.append({"dimension": "pipeline_activity", "status": status,
                     "evidence": ev,
                     "detail": "; ".join(
                         MANUAL_ACTIVITIES.get(str(a.attrs.get("type")),
                                               f"tipo {a.attrs.get('type')} "
                                               "sem mapeamento conhecido")
                         for a in [*manual, *unknown])})
    else:
        dims.append({"dimension": "pipeline_activity",
                     "status": "compatible",
                     "evidence": [a.id for a in activities]})

    # -- linked services / connector / authentication --------------------
    for a in activities:
        for e in _edge_uses(facts, str(a.subject.get("activity_id")), owner):
            ls = ls_by_name.get(e)
            if ls is None:
                continue
            auth = str(ls.attrs.get("auth_kind", "unknown"))
            ltype = str(ls.attrs.get("type", "unknown"))
            if auth in REVIEW_AUTH or auth not in SUPPORTED_AUTH:
                st = ("manual_refactor" if auth in REVIEW_AUTH
                      else "unknown")
                dims.append({"dimension": "authentication",
                             "status": st,
                             "evidence": [ls.id],
                             "detail": f"auth_kind {auth} exige "
                                       f"re-mapeamento para Fabric "
                                       f"connection"})
            else:
                dims.append({"dimension": "authentication",
                             "status": "compatible_with_change",
                             "evidence": [ls.id],
                             "detail": "linked_service -> fabric_connection"})
            recs.append({"kind": "connection_candidate",
                         "source": ls.subject.get("ls_id"),
                         "linked_service": ls.attrs.get("name"),
                         "target_type": "fabric_connection",
                         "auth_kind": auth, "ls_type": ltype})

    # -- integration_runtime ----------------------------------------------
    for a in activities:
        ir_name = a.attrs.get("ir_ref")
        if not ir_name:
            continue
        ir = irs.get(str(ir_name))
        kind = str((ir.attrs.get("kind") if ir else "") or "")
        if "self" in kind.lower() or "shir" in kind.lower():
            dims.append({"dimension": "integration_runtime",
                         "status": "manual_refactor",
                         "evidence": [a.id] + ([ir.id] if ir else []),
                         "detail": "SHIR -> on-premises data gateway / VNet "
                                   "data gateway exige review de rede"})
        else:
            dims.append({"dimension": "integration_runtime",
                         "status": "compatible_with_change",
                         "evidence": [a.id] + ([ir.id] if ir else []),
                         "detail": "Azure IR tem equivalente; revisar regiao"})

    # -- parameters --------------------------------------------------------
    if pipeline.attrs.get("has_global_parameters") or _facts(
            [f for f in facts if f.kind == "mig.global_parameter"
             and f.subject.get("pipeline_id") == pid], "mig.global_parameter"):
        gps = [f for f in _facts(facts, "mig.global_parameter")
               if f.subject.get("pipeline_id") == pid]
        dims.append({"dimension": "parameter",
                     "status": "compatible_with_change",
                     "evidence": [f.id for f in gps] or [pipeline.id],
                     "detail": "global parameters -> variable library"})
        recs.append({"kind": "variable_library_candidate",
                     "source": pid, "parameters": [
                         str(f.subject.get("name")) for f in gps] or None,
                     "target_type": "variable_library"})

    # -- expressions -------------------------------------------------------
    exprs = [f for f in _facts(facts, "mig.global_parameter")
             if f.subject.get("pipeline_id") == pid]
    if pipeline.attrs.get("has_global_parameters"):
        dims.append({"dimension": "expression",
                     "status": "compatible_with_change",
                     "evidence": [f.id for f in exprs] or [pipeline.id],
                     "detail": "@globalParameters -> "
                              "@pipeline.libraryVariables"})

    return {"pipeline_id": pid, "dimensions": dims, "recommendations": recs}


def _edge_uses(facts: list[Any], activity_id: str, owner: str) -> list[str]:
    out = []
    for e in facts:
        if e.kind != "dep.edge":
            continue
        if e.subject.get("src") != activity_id:
            continue
        if e.subject.get("relation") != "uses":
            continue
        dst = str(e.subject.get("dst", ""))
        if dst.startswith(f"{owner}/ls:"):
            out.append(dst.rsplit(":", 1)[-1])
    return out


def check_connection_sharing(facts: list[Any]) -> list[dict[str, Any]]:
    """Two pipelines sharing a linked service with incompatible target auth
    must NOT consolidate into one Fabric connection (prompt §78/scenario 13).
    """
    uses: dict[str, set[str]] = {}
    for e in _facts(facts, "dep.edge"):
        if e.subject.get("relation") != "uses":
            continue
        dst = str(e.subject["dst"])
        if "/ls:" in dst:
            uses.setdefault(dst, set()).add(str(e.subject["src"]))
    findings: list[dict[str, Any]] = []
    ls_facts = {f.subject.get("ls_id"): f
                for f in _facts(facts, "mig.linked_service")}
    for ls_ref, users in sorted(uses.items()):
        if len(users) < 2:
            continue
        ls = ls_facts.get(ls_ref)
        auth = str((ls.attrs.get("auth_kind") if ls else "") or "")
        if auth not in SUPPORTED_AUTH or not ls:
            findings.append({
                "kind": "do_not_consolidate",
                "linked_service": ls_ref,
                "consumers": sorted(users),
                "reason": f"auth_kind {auth or 'unknown'} incompativel: "
                          f"manter conexoes separadas"})
    return findings


def assess_pipelines(facts: list[Any]) -> list[dict[str, Any]]:
    return [assess_pipeline(p, facts)
            for p in _facts(facts, "mig.pipeline")]


__all__ = [
    "MANUAL_ACTIVITIES", "SUPPORTED_ACTIVITIES", "SUPPORTED_AUTH",
    "UNSUPPORTED_ACTIVITIES", "assess_pipeline", "assess_pipelines",
    "check_connection_sharing",
]
