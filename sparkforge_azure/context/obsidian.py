"""Read-only Azure diagnostic projection for the federated Obsidian contract."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

import yaml

_SENSITIVE = ("secret", "token", "password", "credential", "access_key", "session_key")
_SENSITIVE_TEXT = re.compile(
    r"(?i)(\b(?:secret|token|password|credential|access[_-]?key|session[_-]?key)\s*[:=]\s*)([^\s,;]+)"
)


def _safe(value: Any, key: str = "") -> Any:
    if any(marker in key.lower() for marker in _SENSITIVE):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _safe(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe(item, key) for item in value]
    if isinstance(value, str):
        return _SENSITIVE_TEXT.sub(r"\1[REDACTED]", value)
    return value


def _section(title: str, values: Any) -> list[str]:
    safe = _safe(values)
    if safe in (None, "", [], {}):
        return [f"## {title}", "- None reported", ""]
    rendered = yaml.safe_dump(safe, sort_keys=True, allow_unicode=True).rstrip()
    return [f"## {title}", "```yaml", rendered, "```", ""]


def build_obsidian_diagnostic(
    *,
    title: str,
    summary: str,
    workspace: str,
    vault_id: str,
    versions: dict[str, str] | None = None,
    resources: list[Any] | None = None,
    identity: dict[str, Any] | None = None,
    permissions: list[Any] | None = None,
    freshness: str = "unknown",
    source_refs: list[str] | None = None,
    templates: list[str] | None = None,
    note_path: str = "azure-diagnostics/diagnostic.md",
    confidence: str = "unknown",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = _safe({
        "type": "azure-diagnostic",
        "source": "spark-forge-azure",
        "classification": "internal",
        "confidence": confidence,
        "freshness": freshness,
        "provenance": provenance or {},
    })
    lines = ["---", yaml.safe_dump(metadata, sort_keys=True, allow_unicode=True).rstrip(), "---",
             f"# {title.strip() or 'Azure diagnostic'}", "", summary.strip(), ""]
    lines += _section("Versions", versions)
    lines += _section("Resources", resources)
    lines += _section(
        "Identity and permissions",
        {"identity": identity or {}, "permissions": permissions or []},
    )
    lines += _section("Freshness", {"state": freshness, "source_refs": source_refs or []})
    lines += _section("Templates", templates)
    content = "\n".join(lines).rstrip() + "\n"
    return {
        "schema": "theforge/ObsidianNoteRef/v1",
        "version": "v1",
        "workspace": workspace,
        "vault_id": vault_id,
        "path": note_path,
        "source": "spark-forge-azure",
        "classification": "internal",
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "outcome": "projected",
        "provenance": {"adapter": "spark-forge-azure", **_safe(provenance or {})},
        "content": content,
        "warnings": [],
        "unresolved": [],
    }


__all__ = ["build_obsidian_diagnostic"]
