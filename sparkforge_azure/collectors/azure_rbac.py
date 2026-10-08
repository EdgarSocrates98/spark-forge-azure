"""Azure RBAC collector (read-only): role assignments relevant to storage.

Offline ``from_export(path)`` ingests::

    {"assignments": [{principal, role, scope, condition?, condition_result?}],
     "observed_at": "..."}

Live mode uses ``azure-mgmt-authorization`` (lazy import) listing assignments at
a scope.  Failures become unresolved entries with a FailureClass.
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

SOURCE = "azure_rbac"
LIVE_ARGS = ("scope", "subscription_id")


def _to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
    facts: list[Fact] = []
    for rec in records:
        facts.extend(extract.extract_rbac(rec["_payload"], provenance))
    return facts


def _records(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{"_payload": dict(payload)}]


def from_export(path: str | Path, *, raw_dir: str | Path | None = None) -> CollectorResult:
    payload = read_export(path)
    if not isinstance(payload, Mapping) or not isinstance(
            payload.get("assignments"), list):
        raise CollectorInputError("rbac export must be an object with assignments[]")
    observed = payload.get("observed_at")
    return run_pipeline(_records(payload), source=SOURCE, mode="export",
                        observed_at=observed if isinstance(observed, str) else None,
                        to_facts=_to_facts, raw_dir=raw_dir)


def collect_live(*, scope: str, credential: Any | None = None,
                 subscription_id: str = "",
                 raw_dir: str | Path | None = None,
                 observed_at: str | None = None) -> CollectorResult:
    """List role assignments at ``scope`` via azure-mgmt-authorization."""
    try:
        from sparkforge_azure.collectors.auth import (
            get_credential,
            require_module,
        )

        mgmt = require_module("azure.mgmt.authorization", "azure")
        cred = credential or get_credential("default")
        sub = subscription_id or scope.split("/")[2]
        client = mgmt.AuthorizationManagementClient(cred, sub)
        items = client.role_assignments.list_for_scope(scope)
        payload = {"assignments": [
            {"principal": str(getattr(a, "principal_id", "") or ""),
             "role": str(getattr(a, "role_definition_id", "") or "").rsplit("/", 1)[-1],
             "scope": str(getattr(a, "scope", "") or "")}
            for a in items
        ]}
    except Exception as exc:  # noqa: BLE001 - classified, not raised
        result = CollectorResult(source=SOURCE, mode="live", observed_at=observed_at)
        result.unresolved.append(failure.unresolved("rbac", exc, source=SOURCE))
        return result
    return run_pipeline(_records(payload), source=SOURCE, mode="live",
                        observed_at=observed_at, to_facts=_to_facts,
                        raw_dir=raw_dir)


__all__ = ["SOURCE", "collect_live", "from_export"]
