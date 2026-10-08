"""Fabric topology graph builder (SDD FABRIC_GRAPH_TOKENSAVE, P0-D).

Fabric facts -> typed nodes/edges::

    capacity --hosts--> workspace
    workspace --contains--> item (notebook / sjd / lakehouse / pipeline / env)
    notebook|spark_job --uses--> lakehouse          (default lakehouse)
    environment --defines_runtime--> spark_job|notebook
    pipeline --invokes--> notebook|spark_job
    pipeline --writes_to--> lakehouse                (explicit activity ref)
    lakehouse --contains--> onelake_table|shortcut
    shortcut --points_to--> target (onelake item / external url)
    shortcut --authenticates_via--> connection|workspace_identity
    workspace --has_identity--> workspace_identity
    workspace_role --member--> identity
    onelake.security_role --grants--> onelake scope
    identity --member_of--> onelake.security_role

Every edge carries the fact id that produced it.  A reference to an object
absent from the facts produces no edge and lands in ``graph.unresolved`` —
never inferred from display names.
"""
from __future__ import annotations

from typing import Any

from sparkforge_azure.graph.model import Edge, Graph, Node, Provenance, node_id


def _prov(source: str, observed_at: str | None = None) -> Provenance:
    return Provenance("artifact", source, observed_at)


def build_fabric_graph(facts: list[Any], *, case: dict[str, Any] | None = None,
                       sources: dict[str, str] | None = None) -> Graph:
    """Two passes: nodes first, edges second (same discipline as
    ``graph.access`` — an edge never materializes an absent node)."""
    g = Graph()
    prov_default = _prov(",".join(sorted((sources or {}).values()))
                         or "bundle")

    def fprov(f: Any) -> Provenance:
        p = f.provenance if isinstance(f.provenance, dict) else {}
        return _prov(str(p.get("source") or "bundle"), p.get("observed_at"))

    def unresolved(reason: str, **ctx: Any) -> None:
        g.add_unresolved({"reason": reason, **ctx})

    # --- nodes ------------------------------------------------------------
    for f in facts:
        kind = f.kind
        if kind == "fabric.capacity":
            g.add_node(Node(node_id("fabric", "capacity",
                                    str(f.subject["capacity_id"])),
                            "capacity", "fabric",
                            attrs=dict(f.attrs), provenance=fprov(f)))
        elif kind == "fabric.workspace":
            g.add_node(Node(node_id("fabric", "workspace",
                                    str(f.subject["workspace_id"])),
                            "workspace", "fabric",
                            attrs=dict(f.attrs), provenance=fprov(f)))
        elif kind == "fabric.workspace_identity":
            g.add_node(Node(node_id(
                "fabric", "workspace_identity",
                f"{f.subject['workspace_id']}:{f.subject['principal_id']}"),
                "workspace_identity", "fabric", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind in {"fabric.lakehouse", "fabric.notebook",
                      "fabric.spark_job", "fabric.environment",
                      "fabric.pipeline", "fabric.item"}:
            nkind = kind.split(".", 1)[1]
            key = str(f.subject.get("item_id"))
            g.add_node(Node(node_id("fabric", nkind, key), nkind, "fabric",
                            attrs=dict(f.attrs), provenance=fprov(f)))
        elif kind == "onelake.table":
            g.add_node(Node(node_id(
                "fabric", "onelake_table",
                f"{f.subject['lakehouse_id']}:{f.subject['name']}"),
                "onelake_table", "fabric", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "onelake.path":
            g.add_node(Node(node_id(
                "fabric", "onelake_path",
                f"{f.subject['item_id']}:{f.subject['path']}"),
                "onelake_path", "fabric", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "onelake.security_role":
            g.add_node(Node(node_id(
                "fabric", "onelake_role",
                f"{f.subject['item_id']}:{f.subject['role']}"),
                "onelake_role", "fabric", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "fabric.shortcut":
            g.add_node(Node(node_id(
                "fabric", "shortcut", str(f.subject["shortcut_id"])),
                "shortcut", "fabric", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "fabric.connection":
            g.add_node(Node(node_id(
                "fabric", "connection", str(f.subject["connection_id"])),
                "connection", "fabric", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "fabric.workspace_role":
            g.add_node(Node(node_id(
                "fabric", "identity", str(f.subject["principal"])),
                "identity", "fabric",
                attrs={"role_on": str(f.subject["workspace_id"]),
                       "role": str(f.attrs.get("role", ""))},
                provenance=fprov(f)))
        elif kind == "entra.principal":
            g.add_node(Node(node_id("fabric", "identity",
                                    str(f.subject["id"])),
                            "identity", "fabric", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "fabric.pipeline_activity":
            g.add_node(Node(node_id(
                "fabric", "pipeline_activity",
                f"{f.subject['pipeline_id']}:{f.subject['name']}"),
                "pipeline_activity", "fabric", attrs=dict(f.attrs),
                provenance=fprov(f)))

    node_ids = set(g.nodes)

    def edge(src: str, rel: str, dst: str, prov: Provenance) -> None:
        if src in node_ids and dst in node_ids:
            g.add_edge(Edge(src, rel, dst, provenance=prov))
        else:
            unresolved("edge_endpoint_absent", src=src, rel=rel, dst=dst)

    # --- edges ------------------------------------------------------------
    for f in facts:
        prov = fprov(f)
        if f.kind == "fabric.workspace_capacity":
            edge(node_id("fabric", "capacity", str(f.subject["capacity_id"])),
                 "hosts",
                 node_id("fabric", "workspace", str(f.subject["workspace_id"])),
                 prov)
        elif f.kind == "fabric.workspace_identity":
            edge(node_id("fabric", "workspace", str(f.subject["workspace_id"])),
                 "has_identity",
                 node_id("fabric", "workspace_identity",
                         f"{f.subject['workspace_id']}:{f.subject['principal_id']}"),
                 prov)
        elif f.kind == "fabric.workspace_role":
            edge(node_id("fabric", "identity", str(f.subject["principal"])),
                 "member_of",
                 node_id("fabric", "workspace", str(f.subject["workspace_id"])),
                 prov)
        elif f.kind in {"fabric.lakehouse", "fabric.notebook",
                        "fabric.spark_job", "fabric.environment",
                        "fabric.pipeline"}:
            ws = str(f.attrs.get("workspace_id", ""))
            if ws:
                edge(node_id("fabric", "workspace", ws), "contains",
                     node_id("fabric", f.kind.split(".", 1)[1],
                             str(f.subject["item_id"])), prov)
        elif f.kind == "onelake.table":
            edge(node_id("fabric", "lakehouse", str(f.subject["lakehouse_id"])),
                 "contains",
                 node_id("fabric", "onelake_table",
                         f"{f.subject['lakehouse_id']}:{f.subject['name']}"),
                 prov)
        elif f.kind == "onelake.path":
            edge(node_id("fabric", "lakehouse", str(f.subject["item_id"])),
                 "contains",
                 node_id("fabric", "onelake_path",
                         f"{f.subject['item_id']}:{f.subject['path']}"), prov)
        elif f.kind == "onelake.security_role":
            role_node = node_id("fabric", "onelake_role",
                                f"{f.subject['item_id']}:{f.subject['role']}")
            edge(node_id("fabric", "lakehouse", str(f.subject["item_id"])),
                 "secured_by", role_node, prov)
            for member in f.attrs.get("members") or []:
                edge(node_id("fabric", "identity", str(member)),
                     "member_of", role_node, prov)
            for scope in f.attrs.get("scopes") or []:
                if isinstance(scope, dict) and scope.get("table"):
                    edge(role_node, "grants",
                         node_id("fabric", "onelake_table",
                                 f"{f.subject['item_id']}:{scope['table']}"),
                         prov)
        elif f.kind == "fabric.shortcut":
            sc = node_id("fabric", "shortcut", str(f.subject["shortcut_id"]))
            edge(node_id("fabric", "lakehouse", str(f.subject["lakehouse_id"])),
                 "contains", sc, prov)
            tgt_item = str(f.attrs.get("target_item_id", ""))
            tgt_url = str(f.attrs.get("target_url", ""))
            if tgt_item:
                edge(sc, "points_to",
                     node_id("fabric", "lakehouse", tgt_item), prov)
            elif tgt_url:
                tnode = node_id("fabric", "external_target", tgt_url)
                g.add_node(Node(tnode, "external_target", "fabric",
                                attrs={"url": tgt_url}, provenance=prov))
                node_ids.add(tnode)
                edge(sc, "points_to", tnode, prov)
            else:
                unresolved("shortcut_target_missing",
                           shortcut_id=str(f.subject["shortcut_id"]))
            cid = str(f.attrs.get("connection_id", ""))
            if cid:
                edge(sc, "authenticates_via",
                     node_id("fabric", "connection", cid), prov)
            elif f.attrs.get("workspace_identity"):
                unresolved("workspace_identity_link_unresolved",
                           shortcut_id=str(f.subject["shortcut_id"]))
        elif f.kind == "fabric.pipeline_activity":
            act = node_id("fabric", "pipeline_activity",
                          f"{f.subject['pipeline_id']}:{f.subject['name']}")
            edge(node_id("fabric", "pipeline", str(f.subject["pipeline_id"])),
                 "has_activity", act, prov)
            ref = str(f.attrs.get("reference_item_id", ""))
            if ref:
                for kind in ("notebook", "spark_job", "lakehouse"):
                    edge(act, "invokes" if kind != "lakehouse" else "writes_to",
                         node_id("fabric", kind, ref), prov)

    # --- case overlay ------------------------------------------------------
    if case:
        principal = str(case.get("principal", {}).get("id", ""))
        target = case.get("target") or {}
        pnode = node_id("fabric", "identity", principal)
        g.add_node(Node(pnode, "identity", "fabric",
                        attrs={"type": case.get("principal", {}).get("type")},
                        provenance=prov_default))
        node_ids.add(pnode)
        if target.get("lakehouse_id"):
            edge(pnode, str(case.get("operation", "accesses")),
                 node_id("fabric", "lakehouse", str(target["lakehouse_id"])),
                 prov_default)
        job = case.get("job") or {}
        dlh = str(job.get("default_lakehouse_id")
                  or job.get("defaultLakehouseArtifactId") or "")
        if dlh:
            jobnode = node_id("fabric", "spark_job",
                              str(job.get("id") or "case-job"))
            g.add_node(Node(jobnode, "spark_job", "fabric",
                            attrs={"from_case": True}, provenance=prov_default))
            node_ids.add(jobnode)
            edge(jobnode, "uses",
                 node_id("fabric", "lakehouse", dlh), prov_default)
    return g


__all__ = ["build_fabric_graph"]
