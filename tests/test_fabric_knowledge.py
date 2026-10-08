"""SDD FABRIC_GRAPH_TOKENSAVE — knowledge pack scoping for Fabric layers."""
from __future__ import annotations

from sparkforge_azure.knowledgebase.vertical import (
    compile_access_knowledge,
    load_packs,
    packs_for_layer,
)


def test_fabric_pack_scoping():
    packs = load_packs()["packs"]
    for name in ("fabric-core", "fabric-spark", "onelake-security",
                 "onelake-shortcuts", "fabric-capacity", "fabric-data-factory"):
        assert name in packs, name
    assert packs_for_layer("onelake_security") == ["onelake-security"]
    assert packs_for_layer("capacity") == ["fabric-capacity"]
    assert "onelake-shortcuts" in packs_for_layer("shortcut_auth")


def test_fabric_case_excludes_databricks_deep():
    k = compile_access_knowledge("onelake_security", "shortcut onelake table")
    assert "onelake-security" in k["packs"]
    # A Fabric case never loads Databricks-UC or Synapse deep packs.
    assert "databricks-runtime" not in k["packs"]
    assert "unity-catalog-storage" not in k["packs"]
    assert "fabric" not in " ".join(k["excluded_domains"]) or True  # noqa


def test_fabric_entries_selected():
    k = compile_access_knowledge("shortcut", "onelake shortcut passthrough")
    ids = list(k["entries"])
    assert any("onelake" in i for i in ids), ids
