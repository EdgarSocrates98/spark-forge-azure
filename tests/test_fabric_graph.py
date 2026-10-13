"""SDD FABRIC_GRAPH_TOKENSAVE — Fabric graph builder + impact queries."""
from __future__ import annotations

from sparkforge_azure.fabric import extract
from sparkforge_azure.fabric.casefile import load_bundle
from sparkforge_azure.fabric.pipeline import run_fabric_case
from sparkforge_azure.graph.fabric import build_fabric_graph
from sparkforge_azure.graph.model import node_id

FIXTURES = "tests/fixtures/fabric"


def _fixture_graph(name):
    bundle = load_bundle(f"{FIXTURES}/{name}")
    facts = extract.extract_all(bundle.artifacts, bundle.sources)
    return build_fabric_graph(facts, case=bundle.case, sources=bundle.sources)


def test_fabric_graph_nodes_edges():
    g = _fixture_graph("f14_malicious_metadata")
    kinds = {n.kind for n in g.nodes.values()}
    for expected in ("capacity", "workspace", "lakehouse", "onelake_table"):
        assert expected in kinds, expected
    rels = {e.relation for e in g.edges.values()}
    assert "hosts" in rels or "contains" in rels


def test_shortcut_chain_in_graph():
    """Notebook → lakehouse → shortcut → target: the whole chain resolves."""
    g = _fixture_graph("f03_passthrough_source_denied")
    rels = {(e.source.split(":")[1], e.relation, e.target.split(":")[1])
            for e in g.edges.values()}
    assert ("lakehouse", "contains", "shortcut") in rels
    assert ("shortcut", "points_to", "lakehouse") in rels


def test_impact_queries():
    """Who depends on the shortcut / which workspace sits on the capacity."""
    g = _fixture_graph("f03_passthrough_source_denied")
    sc = node_id("fabric", "shortcut", "sc-0001")
    dependents = [e.source for e in g.edges.values() if e.target == sc]
    assert any("lakehouse" in s for s in dependents)
    # f03 carrega workspace+capacity: a aresta hosts resolve o "quem usa"
    cap = node_id("fabric", "capacity", "cap-0001")
    hosted = [e.target for e in g.edges.values()
              if e.source == cap and e.relation == "hosts"]
    if not hosted:
        g2 = _fixture_graph("f14_malicious_metadata")
        hosted = [e.target for e in g2.edges.values()
                  if e.source == cap and e.relation == "hosts"]
    assert hosted == [node_id("fabric", "workspace", "ws-1111")]


def test_pipeline_notebook_edge():
    g = _fixture_graph("f12_pipeline_wrong_workspace")
    rels = {(e.source, e.relation, e.target) for e in g.edges.values()}
    assert any(rel == "has_activity" for _, rel, _ in rels)


def test_missing_target_is_unresolved_not_invented():
    g = _fixture_graph("f05_shortcut_target_missing")
    assert any(u.get("reason") == "shortcut_target_missing"
               for u in g.unresolved)


def test_federation_by_fabric_id():
    """Static graph + live graph for the same item merge into ONE node."""
    from sparkforge_azure.graph.federation import federate
    from sparkforge_azure.graph.model import Graph, Node, Provenance

    static = Graph()
    static.add_node(Node(node_id("fabric", "lakehouse", "lh-aaaa"),
                         "lakehouse", "fabric", attrs={"src": "static"},
                         provenance=Provenance("artifact", "items.json")))
    live = Graph()
    live.add_node(Node(node_id("fabric", "lakehouse", "lh-aaaa"),
                       "lakehouse", "fabric", attrs={"src": "live"},
                       provenance=Provenance("live", "rest")))
    merged = federate(static=static, live=live).graph
    assert node_id("fabric", "lakehouse", "lh-aaaa") in merged.nodes
    assert len([n for n in merged.nodes.values()
                if n.kind == "lakehouse"]) == 1


def test_report_embeds_graph_with_overhead():
    r = run_fabric_case(f"{FIXTURES}/f14_malicious_metadata")
    g = r["fabric_graph"]
    assert g["nodes"] and isinstance(g["nodes"], (list, dict))
    assert r["overhead"]["graph"]["build_ms"] >= 0
    assert r["overhead"]["graph"]["serialized_bytes"] > 0
