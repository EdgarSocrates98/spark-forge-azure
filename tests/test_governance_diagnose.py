"""Multi-layer governance diagnosis: the five conflict scenarios of section 30."""

from __future__ import annotations

import copy

import pytest

from sparkforge_azure.azure.governance import ScenarioError, Verdict, diagnose

ACCT = ("/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Storage/"
        "storageAccounts/lake")
CONT = f"{ACCT}/blobServices/default/containers/raw"
URL = "abfss://raw@lake.dfs.core.windows.net/sales/orders/part-0.parquet"
MI = "mi-connector-1"
CONNECTOR = ("/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Databricks/"
             "accessConnectors/ac1")


def _acl(owner: str = "root", entries: list | None = None) -> dict:
    return {"owner": owner, "owning_group": "g-own",
            "entries": entries or [{"type": "user", "perms": "rwx"},
                                   {"type": "group", "perms": "r-x"},
                                   {"type": "other", "perms": "---"}]}


def _open_acl(identity: str) -> dict:
    ent = [{"type": "user", "perms": "rwx"}, {"type": "user", "id": identity, "perms": "rwx"},
           {"type": "mask", "perms": "rwx"}, {"type": "other", "perms": "---"}]
    return {p: _acl(entries=ent) for p in ("/", "/sales", "/sales/orders",
                                            "/sales/orders/part-0.parquet")}


def base_direct(identity: str = "u1") -> dict:
    return {
        "name": "direct",
        "principal": {"id": identity, "type": "user", "groups": ["g-eng"]},
        "operation": "read",
        "target": {"kind": "path", "url": URL},
        "compute": {"type": "classic_vnet", "subnet_id": "sub-1", "workspace_id": "ws1"},
        "entra": {"principals": {identity: {"enabled": True}, MI: {"enabled": True}}},
        "rbac": {"assignments": [{"principal": identity, "role": "Storage Blob Data Reader",
                                  "scope": CONT}]},
        "adls": {"account_id": ACCT, "hns": True, "acl": _open_acl(identity)},
        "network": {"public_network_access": "Enabled", "default_action": "Allow"},
    }


def base_uc() -> dict:
    sc = base_direct()
    sc["name"] = "uc"
    sc["rbac"] = {"assignments": [{"principal": MI, "role": "Storage Blob Data Contributor",
                                   "scope": ACCT}]}
    sc["adls"]["acl"] = _open_acl(MI)
    sc["unity_catalog"] = {
        "grants": [{"securable": "external_location:raw_loc", "principal": "g-eng",
                    "privileges": ["READ FILES"]}],
        "external_locations": [{"name": "raw_loc", "url": "abfss://raw@lake.dfs.core.windows.net/sales",
                                "credential": "cred1", "isolation_mode": "OPEN"}],
        "storage_credentials": {"cred1": {"access_connector_id": CONNECTOR, "identity_id": MI}},
    }
    return sc


def test_direct_read_allowed_by_rbac_and_acl_not_consulted() -> None:
    d = diagnose(base_direct())
    assert d.status == "allowed", d.to_dict()
    acl = next(r for r in d.chain if r.layer == "adls_acl")
    assert acl.verdict is Verdict.NOT_APPLICABLE and "cannot restrict" in acl.reason


def test_c1_control_plane_role_and_acl_denies() -> None:
    sc = base_direct()
    sc["rbac"]["assignments"] = [{"principal": "u1", "role": "Contributor", "scope": ACCT}]
    sc["adls"]["acl"] = {p: _acl() for p in ("/", "/sales", "/sales/orders",
                                             "/sales/orders/part-0.parquet")}
    d = diagnose(sc)
    assert d.status == "denied"
    assert d.root_cause.layer == "adls_acl"
    assert "rbac_allows_acl_denies" in d.conflicts
    assert d.findings[0].rule_id == "SFA-GOV-001"


def test_acl_requires_execute_on_every_ancestor() -> None:
    sc = base_direct()
    sc["rbac"]["assignments"] = []
    acl = _open_acl("u1")
    acl["/sales"]["entries"] = [{"type": "user", "perms": "rwx"},
                                {"type": "user", "id": "u1", "perms": "r--"},
                                {"type": "other", "perms": "---"}]
    sc["adls"]["acl"] = acl
    d = diagnose(sc)
    assert d.status == "denied" and "/sales lacks x" in d.root_cause.reason


def test_mask_caps_named_user() -> None:
    sc = base_direct()
    sc["rbac"]["assignments"] = []
    acl = _open_acl("u1")
    for v in acl.values():
        v["entries"] = [e if e["type"] != "mask" else {"type": "mask", "perms": "--x"}
                        for e in v["entries"]]
    sc["adls"]["acl"] = acl
    assert diagnose(sc).status == "denied"


def test_c2_identity_valid_network_denies_private_dns() -> None:
    sc = base_direct()
    sc["network"] = {"public_network_access": "Disabled", "private_endpoint": True}
    sc["compute"]["dns_resolves"] = "public"
    d = diagnose(sc)
    assert d.status == "denied" and d.root_cause.layer == "network"
    assert "identity_valid_network_denies" in d.conflicts
    assert "private DNS" in d.root_cause.reason


def test_c3_uc_permission_exists_storage_credential_fails() -> None:
    sc = base_uc()
    sc["rbac"]["assignments"] = []  # access connector MI has no storage role
    sc["adls"]["acl"] = {p: _acl() for p in ("/", "/sales", "/sales/orders",
                                             "/sales/orders/part-0.parquet")}
    d = diagnose(sc)
    assert d.status == "denied"
    assert d.effective_identity == MI
    assert "uc_permission_exists_storage_credential_fails" in d.conflicts


def test_uc_path_allowed_through_access_connector() -> None:
    d = diagnose(base_uc())
    assert d.status == "allowed", d.to_dict()["chain"]
    assert d.effective_identity == MI


def test_c4_workspace_binding_supersedes_grants() -> None:
    sc = base_uc()
    sc["target"] = {"kind": "table", "table": "main.sales.orders"}
    sc["unity_catalog"]["catalogs"] = {"main": {"isolation_mode": "ISOLATED",
                                                "workspaces": ["ws-prod"]}}
    sc["unity_catalog"]["grants"] += [
        {"securable": "main", "principal": "u1", "privileges": ["USE CATALOG"]},
        {"securable": "main.sales", "principal": "u1", "privileges": ["USE SCHEMA"]},
        {"securable": "main.sales.orders", "principal": "u1", "privileges": ["SELECT"]},
    ]
    d = diagnose(sc)
    assert d.status == "denied" and d.root_cause.layer == "uc_binding"
    assert "workspace_access_exists_catalog_denied" in d.conflicts


def test_c5_storage_access_exists_external_location_denied() -> None:
    sc = base_uc()
    sc["unity_catalog"]["grants"] = []
    sc["rbac"]["assignments"].append({"principal": "u1", "role": "Storage Blob Data Reader",
                                      "scope": CONT})
    d = diagnose(sc)
    assert d.status == "denied" and d.root_cause.layer == "uc_privileges"
    assert "storage_access_exists_external_location_denied" in d.conflicts


def test_write_files_without_read_files_is_permission_denied() -> None:
    sc = base_uc()
    sc["operation"] = "write"
    sc["unity_catalog"]["grants"] = [{"securable": "external_location:raw_loc",
                                      "principal": "u1", "privileges": ["WRITE FILES"]}]
    d = diagnose(sc)
    assert d.root_cause.layer == "uc_privileges"
    assert "PERMISSION_DENIED" in d.root_cause.reason


def test_missing_evidence_is_unresolved_never_allowed() -> None:
    sc = base_direct()
    del sc["network"]
    d = diagnose(sc)
    assert d.status == "unresolved"
    assert any(u.startswith("network") for u in d.unresolved)


def test_abac_condition_without_result_is_unknown() -> None:
    sc = base_direct()
    sc["rbac"]["assignments"][0]["condition"] = "@Resource[...] StringEquals 'x'"
    sc["adls"]["acl"] = {p: _acl() for p in ("/", "/sales", "/sales/orders",
                                             "/sales/orders/part-0.parquet")}
    d = diagnose(sc)
    assert d.status == "unresolved"


def test_findings_cite_facts_and_are_data_only() -> None:
    sc = base_direct()
    sc["network"] = {"public_network_access": "Disabled", "private_endpoint": False}
    out = diagnose(sc).to_dict()
    fact_ids = {f["id"] for f in out["facts"]}
    assert out["authority"] == "data_only"
    assert out["findings"] and all(set(f["evidence"]) <= fact_ids for f in out["findings"])


def test_deterministic() -> None:
    a = diagnose(copy.deepcopy(base_uc())).to_dict()
    b = diagnose(copy.deepcopy(base_uc())).to_dict()
    assert a == b


@pytest.mark.parametrize("mutate", [
    lambda s: s.pop("principal"),
    lambda s: s.update(operation="drop"),
    lambda s: s.update(target={"kind": "path", "url": "s3://x/y"}),
])
def test_malformed_scenarios_are_refused(mutate) -> None:
    sc = base_direct()
    mutate(sc)
    with pytest.raises(ScenarioError):
        diagnose(sc)
