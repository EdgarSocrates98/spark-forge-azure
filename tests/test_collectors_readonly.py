"""Collectors are read-only by construction (section 176)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from sparkforge_azure.collectors import cost, databricks, monitor, resource_graph

PKG = Path(__file__).resolve().parents[1] / "sparkforge_azure" / "collectors"
SOURCES = sorted(PKG.glob("*.py"))

# Mutating SDK verbs (azure-mgmt-*, databricks-sdk, azure-storage-*) and HTTP verbs.
FORBIDDEN_CALLS = frozenset({
    "begin_create", "begin_create_or_update", "create_or_update", "begin_delete", "delete",
    "begin_update", "update", "put", "post", "patch", "create", "remove", "purge",
    "begin_purge", "set_access_control", "set_access_control_recursive", "upload_blob",
    "upload_data", "append_data", "flush_data", "delete_file", "delete_directory",
    "run_now", "submit", "start", "stop", "restart", "permanent_delete", "edit",
    "reset", "repair_run", "cancel_run", "grant", "revoke", "rotate", "regenerate_key",
    "set_secret", "begin_restore", "request",
})
FORBIDDEN_TEXT = ("create_or_update", "begin_create", "begin_delete", ".put(", ".post(",
                  ".patch(", "requests.", "urllib.request", "http.client")
COLLECTOR_CLASSES = [
    resource_graph.ResourceGraphCollector,
    databricks.DatabricksCollector,
    cost.CostCollector,
    monitor.MonitorCollector,
]


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_no_mutating_calls_in_collector_sources(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = [
        (node.lineno, node.func.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in FORBIDDEN_CALLS
    ]
    assert bad == [], f"{path.name}: mutating call(s) {bad}"
    text = path.read_text(encoding="utf-8")
    assert not [t for t in FORBIDDEN_TEXT if t in text], path.name


@pytest.mark.parametrize("cls", COLLECTOR_CLASSES, ids=lambda c: c.__name__)
def test_collector_public_surface_is_collect_only(cls):
    public = {
        name for name, member in inspect.getmembers(cls)
        if not name.startswith("_") and callable(member)
    }
    assert public == {"collect"}


def test_sdk_calls_are_reads_only():
    """The only SDK entry points used are documented read/query endpoints."""

    allowed = {"resources", "list", "usage", "query_workspace", "as_dict"}
    seen: set[str] = set()
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, (ast.Name, ast.Attribute))):
                base = node.func.value
                base_name = base.attr if isinstance(base, ast.Attribute) else base.id
                if base_name in {"client", "w", "api", "query"}:
                    seen.add(node.func.attr)
    assert seen and seen <= allowed, seen
