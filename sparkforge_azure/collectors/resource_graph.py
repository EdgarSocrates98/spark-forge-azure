"""Azure Resource Graph inventory collector (section 177) -- read-only.

Live path: one KQL query (``ARG_QUERY``) through ``azure-mgmt-resourcegraph``
(imported lazily), paginated with skip tokens.  The ARG ``resources`` call is
a query endpoint: it reads, it cannot mutate.

Offline path (default, and the one tests use): ``from_export(path)`` ingests
the JSON produced by ``az graph query -q "<ARG_QUERY>" --first 1000`` (an
object with ``data``/``skip_token``), a ``{"value": [...]}`` envelope, or a
bare list of records.

Either way: records -> redaction -> ``assert_clean`` -> facts
``azure.resource`` (subject = ARM id) -> Graphfy live nodes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from sparkforge_azure.collectors.base import (
    CollectorInputError,
    CollectorResult,
    read_export,
    run_pipeline,
)
from sparkforge_azure.findings.models import Fact
from sparkforge_azure.graph.arm import is_arm_id
from sparkforge_azure.graph.live import live_graph_from_facts
from sparkforge_azure.graph.model import Graph

SOURCE = "azure.resource_graph"
ARG_QUERY = (
    "Resources | project id, name, type, location, resourceGroup, subscriptionId, "
    "tenantId, properties"
)
MAX_PAGES = 1000

_FIELD_MAP = (
    ("name", "name"),
    ("type", "type"),
    ("location", "location"),
    ("resourceGroup", "resource_group"),
    ("subscriptionId", "subscription_id"),
    ("tenantId", "tenant_id"),
)


def records_to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
    facts: list[Fact] = []
    for rec in records:
        arm = rec.get("id")
        if not is_arm_id(arm):
            continue
        attrs: dict[str, Any] = {}
        for src, dst in _FIELD_MAP:
            value = rec.get(src)
            if isinstance(value, str):
                attrs[dst] = value.lower() if dst in ("type", "subscription_id",
                                                       "tenant_id") else value
        attrs["properties"] = rec.get("properties") if isinstance(
            rec.get("properties"), Mapping) else {}
        facts.append(
            Fact(
                kind="azure.resource",
                subject={"arm_id": str(arm).strip().rstrip("/").lower()},
                attrs=attrs,
                provenance=dict(provenance),
            )
        )
    return facts


def _records_from_payload(payload: Any) -> tuple[list[dict[str, Any]], str | None]:
    observed_at = None
    if isinstance(payload, Mapping):
        observed_at = payload.get("observed_at")
        rows = payload.get("data", payload.get("value"))
        if isinstance(rows, Mapping) and "rows" in rows:  # table result format
            cols = [c.get("name") for c in rows.get("columns", [])]
            rows = [dict(zip(cols, r, strict=False)) for r in rows.get("rows", [])]
    else:
        rows = payload
    if not isinstance(rows, list) or not all(isinstance(r, Mapping) for r in rows):
        raise CollectorInputError("ARG export must hold a list of resource objects")
    return [dict(r) for r in rows], observed_at if isinstance(observed_at, str) else None


def _with_invalid(records: list[dict[str, Any]], result: CollectorResult) -> CollectorResult:
    for i, rec in enumerate(records):
        if not is_arm_id(rec.get("id")):
            result.unresolved.append({"reason": "invalid_arm_id", "record": i})
    return result


def from_export(
    path: str | Path,
    *,
    hash_principals: bool = False,
    raw_dir: str | Path | None = None,
    observed_at: str | None = None,
) -> CollectorResult:
    records, exported_at = _records_from_payload(read_export(path))
    result = run_pipeline(
        records,
        source=SOURCE,
        mode="export",
        observed_at=observed_at or exported_at,
        to_facts=records_to_facts,
        hash_principals=hash_principals,
        raw_dir=raw_dir,
    )
    return _with_invalid(records, result)


def to_graph(result: CollectorResult) -> Graph:
    return live_graph_from_facts(result.facts, source=SOURCE)


def _default_request_builder(
    subscriptions: Sequence[str], query: str, skip_token: str | None, top: int
) -> Any:
    from sparkforge_azure.collectors.auth import require_module

    models = require_module("azure.mgmt.resourcegraph.models", "azure")
    options = models.QueryRequestOptions(
        skip_token=skip_token, top=top, result_format="objectArray"
    )
    return models.QueryRequest(subscriptions=list(subscriptions), query=query, options=options)


class ResourceGraphCollector:
    """Read-only ARG inventory.  Public surface: ``collect`` only."""

    def __init__(
        self,
        subscriptions: Iterable[str],
        *,
        credential: Any | None = None,
        client: Any | None = None,
        request_builder: Callable[[Sequence[str], str, str | None, int], Any] | None = None,
        page_size: int = 1000,
        query: str = ARG_QUERY,
        cache: Any | None = None,
        allow_stale: bool = False,
    ) -> None:
        self._subscriptions = tuple(sorted({s.lower() for s in subscriptions}))
        self._credential = credential
        self._client = client
        self._request_builder = request_builder or _default_request_builder
        self._page_size = page_size
        self._query = query
        self._cache = cache
        self._allow_stale = allow_stale

    def _resolve_client(self) -> Any:
        if self._client is not None:
            return self._client
        from sparkforge_azure.collectors.auth import get_credential, require_module

        mod = require_module("azure.mgmt.resourcegraph", "azure")
        credential = self._credential or get_credential("default")
        return mod.ResourceGraphClient(credential)

    def _pages(self) -> Iterable[list[dict[str, Any]]]:
        client = self._resolve_client()
        skip: str | None = None
        for _ in range(MAX_PAGES):
            request = self._request_builder(self._subscriptions, self._query, skip,
                                            self._page_size)
            response = client.resources(request)  # ARG query endpoint (read-only)
            data = getattr(response, "data", None)
            if data is None and isinstance(response, Mapping):
                data = response.get("data")
            yield [dict(r) for r in (data or [])]
            skip = getattr(response, "skip_token", None)
            if skip is None and isinstance(response, Mapping):
                skip = response.get("skip_token")
            if not skip:
                return
        raise CollectorInputError("ARG pagination exceeded MAX_PAGES")

    def collect(
        self,
        *,
        hash_principals: bool = False,
        raw_dir: str | Path | None = None,
        observed_at: str | None = None,
    ) -> CollectorResult:
        if not self._subscriptions:
            raise CollectorInputError("at least one subscription scope is required")
        origin = "live"
        cache_age: float | None = None
        if self._cache is not None:
            # key = (scope, query); freshness decides whether a hit counts
            scope = ",".join(self._subscriptions)

            def _fetch() -> list[dict[str, Any]]:
                return [r for page in self._pages() for r in page]

            records, origin = self._cache.get_or_call(
                scope, self._query, _fetch, allow_stale=self._allow_stale)
            if origin != "live":
                hit = self._cache.get(scope, self._query)
                cache_age = hit.age_seconds if hit else None
        else:
            records = [r for page in self._pages() for r in page]
        if observed_at is None:
            from datetime import datetime, timezone

            observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        result = run_pipeline(
            records,
            source=SOURCE,
            mode="live",
            observed_at=observed_at,
            to_facts=records_to_facts,
            hash_principals=hash_principals,
            raw_dir=raw_dir,
        )
        if origin == "stale":
            # Fallback visível: stale cache nunca passa por dado current.
            result.unresolved.append({
                "reason": "cache_stale",
                "detail": "cached records served past TTL; treat as degraded",
                "cache_age_seconds": cache_age,
            })
        return _with_invalid(records, result)


__all__ = ["ARG_QUERY", "SOURCE", "ResourceGraphCollector", "from_export", "records_to_facts",
           "to_graph"]
