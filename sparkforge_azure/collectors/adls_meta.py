"""ADLS Gen2 metadata collector (read-only): account posture + ACLs.

Offline ``from_export(path)`` ingests::

    {"account_id": "<ARM id>", "hns": true,
     "acl": {"/dir": {"owner": ..., "owning_group": ..., "entries": [...]}},
     "observed_at": "..."}

Live mode reads account properties via ``azure-mgmt-storage`` and ACLs via
``azure-storage-file-datalake`` (lazy imports).  Failures become unresolved
entries with a FailureClass -- never "resource absent".
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

SOURCE = "adls_meta"
LIVE_ARGS = ("account_url", "container", "paths")


def _to_facts(records: list[dict[str, Any]], provenance: dict[str, Any]) -> list[Fact]:
    facts: list[Fact] = []
    for rec in records:
        facts.extend(extract.extract_adls(rec["_payload"], provenance))
    return facts


def _records(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{"_payload": dict(payload)}]


def from_export(path: str | Path, *, raw_dir: str | Path | None = None) -> CollectorResult:
    payload = read_export(path)
    if not isinstance(payload, Mapping):
        raise CollectorInputError("adls export must be an object")
    if "acl" in payload and not isinstance(payload["acl"], Mapping):
        raise CollectorInputError("adls export: acl must be an object")
    observed = payload.get("observed_at")
    return run_pipeline(_records(payload), source=SOURCE, mode="export",
                        observed_at=observed if isinstance(observed, str) else None,
                        to_facts=_to_facts, raw_dir=raw_dir)


def collect_live(*, account_url: str, container: str, paths: list[str],
                 credential: Any | None = None,
                 raw_dir: str | Path | None = None,
                 observed_at: str | None = None) -> CollectorResult:
    """Read ACLs for ``paths`` in one filesystem via DataLakeServiceClient."""
    try:
        from sparkforge_azure.collectors.auth import (
            get_credential,
            require_module,
        )

        dl = require_module("azure.storage.filedatalake", "azure")
        cred = credential or get_credential("default")
        service = dl.DataLakeServiceClient(account_url=account_url, credential=cred)
        fs = service.get_file_system_client(container)
        acl: dict[str, Any] = {}
        for path in paths:
            try:
                dc = fs.get_directory_client(path) if path != "/" else fs
                props = dc.get_access_control()  # read-only
                acl[path] = _acl_payload(props)
            except Exception as exc:  # noqa: BLE001
                acl[path] = {"_error": failure.unresolved(path, exc, source=SOURCE)}
    except Exception as exc:  # noqa: BLE001 - classified, not raised
        result = CollectorResult(source=SOURCE, mode="live", observed_at=observed_at)
        result.unresolved.append(failure.unresolved("adls", exc, source=SOURCE))
        return result
    errors = [{"what": p, **v.pop("_error")} for p, v in acl.items() if "_error" in v]
    payload = {"acl": acl}
    result = run_pipeline(_records(payload), source=SOURCE, mode="live",
                          observed_at=observed_at, to_facts=_to_facts,
                          raw_dir=raw_dir)
    result.unresolved.extend(errors)
    return result


def _acl_payload(props: Mapping[str, Any]) -> dict[str, Any]:
    raw = props.get("acl", "") if isinstance(props, Mapping) else str(props)
    entries = []
    for part in str(raw).split(","):
        fields = part.split(":")
        if len(fields) < 4:
            continue
        entries.append({"type": fields[0], "id": fields[1] or None,
                        "perms": fields[2]})
    return {"entries": entries}


__all__ = ["SOURCE", "collect_live", "from_export"]
