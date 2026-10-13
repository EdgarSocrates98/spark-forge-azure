"""Static(bundle) + live(collector) access graphs federate on explicit ids."""
from __future__ import annotations

from sparkforge_azure.azure import extract
from sparkforge_azure.findings.models import Fact
from sparkforge_azure.graph.access import build_access_graph
from sparkforge_azure.graph.federation import federate
from sparkforge_azure.graph.live import live_graph_from_facts

CONNECTOR_ARM = ("/subscriptions/11111111-1111-1111-1111-111111111111/"
                 "resourceGroups/rg/providers/"
                 "Microsoft.Databricks/accessConnectors/ac1")
CONNECTOR_NODE = ("azure:/subscriptions/11111111-1111-1111-1111-111111111111/"
                  "resourcegroups/rg/providers/"
                  "microsoft.databricks/accessconnectors/ac1")

UC_PAYLOAD = {
    "storage_credentials": {"cred_lake": {"identity_id": "mi-1",
                                          "access_connector_id": CONNECTOR_ARM}},
    "external_locations": [
        {"name": "loc_finance", "url": "abfss://lake@stg.dfs.core.windows.net/finance",
         "credential": "cred_lake"},
    ],
}


def _bundle_graph() -> object:
    prov = {"source": "unity_catalog.json", "mode": "bundle", "observed_at": None}
    return build_access_graph(extract.extract_uc(UC_PAYLOAD, prov))


def _live_facts() -> list[Fact]:
    """Same access connector observed via Resource Graph, with drift on location."""
    return [Fact(
        kind="azure.resource",
        subject={"arm_id": CONNECTOR_ARM},
        attrs={"type": "Microsoft.Databricks/accessConnectors",
               "name": "ac1", "location": "eastus2"},
        provenance={"source": "azure.resource_graph", "mode": "live",
                    "observed_at": "2026-10-07T12:00:00Z"},
    )]


def test_static_live_merge_and_divergence() -> None:
    artifact = _bundle_graph()
    live = live_graph_from_facts(_live_facts())
    assert CONNECTOR_NODE in live.nodes, f"connector node missing: {sorted(live.nodes)}"

    result = federate(artifact=artifact, live=live)
    node = result.graph.nodes[CONNECTOR_NODE]
    # One node, both observations recorded.
    assert set(node.attrs.get("observed_by") or []) == {
        "artifact:unity_catalog.json",
        "live:azure.resource_graph",
    }
    # first writer in merge order (static -> live -> artifact) wins the label
    assert node.provenance.kind == "live"
    # The live attrs arrived: this is the merge unifying on the ARM id.
    assert node.attrs.get("location") == "eastus2"
    assert node.attrs.get("fact_id")


def test_attribute_divergence_declares_conflict() -> None:
    prov = {"source": "unity_catalog.json", "mode": "bundle", "observed_at": None}
    facts = extract.extract_uc(
        {"storage_credentials": {"cred_lake": {
            "identity_id": "mi-1", "access_connector_id": CONNECTOR_ARM,
            # static view asserts a location; the live view will disagree
            "_connector_attrs": {"location": "eastus"}}}},
        prov)
    artifact = build_access_graph(facts)
    live = live_graph_from_facts(_live_facts())
    result = federate(artifact=artifact, live=live)
    node = result.graph.nodes[CONNECTOR_NODE]
    # conflicts are recorded as canonical JSON (quoted) values
    loc_conflict = node.attrs.get("attr_conflicts", {}).get("location", [])
    assert '"eastus"' in loc_conflict and '"eastus2"' in loc_conflict


def test_live_observed_at_is_carried() -> None:
    live = live_graph_from_facts(_live_facts())
    node = live.nodes[CONNECTOR_NODE]
    assert node.provenance.kind == "live"
    assert node.provenance.observed_at == "2026-10-07T12:00:00Z"
    assert live.nodes[CONNECTOR_NODE].kind == "identity"
