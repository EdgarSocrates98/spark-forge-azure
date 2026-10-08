"""Collectors do vertical: export offline + falha -> unresolved com FailureClass."""
from __future__ import annotations

import json
from pathlib import Path

from sparkforge_azure.collectors import adls_meta, azure_rbac, failure, unity_catalog


def test_collector_failure_is_unresolved() -> None:
    # SDK ausente -> CollectorUnavailable -> unresolved com failure_class, nunca
    # "recurso ausente"
    result = unity_catalog.collect_live(host="https://adb-x.azuredatabricks.net",
                                      workspace_id="1234567890123456")
    assert result.unresolved
    assert result.unresolved[0]["failure_class"] in {
        failure.FailureClass.UNSUPPORTED.value,
        failure.FailureClass.AUTHENTICATION.value,
    }
    assert result.facts == []

    class FakeHttpError(Exception):
        status_code = 403

    classified = failure.classify(FakeHttpError("forbidden"))
    assert classified == failure.FailureClass.AUTHORIZATION

    classified = failure.classify(ConnectionError("dns failed"))
    assert classified == failure.FailureClass.NETWORK


def test_uc_export_produces_facts(tmp_path: Path) -> None:
    export = tmp_path / "uc.json"
    export.write_text(json.dumps({
        "storage_credentials": {"c1": {"identity_id": "mi-1"}},
        "external_locations": [{"name": "l1", "url": "abfss://c@a.dfs.core.windows.net/p",
                                "credential": "c1"}],
        "grants": [{"securable": "external_location:l1", "principal": "spn",
                    "privileges": ["READ FILES"]}],
    }), encoding="utf-8")
    result = unity_catalog.from_export(export)
    assert result.mode == "export"
    kinds = {f.kind for f in result.facts}
    assert "unity_catalog.external_location" in kinds


def test_rbac_export_produces_facts(tmp_path: Path) -> None:
    export = tmp_path / "rbac.json"
    export.write_text(json.dumps({"assignments": [
        {"principal": "mi-1", "role": "Storage Blob Data Reader",
         "scope": "/subscriptions/s1/x"},
    ]}), encoding="utf-8")
    result = azure_rbac.from_export(export)
    assert any(f.kind == "azure_rbac.assignment" for f in result.facts)


def test_adls_export_produces_facts(tmp_path: Path) -> None:
    export = tmp_path / "adls.json"
    export.write_text(json.dumps({
        "account_id": "/subscriptions/s1/storageAccounts/stg", "hns": True,
        "acl": {"/p": {"owner": "o", "entries": [{"type": "other", "perms": "---"}]}},
    }), encoding="utf-8")
    result = adls_meta.from_export(export)
    kinds = {f.kind for f in result.facts}
    assert "adls.account" in kinds
    assert "adls.acl" in kinds
