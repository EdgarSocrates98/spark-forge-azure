"""Microsoft Fabric collector (read-only, opt-in).

Two ingestion paths:

* ``from_export(path, artifact)`` — ingest a bundle-shaped artifact file
  (``workspace``, ``items``, ``lakehouse``, ``onelake_security``,
  ``shortcuts``, ``connections``, ``capacity``, ``environment``,
  ``pipelines``, ``identity``) into Facts via ``fabric.extract``.
* ``collect_live(workspace_id, fetch=None)`` — call the official Fabric
  REST API (``api.fabric.microsoft.com/v1``) through an injected fetch
  callable.  No SDK is required by the package itself; the caller supplies
  an authenticated ``fetch(method, url) -> dict`` (e.g. an httpx wrapper or
  a test double).  Live mode is NEVER invoked by the offline pipeline.

Every failure lands in ``unresolved`` with a FailureClass — never a
fabricated empty fact.  Responses are redacted at the boundary.
"""
from __future__ import annotations

import datetime as _dt
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.collectors import failure
from sparkforge_azure.collectors.base import (
    CollectorInputError,
    CollectorResult,
    CollectorUnavailable,
    read_export,
    run_pipeline,
)
from sparkforge_azure.fabric import extract as fabric_extract
from sparkforge_azure.findings.models import Fact

SOURCE = "fabric"
FABRIC_API = "https://api.fabric.microsoft.com/v1"

#: artifact name -> extractor
_EXPORTERS = {
    "workspace": fabric_extract.extract_workspace,
    "items": fabric_extract.extract_items,
    "lakehouse": fabric_extract.extract_lakehouse,
    "onelake_security": fabric_extract.extract_onelake_security,
    "shortcuts": fabric_extract.extract_shortcuts,
    "connections": fabric_extract.extract_connections,
    "capacity": fabric_extract.extract_capacity,
    "environment": fabric_extract.extract_environment,
    "pipelines": fabric_extract.extract_pipelines,
    "identity": fabric_extract.extract_identity,
}


def from_export(path: str | Path, *, artifact: str,
                raw_dir: str | Path | None = None) -> CollectorResult:
    extractor = _EXPORTERS.get(artifact)
    if extractor is None:
        raise CollectorInputError(f"unknown fabric artifact: {artifact!r}")
    payload = read_export(path)
    if not isinstance(payload, Mapping):
        raise CollectorInputError(f"fabric export must be an object: {artifact}")
    observed = payload.get("observed_at")

    def to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
        facts: list[Fact] = []
        for rec in records:
            facts.extend(extractor(rec["_payload"], provenance))
        return facts

    return run_pipeline([{"_payload": dict(payload)}], source=SOURCE,
                        mode="export",
                        observed_at=observed if isinstance(observed, str) else None,
                        to_facts=to_facts, raw_dir=raw_dir)


def _default_fetch() -> Callable[[str, str], Any]:
    raise CollectorUnavailable(
        "fabric live collection requires an injected `fetch` callable "
        "(no SDK is bundled — pass one explicitly)")


def collect_live(*, workspace_id: str,
                 fetch: Callable[[str, str], Any] | None = None,
                 raw_dir: str | Path | None = None,
                 observed_at: str | None = None) -> CollectorResult:
    """Read-only Fabric REST inventory of one workspace.

    ``fetch(method, url)`` must return the decoded JSON body.  Read-only:
    only GET endpoints under ``/workspaces/{id}/items`` and
    ``/workspaces/{id}/lakehouses`` are issued.  Any failure becomes an
    ``unresolved`` entry, never a fabricated fact.
    """
    fetch = fetch or _default_fetch()
    observed = observed_at or _dt.datetime.now(_dt.timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    def grab(name: str, url: str) -> None:
        try:
            body = fetch("GET", url)
            records.append({"_artifact": name, "_payload": body or {}})
        except Exception as exc:  # noqa: BLE001 - failure becomes unresolved
            errors.append(failure.unresolved(name, exc, source=SOURCE))

    grab("items", f"{FABRIC_API}/workspaces/{workspace_id}/items")
    grab("lakehouses", f"{FABRIC_API}/workspaces/{workspace_id}/lakehouses")
    # Capacity/workspace metadata: item list responses carry workspace ids;
    # deeper endpoints (OneLake security, connections) need explicit consent
    # per artifact, so live mode stays a thin inventory surface.
    def to_facts(recs: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
        facts: list[Fact] = []
        for rec in recs:
            name = rec["_artifact"]
            payload = rec["_payload"]
            if name == "items":
                facts.extend(fabric_extract.extract_items(payload, provenance))
            elif name == "lakehouses":
                for lh in payload.get("value") or []:
                    facts.extend(fabric_extract.extract_lakehouse(
                        dict(lh), provenance))
        return facts

    result = run_pipeline(records, source=SOURCE, mode="live",
                          observed_at=observed, to_facts=to_facts,
                          raw_dir=raw_dir)
    result.unresolved.extend(errors)
    return result


__all__ = ["FABRIC_API", "SOURCE", "collect_live", "from_export"]
