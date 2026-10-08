"""High-value access queries: deterministic, bounded, evidence-carrying."""
from __future__ import annotations

from sparkforge_azure.azure import extract
from sparkforge_azure.facts.notebook_scan import scan_source
from sparkforge_azure.graph import access_queries as q
from sparkforge_azure.graph.access import build_access_graph

UC_PAYLOAD = {
    "storage_credentials": {
        "cred_lake": {"identity_id": "mi-1",
                      "access_connector_id": "/subscriptions/11111111-1111-"
                                             "1111-1111-111111111111/"
                                             "resourceGroups/rg/providers/"
                                             "Microsoft.Databricks/"
                                             "accessConnectors/ac1"}},
    "external_locations": [
        {"name": "loc_finance", "url": "abfss://lake@stg.dfs.core.windows.net/finance",
         "credential": "cred_lake"},
    ],
    "catalogs": {"prod": {"isolation_mode": "OPEN"}},
    "tables": {"prod.finance.orders": {
        "location": "abfss://lake@stg.dfs.core.windows.net/finance/orders",
        "format": "delta"}},
    "grants": [{"securable": "prod.finance.orders", "principal": "spn-job-1",
                "privileges": ["SELECT"]}],
}

RBAC_PAYLOAD = {"assignments": [
    {"principal": "mi-1", "role": "Storage Blob Data Contributor",
     "scope": "/subscriptions/11111111-1111-1111-1111-111111111111/"
              "resourceGroups/rg/providers/Microsoft.Storage/"
              "storageAccounts/stg"}]}

COMPUTE_PAYLOAD = {"workspace_id": "1234567890123456", "job_id": "job-42",
                   "cluster_id": "cluster-9", "notebook_path": "notebooks/etl.py",
                   "data_security_mode": "USER_ISOLATION"}

NOTEBOOK = (
    'df = spark.read.load("abfss://lake@stg.dfs.core.windows.net/finance/orders")\n'
    'spark.table("prod.finance.orders")\n'
    'df.write.saveAsTable("prod.finance.orders")\n'
)


def _graph():
    prov = {"source": "bundle", "mode": "bundle", "observed_at": None}
    facts = extract.extract_uc(UC_PAYLOAD, prov)
    facts += extract.extract_rbac(RBAC_PAYLOAD, prov)
    facts += extract.extract_compute(COMPUTE_PAYLOAD, prov)
    facts += scan_source(NOTEBOOK, filename="notebooks/etl.py", provenance=prov)
    return build_access_graph(facts)


def test_high_value_queries() -> None:
    g = _graph()
    fs = "azure:filesystem:stg/lake/finance"

    who = q.who_can_access(g, fs)
    assert "azure:identity:mi-1" in who["principals"]
    assert "azure:identity:spn-job-1" in who["principals"]
    assert who["truncated"] is False

    loc = "azure:unity_catalog:external_location:loc_finance"
    deps = q.jobs_depending_on(g, loc)
    assert deps["jobs"] == ["data:job:databricks:1234567890123456/job-42"]
    assert "data:notebook:notebooks/etl.py" in deps["via_notebooks"]

    impact = q.what_breaks_if_changed(g, loc)
    impacted_ids = {e["id"] for entries in impact["impacted"].values() for e in entries}
    assert "data:table:prod.finance.orders" in impacted_ids
    assert "data:job:databricks:1234567890123456/job-42" in impacted_ids

    tables = q.tables_of_credential(
        g, "azure:unity_catalog:storage_credential:cred_lake")
    assert tables["tables"] == ["data:table:prod.finance.orders"]
    assert tables["via_locations"] == ["azure:unity_catalog:external_location:loc_finance"]

    repos = q.repo_defining(
        g, "azure:/subscriptions/11111111-1111-1111-1111-111111111111/"
           "resourcegroups/rg/providers/microsoft.storage/storageaccounts/stg")
    assert repos["repos"] == []
    assert repos["unresolved"], "no IaC binding exists -> declared, not guessed"


def test_queries_are_bounded_and_deterministic() -> None:
    g = _graph()
    fs = "azure:filesystem:stg/lake/finance"
    a = q.who_can_access(g, fs, max_nodes=4)
    assert a["truncated"] is True
    assert a["budget"] == 4
    b = q.who_can_access(g, fs)
    assert b == q.who_can_access(g, fs)
    missing = q.jobs_depending_on(g, "azure:unity_catalog:external_location:nope")
    assert missing["jobs"] == []
    assert missing["unresolved"]


def test_queries_reject_bad_input_named() -> None:
    g = _graph()
    try:
        q.who_can_access(g, "not-a-node")
    except ValueError as exc:
        assert "not-a-node" in str(exc)
    else:
        raise AssertionError("unknown node must raise, not return empty")
