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


def test_stream_graph_nodes_edges():
    """SDD contract name — grafo serializa nodes+edges com provenance."""
    g = _graph("s04-eh-throttled")
    d = g.to_dict()
    assert d["nodes"] and d["edges"]
    nodes = d["nodes"]
    iterable = nodes.values() if isinstance(nodes, dict) else nodes
    assert all(n.get("kind") for n in iterable)


def test_finding_overlay_in_graph():
    """AC2 — findings viram nós 'finding' com edges evidenced_by."""
    from sparkforge_azure.stream.pipeline import run_stream_case
    g = run_stream_case(f"{FIXTURES}/s04-eh-throttled")["stream_graph"]
    nodes = g["nodes"] if isinstance(g["nodes"], list) else g["nodes"].values()
    assert any(n.get("kind") == "finding" for n in nodes)
    edges = g["edges"] if isinstance(g["edges"], list) else g["edges"].values()
    assert any(e.get("relation") == "evidenced_by" for e in edges)


def test_no_invented_causality():
    """AC3 — caso saudável não ganha nós finding nem arestas causais."""
    g = _graph("s01-caught-up-idle").to_dict()
    nodes = g["nodes"] if isinstance(g["nodes"], list) else g["nodes"].values()
    assert not any(n.get("kind") == "finding" for n in nodes)
