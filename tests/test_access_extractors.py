"""Extratores do vertical de acesso: artefatos UC/RBAC/ADLS viram Facts."""
from __future__ import annotations

from sparkforge_azure.azure import extract
from sparkforge_azure.facts import notebook_scan

PROV = {"source": "test", "mode": "export", "observed_at": "2026-10-06T00:00:00Z"}

UC_PAYLOAD = {
    "storage_credentials": {
        "cred_lake": {
            "identity_id": "mi-conn-1",
            "access_connector_id": "/subscriptions/s1/resourceGroups/rg/providers/"
            "Microsoft.Databricks/accessConnectors/ac1",
        }
    },
    "external_locations": [
        {"name": "loc_finance", "url": "abfss://lake@stg.dfs.core.windows.net/finance",
         "credential": "cred_lake"}
    ],
    "catalogs": {
        "prod": {"isolation_mode": "ISOLATED", "workspaces": ["1234567890123456"]}
    },
    "schemas": {"prod.finance": {"owner": "data-eng"}},
    "tables": {
        "prod.finance.orders": {
            "location": "abfss://lake@stg.dfs.core.windows.net/finance/orders",
            "format": "delta",
        }
    },
    "grants": [
        {"securable": "prod", "principal": "spn-job-1", "privileges": ["USE CATALOG"]},
        {"securable": "prod.finance", "principal": "spn-job-1", "privileges": ["USE SCHEMA"]},
        {"securable": "prod.finance.orders", "principal": "spn-job-1",
         "privileges": ["SELECT"]},
    ],
}


def test_uc_artifacts_become_facts() -> None:
    facts = extract.extract_uc(UC_PAYLOAD, dict(PROV))
    kinds = {f.kind for f in facts}
    assert "unity_catalog.storage_credential" in kinds
    assert "unity_catalog.external_location" in kinds
    assert "unity_catalog.catalog" in kinds
    assert "unity_catalog.grant" in kinds
    assert "unity_catalog.table" in kinds
    cred = next(f for f in facts if f.kind == "unity_catalog.storage_credential")
    assert cred.subject["name"] == "cred_lake"
    assert cred.attrs["identity_id"] == "mi-conn-1"
    assert cred.provenance["source"] == "test"
    loc = next(f for f in facts if f.kind == "unity_catalog.external_location")
    assert loc.attrs["url"] == "abfss://lake@stg.dfs.core.windows.net/finance"
    grant = next(f for f in facts
                 if f.kind == "unity_catalog.grant"
                 and f.subject["securable"] == "prod.finance.orders")
    assert "SELECT" in grant.attrs["privileges"]


def test_rbac_and_adls_become_facts() -> None:
    rbac = {"assignments": [
        {"principal": "mi-conn-1",
         "scope": "/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Storage/"
                  "storageAccounts/stg/blobServices/default/containers/lake",
         "role": "Storage Blob Data Contributor"},
    ]}
    facts = extract.extract_rbac(rbac, dict(PROV))
    assert len(facts) == 1
    f = facts[0]
    assert f.kind == "azure_rbac.assignment"
    assert f.attrs["role"] == "Storage Blob Data Contributor"
    assert f.subject["principal"] == "mi-conn-1"

    adls = {"account_id": "/subscriptions/s1/.../stg", "hns": True,
            "acl": {"/finance": {"owner": "superuser", "entries": [
                {"type": "user", "perms": "rwx"},
                {"type": "other", "perms": "---"}]}}}
    facts = extract.extract_adls(adls, dict(PROV))
    kinds = {f.kind for f in facts}
    assert "adls.account" in kinds
    assert "adls.acl" in kinds
    acl = next(f for f in facts if f.kind == "adls.acl")
    assert acl.subject["path"] == "/finance"


def test_notebook_scan_recognizes_uc_and_adls() -> None:
    source = (
        'df = spark.read.load("abfss://lake@stg.dfs.core.windows.net/finance/orders")\n'
        "df.write.mode(\"overwrite\").saveAsTable(\"prod.finance.orders\")\n"
        'spark.sql("MERGE INTO prod.finance.orders t USING s ON t.id = s.id")\n'
        'dbutils.fs.ls("abfss://lake@stg.dfs.core.windows.net/finance")\n'
        'delta = spark.table("prod.finance.orders")\n'
    )
    facts = notebook_scan.scan_source(source, filename="job.py")
    kinds = {f.kind for f in facts}
    assert "notebook.abfss_path" in kinds
    assert "notebook.uc_table" in kinds
    assert "notebook.dbutils" in kinds
    assert "notebook.delta_op" in kinds
    abfss = next(f for f in facts if f.kind == "notebook.abfss_path")
    assert abfss.attrs["url"] == "abfss://lake@stg.dfs.core.windows.net/finance/orders"
    assert abfss.subject["file"] == "job.py"
    merge = next(f for f in facts
                 if f.kind == "notebook.delta_op" and f.attrs["op"] == "MERGE")
    assert merge.attrs["table"] == "prod.finance.orders"
