"""Graphfy model: typed nodes/edges, deterministic ids and serialization."""

from __future__ import annotations

import pytest

from sparkforge_azure.graph.model import (
    Edge,
    Graph,
    GraphError,
    Node,
    Provenance,
    azure_node_id,
    node_id,
)

S = Provenance("static", "test")
L = Provenance("live", "arg", "2026-10-01T00:00:00+00:00")
ARM = ("/subscriptions/00000000-0000-4000-8000-00000000aaaa/resourceGroups/rg/providers/"
       "Microsoft.Storage/storageAccounts/st1")


def _graph(order: int) -> Graph:
    nodes = [
        Node(node_id("code", "file", "r/a.py"), "file", "code", {"path": "a.py"}, S),
        Node(node_id("code", "file", "r/b.py"), "file", "code", {"path": "b.py"}, S),
        Node(azure_node_id(ARM), "storage_account", "azure", {"name": "st1"}, L),
    ]
    edges = [
        Edge(nodes[0].id, "imports", nodes[1].id, {}, S),
        Edge(nodes[1].id, "references", nodes[2].id, {}, S),
    ]
    g = Graph()
    for n in (nodes if order == 0 else list(reversed(nodes))):
        g.add_node(n)
    for e in (edges if order == 0 else list(reversed(edges))):
        g.add_edge(e)
    return g


def test_layers_and_kinds_are_validated():
    with pytest.raises(GraphError):
        Node("code:blob:x", "blob", "code")
    with pytest.raises(GraphError):
        Node("azure:x", "file", "azure")
    with pytest.raises(GraphError):
        Node("data:table:x", "table", "nolayer")
    with pytest.raises(GraphError):
        Provenance("guessed", "x")
    with pytest.raises(GraphError):
        Edge("a", "Bad Relation", "b")


def test_azure_id_is_case_insensitive_and_kind_free():
    assert azure_node_id(ARM) == azure_node_id(ARM.upper())
    assert azure_node_id(ARM + "/") == azure_node_id(ARM)
    with pytest.raises(GraphError):
        azure_node_id("stlakehouse")


def test_serialization_is_deterministic_regardless_of_insertion_order():
    a, b = _graph(0), _graph(1)
    assert a.to_json() == b.to_json()
    assert a.fingerprint() == b.fingerprint()
    again = Graph.from_json(a.to_json())
    assert again.to_json() == a.to_json()


def test_merge_unifies_only_identical_ids_and_records_provenance():
    g = _graph(0)
    other = Graph()
    nid = azure_node_id(ARM)
    other.add_node(Node(nid, "storage_account", "azure", {"location": "brazilsouth",
                                                           "name": "st1"}, S))
    merged = g.merge(other)
    node = merged.nodes[nid]
    assert node.attrs["location"] == "brazilsouth"
    assert node.attrs["observed_by"] == ["live:arg", "static:test"]
    assert len(merged.nodes) == len(g.nodes)
    # the original is untouched
    assert "location" not in g.nodes[nid].attrs


def test_kind_conflict_is_unresolved_not_overwritten():
    g = _graph(0)
    nid = azure_node_id(ARM)
    g.add_node(Node(nid, "key_vault", "azure", {}, S))
    assert g.nodes[nid].kind == "storage_account"
    assert g.unresolved[0]["reason"] == "kind_conflict"


def test_attr_conflict_keeps_first_and_records_both():
    g = Graph()
    nid = node_id("data", "table", "t")
    g.add_node(Node(nid, "table", "data", {"owner": "a"}, S))
    g.add_node(Node(nid, "table", "data", {"owner": "b"}, L))
    assert g.nodes[nid].attrs["owner"] == "a"
    assert set(g.nodes[nid].attrs["attr_conflicts"]["owner"]) == {'"a"', '"b"'}


def test_neighbors_subgraph_and_dangling():
    g = _graph(0)
    a, b = node_id("code", "file", "r/a.py"), node_id("code", "file", "r/b.py")
    assert g.neighbors(a) == (b,)
    assert g.neighbors(b, direction="in") == (a,)
    assert g.neighbors(b, relation="imports") == ()
    sub = g.subgraph([a, b])
    assert len(sub.nodes) == 2 and len(sub.edges) == 1
    g.add_edge(Edge(a, "calls", "code:function:missing", {}, S))
    assert [e.target for e in g.dangling_edges()] == ["code:function:missing"]


def test_from_dict_rejects_other_schema():
    with pytest.raises(GraphError):
        Graph.from_dict({"schema_version": 99})
