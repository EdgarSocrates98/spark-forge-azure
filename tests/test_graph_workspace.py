"""Workspace manifest validation, static workspace graph and incremental store."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from sparkforge_azure.graph import (
    WorkspaceError,
    build_incremental,
    build_workspace_graph,
    load_graph,
    load_workspace_manifest,
    parse_workspace_manifest,
)
from sparkforge_azure.graph.model import GraphError, azure_node_id

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "workspace"
SUB = "00000000-0000-4000-8000-00000000aaaa"
LAKE = (f"/subscriptions/{SUB}/resourceGroups/rg-data/providers/"
        "Microsoft.Storage/storageAccounts/stlakehouse")


def _base(**extra):
    raw = {
        "schema_version": 1,
        "workspace": "w",
        "repositories": [{"name": "infra", "path": "infra", "role": "terraform"}],
    }
    raw.update(extra)
    return raw


@pytest.fixture()
def workspace(tmp_path):
    dst = tmp_path / "ws"
    shutil.copytree(EXAMPLE, dst)
    return dst


def test_example_manifest_loads():
    m = load_workspace_manifest(EXAMPLE)
    assert [r.name for r in m.repositories] == ["adf", "databricks", "fabric", "shared",
                                                "terraform"]
    assert m.subscriptions() == (SUB,)
    assert m.resource("lake").arm_id == LAKE
    assert m.resource(LAKE.upper()) is not None


@pytest.mark.parametrize("path", ["../outside", "a/../../x", "/etc", "C:/Windows", "~/x",
                                  "..\\up"])
def test_repository_path_traversal_refused(tmp_path, path):
    raw = _base(repositories=[{"name": "r", "path": path, "role": "shared"}])
    with pytest.raises(WorkspaceError):
        parse_workspace_manifest(raw, tmp_path)


@pytest.mark.parametrize("arm", [
    "stlakehouse",
    "/subscriptions/not-a-guid/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/x",
    f"/subscriptions/{SUB}/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts",
    f"/subscriptions/{SUB}/resourceGroups/../providers/Microsoft.Storage/storageAccounts/x",
    f"/subscriptions/{SUB}/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/x?y=1",
])
def test_invalid_arm_ids_rejected(tmp_path, arm):
    raw = _base(cloud_resources=[{"name": "x", "arm_id": arm}])
    with pytest.raises(WorkspaceError):
        parse_workspace_manifest(raw, tmp_path)


def test_other_explicit_ids_validated(tmp_path):
    for bad in ({"name": "f", "fabric_workspace_id": "not-guid"},
                {"name": "d", "databricks_workspace_id": "abc"},
                {"name": "u", "databricks_workspace_id": "123456789", "workspace_url": "http://x"},
                {"name": "n"}):
        with pytest.raises(WorkspaceError):
            parse_workspace_manifest(_base(cloud_resources=[bad]), tmp_path)


def test_relationship_and_binding_must_reference_declared_repos(tmp_path):
    with pytest.raises(WorkspaceError):
        parse_workspace_manifest(
            _base(relationships=[{"source": "infra", "relation": "uses", "target": "ghost"}]),
            tmp_path)
    with pytest.raises(WorkspaceError):
        parse_workspace_manifest(
            _base(bindings=[{"repository": "ghost", "address": "a.b", "target": "x"}]), tmp_path)


def test_unknown_role_and_bad_schema(tmp_path):
    with pytest.raises(WorkspaceError):
        parse_workspace_manifest(
            _base(repositories=[{"name": "r", "path": "r", "role": "aws"}]), tmp_path)
    with pytest.raises(WorkspaceError):
        parse_workspace_manifest(_base(schema_version=2), tmp_path)


def test_static_graph_structure():
    g = build_workspace_graph(load_workspace_manifest(EXAMPLE))
    lake = azure_node_id(LAKE)
    assert g.nodes[lake].attrs["declared"] is True
    assert g.nodes[lake].provenance.kind == "static"
    assert ("code:symbol:terraform/azurerm_storage_account.lake", "binds_to", lake) in g.edges
    assert "data:notebook:databricks/notebooks/silver_orders.py" in g.nodes
    assert ("code:test:databricks/tests/test_transforms.py", "tests",
            "code:file:databricks/src/lakehouse/transforms.py") in g.edges
    assert ("code:repository:databricks", "depends_on", "code:repository:terraform") in g.edges
    assert ("code:repository:adf", "member_of", "knowledge:domain:sales") in g.edges
    assert "azure:fabric:33333333-3333-4333-8333-333333333333" in g.nodes
    assert ("code:config:databricks/databricks.yml", "configures",
            "code:file:databricks/notebooks/silver_orders.py") in g.edges


def test_static_graph_is_deterministic_and_engine_independent():
    m = load_workspace_manifest(EXAMPLE)
    a = build_workspace_graph(m)
    b = build_workspace_graph(m)
    assert a.to_json() == b.to_json()
    c = build_workspace_graph(m, use_codeintel=False)
    assert set(a.edges) == set(c.edges)
    assert set(a.nodes) == set(c.nodes)


def test_binding_to_missing_address_is_unresolved(workspace):
    path = workspace / "sparkforge-azure.workspace.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["bindings"].append({"repository": "terraform", "address": "azurerm_key_vault.nope",
                            "target": "lake"})
    raw["bindings"].append({"repository": "terraform", "address": "azurerm_storage_account.lake",
                            "target": "undeclared-name"})
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    g = build_workspace_graph(load_workspace_manifest(path))
    reasons = sorted(u["reason"] for u in g.unresolved)
    assert "binding_source_not_found" in reasons
    assert "binding_target_undeclared" in reasons
    assert not any(k[0].endswith("azurerm_key_vault.nope") for k in g.edges)


def test_boundary_violation_reported(workspace):
    path = workspace / "sparkforge-azure.workspace.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["relationships"].append({"source": "fabric", "relation": "depends_on",
                                 "target": "terraform"})
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    g = build_workspace_graph(load_workspace_manifest(path))
    assert any(u["reason"] == "boundary_violation" for u in g.unresolved)


def test_incremental_store_rebuilds_only_changed_repos(workspace, tmp_path):
    m = load_workspace_manifest(workspace)
    state = tmp_path / "state"
    g1, r1 = build_incremental(m, state_dir=state)
    assert r1["rebuilt"] == ["adf", "databricks", "fabric", "shared", "terraform"]
    g2, r2 = build_incremental(m, state_dir=state)
    assert r2["rebuilt"] == [] and len(r2["reused"]) == 5
    assert g1.fingerprint() == g2.fingerprint()
    (workspace / "databricks" / "src" / "lakehouse" / "extra.py").write_text(
        "def extra():\n    return 1\n", encoding="utf-8")
    g3, r3 = build_incremental(load_workspace_manifest(workspace), state_dir=state)
    assert r3["rebuilt"] == ["databricks"]
    assert "code:function:databricks/src/lakehouse/extra.py::extra" in g3.nodes
    loaded = load_graph(state / "graph.json")
    assert loaded.fingerprint() == g3.fingerprint()


def test_tampered_graph_is_refused(workspace, tmp_path):
    state = tmp_path / "state"
    build_incremental(load_workspace_manifest(workspace), state_dir=state)
    path = state / "graph.json"
    path.write_text(path.read_text(encoding="utf-8").replace("stlakehouse", "stevil", 1),
                    encoding="utf-8")
    with pytest.raises(GraphError):
        load_graph(path)
