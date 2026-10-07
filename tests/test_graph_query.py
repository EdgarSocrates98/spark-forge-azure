"""Deterministic Graphfy queries + CLI/MCP surfaces for graph commands."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pytest

from sparkforge_azure.graph import (
    Edge,
    Graph,
    Node,
    Provenance,
    find_nodes,
    neighbors,
    node_id,
    shortest_path,
    slice_graph,
)
from sparkforge_azure.graph.model import GraphError

ROOT = Path(__file__).resolve().parents[1]
P = Provenance("static", "t")


def _chain(n: int) -> Graph:
    g = Graph()
    ids = [node_id("code", "function", f"m.py::f{i}") for i in range(n)]
    for i, nid in enumerate(ids):
        g.add_node(Node(nid, "function", "code", {"i": i, "even": i % 2 == 0}, P))
    for a, b in zip(ids, ids[1:], strict=False):
        g.add_edge(Edge(a, "calls", b, {}, P))
    g.add_node(Node(node_id("code", "test", "t.py"), "test", "code", {}, P))
    g.add_edge(Edge(node_id("code", "test", "t.py"), "tests", ids[0], {}, P))
    return g


def test_find_nodes_by_kind_layer_attrs():
    g = _chain(5)
    assert len(find_nodes(g, kind="function")) == 5
    assert [n.attrs["i"] for n in find_nodes(g, kind="function", attrs={"even": True})] == [0, 2,
                                                                                          4]
    assert len(find_nodes(g, layer="code", limit=2)) == 2
    assert find_nodes(g, layer="azure") == []


def test_neighbors_with_relation_filter():
    g = _chain(3)
    f0 = node_id("code", "function", "m.py::f0")
    assert [x["id"] for x in neighbors(g, f0, direction="in")] == ["code:test:t.py"]
    assert neighbors(g, f0, relation="tests") == []
    assert [x["relation"] for x in neighbors(g, f0, direction="both")] == ["calls", "tests"]
    with pytest.raises(GraphError):
        neighbors(g, "code:file:missing")


def test_shortest_path_bounded_and_deterministic():
    g = _chain(6)
    f0, f5 = node_id("code", "function", "m.py::f0"), node_id("code", "function", "m.py::f5")
    path = shortest_path(g, f0, f5)
    assert path is not None and len(path) == 6
    assert shortest_path(g, f0, f5, max_depth=3) is None
    assert shortest_path(g, f5, f0, directed=True) is None
    assert shortest_path(g, f5, f0)[0] == f5
    assert shortest_path(g, f0, f5, relations=["tests"]) is None


def test_slice_respects_budget():
    g = _chain(20)
    seed = node_id("code", "function", "m.py::f10")
    sub, truncated = slice_graph(g, [seed], budget=4, max_depth=5)
    assert len(sub.nodes) == 4 and truncated is True
    assert seed in sub.nodes
    sub2, truncated2 = slice_graph(g, [seed], budget=100, max_depth=1)
    assert len(sub2.nodes) == 3 and truncated2 is False
    with pytest.raises(GraphError):
        slice_graph(g, [seed], budget=0)


def _run(module, argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    module.register(sub)
    args = parser.parse_args(argv)
    return args.func(args)


def test_cli_graph_build_query_impact_federate(tmp_path):
    from sparkforge_azure.cli import cmd_collect, cmd_graph

    ws = tmp_path / "ws"
    shutil.copytree(ROOT / "examples" / "workspace", ws)
    out = tmp_path / "static.json"
    built = _run(cmd_graph, ["graph", "build", "--root", str(ws), "--out", str(out)])
    assert built["status"] == "ok" and out.is_file()
    assert (ws / ".sparkforge-azure" / "graph" / "index.json").is_file()
    q = _run(cmd_graph, ["graph", "query", "--graph", str(out), "--kind", "repository"])
    assert q["total"] == 5
    imp = _run(cmd_graph, ["graph", "impact", "--graph", str(out), "--changed",
                           "databricks/src/lakehouse/transforms.py"])
    assert imp["status"] == "ok" and "tests" in imp["impacted"]
    live = tmp_path / "live.json"
    col = _run(cmd_collect, ["collect", "workspace-graph", "--manifest", str(ws),
                             "--export", str(ROOT / "fixtures" / "azure" / "arg_export.json"),
                             "--out", str(live)])
    assert col["status"] == "ok" and col["out_of_scope"] == 1
    fed = _run(cmd_graph, ["graph", "federate", "--static", str(out), "--live", str(live)])
    assert fed["status"] == "ok"
    assert fed["sources"] == ["static", "live"]
    json.dumps(fed)


def test_cli_refusals(tmp_path):
    from sparkforge_azure.cli import cmd_collect, cmd_graph
    from sparkforge_azure.cli.main import CliError

    with pytest.raises(CliError):
        _run(cmd_graph, ["graph", "query", "--graph", str(tmp_path / "nope.json"), "--kind", "x"])
    with pytest.raises(CliError):
        _run(cmd_graph, ["graph", "federate"])
    with pytest.raises(CliError):
        _run(cmd_collect, ["collect", "workspace-graph", "--manifest",
                           str(ROOT / "examples" / "workspace")])


GRAPH_TOOLS = ("sfa_graph_query", "sfa_graph_impact", "sfa_collect_workspace_graph")


@pytest.fixture()
def graph_tools():
    """Register the graph tools for this test only and restore the global
    registry afterwards (the module may not be wired into TOOL_MODULES yet)."""

    import importlib

    from sparkforge_azure.mcp.tools import TOOLS

    before = dict(TOOLS)
    module = importlib.import_module("sparkforge_azure.mcp.graph_tools")
    for name in GRAPH_TOOLS:
        TOOLS.pop(name, None)
    module = importlib.reload(module)
    try:
        yield module
    finally:
        TOOLS.clear()
        TOOLS.update(before)


def test_mcp_graph_tools_declared_and_gated(tmp_path, monkeypatch, graph_tools):
    from sparkforge_azure.mcp.tools import TOOLS, authorize

    assert TOOLS["sfa_graph_query"].risk.read_only
    assert TOOLS["sfa_graph_impact"].compact is True
    assert authorize(TOOLS["sfa_graph_query"]).allowed
    collect = TOOLS["sfa_collect_workspace_graph"]
    assert collect.risk.cloud_read
    assert not authorize(collect).allowed
    assert authorize(collect, cloud_read_enabled=True).allowed

    g = _chain(3)
    (tmp_path / "g.json").write_text(g.to_json(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    res = graph_tools.graph_query({"graph": "g.json", "kind": "test"})
    assert res["total"] == 1
    imp = graph_tools.graph_impact({"graph": "g.json", "changed": ["code:function:m.py::f2"]})
    assert imp["total"] >= 2
    with pytest.raises(ValueError):
        graph_tools.graph_query({"graph": "../outside.json"})
