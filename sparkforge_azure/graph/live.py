"""Live graph from authorized, already-redacted observations (section 63).

Input is collector output: ``Fact`` objects (or their dicts) produced by
``sparkforge_azure.collectors``.  This module never calls Azure and never sees
raw payloads; collectors redact and ``assert_clean`` before facts exist.

Every node gets ``provenance=live`` with the observation time.  Edges are
derived ONLY from explicit ids: the ARM hierarchy (resource -> resource group
-> subscription -> tenant) and ARM ids that appear verbatim inside resource
properties (e.g. a private endpoint's ``privateLinkServiceId``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from sparkforge_azure.graph.access import build_access_graph
from sparkforge_azure.graph.arm import ARM_IN_TEXT_RE, is_arm_id, kind_for_type, parse_arm_id
from sparkforge_azure.graph.model import Edge, Graph, Node, Provenance, azure_node_id, node_id

_KEEP_ATTRS = ("name", "type", "location", "resource_group", "subscription_id", "tenant_id")

# Fact kinds of the access vertical (P0-B) are emitted here through the same
# builder used for offline bundles: the merge keeps ``mode=live`` provenance,
# so collectors' facts federate with artifact graphs on identical ARM ids.
_ACCESS_PREFIXES = (
    "azure_rbac.", "adls.", "databricks.compute", "notebook.",
    "unity_catalog.storage_credential", "unity_catalog.external_location",
    "unity_catalog.binding", "unity_catalog.table", "unity_catalog.grant",
)


def _as_dict(fact: object) -> dict[str, Any]:
    if isinstance(fact, Mapping):
        return dict(fact)
    to_dict = getattr(fact, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    raise TypeError(f"unsupported fact type: {type(fact).__name__}")


def live_graph_from_facts(
    facts: Iterable[object], *, source: str = "azure.resource_graph"
) -> Graph:
    graph = Graph()
    access_facts: list[dict[str, Any]] = []
    for raw in facts:
        fact = _as_dict(raw)
        kind = fact.get("kind")
        prov_raw = fact.get("provenance") or {}
        # Observations are live provenance whether fetched now (mode=live) or
        # ingested from an offline export of the same API (mode=export).
        prov = Provenance(
            "live", str(prov_raw.get("source") or source), prov_raw.get("observed_at")
        )
        if kind == "azure.resource":
            _resource(graph, fact, prov)
        elif kind == "databricks.job":
            _workspace_child(graph, fact, prov, "data", "job")
        elif kind == "databricks.cluster":
            _workspace_child(graph, fact, prov, "data", "cluster")
        elif kind == "unity_catalog.catalog":
            _workspace_child(graph, fact, prov, "azure", "unity_catalog")
        elif isinstance(kind, str) and kind.startswith(_ACCESS_PREFIXES):
            access_facts.append(fact)
        else:
            graph.add_unresolved({"reason": "unsupported_fact_kind", "kind": str(kind)})
    if access_facts:
        # The access builder needs all facts before edges (two passes), so it
        # returns its own graph which we merge in.
        graph = graph.merge(build_access_graph(access_facts))
    graph.meta = {"kind": "live", "source": source}
    return graph


def _resource(graph: Graph, fact: Mapping[str, Any], prov: Provenance) -> None:
    arm = (fact.get("subject") or {}).get("arm_id")
    if not is_arm_id(arm):
        graph.add_unresolved({"reason": "invalid_arm_id", "fact": fact.get("id")})
        return
    attrs_in = fact.get("attrs") or {}
    parsed = parse_arm_id(arm)
    nid = azure_node_id(arm)
    attrs = {k: attrs_in[k] for k in _KEEP_ATTRS if attrs_in.get(k) is not None}
    attrs["arm_id"] = parsed.normalized
    attrs["fact_id"] = fact.get("id")
    props = attrs_in.get("properties")
    for key in ("workspaceId", "workspaceUrl"):
        if isinstance(props, Mapping) and isinstance(props.get(key), (str, int)):
            attrs["databricks_" + ("workspace_id" if key == "workspaceId" else "workspace_url")] = (
                str(props[key])
            )
    graph.add_node(Node(nid, kind_for_type(attrs_in.get("type")), "azure", attrs, prov))
    # explicit hierarchy
    sub_id = azure_node_id(parsed.subscription_scope)
    graph.add_node(Node(sub_id, "subscription", "azure",
                        {"subscription_id": parsed.subscription_id.lower()}, prov))
    parent = sub_id
    if parsed.resource_group_scope:
        rg_id = azure_node_id(parsed.resource_group_scope)
        graph.add_node(Node(rg_id, "resource_group", "azure",
                            {"name": parsed.resource_group}, prov))
        graph.add_edge(Edge(rg_id, "located_in", sub_id, {}, prov))
        parent = rg_id
    graph.add_edge(Edge(nid, "located_in", parent, {}, prov))
    tenant = attrs_in.get("tenant_id")
    if isinstance(tenant, str) and tenant:
        tid = node_id("azure", "tenant", tenant.lower())
        graph.add_node(Node(tid, "tenant", "azure", {"tenant_id": tenant.lower()}, prov))
        graph.add_edge(Edge(sub_id, "member_of", tid, {}, prov))
    # ARM ids referenced verbatim in properties (verified references)
    for ref in sorted(set(_arm_refs(props))):
        target = ref.rstrip("/").lower()
        if target == parsed.normalized or not is_arm_id(target):
            continue
        graph.add_edge(Edge(nid, "references", azure_node_id(target), {"via": "properties"},
                            prov))


def _arm_refs(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield from ARM_IN_TEXT_RE.findall(value)
    elif isinstance(value, Mapping):
        for v in value.values():
            yield from _arm_refs(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _arm_refs(v)


def _workspace_child(
    graph: Graph, fact: Mapping[str, Any], prov: Provenance, layer: str, kind: str
) -> None:
    subject = fact.get("subject") or {}
    ws = str(subject.get("workspace_id") or "")
    key = str(subject.get("id") or subject.get("name") or "")
    if not ws or not key:
        graph.add_unresolved({"reason": "missing_explicit_id", "fact": fact.get("id")})
        return
    ws_node = f"azure:databricks:{ws}"
    graph.add_node(Node(ws_node, "databricks_workspace", "azure",
                        {"databricks_workspace_id": ws}, prov))
    nid = node_id(layer, kind, f"databricks:{ws}/{key}")
    attrs = {k: v for k, v in (fact.get("attrs") or {}).items()
             if isinstance(v, (str, int, float, bool))}
    attrs["fact_id"] = fact.get("id")
    graph.add_node(Node(nid, kind, layer, attrs, prov))
    graph.add_edge(Edge(nid, "runs_in", ws_node, {}, prov))


__all__ = ["live_graph_from_facts"]
