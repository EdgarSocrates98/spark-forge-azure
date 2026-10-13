"""Databricks collector (jobs, clusters, Unity Catalog catalogs) -- read-only.

Offline ``from_export(path)`` ingests::

    {"workspace": {"workspace_id": "1234567890123456", "arm_id": "/subscriptions/...",
                   "url": "https://adb-....azuredatabricks.net"},
     "observed_at": "...", "jobs": [...], "clusters": [...], "catalogs": [...]}

(the ``as_dict()`` shapes of databricks-sdk ``jobs.list`` / ``clusters.list`` /
``catalogs.list``).  The live method uses ``databricks-sdk`` (lazy import) with
list operations only.
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
from sparkforge_azure.graph.arm import DATABRICKS_WORKSPACE_ID_RE

SOURCE = "databricks.workspace"
_KINDS = (("jobs", "databricks.job", "job_id"), ("clusters", "databricks.cluster", "cluster_id"),
          ("catalogs", "unity_catalog.catalog", "name"))
_SCALARS = (str, int, float, bool)


def _flat(rec: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    settings = rec.get("settings") if isinstance(rec.get("settings"), Mapping) else {}
    for key, value in {**settings, **rec}.items():
        if isinstance(value, _SCALARS) and key != "settings":
            out[key] = value
    return out


def _to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
    facts = []
    for rec in records:
        kind = rec["_kind"]
        ws = rec["_workspace_id"]
        key = rec["_key"]
        attrs = {k: v for k, v in _flat(rec).items() if not k.startswith("_")}
        facts.append(Fact(kind=kind, subject={"workspace_id": ws, "id": str(key)},
                          attrs=attrs, provenance=dict(provenance)))
    return facts


def _records(payload: Mapping[str, Any], workspace_id: str) -> list[dict[str, Any]]:
    out = []
    for section, kind, key_field in _KINDS:
        items = payload.get(section) or []
        if not isinstance(items, list):
            raise CollectorInputError(f"{section} must be a list")
        for item in items:
            if not isinstance(item, Mapping) or item.get(key_field) in (None, ""):
                continue
            out.append({**item, "_kind": kind, "_workspace_id": workspace_id,
                        "_key": item[key_field]})
    return out


def from_export(path: str | Path, *, raw_dir: str | Path | None = None) -> CollectorResult:
    payload = read_export(path)
    if not isinstance(payload, Mapping):
        raise CollectorInputError("databricks export must be an object")
    ws = payload.get("workspace") if isinstance(payload.get("workspace"), Mapping) else {}
    wid = str(ws.get("workspace_id", ""))
    if not DATABRICKS_WORKSPACE_ID_RE.match(wid):
        raise CollectorInputError("databricks export needs workspace.workspace_id (numeric)")
    observed = payload.get("observed_at")
    return run_pipeline(_records(payload, wid), source=SOURCE, mode="export",
                        observed_at=observed if isinstance(observed, str) else None,
                        to_facts=_to_facts, raw_dir=raw_dir)


class DatabricksCollector:
    """Read-only Databricks inventory.  Public surface: ``collect`` only."""

    def __init__(self, host: str, workspace_id: str, *, client: Any | None = None) -> None:
        if not DATABRICKS_WORKSPACE_ID_RE.match(str(workspace_id)):
            raise CollectorInputError("workspace_id must be numeric")
        self._host = host
        self._workspace_id = str(workspace_id)
        self._client = client

    def _resolve_client(self) -> Any:
        if self._client is not None:
            return self._client
        from sparkforge_azure.collectors.auth import require_module

        sdk = require_module("databricks.sdk", "databricks")
        return sdk.WorkspaceClient(host=self._host)

    def collect(self, *, raw_dir: str | Path | None = None,
                observed_at: str | None = None) -> CollectorResult:
        w = self._resolve_client()
        payload: dict[str, Any] = {}
        for section, api in (("jobs", w.jobs), ("clusters", w.clusters),
                             ("catalogs", w.catalogs)):
            payload[section] = [
                item.as_dict() if hasattr(item, "as_dict") else dict(item)
                for item in api.list()
            ]
        return run_pipeline(_records(payload, self._workspace_id), source=SOURCE, mode="live",
                            observed_at=observed_at, to_facts=_to_facts, raw_dir=raw_dir)


__all__ = ["SOURCE", "DatabricksCollector", "from_export"]
