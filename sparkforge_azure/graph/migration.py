"""Migration topology graph builder (Cycle 5, SDDs MIGRATION_INVENTORY /
MIGRATION_PLANNER).

Facts -> typed nodes/edges over the ``migration`` layer::

    adf_factory|synapse_workspace --contains--> pipeline|linked_service|...
    pipeline --contains--> activity
    activity --uses--> linked_service | --reads/writes--> dataset
    activity --depends_on--> integration_runtime|activity
    synapse_notebook --runs_on--> spark_pool | --references--> lake_database
    fabric_workspace --contains--> fabric_item
    source_asset --migrates_to{status}--> target_asset   (prompt §18-19)

Every edge carries the fact id that produced it (``attrs["fact"]``) or the
recommendation ref.  A reference to an absent node produces no edge and
lands in ``graph.unresolved`` — never an invented endpoint.
"""
from __future__ import annotations

from typing import Any

from sparkforge_azure.graph.model import Edge, Graph, Node, Provenance, node_id
from sparkforge_azure.migration.model import MIGRATION_STATUS

#: fact kind -> (node kind, subject key holding the canonical id)
_NODE_FOR = {
    "mig.adf_factory": ("adf_factory", "factory_id"),
    "mig.synapse_workspace": ("synapse_workspace", "workspace_id"),
    "mig.pipeline": ("pipeline", "pipeline_id"),
    "mig.activity": ("activity", "activity_id"),
    "mig.dataset": ("dataset", "dataset_id"),
    "mig.linked_service": ("linked_service", "ls_id"),
    "mig.trigger": ("trigger", "trigger_id"),
    "mig.integration_runtime": ("integration_runtime", "ir_id"),
    "mig.global_parameter": ("global_parameter", "parameter_id"),
    "mig.synapse_notebook": ("synapse_notebook", "notebook_id"),
    "mig.spark_pool": ("spark_pool", "pool_id"),
    "mig.lake_database": ("lake_database", "lake_database_id"),
    "mig.table": ("table", "table"),
    "mig.library": ("library", "library"),
    "mig.spark_config": ("spark_config", "key"),
    "mig.adls_path": ("adls_path", "path"),
    "mig.storage_account": ("storage_account", "storage_account_id"),
    "mig.fabric_workspace": ("fabric_workspace", "fabric_workspace_id"),
    "mig.fabric_item": ("fabric_item", "item_id"),
    "mig.assessment_result": ("assessment_result", "asset_id"),
}

#: dep.edge ref prefix -> (node kind, owner key used in subject)
_REF_KIND = {
    "/ls:": "linked_service", "/ds:": "dataset", "/gp:": "global_parameter",
    "/ir:": "integration_runtime", "/nb:": "synapse_notebook",
    "/pool:": "spark_pool", "/ldb:": "lake_database",
    "/lib:": "library", "/pipeline:": "pipeline",
    "/path:": "adls_path", "/table:": "table",
}


def _prov(source: str, observed_at: str | None = None) -> Provenance:
    return Provenance("artifact", source, observed_at)


def _ref_node_id(ref: str) -> tuple[str, str] | None:
    """Resolve a dep.edge endpoint ref to a (node kind, id)."""
    if ref.startswith("adls:"):
        return ("adls_path", ref[5:])
    for marker, kind in _REF_KIND.items():
        if marker in ref:
            owner, _, rest = ref.partition(marker)
            if kind == "adls_path":
                return (kind, f"{owner}/{rest}")
            if kind == "table":
                return (kind, f"{owner}/{rest}")
            return (kind, f"{owner}{marker[:-1]}"
                    if False else f"{ref}")
    return None


def build_migration_graph(
        facts: list[Any],
        *,
        case: dict[str, Any] | None = None,
        sources: dict[str, str] | None = None,
        recommendations: list[dict[str, Any]] | None = None,
        waves: list[dict[str, Any]] | None = None) -> Graph:
    """Two passes: asset nodes first, typed edges second."""
    g = Graph()

    def fprov(f: Any) -> Provenance:
        p = f.provenance if isinstance(f.provenance, dict) else {}
        return _prov(str(p.get("source") or "bundle"), p.get("observed_at"))

    def nid(kind: str, key: str) -> str:
        return node_id("migration", kind, key)

    # -- pass 1: asset nodes ---------------------------------------------
    for f in facts:
        spec = _NODE_FOR.get(f.kind)
        if spec is None:
            continue
        kind, key = spec
        ident = str(f.subject.get(key) or f.subject.get("name") or "?")
        attrs = dict(f.attrs)
        for extra_k, extra_v in f.subject.items():
            attrs.setdefault(extra_k, extra_v)
        g.add_node(Node(nid(kind, ident), kind, "migration",
                        attrs=attrs, provenance=fprov(f)))

    def exists(kind: str, ident: str) -> bool:
        return nid(kind, ident) in g.nodes

    # -- pass 2: dep.edge -> typed edges ----------------------------------
    for e in (f for f in facts if f.kind == "dep.edge"):
        src, dst = str(e.subject["src"]), str(e.subject["dst"])
        rel = str(e.subject["relation"])
        sref = _endpoint(src, facts)
        dref = _endpoint(dst, facts)
        if sref is None or dref is None:
            g.add_unresolved({"reason": "edge_endpoint_not_observed",
                              "relation": rel, "src": src, "dst": dst,
                              "fact": e.id})
            continue
        skind, skey = sref
        dkind, dkey = dref
        if not (exists(skind, skey) and exists(dkind, dkey)):
            g.add_unresolved({"reason": "edge_endpoint_not_observed",
                              "relation": rel, "src": src, "dst": dst,
                              "fact": e.id})
            continue
        g.add_edge(Edge(nid(skind, skey), rel, nid(dkind, dkey),
                        attrs={"fact": e.id}, provenance=fprov(e)))

    # -- pass 3: recommendation -> migrates_to + recommendation node ------
    for i, rec in enumerate(recommendations or []):
        src = str(rec.get("source") or rec.get("asset") or "")
        status = str(rec.get("migration_status")
                     or rec.get("status") or "manual")
        if status not in MIGRATION_STATUS:
            status = "manual"
        ttype = str(rec.get("target_type") or "unknown")
        tgt_key = f"{ttype}:{src or i}"
        rid = nid("recommendation", f"rec-{i}-{status}")
        g.add_node(Node(rid, "recommendation", "migration",
                        attrs={"kind": rec.get("kind"), "status": status,
                               "evidence": rec.get("evidence")},
                        provenance=_prov("assessment")))
        if src:
            sref = _endpoint(src, facts)
            if sref is not None and exists(*sref):
                g.add_edge(Edge(nid(sref[0], sref[1]), "migrates_to", rid,
                                attrs={"status": status},
                                provenance=_prov("assessment")))
                g.add_node(Node(nid(ttype, tgt_key), ttype
                                if ttype in _VALID_TARGET else
                                "fabric_item", "migration",
                                attrs={"target_type": ttype},
                                provenance=_prov("assessment")))
                g.add_edge(Edge(rid, "targets", nid(
                    ttype if ttype in _VALID_TARGET else "fabric_item",
                    tgt_key), attrs={"status": status},
                    provenance=_prov("assessment")))
            else:
                g.add_unresolved({"reason": "recommendation_source_absent",
                                  "source": src})

    # -- pass 4: waves ----------------------------------------------------
    for w in waves or []:
        wid = nid("wave", f"wave-{w.get('wave')}")
        g.add_node(Node(wid, "wave", "migration",
                        attrs={"rollback": w.get("rollback"),
                               "receipt": w.get("receipt")},
                        provenance=_prov("assessment")))
        for a in w.get("assets") or []:
            ref = _endpoint(str(a), facts)
            if ref is not None and exists(*ref):
                g.add_edge(Edge(wid, "schedules", nid(ref[0], ref[1]),
                                provenance=_prov("assessment")))
            else:
                g.add_unresolved({"reason": "wave_asset_absent",
                                  "wave": w.get("wave"), "asset": a})
    return g


_VALID_TARGET = {"fabric_pipeline", "fabric_connection",
                 "fabric_notebook", "fabric_environment",
                 "fabric_lakehouse", "fabric_shortcut",
                 "variable_library", "fabric_workspace", "fabric_item"}

_SUBJECT_KEY = {k: v for k, v in
                ((kind, key) for kind, key in _NODE_FOR.values())}


def _endpoint(ref: str, facts: list[Any]) -> tuple[str, str] | None:
    """Resolve a dep.edge/recommendation endpoint to (node kind, key).

    Order: exact canonical-id match on any asset node, then synthetic
    ``owner/kind:name`` refs, then adls: refs.
    """
    for f in facts:
        spec = _NODE_FOR.get(f.kind)
        if spec is None:
            continue
        kind, key = spec
        if str(f.subject.get(key)) == ref:
            return (kind, ref)
    if ref.startswith("adls:"):
        return None  # paths only resolve against observed mig.adls_path
    resolved = _ref_node_id(ref)
    if resolved is None:
        return None
    kind, ident = resolved
    # synthetic refs: owner/kind:name -> look up the named asset's fact
    for marker, k in _REF_KIND.items():
        if marker not in ref:
            continue
        owner, _, name = ref.partition(marker)
        for f in facts:
            spec = _NODE_FOR.get(f.kind)
            if spec is None or spec[0] != k:
                continue
            if str(f.attrs.get("name")) == name and str(
                    f.subject.get("owner", owner)).startswith(owner):
                return (k, str(f.subject.get(spec[1])))
    return (kind, ident)


__all__ = ["build_migration_graph"]
