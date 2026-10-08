"""Migration assessment pipeline (offline by default; Cycle 5).

    bundle -> casefile -> extractors -> facts -> compat/pipelines/spark/
        data -> planner -> validate -> graph -> trust -> receipt -> report

This is an *assessment*, not a failure diagnosis: the output is a
readiness report with waves, recommendations and conflicts.  AgentOps
spans are ``migration.<stage>`` (prompt §282).  Live collection stays a
separate opt-in step writing the same artifact files.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.trust import TrustEnvelope
from sparkforge_azure.azure import receipt
from sparkforge_azure.graph.migration import build_migration_graph
from sparkforge_azure.knowledgebase.vertical import compile_access_knowledge
from sparkforge_azure.migration import (
    casefile,
    compat,
    data,
    extract,
    inventory,
    pipelines,
    planner,
    spark,
    validate,
)
from sparkforge_azure.migration.fingerprint import migration_fingerprint
from sparkforge_azure.observability.context_ledger import shared_ledger
from sparkforge_azure.rules.engine import judge
from sparkforge_azure.rules.loader import load_catalog


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def _record_stage(name: str, start: float, resultado: dict[str, Any],
                  stages: dict[str, dict[str, float]]) -> float:
    shared_ledger().record(
        name=f"migration.{name}", resultado=resultado,
        detail_level="stage", outcome="ok", start_time=start,
        channel="assess")
    elapsed = round((time.time() - start) * 1000, 3)
    stages[name] = {"ms": elapsed}
    return elapsed


def _migration_rules() -> list[dict[str, Any]]:
    return [r for r in load_catalog()
            if str(r.get("id", "")).startswith("SF-MIG")]


def _trust_scan(bundle: casefile.MigrationBundle) -> dict[str, Any]:
    parts = [json.dumps(bundle.case, sort_keys=True, default=str),
             json.dumps(bundle.artifacts, sort_keys=True, default=str)]
    for nb in bundle.notebook_files:
        try:
            parts.append(nb.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    payload = "\n".join(parts) or "{}"
    env = TrustEnvelope.external(payload, origin="migration.bundle")
    d = env.to_dict()
    d.pop("content", None)
    return {"trust": d["trust"],
            "instruction_authority": d["instruction_authority"],
            "taint": d["taint"]}


def _notebook_sources(bundle: casefile.MigrationBundle) -> dict[str, str]:
    out: dict[str, str] = {}
    for nb in bundle.notebook_files:
        try:
            out[str(nb.relative_to(bundle.root)).replace("\\", "/")] = (
                nb.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return out


def assess_bundle(bundle: casefile.MigrationBundle) -> dict[str, Any]:
    """facts -> per-asset readiness + recommendations + waves +
    validation.  Deterministic; official assessment stays evidence."""
    facts = list(extract.extract_all(bundle.artifacts, bundle.sources))

    # -- per-pipeline assessment ------------------------------------------
    pipe_reports = pipelines.assess_pipelines(facts)
    readiness: dict[str, str] = {}
    dim_by_asset: dict[str, list[dict[str, Any]]] = {}
    recs: list[dict[str, Any]] = []
    for rep in pipe_reports:
        pid = str(rep["pipeline_id"])
        dim_by_asset[pid] = rep["dimensions"]
        recs.extend(dict(r, asset=pid) for r in rep["recommendations"])
        readiness[pid] = compat.assess_readiness(
            facts, rep["dimensions"], asset_key=pid)["readiness"]

    # -- notebooks ---------------------------------------------------------
    sources = _notebook_sources(bundle)
    nb_reports = []
    nbs = [{"name": str(f.attrs.get("name")),
            "path": str(f.attrs.get("path") or "")}
           for f in _facts(facts, "mig.synapse_notebook")]
    for f in _facts(facts, "mig.synapse_notebook"):
        path = str(f.attrs.get("path") or "")
        src = sources.get(path.lstrip("/")) or sources.get(
            Path(path).name)
        rep = spark.assess_notebook(f, src, path or "unknown")
        nb_reports.append(rep)
        readiness[str(rep["notebook_id"])] = rep["readiness"]
    nb_graph = spark.notebook_dependency_graph(nbs, sources)

    # -- libraries / spark configs / data strategies -----------------------
    lib_reports = spark.assess_libraries(facts)
    for rep in lib_reports:
        readiness[f"lib:{rep['library']}"] = rep["readiness"]
    config_reports = [
        {"key": str(f.subject.get("key")),
         "owner": f.subject.get("owner"),
         "classification": spark.classify_spark_config(
             str(f.subject.get("key")))}
        for f in _facts(facts, "mig.spark_config")]
    for rep in config_reports:
        readiness[f"cfg:{rep['key']}"] = (
            "READY" if rep["classification"] == "supported"
            else "REVIEW" if rep["classification"] == "not_migratable"
            else "UNRESOLVED")
    data_recs = data.recommend_data_strategy(facts)
    recs.extend(data_recs)

    # -- readiness roll-up: any asset with a pipeline/notebook/etc ---------
    per_asset: dict[str, Any] = {}
    for f in facts:
        if not f.kind.startswith("mig.") or f.kind in {
                "mig.assessment_result", "mig.validation"}:
            continue
        key = str(next(iter(f.subject.values())))
        per_asset.setdefault(key, {"kind": f.kind})
    conflicts: list[dict[str, Any]] = []
    stale = False
    for key, entry in per_asset.items():
        assessed = compat.assess_readiness(
            facts, dim_by_asset.get(key, []), asset_key=key)
        stale = stale or assessed["assessment_stale"]
        conflicts.extend(assessed["conflicts"])
        entry["readiness"] = readiness.get(key) or assessed["readiness"]
        entry["conflict"] = bool(assessed["conflicts"])
        if entry["conflict"] and entry["readiness"] != "BLOCKED":
            entry["readiness"] = "REVIEW"
            readiness[key] = "REVIEW"

    summary = inventory.estate_summary(facts, readiness)
    sharing = pipelines.check_connection_sharing(facts)
    plan = planner.plan_waves(facts, readiness)
    upstream = planner.shared_upstream_blockers(facts, readiness)
    hms = data.hms_assessment(facts)
    validation = (validate.validate_migration(facts)
                  if _facts(facts, "mig.validation") else None)
    return {
        "facts": facts,
        "estate": summary,
        "readiness": readiness,
        "per_asset": per_asset,
        "pipelines": pipe_reports,
        "notebooks": nb_reports,
        "notebook_graph": nb_graph,
        "libraries": lib_reports,
        "spark_configs": config_reports,
        "recommendations": recs,
        "connection_sharing": sharing,
        "conflicts": conflicts,
        "assessment_stale": stale,
        "hms": hms,
        "plan": plan,
        "upstream_blockers": upstream,
        "validation": validation,
    }


def _knowledge_for(result: dict[str, Any]) -> dict[str, Any]:
    """Scoped knowledge: layer = the assessment stage that owns the worst
    readiness signal (prompt §282 stage names become pack layers)."""
    if any(d["status"] == "unsupported"
           for r in result["pipelines"] for d in r["dimensions"]):
        layer = "compatibility"
    elif result["conflicts"]:
        layer = "compatibility"
    elif any(n["readiness"] in {"BLOCKED", "MANUAL"}
             for n in result["notebooks"]):
        layer = "spark"
    elif result["plan"]["status"] == "REVIEW":
        layer = "plan"
    elif result["validation"] and result["validation"]["overall"] != "pass":
        layer = "validation"
    elif result["recommendations"]:
        layer = "data"
    else:
        layer = "inventory"
    return compile_access_knowledge(
        layer, "migration assessment", vertical="migration")


def run_migration_case(root: str | Path,
                       *, profile: str = "balanced") -> dict[str, Any]:
    """Run the full offline migration assessment on a bundle directory."""
    stage_ms: dict[str, dict[str, float]] = {}
    t = time.time()
    bundle = casefile.load_bundle(root)
    _record_stage("load", t, {"case": str(bundle.case.get("name", ""))},
                  stage_ms)

    t = time.time()
    result = assess_bundle(bundle)
    facts = result["facts"]
    _record_stage("inventory", t,
                  {"facts": len(facts),
                   "assets": result["estate"]["asset_count"]}, stage_ms)
    _record_stage("assess", t, {"pipelines": len(result["pipelines"]),
                                "notebooks": len(result["notebooks"])},
                  stage_ms)

    t = time.time()
    rule_findings, skipped = judge(
        facts, _migration_rules(), runtime={}, return_skipped=True)
    findings = [f for f in rule_findings]
    _record_stage("compatibility", t,
                  {"findings": len(findings), "skipped": len(skipped)},
                  stage_ms)

    t = time.time()
    graph = build_migration_graph(
        facts, case=bundle.case, sources=bundle.sources,
        recommendations=result["recommendations"],
        waves=result["plan"].get("waves") or [])
    _record_stage("graph", t,
                  {"nodes": len(graph.nodes), "edges": len(graph.edges)},
                  stage_ms)

    t = time.time()
    trust = _trust_scan(bundle)
    _record_stage("validate", t,
                  {"verdict": (result["validation"] or {}).get("overall")},
                  stage_ms)

    unresolved = [
        {"asset": k, "readiness": v}
        for k, v in result["readiness"].items() if v == "UNRESOLVED"]
    unresolved.extend(
        {"asset": k, "readiness": "UNRESOLVED"}
        for k, v in result["per_asset"].items()
        if v.get("readiness") == "UNRESOLVED"
        and k not in result["readiness"])
    readiness_states = set(result["readiness"].values())
    status = "pass"
    if (result["conflicts"] or result["assessment_stale"]
            or result["plan"]["status"] == "REVIEW"
            or readiness_states & {"REVIEW", "MANUAL", "DEFERRED"}):
        status = "review"
    if result["estate"]["unsupported_count"] or "BLOCKED" in readiness_states:
        status = "blocked"
    if not facts or not result["readiness"] or (
            readiness_states == {"UNRESOLVED"}):
        status = "unresolved"

    return {
        "status": status,
        "case": str(bundle.case.get("name", "migration")),
        "case_meta": {
            "name": bundle.case.get("name", "migration"),
            "principal": dict(bundle.case.get("principal") or {}),
            "operation": bundle.case.get("operation", "migrate"),
            "target": dict(bundle.case.get("target") or {}),
            "environment_fingerprint": migration_fingerprint(
                bundle.case, facts),
        },
        "estate": result["estate"],
        "readiness": result["readiness"],
        "per_asset": result["per_asset"],
        "pipelines": result["pipelines"],
        "notebooks": result["notebooks"],
        "notebook_graph": result["notebook_graph"],
        "libraries": result["libraries"],
        "recommendations": result["recommendations"],
        "connection_sharing": result["connection_sharing"],
        "conflicts": result["conflicts"],
        "hms": result["hms"],
        "plan": result["plan"],
        "upstream_blockers": result["upstream_blockers"],
        "validation": result["validation"],
        "findings": [f.to_dict() for f in findings],
        "rules_skipped": skipped,
        "unresolved": unresolved,
        "facts": [f.to_dict() for f in facts],
        "migration_graph": graph.to_dict(),
        "knowledge": _knowledge_for(result),
        "overhead": {"graph": {"nodes": len(graph.nodes),
                               "edges": len(graph.edges)},
                     "stages": stage_ms},
        "trust": trust,
        "receipt": receipt.build(
            case=str(bundle.case.get("name", "migration")),
            profile=profile,
            tools=["casefile", "extract", "assess_bundle"],
            sources=bundle.sources, facts=len(facts),
            rules=len(findings), findings=len(findings),
            unresolved=unresolved).to_dict(),
    }


__all__ = ["assess_bundle", "run_migration_case"]
