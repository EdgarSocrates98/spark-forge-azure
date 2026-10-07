"""Azure Monitor / Log Analytics collector -- read-only.

Offline ``from_export(path)`` ingests a Log Analytics query result
(``{"tables": [{"name": ..., "columns": [{"name": ...}], "rows": [[...]]}]}``,
the shape returned by the REST API and ``az monitor log-analytics query``
with ``-o json`` normalized to tables).  Log rows are DATA: they are redacted
like any other payload (logs routinely carry tokens).

Facts ``azure.log_analytics.row`` (subject = query name + table + row index).
Live method: ``LogsQueryClient.query_workspace`` (azure-monitor-query, lazy).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.collectors.base import (
    CollectorInputError,
    CollectorResult,
    read_export,
    run_pipeline,
)
from sparkforge_azure.findings.models import Fact

SOURCE = "azure.log_analytics"


def _to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
    return [
        Fact(
            kind="azure.log_analytics.row",
            subject={"query": rec["_query"], "table": rec["_table"], "row": rec["_row"]},
            attrs={k: v for k, v in rec.items() if not k.startswith("_")},
            provenance=dict(provenance),
        )
        for rec in records
    ]


def _records(payload: Any, query_name: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):  # bare list of row objects
        tables = [{"name": "PrimaryResult", "rows_obj": payload}]
    elif isinstance(payload, Mapping) and isinstance(payload.get("tables"), list):
        tables = payload["tables"]
    else:
        raise CollectorInputError("Log Analytics export needs a 'tables' list")
    out = []
    for table in tables:
        if not isinstance(table, Mapping):
            continue
        name = str(table.get("name", "PrimaryResult"))
        if "rows_obj" in table:
            rows = [dict(r) for r in table["rows_obj"] if isinstance(r, Mapping)]
        else:
            cols = [c.get("name") if isinstance(c, Mapping) else str(c)
                    for c in table.get("columns", [])]
            rows = [dict(zip(cols, r, strict=False)) for r in table.get("rows", [])
                    if isinstance(r, list)]
        for i, row in enumerate(rows):
            out.append({**row, "_query": query_name, "_table": name, "_row": i})
    return out


def from_export(path: str | Path, *, query_name: str | None = None,
                raw_dir: str | Path | None = None,
                observed_at: str | None = None) -> CollectorResult:
    return run_pipeline(_records(read_export(path), query_name or Path(path).stem),
                        source=SOURCE, mode="export", observed_at=observed_at,
                        to_facts=_to_facts, raw_dir=raw_dir)


class MonitorCollector:
    """Read-only Log Analytics query.  Public surface: ``collect`` only."""

    def __init__(self, workspace_id: str, *, credential: Any | None = None,
                 client: Any | None = None) -> None:
        self._workspace_id = workspace_id
        self._credential = credential
        self._client = client

    def collect(self, query: str, *, timespan: Any, query_name: str = "query",
                observed_at: str | None = None) -> CollectorResult:
        from sparkforge_azure.collectors.auth import get_credential, require_module

        client = self._client
        if client is None:
            mod = require_module("azure.monitor.query", "azure")
            client = mod.LogsQueryClient(self._credential or get_credential("default"))
        response = client.query_workspace(self._workspace_id, query, timespan=timespan)
        tables = [
            {"name": getattr(t, "name", "PrimaryResult"),
             "columns": [{"name": c} for c in getattr(t, "columns", [])],
             "rows": [list(r) for r in getattr(t, "rows", [])]}
            for t in getattr(response, "tables", [])
        ]
        return run_pipeline(_records({"tables": tables}, query_name), source=SOURCE,
                            mode="live", observed_at=observed_at, to_facts=_to_facts)


__all__ = ["SOURCE", "MonitorCollector", "from_export"]
