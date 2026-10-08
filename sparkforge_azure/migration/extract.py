"""Deterministic extractors: migration artifacts -> Facts
(SDD MIGRATION_INVENTORY).

Same contract as ``stream.extract``: no judgement — Facts are anchored
observations.  Asset identity is the official/ARM id; display names are
attributes.  Dependency edges are typed facts (`dep.edge`).  Secrets in
linked services never reach Facts — ``collectors.redact`` strips them at
the boundary.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure.findings.models import Fact, sort_facts
from sparkforge_azure.migration.model import canonical_id

Prov = dict[str, Any]

_ENV_KEYS = ("tenant_id", "subscription_id", "workspace_id", "factory_id",
             "region", "cloud")


def _p(prov: Prov, extractor: str) -> Prov:
    return {**prov, "extractor": extractor}


def _num(v: Any) -> int | float | None:
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _fact(kind: str, subject: dict[str, Any], attrs: dict[str, Any],
          prov: Prov) -> Fact:
    return Fact(kind=kind, subject=subject,
                attrs={k: v for k, v in attrs.items() if v is not None},
                provenance=dict(prov))


def _dep(facts: list[Fact], src: str, relation: str, dst: str,
         prov: Prov) -> None:
    """Typed dependency edge as a fact (source graph, prompt §16)."""
    facts.append(_fact(
        "dep.edge",
        {"src": str(src), "relation": str(relation), "dst": str(dst)},
        {}, prov))


def _extract_pipeline(pipe: Mapping[str, Any], owner: str, owner_kind: str,
                      prov: Prov) -> list[Fact]:
    """Shared ADF/Synapse pipeline shape -> pipeline/activity/dep facts."""
    facts: list[Fact] = []
    pid = canonical_id(pipe.get("id"), "pipeline", pipe.get("name"))
    facts.append(_fact(
        "mig.pipeline",
        {"pipeline_id": pid, "owner": owner},
        {"name": pipe.get("name"), "owner_kind": owner_kind,
         "activity_count": len(pipe.get("activities") or []),
         "has_global_parameters": bool(pipe.get("global_parameters"))}, prov))
    _dep(facts, owner, "contains", pid, prov)
    for dep in pipe.get("depends_on") or []:
        _dep(facts, pid, "depends_on", str(dep), prov)
    for act in pipe.get("activities") or []:
        if not isinstance(act, Mapping):
            continue
        aid = f"{pid}#{act.get('name', act.get('type', '?'))}"
        facts.append(_fact(
            "mig.activity",
            {"activity_id": aid, "pipeline_id": pid},
            {"name": act.get("name"), "type": act.get("type"),
             "ir_ref": act.get("integration_runtime"),
             "expressions": act.get("expressions")}, prov))
        _dep(facts, pid, "contains", aid, prov)
        for dep in act.get("depends_on") or []:
            _dep(facts, aid, "depends_on", f"{pid}#{dep}", prov)
        ls = act.get("linked_service")
        if ls:
            _dep(facts, aid, "uses", f"{owner}/ls:{ls}", prov)
        for ds in act.get("dataset_refs") or []:
            rel = "writes" if str(ds.get("mode", "read")) == "write" else "reads"
            _dep(facts, aid, rel, f"{owner}/ds:{ds.get('name', ds)}", prov)
        for nb in act.get("notebook_refs") or []:
            _dep(facts, aid, "invokes", f"{owner}/nb:{nb}", prov)
        ir = act.get("integration_runtime")
        if ir:
            _dep(facts, aid, "depends_on", f"{owner}/ir:{ir}", prov)
    for gp in pipe.get("global_parameters") or []:
        name = gp.get("name") if isinstance(gp, Mapping) else gp
        facts.append(_fact(
            "mig.global_parameter",
            {"parameter_id": f"{pid}#{name}", "pipeline_id": pid,
             "name": str(name)},
            {"type": gp.get("type") if isinstance(gp, Mapping) else None},
            prov))
        _dep(facts, pid, "uses", f"{owner}/gp:{name}", prov)
    return facts


def extract_estate(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    """Estate inventory -> asset + dependency facts (prompt §14/§16)."""
    prov = _p(prov, "extract_estate")
    facts: list[Fact] = []
    for fac in payload.get("adf_factories") or []:
        if not isinstance(fac, Mapping):
            continue
        fid = canonical_id(fac.get("id"), "adf_factory", fac.get("name"))
        facts.append(_fact(
            "mig.adf_factory", {"factory_id": fid},
            {"name": fac.get("name"), "location": fac.get("location")}, prov))
        for pipe in fac.get("pipelines") or []:
            if isinstance(pipe, Mapping):
                facts.extend(_extract_pipeline(pipe, fid, "adf_factory", prov))
        for ls in fac.get("linked_services") or []:
            if not isinstance(ls, Mapping):
                continue
            lid = canonical_id(ls.get("id"), "linked_service", ls.get("name"))
            facts.append(_fact(
                "mig.linked_service",
                {"ls_id": lid, "owner": fid},
                {"name": ls.get("name"), "type": ls.get("type"),
                 "auth_kind": ls.get("auth_kind"),
                 "target_type": ls.get("target_type")}, prov))
            _dep(facts, fid, "contains", lid, prov)
        for ds in fac.get("datasets") or []:
            if not isinstance(ds, Mapping):
                continue
            did = canonical_id(ds.get("id"), "dataset", ds.get("name"))
            facts.append(_fact(
                "mig.dataset", {"dataset_id": did, "owner": fid},
                {"name": ds.get("name"), "type": ds.get("type"),
                 "format": ds.get("format"), "path": ds.get("path"),
                 "linked_service": ds.get("linked_service")}, prov))
            _dep(facts, fid, "contains", did, prov)
            if ds.get("linked_service"):
                _dep(facts, did, "uses",
                     f"{fid}/ls:{ds['linked_service']}", prov)
        for tr in fac.get("triggers") or []:
            if not isinstance(tr, Mapping):
                continue
            tid = canonical_id(tr.get("id"), "trigger", tr.get("name"))
            facts.append(_fact(
                "mig.trigger", {"trigger_id": tid, "owner": fid},
                {"name": tr.get("name"), "type": tr.get("type")}, prov))
            _dep(facts, fid, "contains", tid, prov)
            for pl in tr.get("pipelines") or []:
                _dep(facts, tid, "invokes", f"{fid}/pipeline:{pl}", prov)
        for ir in fac.get("integration_runtimes") or []:
            if not isinstance(ir, Mapping):
                continue
            rid = canonical_id(ir.get("id"), "integration_runtime",
                               ir.get("name"))
            facts.append(_fact(
                "mig.integration_runtime",
                {"ir_id": rid, "owner": fid},
                {"name": ir.get("name"), "kind": ir.get("kind"),
                 "nodes": _num(ir.get("nodes")),
                 "region": ir.get("region")}, prov))
            _dep(facts, fid, "contains", rid, prov)
    for ws in payload.get("synapse_workspaces") or []:
        if not isinstance(ws, Mapping):
            continue
        wid = canonical_id(ws.get("id"), "synapse_workspace",
                           ws.get("name"))
        facts.append(_fact(
            "mig.synapse_workspace", {"workspace_id": wid},
            {"name": ws.get("name"), "location": ws.get("location")}, prov))
        for pipe in ws.get("pipelines") or []:
            if isinstance(pipe, Mapping):
                facts.extend(_extract_pipeline(pipe, wid,
                                               "synapse_workspace", prov))
        for ls in ws.get("linked_services") or []:
            if not isinstance(ls, Mapping):
                continue
            lid = canonical_id(ls.get("id"), "linked_service", ls.get("name"))
            facts.append(_fact(
                "mig.linked_service",
                {"ls_id": lid, "owner": wid},
                {"name": ls.get("name"), "type": ls.get("type"),
                 "auth_kind": ls.get("auth_kind"),
                 "target_type": ls.get("target_type")}, prov))
            _dep(facts, wid, "contains", lid, prov)
        for nb in ws.get("notebooks") or []:
            if not isinstance(nb, Mapping):
                continue
            nid = canonical_id(nb.get("id"), "synapse_notebook",
                               nb.get("name"))
            facts.append(_fact(
                "mig.synapse_notebook",
                {"notebook_id": nid, "owner": wid},
                {"name": nb.get("name"), "path": nb.get("path"),
                 "language": nb.get("language")}, prov))
            _dep(facts, wid, "contains", nid, prov)
            if nb.get("spark_pool_id"):
                _dep(facts, nid, "runs_on",
                     f"{wid}/pool:{nb['spark_pool_id']}", prov)
            for ref in nb.get("lake_database_refs") or []:
                _dep(facts, nid, "references", f"{wid}/ldb:{ref}", prov)
            for ref in nb.get("notebook_calls") or []:
                _dep(facts, nid, "invokes", f"{wid}/nb:{ref}", prov)
            for adls in nb.get("adls_paths") or []:
                _dep(facts, nid, "reads", f"adls:{adls}", prov)
        for pool in ws.get("spark_pools") or []:
            if not isinstance(pool, Mapping):
                continue
            spid = canonical_id(pool.get("id"), "spark_pool",
                                pool.get("name"))
            facts.append(_fact(
                "mig.spark_pool",
                {"pool_id": spid, "owner": wid},
                {"name": pool.get("name"), "node_size": pool.get("node_size"),
                 "node_count": _num(pool.get("node_count")),
                 "spark_version": pool.get("spark_version"),
                 "libraries": pool.get("libraries"),
                 "spark_configs": pool.get("spark_configs")}, prov))
            _dep(facts, wid, "contains", spid, prov)
        for lib in ws.get("libraries") or []:
            if not isinstance(lib, Mapping):
                continue
            facts.append(_fact(
                "mig.library",
                {"library": str(lib.get("name")), "owner": wid},
                {"kind": lib.get("kind"), "version": lib.get("version")},
                prov))
            _dep(facts, wid, "contains",
                 f"{wid}/lib:{lib.get('name')}", prov)
        for cfg in ws.get("spark_configs") or []:
            if not isinstance(cfg, Mapping):
                continue
            facts.append(_fact(
                "mig.spark_config",
                {"key": str(cfg.get("key")), "owner": wid},
                {"value": cfg.get("value")}, prov))
        for ldb in ws.get("lake_databases") or []:
            if not isinstance(ldb, Mapping):
                continue
            lid = canonical_id(ldb.get("id"), "lake_database",
                               ldb.get("name"))
            facts.append(_fact(
                "mig.lake_database", {"lake_database_id": lid, "owner": wid},
                {"name": ldb.get("name")}, prov))
            _dep(facts, wid, "contains", lid, prov)
            for tbl in ldb.get("tables") or []:
                if not isinstance(tbl, Mapping):
                    continue
                facts.append(_fact(
                    "mig.table",
                    {"table": f"{lid}/{tbl.get('name')}"},
                    {"name": tbl.get("name"), "kind": tbl.get("kind"),
                     "format": tbl.get("format"),
                     "location": tbl.get("location")}, prov))
                _dep(facts, lid, "contains",
                     f"{lid}/table:{tbl.get('name')}", prov)
    for ws in payload.get("fabric_workspaces") or []:
        if not isinstance(ws, Mapping):
            continue
        wid = canonical_id(ws.get("id"), "fabric_workspace",
                           ws.get("name"))
        facts.append(_fact(
            "mig.fabric_workspace", {"fabric_workspace_id": wid},
            {"name": ws.get("name")}, prov))
        for item in ws.get("items") or []:
            if not isinstance(item, Mapping):
                continue
            iid = canonical_id(item.get("id"), "fabric_item",
                               item.get("name"))
            facts.append(_fact(
                "mig.fabric_item",
                {"item_id": iid, "fabric_workspace_id": wid},
                {"name": item.get("name"), "type": item.get("type")}, prov))
            _dep(facts, wid, "contains", iid, prov)
    for sa in payload.get("storage_accounts") or []:
        if not isinstance(sa, Mapping):
            continue
        sid = canonical_id(sa.get("id"), "storage_account", sa.get("name"))
        facts.append(_fact(
            "mig.storage_account", {"storage_account_id": sid},
            {"name": sa.get("name"), "kind": sa.get("kind"),
             "retirement": sa.get("retirement"),
             "hns": sa.get("hns")}, prov))
        for path in sa.get("adls_paths") or []:
            if not isinstance(path, Mapping):
                continue
            facts.append(_fact(
                "mig.adls_path",
                {"path": f"{sid}/{path.get('path')}"},
                {"name": path.get("path"), "format": path.get("format"),
                 "size_gb": _num(path.get("size_gb")),
                 "retirement": path.get("retirement")}, prov))
            _dep(facts, sid, "contains",
                 f"{sid}/path:{path.get('path')}", prov)
    return sort_facts(facts)


def extract_assessment(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    """Official Microsoft assessment export -> assessment.* facts.

    DATA_ONLY: official status is recorded verbatim (prompt §31-34); the
    internal mapping happens in ``compat`` with provenance preserved.
    """
    prov = _p(prov, "extract_assessment")
    facts: list[Fact] = []
    tool = str(payload.get("tool", "unknown"))
    assessed_at = payload.get("assessed_at")
    for res in payload.get("results") or []:
        if not isinstance(res, Mapping):
            continue
        facts.append(_fact(
            "mig.assessment_result",
            {"asset_id": str(res.get("asset_id",
                                     res.get("asset_name", "unknown")))},
            {"tool": tool, "assessed_at": assessed_at,
             "official_status": res.get("official_status"),
             "notes": res.get("notes")}, prov))
    return sort_facts(facts)


def extract_validation(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    """Post-migration evidence -> validation.* facts (prompt §147)."""
    prov = _p(prov, "extract_validation")
    facts: list[Fact] = []
    for res in payload.get("results") or []:
        if not isinstance(res, Mapping):
            continue
        facts.append(_fact(
            "mig.validation",
            {"asset_id": str(res.get("asset_id", "unknown")),
             "dimension": str(res.get("dimension", "unknown")),
             "metric": str(res.get("metric", "unknown"))},
            {"source_value": res.get("source_value"),
             "target_value": res.get("target_value"),
             "verdict": res.get("verdict"),
             "observed_at": res.get("observed_at")}, prov))
    return sort_facts(facts)


def _env_values(value: Any, key: str, out: set[str]) -> None:
    if isinstance(value, Mapping):
        for k, v in value.items():
            if isinstance(k, str) and k.lower() == key and isinstance(
                    v, str) and v:
                out.add(v.lower())
            _env_values(v, key, out)
    elif isinstance(value, list):
        for item in value:
            _env_values(item, key, out)


def extract_env(artifacts: Mapping[str, Any],
                sources: Mapping[str, str]) -> list[Fact]:
    facts: list[Fact] = []
    for name, payload in sorted(artifacts.items()):
        if not isinstance(payload, Mapping):
            continue
        prov = {"source": sources.get(name, name), "mode": "bundle",
                "observed_at": None, "extractor": "extract_env"}
        for key in _ENV_KEYS:
            found: set[str] = set()
            _env_values(payload, key, found)
            for value in sorted(found):
                facts.append(Fact(
                    kind="environment.scope",
                    subject={"source": sources.get(name, name), "key": key,
                             "value": value},
                    attrs={"key": key, "value": value},
                    provenance=dict(prov)))
    return facts


_EXTRACTORS = {
    "estate": extract_estate,
    "assessment": extract_assessment,
    "validation": extract_validation,
}


def extract_all(artifacts: Mapping[str, Any],
                sources: Mapping[str, str]) -> list[Fact]:
    """Run every extractor whose artifact is present.

    Artifacts are redacted at the extraction boundary: bundle files stay
    byte-identical on disk, but Facts never carry secret material.
    """
    from sparkforge_azure.collectors.redact import redact

    facts: list[Fact] = []
    for name, payload in artifacts.items():
        extractor = _EXTRACTORS.get(name)
        if extractor is None or payload is None:
            continue
        prov = {"source": sources.get(name, name), "mode": "bundle",
                "observed_at": None}
        facts.extend(extractor(redact(payload), prov))
    facts.extend(extract_env(artifacts, sources))
    return sort_facts(facts)


__all__ = [
    "extract_all", "extract_assessment", "extract_env", "extract_estate",
    "extract_validation",
]
