"""Federation: composition only by explicit ids, declared bindings or verified
references -- never by similar/identical names (section 64)."""

from __future__ import annotations

from pathlib import Path

from sparkforge_azure.collectors import databricks, resource_graph
from sparkforge_azure.graph import (
    Graph,
    Node,
    Provenance,
    build_workspace_graph,
    federate,
    from_fragment,
    knowledge_graph,
    live_graph_from_facts,
    load_workspace_manifest,
    to_fragment,
)
from sparkforge_azure.graph.model import azure_node_id

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "workspace"
FIX = ROOT / "fixtures" / "azure"
A = "00000000-0000-4000-8000-00000000aaaa"
B = "00000000-0000-4000-8000-00000000bbbb"
SHARED_A = azure_node_id(
    f"/subscriptions/{A}/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/stshared")
SHARED_B = azure_node_id(
    f"/subscriptions/{B}/resourceGroups/rg-other/providers/Microsoft.Storage/storageAccounts/stshared")
LAKE = azure_node_id(
    f"/subscriptions/{A}/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/"
    "stlakehouse")
DBW = azure_node_id(
    f"/subscriptions/{A}/resourceGroups/rg-data/providers/Microsoft.Databricks/workspaces/"
    "dbw-analytics")


def _fed():
    static = build_workspace_graph(load_workspace_manifest(EXAMPLE))
    live = resource_graph.to_graph(resource_graph.from_export(FIX / "arg_export.json"))
    return static, live, federate(static, live)


def test_same_name_different_arm_ids_stay_separate():
    _, live, result = _fed()
    g = result.graph
    assert SHARED_A in g.nodes and SHARED_B in g.nodes
    assert g.nodes[SHARED_A].attrs["name"] == g.nodes[SHARED_B].attrs["name"] == "stshared"
    between = [k for k in g.edges if {k[0], k[2]} == {SHARED_A, SHARED_B}]
    assert between == []
    amb = {a["name"]: a for a in result.ambiguous_names}
    assert amb["stshared"]["ids"] == sorted([SHARED_A, SHARED_B])
    assert amb["stshared"]["linked"] is False


def test_declared_binding_links_repo_resource_to_observed_arm_node():
    _, _, result = _fed()
    g = result.graph
    edge = ("code:symbol:terraform/azurerm_storage_account.lake", "binds_to", LAKE)
    assert edge in g.edges
    # one node for the ARM id, observed by both the manifest and Resource Graph
    assert g.nodes[LAKE].attrs["observed_by"] == ["live:azure.resource_graph",
                                                  "static:manifest:contoso-lakehouse"]
    assert g.nodes[LAKE].attrs["location"] == "brazilsouth"


def test_unbound_iac_resource_goes_to_unresolved_with_candidates_but_no_link():
    _, _, result = _fed()
    g = result.graph
    tf = "code:symbol:terraform/azurerm_storage_account.stshared"
    items = [u for u in g.unresolved if u.get("id") == tf]
    assert len(items) == 1 and items[0]["reason"] == "unbound_iac_resource"
    assert items[0]["name_candidates"] == sorted([SHARED_A, SHARED_B])
    assert not [k for k in g.edges if k[0] == tf and k[1] != "defines"]


def test_declared_not_observed_and_verified_property_reference():
    _, _, result = _fed()
    g = result.graph
    reasons = {(u["reason"], u.get("id")) for u in g.unresolved}
    assert ("declared_not_observed",
            "azure:fabric:33333333-3333-4333-8333-333333333333") in reasons
    pe = azure_node_id(
        f"/subscriptions/{A}/resourceGroups/rg-net/providers/Microsoft.Network/"
        "privateEndpoints/pe-stlakehouse-dfs")
    assert (pe, "references", LAKE) in g.edges


def test_databricks_alias_linked_by_explicit_workspace_id():
    static, live, _ = _fed()
    dbx = live_graph_from_facts(databricks.from_export(FIX / "databricks_export.json").facts)
    result = federate(static, live.merge(dbx))
    g = result.graph
    assert (DBW, "same_as", "azure:databricks:1234567890123456") in g.edges
    assert ("data:job:databricks:1234567890123456/101", "runs_in",
            "azure:databricks:1234567890123456") in g.edges


def test_same_display_name_in_other_layers_is_not_linked():
    g1, g2 = Graph(), Graph()
    p = Provenance("static", "t")
    g1.add_node(Node("data:table:sales.orders", "table", "data", {"name": "orders"}, p))
    g2.add_node(Node("data:table:other.orders", "table", "data", {"name": "orders"}, p))
    result = federate(g1, artifact=g2)
    assert len(result.graph.nodes) == 2 and not result.graph.edges


def test_explicit_binding_with_missing_endpoint_is_unresolved():
    static, live, _ = _fed()
    result = federate(static, live, bindings=[
        {"source": "code:symbol:terraform/azurerm_storage_account.stshared",
         "target": f"/subscriptions/{B}/resourceGroups/rg-other/providers/"
                   "Microsoft.Storage/storageAccounts/stshared"},
        {"source": "code:symbol:ghost", "target": LAKE},
    ])
    g = result.graph
    assert ("code:symbol:terraform/azurerm_storage_account.stshared", "binds_to",
            SHARED_B) in g.edges
    assert not any(u.get("id") == "code:symbol:terraform/azurerm_storage_account.stshared"
                   for u in g.unresolved)
    assert any(u["reason"] == "binding_endpoint_missing" for u in g.unresolved)


def test_knowledge_layer_and_fragment_roundtrip(tmp_path):
    (tmp_path / "knowledge" / "azure").mkdir(parents=True)
    (tmp_path / "knowledge" / "azure" / "a.md").write_text(
        "---\nid: azure.a\ndomain: azure\nrelated: [azure.b, azure.ghost]\n---\n# A\n",
        encoding="utf-8")
    (tmp_path / "knowledge" / "azure" / "b.md").write_text(
        "---\nid: azure.b\ndomain: azure\n---\n# B\n", encoding="utf-8")
    (tmp_path / "skills" / "s1").mkdir(parents=True)
    (tmp_path / "skills" / "s1" / "SKILL.md").write_text(
        "---\nname: s1\nmetadata:\n  knowledge_refs: [knowledge/azure/, nope/]\n---\n",
        encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "ag.md").write_text(
        "---\nid: ag\nskills: [s1, s2]\nknowledge_refs: [azure.b]\n---\n", encoding="utf-8")
    k = knowledge_graph(tmp_path)
    assert ("knowledge:knowledge:azure.a", "related", "knowledge:knowledge:azure.b") in k.edges
    assert ("knowledge:skill:s1", "refers_knowledge", "knowledge:knowledge:azure.a") in k.edges
    assert ("knowledge:agent:ag", "uses_skill", "knowledge:skill:s1") in k.edges
    assert ("knowledge:agent:ag", "refers_knowledge", "knowledge:knowledge:azure.b") in k.edges
    reasons = sorted(u["reason"] for u in k.unresolved)
    assert reasons == ["unknown_knowledge_ref", "unknown_related", "unknown_skill"]
    back = from_fragment(to_fragment(k, "kb"))
    assert set(back.nodes) == set(k.nodes) and set(back.edges) == set(k.edges)


def test_knowledge_adapter_tolerates_absent_dirs(tmp_path):
    k = knowledge_graph(tmp_path)
    assert not k.nodes and not k.unresolved


def test_real_repository_knowledge_parses():
    k = knowledge_graph(ROOT)
    kinds = {n.kind for n in k.nodes.values()}
    assert {"knowledge", "skill", "agent"} <= kinds
