"""Access graph builder: facts -> typed nodes/edges with provenance (P0-C)."""
from __future__ import annotations

from sparkforge_azure.azure import extract
from sparkforge_azure.facts.notebook_scan import scan_source
from sparkforge_azure.findings.models import Fact
from sparkforge_azure.graph.access import build_access_graph

UC_PAYLOAD = {
    "storage_credentials": {
        "cred_lake": {
            "identity_id": "mi-1",
            "access_connector_id": "/subscriptions/11111111-1111-1111-1111-"
                                   "111111111111/resourceGroups/rg/providers/"
                                   "Microsoft.Databricks/accessConnectors/ac1",
        }
    },
    "external_locations": [
        {"name": "loc_finance", "url": "abfss://lake@stg.dfs.core.windows.net/finance",
         "credential": "cred_lake"},
        {"name": "loc_broken", "url": "abfss://lake@stg.dfs.core.windows.net/other",
         "credential": "cred_missing"},
    ],
    "catalogs": {"prod": {"isolation_mode": "ISOLATED", "workspaces": ["1234567890123456"]}},
    "tables": {"prod.finance.orders": {
        "location": "abfss://lake@stg.dfs.core.windows.net/finance/orders",
        "format": "delta"}},
    "grants": [{"securable": "prod.finance.orders", "principal": "spn-job-1",
                "privileges": ["SELECT"]}],
}

RBAC_PAYLOAD = {
    "assignments": [
        {"principal": "mi-1", "role": "Storage Blob Data Contributor",
         "scope": "/subscriptions/11111111-1111-1111-1111-111111111111/"
                  "resourceGroups/rg/providers/Microsoft.Storage/"
                  "storageAccounts/stg"},
    ]
}

COMPUTE_PAYLOAD = {
    "workspace_id": "1234567890123456",
    "data_security_mode": "USER_ISOLATION",
    "job_id": "job-42",
    "cluster_id": "cluster-9",
    "notebook_path": "notebooks/etl.py",
}


def _facts() -> list[Fact]:
    prov = {"source": "test", "mode": "bundle", "observed_at": "2026-10-07T00:00:00Z"}
    facts = extract.extract_uc(UC_PAYLOAD, prov)
    facts += extract.extract_rbac(RBAC_PAYLOAD, prov)
    facts += extract.extract_compute(COMPUTE_PAYLOAD, prov)
    facts += scan_source(
        'df = spark.read.load("abfss://lake@stg.dfs.core.windows.net/finance/orders")\n'
        'df.write.saveAsTable("prod.finance.orders")\n'
        'spark.table("prod.finance.orders")\n',
        filename="notebooks/etl.py",
        provenance=prov,
    )
    return facts


def _edges(graph):
    return {(e.source, e.relation, e.target) for e in graph.edges.values()}


def test_access_relations_have_provenance() -> None:
    graph = build_access_graph(_facts())
    rels = {e.relation for e in graph.edges.values()}
    for expected in (
        "uses", "executes", "reads", "writes", "uses_identity", "has_role",
        "points_to", "located_at", "bound_to", "has_privilege", "accesses",
    ):
        assert expected in rels, f"missing relation {expected}: {rels}"
    for edge in graph.edges.values():
        assert edge.provenance.kind == "artifact"
        assert edge.provenance.source == "test"
    for node in graph.nodes.values():
        assert node.provenance.kind == "artifact"


def test_chain_shape_is_explicit() -> None:
    graph = build_access_graph(_facts())
    edges = _edges(graph)
    loc = "azure:unity_catalog:external_location:loc_finance"
    cred = "azure:unity_catalog:storage_credential:cred_lake"
    connector = ("azure:/subscriptions/11111111-1111-1111-1111-111111111111/"
                 "resourcegroups/rg/providers/"
                 "microsoft.databricks/accessconnectors/ac1")
    fs = "azure:filesystem:stg/lake/finance"
    assert (loc, "uses", cred) in edges
    assert (cred, "uses_identity", connector) in edges
    assert (loc, "points_to", fs) in edges
    assert ("data:table:prod.finance.orders", "located_at", loc) in edges
    job = "data:job:databricks:1234567890123456/job-42"
    assert (job, "uses", "data:cluster:databricks:1234567890123456/cluster-9") in edges
    assert (job, "executes", "data:notebook:notebooks/etl.py") in edges
    assert ("data:notebook:notebooks/etl.py", "writes", "data:table:prod.finance.orders") in edges
    assert ("data:notebook:notebooks/etl.py", "reads", "data:table:prod.finance.orders") in edges
    # the notebook's deeper path nests under the location's filesystem node
    assert ("data:notebook:notebooks/etl.py", "accesses",
            "azure:filesystem:stg/lake/finance/orders") in edges
    assert ("azure:filesystem:stg/lake/finance/orders", "part_of", fs) in edges
    scope_arm = ("/subscriptions/11111111-1111-1111-1111-111111111111/"
                 "resourcegroups/rg/providers/microsoft.storage/storageaccounts/stg")
    assert ("azure:identity:mi-1", "has_role",
            f"azure:resource:roleAssignment:mi-1@{scope_arm}") in edges
    assert ("azure:identity:spn-job-1", "has_privilege",
            "azure:unity_catalog:securable:prod.finance.orders") in edges
    assert ("azure:unity_catalog:catalog:prod", "bound_to",
            "azure:databricks:1234567890123456") in edges


def test_no_name_matching_edges() -> None:
    """loc_broken references cred_missing by name — no such credential exists.

    The edge must not be emitted (no lookup by name coincidence) and the
    binding gap lands in unresolved with a reason.
    """
    graph = build_access_graph(_facts())
    broken = "azure:unity_catalog:external_location:loc_broken"
    assert all(not (e.source == broken and e.relation == "uses")
               for e in graph.edges.values())
    gaps = [u for u in graph.unresolved
            if u.get("reason") == "credential_not_observed"
            and u.get("external_location") == "loc_broken"]
    assert gaps, "missing credential must land in unresolved"
    # points_to still holds: the URL is explicit evidence, not a lookup.
    assert ("azure:unity_catalog:external_location:loc_broken", "points_to",
            "azure:filesystem:stg/lake/other") in _edges(graph)
