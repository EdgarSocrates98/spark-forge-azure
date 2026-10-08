"""Vertical knowledge packs, scoped compilation, and query expansion.

Prompt 151-153: the Databricks/UC/ADLS access vertical ships the six minimum
knowledge packs; a UC failure compiles only vertical-scope entries (never
fabric/synapse/adf); ``external location denied`` expands deterministically
into credential/identity/RBAC/ACL/binding/network terms.
"""

from __future__ import annotations

from sparkforge_azure import doctor
from sparkforge_azure.azure.pipeline import run_case
from sparkforge_azure.knowledgebase.expansion import expand
from sparkforge_azure.knowledgebase.loader import KnowledgeBase
from sparkforge_azure.knowledgebase.vertical import (
    compile_access_knowledge,
    load_packs,
    packs_for_layer,
    vertical_domains,
)
from tests.test_access_pipeline import FIXTURES

PACKS = {
    "databricks-runtime",
    "unity-catalog-storage",
    "adls-access",
    "azure-identity",
    "azure-network",
    "delta-performance",
}

NON_VERTICAL_DOMAINS = {
    "azure-data-factory",
    "azure-synapse",
    "fabric-data-engineering",
    "fabric-data-factory",
    "fabric-onelake",
    "fabric-realtime",
}


def test_packs_manifest_declares_the_six_packs():
    manifest = load_packs()
    assert set(manifest["packs"]) == PACKS
    for spec in manifest["packs"].values():
        assert spec["domains"], "pack sem dominio"
        assert spec["failure_layers"], "pack sem failure_layer"


def test_every_pack_domain_exists_in_the_index():
    index = KnowledgeBase().load_index()
    known = {e.domain for e in index.values()}
    assert vertical_domains() <= known


def test_layer_to_pack_mapping_is_minimal():
    assert packs_for_layer("unity_catalog") == ["unity-catalog-storage"]
    assert packs_for_layer("adls_acl") == ["adls-access"]
    assert packs_for_layer("network") == ["azure-network"]
    assert packs_for_layer("unresolved") == sorted(PACKS)


def test_uc_failure_excludes_unrelated_domains():
    out = compile_access_knowledge("unity_catalog", "permission_denied external location")
    assert out["domains"] == ["governance", "unity-catalog"]
    assert out["entries"], "expected at least one knowledge entry"
    assert NON_VERTICAL_DOMAINS <= set(out["excluded_domains"])
    index = KnowledgeBase().load_index()
    for entry_id in out["entries"]:
        assert index[entry_id].domain not in NON_VERTICAL_DOMAINS


def test_network_failure_scopes_to_network_pack():
    out = compile_access_knowledge("network", "private endpoint dns nxdomain")
    assert set(out["domains"]) == {"governance", "azure-networking"}
    assert "azure.network.private-link-dns" in out["entries"]


def test_external_location_denied_expands_into_layered_terms():
    exp = expand("external location denied", KnowledgeBase().rules())
    terms = {t.casefold() for t in exp.terms}
    for expected in (
        "storage credential",
        "managed identity",
        "workspace binding",
        "private endpoint",
        "adls rbac",
        "adls acl",
    ):
        assert expected in terms
    assert "azure.unity-catalog.troubleshooting-external-locations" in exp.ids
    assert "azure.adls.gen2" in exp.ids


def test_report_carries_scoped_knowledge_block():
    report = run_case(FIXTURES / "s04_private_dns_not_linked")
    knowledge = report["knowledge"]
    assert knowledge["failure_layer"] == "network"
    assert set(knowledge["domains"]) == {"governance", "azure-networking"}
    assert "azure-finops" in knowledge["excluded_domains"]


def test_doctor_reports_live_collectors():
    check = doctor._live_collectors()
    assert check.area == "live_collectors"
    assert check.status == "ok"
    per = check.data["collectors"]
    assert set(per) == {
        "databricks", "unity_catalog", "azure_rbac", "adls_meta", "resource_graph",
    }
    for info in per.values():
        assert info["module"] == "available"
        assert info["live"] in {"available", "unavailable"}


def test_doctor_full_run_includes_collectors_and_no_secrets():
    out = doctor.run(areas=["live_collectors"])
    assert out["checks"][0]["area"] == "live_collectors"
    assert out["network_calls"] == 0
    assert out["cloud_mutation"] == "none"
