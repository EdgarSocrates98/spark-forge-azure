"""SDD MIGRATION_INVENTORY — extractor contract: canonical ids, typed
dependency facts, unresolved-first census, secret redaction."""
from __future__ import annotations

import pytest

from sparkforge_azure.migration import extract, inventory
from sparkforge_azure.migration.casefile import (
    MigrationCaseError,
    load_bundle,
)

ESTATE = {
    "adf_factories": [{
        "id": "/subscriptions/sub-1/resourceGroups/rg/providers/"
              "Microsoft.DataFactory/factories/adf-prod",
        "name": "adf-prod",
        "location": "eastus2",
        "pipelines": [{
            "id": "adf-prod/pipeline/pl_daily",
            "name": "pl_daily",
            "activities": [
                {"name": "copy_main", "type": "Copy",
                 "linked_service": "ls_adls",
                 "dataset_refs": [{"name": "ds_out", "mode": "write"}]},
                {"name": "nb_transform", "type": "SynapseNotebook",
                 "depends_on": ["copy_main"]},
            ],
            "global_parameters": [{"name": "env", "type": "string"}],
        }],
        "linked_services": [
            {"id": "adf-prod/ls/ls_adls", "name": "ls_adls",
             "type": "AzureBlobFS", "auth_kind": "service_principal",
             "connection_string": "AccountKey=SUPERSECRETVALUE==",
             "credential": {"client_secret": "shh"}},
        ],
        "triggers": [{"id": "adf-prod/tr/tr_daily", "name": "tr_daily",
                      "type": "ScheduleTrigger",
                      "pipelines": ["pl_daily"]}],
        "integration_runtimes": [
            {"id": "adf-prod/ir/auto", "name": "auto", "kind": "Managed",
             "region": "eastus2"}],
    }],
    "synapse_workspaces": [{
        "id": "/subscriptions/sub-1/resourceGroups/rg/providers/"
              "Microsoft.Synapse/workspaces/syn-prod",
        "name": "syn-prod",
        "notebooks": [{"id": "syn-prod/nb/nb_etl", "name": "nb_etl",
                       "path": "notebooks/nb_etl.py",
                       "spark_pool_id": "pool1",
                       "adls_paths": ["sa1/fs/silver"]}],
        "spark_pools": [{"id": "syn-prod/pool/pool1", "name": "pool1",
                         "node_size": "Medium", "node_count": 6,
                         "spark_version": "3.4"}],
        "lake_databases": [{"id": "syn-prod/ldb/ldb1", "name": "ldb1",
                            "tables": [
                                {"name": "t_managed", "kind": "managed",
                                 "format": "delta"},
                                {"name": "t_ext", "kind": "external",
                                 "format": "delta",
                                 "location": "abfss://sa1/fs/ext"}]}],
    }],
    "fabric_workspaces": [{
        "id": "11111111-2222-3333-4444-555555555555",
        "name": "ws-analytics",
        "items": [{"id": "aaaa-bbbb", "type": "Lakehouse",
                   "name": "lh_main"}],
    }],
    "storage_accounts": [{
        "id": "/subscriptions/sub-1/resourceGroups/rg/providers/"
              "Microsoft.Storage/storageAccounts/sa1",
        "name": "sa1", "kind": "StorageV2", "hns": True,
        "adls_paths": [{"path": "fs/silver", "format": "delta"}],
    }],
}


def _facts():
    return extract.extract_all({"estate": ESTATE},
                               {"estate": "estate.json"})


def test_assets_have_canonical_ids():
    """AC1: identity is the ARM id / GUID, never the display name."""
    facts = _facts()
    factory = next(f for f in facts if f.kind == "mig.adf_factory")
    assert factory.subject["factory_id"].endswith(
        "/factories/adf-prod")
    assert factory.subject["factory_id"] != factory.attrs["name"]
    fws = next(f for f in facts if f.kind == "mig.fabric_workspace")
    assert fws.subject["fabric_workspace_id"] == (
        "11111111-2222-3333-4444-555555555555")
    pool = next(f for f in facts if f.kind == "mig.spark_pool")
    assert pool.subject["pool_id"] == "syn-prod/pool/pool1"


def test_dependency_facts_are_typed():
    """AC2: dep.edge facts carry typed relations from the closed set."""
    from sparkforge_azure.migration.model import DEP_RELATIONS
    facts = _facts()
    edges = [f for f in facts if f.kind == "dep.edge"]
    assert edges, "no dependency edges extracted"
    rels = {f.subject["relation"] for f in edges}
    assert rels <= DEP_RELATIONS
    assert {"contains", "uses", "depends_on", "invokes", "reads",
            "runs_on"} <= rels
    for e in edges:
        assert e.subject["src"] and e.subject["dst"]


def test_absence_is_unresolved_not_ready():
    """AC3: no assessment evidence -> every asset UNRESOLVED, never READY."""
    facts = _facts()
    summary = inventory.estate_summary(facts)
    assert summary["assessment_present"] is False
    assert summary["ready"] == 0
    assert summary["unknown"] == summary["asset_count"]
    # a supplied readiness map shifts the census deterministically
    pipes = [f for f in facts if f.kind == "mig.pipeline"]
    summary2 = inventory.estate_summary(
        facts, {pipes[0].subject["pipeline_id"]: "READY"})
    assert summary2["ready"] == 1
    assert summary2["unknown"] == summary["asset_count"] - 1


def test_linked_service_secrets_redacted():
    """AC4: connection strings / credentials never reach facts."""
    facts = _facts()
    blob = repr([f.to_dict() for f in facts])
    assert "SUPERSECRETVALUE" not in blob
    assert "shh" not in blob
    assert "client_secret" not in blob
    ls = next(f for f in facts if f.kind == "mig.linked_service")
    assert "connection_string" not in ls.attrs
    assert "credential" not in ls.attrs


def test_bundle_requires_case_and_known_shape(tmp_path):
    with pytest.raises(MigrationCaseError):
        load_bundle(tmp_path)
    (tmp_path / "case.yaml").write_text(
        "name: t\nprincipal: {kind: sp}\noperation: migrate\n"
        "target: {fabric_workspace_id: ws1}\n", encoding="utf-8")
    b = load_bundle(tmp_path)
    assert b.case["operation"] == "migrate"


def test_dependency_map_adjacency():
    facts = _facts()
    dep = inventory.dependency_map(facts)
    nb = "syn-prod/nb/nb_etl"
    rels = {d["relation"] for d in dep.get(nb, [])}
    assert "runs_on" in rels and "reads" in rels
