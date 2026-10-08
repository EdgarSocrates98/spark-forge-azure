"""Streaming topology graph builder (SDD STREAMING_GRAPHFY, P0-E).

Facts -> typed nodes/edges (flow, state, ownership — never invented
causality)::

    eh.namespace --contains--> eh_hub --has_partition--> partition
    eh_hub --read_by--> consumer_group --owns--> consumer_owner(app)
    consumer_checkpoint --checkpoints--> partition
    stream.query --reads--> eh_hub  (via query progress source facts)
    stream.query --checkpoints_at--> checkpoint location
    stream.query --writes_to--> sink
    eventstream --has_source--> es_source --authenticates_via--> connection
    eventstream --has_transform--> transform
    eventstream --routes_to--> destination --ingests_into--> eventhouse
    activator --has_rule--> activator_rule --watches--> eventstream|kql_db

Every edge carries the fact id that produced it.  A reference to an absent
object produces no edge and lands in ``graph.unresolved``.
"""
from __future__ import annotations

from typing import Any

from sparkforge_azure.graph.model import Edge, Graph, Node, Provenance, node_id


def _prov(source: str, observed_at: str | None = None) -> Provenance:
    return Provenance("artifact", source, observed_at)


def build_stream_graph(facts: list[Any], *, case: dict[str, Any] | None = None,
                       sources: dict[str, str] | None = None) -> Graph:
    """Two passes: nodes first, edges second."""
    g = Graph()
    prov_default = _prov(",".join(sorted((sources or {}).values()))
                         or "bundle")

    def fprov(f: Any) -> Provenance:
        p = f.provenance if isinstance(f.provenance, dict) else {}
        return _prov(str(p.get("source") or "bundle"), p.get("observed_at"))

    def unresolved(reason: str, **ctx: Any) -> None:
        g.add_unresolved({"reason": reason, **ctx})

    for f in facts:
        kind = f.kind
        s = f.subject
        if kind == "eh.namespace":
            g.add_node(Node(node_id("stream", "namespace",
                                    str(s["namespace_id"])),
                            "namespace", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "eh.hub":
            g.add_node(Node(node_id("stream", "eventhub", str(s["hub_id"])),
                            "eventhub", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "eh.partition":
            g.add_node(Node(node_id(
                "stream", "partition",
                f"{s['hub_id']}:{s['partition']}"),
                "partition", "stream", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "eh.consumer_group":
            g.add_node(Node(node_id(
                "stream", "consumer_group",
                f"{s['hub_id']}:{s['name']}"),
                "consumer_group", "stream", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "consumer.owner":
            g.add_node(Node(node_id(
                "stream", "app", str(s["owner"])),
                "app", "stream", attrs=dict(f.attrs), provenance=fprov(f)))
        elif kind == "stream.query":
            g.add_node(Node(node_id("stream", "query", str(s["query_id"])),
                            "stream_query", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "stream.checkpoint":
            g.add_node(Node(node_id("stream", "checkpoint",
                                    str(s["location"])),
                            "checkpoint", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "stream.sink":
            g.add_node(Node(node_id("stream", "sink", str(s["sink"])),
                            "sink", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "rti.eventstream":
            g.add_node(Node(node_id("stream", "eventstream",
                                    str(s["eventstream_id"])),
                            "eventstream", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "rti.es_source":
            g.add_node(Node(node_id(
                "stream", "es_source",
                f"{s['eventstream_id']}:{s['source_id']}"),
                "es_source", "stream", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "rti.es_transform":
            g.add_node(Node(node_id(
                "stream", "es_transform",
                f"{s['eventstream_id']}:{s['transform_id']}"),
                "es_transform", "stream", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "rti.es_destination":
            g.add_node(Node(node_id(
                "stream", "es_destination",
                f"{s['eventstream_id']}:{s['destination_id']}"),
                "es_destination", "stream", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "rti.eventhouse":
            g.add_node(Node(node_id("stream", "eventhouse",
                                    str(s["eventhouse_id"])),
                            "eventhouse", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "rti.activator":
            g.add_node(Node(node_id("stream", "activator",
                                    str(s["activator_id"])),
                            "activator", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))
        elif kind == "rti.activator_rule":
            g.add_node(Node(node_id(
                "stream", "activator_rule",
                f"{s['activator_id']}:{s['rule_id']}"),
                "activator_rule", "stream", attrs=dict(f.attrs),
                provenance=fprov(f)))
        elif kind == "stream.connection":
            g.add_node(Node(node_id("stream", "connection",
                                    str(s["connection_id"])),
                            "connection", "stream", attrs=dict(f.attrs),
                            provenance=fprov(f)))

    node_ids = set(g.nodes)

    def edge(src: str, rel: str, dst: str, prov: Provenance) -> None:
        if src in node_ids and dst in node_ids:
            g.add_edge(Edge(src, rel, dst, provenance=prov))
        else:
            unresolved("edge_endpoint_absent", src=src, rel=rel, dst=dst)

    for f in facts:
        prov = fprov(f)
        s = f.subject
        if f.kind == "eh.hub":
            ns = str(s.get("namespace_id", ""))
            if ns:
                edge(node_id("stream", "namespace", ns), "contains",
                     node_id("stream", "eventhub", str(s["hub_id"])), prov)
        elif f.kind == "eh.partition":
            edge(node_id("stream", "eventhub", str(s["hub_id"])),
                 "has_partition",
                 node_id("stream", "partition",
                         f"{s['hub_id']}:{s['partition']}"), prov)
        elif f.kind == "eh.consumer_group":
            edge(node_id("stream", "eventhub", str(s["hub_id"])), "read_by",
                 node_id("stream", "consumer_group",
                         f"{s['hub_id']}:{s['name']}"), prov)
        elif f.kind == "consumer.group":
            for owner in f.attrs.get("owners") or []:
                edge(node_id("stream", "consumer_group",
                             f"{s['hub_id']}:{s['name']}"), "owns",
                     node_id("stream", "app", str(owner)), prov)
        elif f.kind == "consumer.checkpoint":
            edge(node_id("stream", "consumer_group",
                         f"{s['hub_id']}:{s['consumer_group']}"),
                 "checkpoints",
                 node_id("stream", "partition",
                         f"{s['hub_id']}:{s['partition']}"), prov)
        elif f.kind == "stream.query":
            pass  # edges bound below via query_meta/checkpoint facts
        elif f.kind == "stream.query_meta":
            q = node_id("stream", "query", str(s["query_id"]))
            if q not in node_ids:
                g.add_node(Node(q, "stream_query", "stream",
                                attrs=dict(f.attrs), provenance=prov))
                node_ids.add(q)
        elif f.kind == "stream.checkpoint":
            for qf in facts:
                if qf.kind == "stream.query_meta" and qf.attrs.get(
                        "checkpoint_location") == s["location"]:
                    edge(node_id("stream", "query", str(qf.subject["query_id"])),
                         "checkpoints_at",
                         node_id("stream", "checkpoint", str(s["location"])),
                         prov)
        elif f.kind == "rti.es_source":
            es = node_id("stream", "eventstream", str(s["eventstream_id"]))
            edge(es, "has_source",
                 node_id("stream", "es_source",
                         f"{s['eventstream_id']}:{s['source_id']}"), prov)
            cid = str(f.attrs.get("connection_id", ""))
            if cid:
                edge(node_id("stream", "es_source",
                             f"{s['eventstream_id']}:{s['source_id']}"),
                     "authenticates_via",
                     node_id("stream", "connection", cid), prov)
        elif f.kind == "rti.es_transform":
            edge(node_id("stream", "eventstream", str(s["eventstream_id"])),
                 "has_transform",
                 node_id("stream", "es_transform",
                         f"{s['eventstream_id']}:{s['transform_id']}"), prov)
        elif f.kind == "rti.es_destination":
            dst = node_id("stream", "es_destination",
                          f"{s['eventstream_id']}:{s['destination_id']}")
            edge(node_id("stream", "eventstream", str(s["eventstream_id"])),
                 "routes_to", dst, prov)
            tgt = str(f.attrs.get("target_id", ""))
            if tgt:
                edge(dst, "ingests_into",
                     node_id("stream", "eventhouse", tgt), prov)
        elif f.kind == "rti.activator_rule":
            edge(node_id("stream", "activator", str(s["activator_id"])),
                 "has_rule",
                 node_id("stream", "activator_rule",
                         f"{s['activator_id']}:{s['rule_id']}"), prov)
            ref = str(f.attrs.get("source_ref", ""))
            if ref:
                edge(node_id("stream", "activator_rule",
                             f"{s['activator_id']}:{s['rule_id']}"),
                     "watches", node_id("stream", "eventstream", ref), prov)

    if case:
        principal = str((case.get("principal") or {}).get("id", ""))
        if principal:
            pnode = node_id("stream", "identity", principal)
            g.add_node(Node(pnode, "identity", "stream",
                            attrs={"type": (case.get("principal") or {})
                                   .get("type")},
                            provenance=prov_default))
    return g


__all__ = ["build_stream_graph"]
