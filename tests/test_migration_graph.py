"""Cycle 5 — migration graph: typed nodes/edges, migrates_to with status,
unresolved endpoints never fabricated, source/target auth kept separate."""
from __future__ import annotations

from sparkforge_azure.graph.migration import build_migration_graph
from sparkforge_azure.migration import extract

ESTATE = {
    "adf_factories": [{
        "id": "adf-1", "name": "adf1",
        "pipelines": [{
            "id": "adf-1/pl/pl1", "name": "pl1",
            "activities": [{"name": "c1", "type": "Copy",
                            "linked_service": "ls_adls"}]}],
        "linked_services": [{"id": "adf-1/ls/ls_adls", "name": "ls_adls",
                             "type": "AzureBlobFS",
                             "auth_kind": "service_principal"}]}],
    "fabric_workspaces": [{
        "id": "ws-1", "name": "ws",
        "items": [{"id": "lh-1", "type": "Lakehouse", "name": "lh"}]}]}


def _graph(**kw):
    facts = extract.extract_all({"estate": ESTATE}, {"estate": "e.json"})
    return build_migration_graph(facts, **kw)


def test_nodes_and_typed_edges():
    g = _graph()
    kinds = {n.kind for n in g.nodes.values()}
    assert {"adf_factory", "pipeline", "activity", "linked_service",
            "fabric_workspace", "fabric_item"} <= kinds
    rels = {e.relation for e in g.edges.values()}
    assert {"contains", "uses"} <= rels
    # every edge carries the producing fact
    assert all(e.attrs.get("fact") for e in g.edges.values())


def test_migrates_to_edges_have_status():
    g = _graph(recommendations=[{
        "kind": "connection_candidate", "source": "adf-1/ls/ls_adls",
        "target_type": "fabric_connection", "migration_status": "manual"}])
    mig = [e for e in g.edges.values() if e.relation == "migrates_to"]
    assert mig
    assert all(e.attrs.get("status") in
               {"automatic", "assisted", "manual", "refactor",
                "not_supported", "deferred"} for e in mig)
    rec_kinds = {n.kind for n in g.nodes.values()}
    assert "recommendation" in rec_kinds


def test_absent_endpoint_is_unresolved_not_invented():
    g = _graph(recommendations=[{
        "kind": "x", "source": "adf-1/ls/ghost", "target_type":
        "fabric_connection"}])
    assert g.unresolved
    assert any(u["reason"] == "recommendation_source_absent"
               for u in g.unresolved)


def test_waves_are_nodes_scheduling_assets():
    g = _graph(waves=[{"wave": 1, "assets": ["adf-1/pl/pl1"],
                       "rollback": {"trigger": "t", "steps": ["s"]},
                       "receipt": {"asset_count": 1}}])
    assert any(n.kind == "wave" for n in g.nodes.values())
    sched = [e for e in g.edges.values() if e.relation == "schedules"]
    assert sched


def test_serialized_graph_is_bounded():
    g = _graph()
    d = g.to_dict()
    assert d["stats"]["layers"]["migration"] == len(d["nodes"])
