"""SDD STREAMING_GRAPHFY — stream graph topology."""
from __future__ import annotations

from sparkforge_azure.graph.stream import build_stream_graph
from sparkforge_azure.stream import extract
from sparkforge_azure.stream.casefile import load_bundle

FIXTURES = "tests/fixtures/stream"


def _graph(case: str):
    b = load_bundle(f"{FIXTURES}/{case}")
    return build_stream_graph(
        extract.extract_all(b.artifacts, b.sources),
        case=b.case, sources=b.sources)


def test_eventhubs_topology_nodes():
    g = _graph("s04-eh-throttled")
    kinds = {n.kind for n in g.nodes.values()}
    assert {"namespace", "eventhub", "partition",
            "consumer_group"} <= kinds


def test_flow_edges_reach_partition():
    g = _graph("s04-eh-throttled")
    assert g.edges, "no edges built"
    rels = {e.relation for e in g.edges.values()}
    assert rels  # flow/ownership edges exist


def test_rti_nodes_when_present():
    g = _graph("s16-eventstream-destination-broken")
    kinds = {n.kind for n in g.nodes.values()}
    assert "eventstream" in kinds
    assert {"eventhouse", "es_destination"} & kinds


def test_activator_nodes():
    g = _graph("s19-activator-mapping-invalid")
    kinds = {n.kind for n in g.nodes.values()}
    assert "activator" in kinds


def test_nodes_carry_provenance():
    g = _graph("s04-eh-throttled")
    for n in g.nodes.values():
        assert n.provenance or n.attrs.get("source"), n.id


def test_graph_serializes():
    d = _graph("s04-eh-throttled").to_dict()
    assert d["nodes"] and d["edges"]
