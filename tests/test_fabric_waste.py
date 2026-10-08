"""SDD FABRIC_GRAPH_TOKENSAVE — fabric waste detectors (hypothesis level)."""
from __future__ import annotations

from sparkforge_azure.fabric.waste import detect_fabric_waste


def test_repeated_item_fetch_detected():
    spans = [
        {"name": "fabric.fetch_items", "resultado": {}},
        {"name": "fabric.fetch_items", "resultado": {}},
    ]
    findings = detect_fabric_waste(spans)
    assert any(f["kind"] == "repeated_item_fetch" for f in findings)
    assert all(f["evidence"] == "hypothesis" for f in findings)


def test_single_fetch_no_waste():
    spans = [{"name": "fabric.fetch_items", "resultado": {}}]
    assert detect_fabric_waste(spans) == []


def test_whole_workspace_after_graph():
    spans = [
        {"name": "fabric.graph_query", "resultado": {"graph_assisted": True}},
        {"name": "fabric.list_items", "resultado": {}},
    ]
    findings = detect_fabric_waste(spans)
    assert any(f["kind"] == "whole_workspace_after_graph" for f in findings)
