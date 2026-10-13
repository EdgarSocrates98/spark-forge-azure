"""Unity Catalog collector (read-only): storage credentials, external locations,
catalogs/schemas/tables, grants, workspace bindings.

Offline ``from_export(path)`` ingests::

    {"storage_credentials": {name: {identity_id, access_connector_id}},
     "external_locations": [{name, url, credential, isolation_mode?, workspaces?}],
     "catalogs": {name: {isolation_mode, workspaces}}, "schemas": {...},
     "tables": {name: {location, format}}, "grants": [{securable, principal,
     privileges}], "observed_at": "..."}

Live mode lists via ``databricks-sdk`` (lazy import).  Every failure becomes an
``unresolved`` entry with a FailureClass -- never a fabricated empty fact.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.azure import extract
from sparkforge_azure.collectors import failure
from sparkforge_azure.collectors.base import (
    CollectorInputError,
    CollectorResult,
    read_export,
    run_pipeline,
)
from sparkforge_azure.findings.models import Fact

SOURCE = "unity_catalog"
LIVE_ARGS = ("host", "workspace_id")


def _records(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Flatten the UC payload into per-object records carrying the whole payload ref."""
    return [{"_payload": dict(payload)}]


def _to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
    facts: list[Fact] = []
    for rec in records:
        facts.extend(extract.extract_uc(rec["_payload"], provenance))
    return facts


def _check_payload(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise CollectorInputError("unity catalog export must be an object")
    for key in ("external_locations", "grants"):
        if key in payload and not isinstance(payload[key], list):
            raise CollectorInputError(f"unity catalog export: {key} must be a list")
    for key in ("storage_credentials", "catalogs", "schemas", "tables"):
        if key in payload and not isinstance(payload[key], Mapping):
            raise CollectorInputError(f"unity catalog export: {key} must be an object")
    return payload


def from_export(path: str | Path, *, raw_dir: str | Path | None = None) -> CollectorResult:
    payload = _check_payload(read_export(path))
    observed = payload.get("observed_at")
    return run_pipeline(_records(payload), source=SOURCE, mode="export",
                        observed_at=observed if isinstance(observed, str) else None,
                        to_facts=_to_facts, raw_dir=raw_dir)


def _live_payload(w: Any) -> dict[str, Any]:
    """Read-only listings via a databricks-sdk WorkspaceClient."""
    payload: dict[str, Any] = {}

    def grab(section: str, call: Any) -> None:
        try:
            items = call()
            payload[section] = [
                i.as_dict() if hasattr(i, "as_dict") else dict(i) for i in items
            ]
        except Exception as exc:  # noqa: BLE001 - failure becomes unresolved upstream
            payload.setdefault("_errors", []).append(
                failure.unresolved(section, exc, source=SOURCE))

    grab("storage_credentials_list", lambda: w.storage_credentials.list())
    grab("external_locations_list", lambda: w.external_locations.list())
    grab("catalogs_list", lambda: w.catalogs.list())
    creds = {c.get("name"): {"identity_id": ((c.get("azure_managed_identity") or {})
                                             .get("object_id")
                                             or (c.get("azure_managed_identity") or {})
                                             .get("managed_identity_id")),
                             "access_connector_id": (c.get("azure_managed_identity") or {})
                             .get("access_connector_id")}
             for c in payload.pop("storage_credentials_list", [])}
    payload["storage_credentials"] = creds
    payload["external_locations"] = [
        {"name": loc.get("name"), "url": loc.get("url"),
         "credential": loc.get("credential_name"),
         "isolation_mode": loc.get("isolation_mode")}
        for loc in payload.pop("external_locations_list", [])
    ]
    payload["catalogs"] = {c.get("name"): c
                           for c in payload.pop("catalogs_list", []) if c.get("name")}
    return payload


def collect_live(*, host: str, workspace_id: str, client: Any | None = None,
                 raw_dir: str | Path | None = None,
                 observed_at: str | None = None) -> CollectorResult:
    """Read-only UC inventory.  Any failure -> unresolved, never absent."""
    try:
        if client is None:
            from sparkforge_azure.collectors.auth import require_module

            sdk = require_module("databricks.sdk", "databricks")
            client = sdk.WorkspaceClient(host=host)
        payload = _live_payload(client)
    except Exception as exc:  # noqa: BLE001 - classified, not raised
        result = CollectorResult(source=SOURCE, mode="live", observed_at=observed_at)
        result.unresolved.append(
            failure.unresolved("unity_catalog", exc, source=SOURCE))
        return result
    errors = payload.pop("_errors", [])
    result = run_pipeline(_records(payload), source=SOURCE, mode="live",
                          observed_at=observed_at, to_facts=_to_facts,
                          raw_dir=raw_dir)
    result.unresolved.extend(errors)
    return result


__all__ = ["SOURCE", "collect_live", "from_export"]
