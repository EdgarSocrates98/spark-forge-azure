"""Change impact: dependents grouped by category, depth-bounded, exact resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from sparkforge_azure.collectors import resource_graph
from sparkforge_azure.graph import (
    build_workspace_graph,
    federate,
    impact,
    knowledge_graph,
    load_workspace_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "workspace"


@pytest.fixture(scope="module")
def graph():
    static = build_workspace_graph(load_workspace_manifest(EXAMPLE))
    live = resource_graph.to_graph(
        resource_graph.from_export(ROOT / "fixtures" / "azure" / "arg_export.json"))
    return federate(static, live).graph


def _ids(result, category):
    return [item["id"] for item in result["impacted"].get(category, [])]


def test_changing_a_module_reaches_symbols_callers_and_tests(graph):
    r = impact(graph, ["databricks/src/lakehouse/transforms.py"])
    assert r["changed"] == ["code:file:databricks/src/lakehouse/transforms.py"]
    assert "code:function:databricks/src/lakehouse/transforms.py::normalize_order" in _ids(
        r, "symbols")
    assert "code:test:databricks/tests/test_transforms.py" in _ids(r, "tests")
    callers = _ids(r, "callers")
    assert "code:function:databricks/tests/test_transforms.py::test_normalize_order" in callers
    assert "code:function:databricks/notebooks/silver_orders.py::run" in callers
    assert r["unresolved"] == []


def test_changing_a_notebook_reaches_its_config(graph):
    r = impact(graph, ["databricks/notebooks/silver_orders.py"])
    assert "code:config:databricks/databricks.yml" in _ids(r, "configs")
    assert "data:notebook:databricks/notebooks/silver_orders.py" in _ids(r, "data")


def test_changing_terraform_reaches_bound_azure_resources_only(graph):
    r = impact(graph, ["terraform/main.tf"])
    resources = _ids(r, "resources")
    assert any(i.endswith("storageaccounts/stlakehouse") for i in resources)
    assert any(i.endswith("workspaces/dbw-analytics") for i in resources)
    # stshared is not bound: it must not appear as impacted (no name matching)
    assert not any(i.endswith("storageaccounts/stshared") for i in resources)


def test_depth_bound_and_unknown_items(graph):
    shallow = impact(graph, ["databricks/src/lakehouse/transforms.py"], max_depth=1)
    deep = impact(graph, ["databricks/src/lakehouse/transforms.py"], max_depth=4)
    assert shallow["total"] < deep["total"]
    assert all(item["depth"] <= 1 for items in shallow["impacted"].values() for item in items)
    r = impact(graph, ["transforms.py", "nope/x.py"])
    assert r["changed"] == []  # basename alone is not an exact path: no guessing
    assert [u["changed"] for u in r["unresolved"]] == ["transforms.py", "nope/x.py"]
    with pytest.raises(ValueError):
        impact(graph, ["x"], max_depth=-1)


def test_impact_is_deterministic(graph):
    a = impact(graph, ["terraform/main.tf", "databricks/src/lakehouse/transforms.py"])
    b = impact(graph, ["databricks/src/lakehouse/transforms.py", "terraform/main.tf"])
    assert a == b


def test_knowledge_change_reaches_skills_and_agents(tmp_path):
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "knowledge" / "k.md").write_text("---\nid: k1\ndomain: d\n---\n",
                                                 encoding="utf-8")
    (tmp_path / "skills" / "s").mkdir(parents=True)
    (tmp_path / "skills" / "s" / "SKILL.md").write_text(
        "---\nname: s\nmetadata:\n  knowledge_refs: [k1]\n---\n", encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "a.md").write_text("---\nid: a\nskills: [s]\n---\n",
                                              encoding="utf-8")
    r = impact(knowledge_graph(tmp_path), ["k1"])
    assert _ids(r, "skills") == ["knowledge:skill:s"]
    assert _ids(r, "agents") == ["knowledge:agent:a"]
