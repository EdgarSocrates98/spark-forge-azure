"""Cost Management collector -- read-only.

Offline ``from_export(path)`` accepts:

* the Cost Management *query* result JSON
  (``{"properties": {"columns": [{"name": ...}], "rows": [[...]]}}``);
* a cost export CSV (header row; ``ResourceId``/``CostInBillingCurrency`` or
  ``Cost``/``PreTaxCost``, optional ``Date``/``UsageDate`` and currency).

Facts ``azure.cost`` (subject = lowercased resource id + date).  A missing
cost is ``None`` -- Unknown is not Zero.  The live method runs the read-only
``query.usage`` endpoint via ``azure-mgmt-costmanagement`` (lazy import).
"""

from __future__ import annotations

import csv
import io
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

SOURCE = "azure.cost_management"
_RESOURCE_COLS = ("resourceid", "resource_id", "instanceid")
_COST_COLS = ("costinbillingcurrency", "cost", "pretaxcost", "costusd")
_DATE_COLS = ("date", "usagedate", "usage_date")
_CURRENCY_COLS = ("billingcurrency", "currency", "billingcurrencycode")


def _pick(row: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    lowered = {str(k).lower(): v for k, v in row.items()}
    for name in names:
        if name in lowered and lowered[name] not in (None, ""):
            return lowered[name]
    return None


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
    facts = []
    for rec in records:
        rid = _pick(rec, _RESOURCE_COLS)
        if not isinstance(rid, str) or not rid:
            continue
        date = _pick(rec, _DATE_COLS)
        facts.append(Fact(
            kind="azure.cost",
            subject={"resource_id": rid.strip().lower(),
                     "date": str(date) if date is not None else None},
            measures={"cost": _number(_pick(rec, _COST_COLS))},
            attrs={"currency": _pick(rec, _CURRENCY_COLS)},
            provenance=dict(provenance),
        ))
    return facts


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, str):
        return [dict(r) for r in csv.DictReader(io.StringIO(payload))]
    if isinstance(payload, Mapping):
        props = payload.get("properties", payload)
        cols = [c.get("name") for c in props.get("columns", []) if isinstance(c, Mapping)]
        rows = props.get("rows", [])
        if cols and isinstance(rows, list):
            return [dict(zip(cols, r, strict=False)) for r in rows if isinstance(r, list)]
    raise CollectorInputError("unsupported cost export shape")


def from_export(path: str | Path, *, raw_dir: str | Path | None = None,
                observed_at: str | None = None) -> CollectorResult:
    return run_pipeline(_records(read_export(path)), source=SOURCE, mode="export",
                        observed_at=observed_at, to_facts=_to_facts, raw_dir=raw_dir)


class CostCollector:
    """Read-only Cost Management query.  Public surface: ``collect`` only."""

    def __init__(self, scope: str, *, credential: Any | None = None,
                 client: Any | None = None) -> None:
        self._scope = scope
        self._credential = credential
        self._client = client

    def collect(self, *, timeframe: str = "MonthToDate",
                observed_at: str | None = None) -> CollectorResult:
        from sparkforge_azure.collectors.auth import get_credential, require_module

        client = self._client
        if client is None:
            mod = require_module("azure.mgmt.costmanagement", "azure")
            client = mod.CostManagementClient(self._credential or get_credential("default"))
        definition = {
            "type": "ActualCost",
            "timeframe": timeframe,
            "dataset": {
                "granularity": "Daily",
                "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": "ResourceId"}],
            },
        }
        response = client.query.usage(self._scope, definition)  # query endpoint, read-only
        as_dict = response.as_dict() if hasattr(response, "as_dict") else dict(response)
        return run_pipeline(_records(as_dict), source=SOURCE, mode="live",
                            observed_at=observed_at, to_facts=_to_facts)


__all__ = ["SOURCE", "CostCollector", "from_export"]
