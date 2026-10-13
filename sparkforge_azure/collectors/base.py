"""Shared collector pipeline (section 174).

    Azure API / offline export -> raw records (memory) -> redact -> assert_clean
    -> facts (+ Graphfy live nodes).  Rules/findings run elsewhere.

Raw records live in memory.  When a caller asks to keep them
(``raw_dir``), only the REDACTED and ``assert_clean``-ed copy is written,
under ``.sparkforge-azure/raw/`` with a local ``.gitignore`` of ``*`` so it can
never be committed.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sparkforge_azure.collectors.redact import RedactionReport, assert_clean, redact
from sparkforge_azure.findings.models import Fact, sort_facts

MAX_EXPORT_BYTES = 64 * 1024 * 1024
RAW_DIR = Path(".sparkforge-azure") / "raw"


class CollectorUnavailable(RuntimeError):
    """A live collector was requested but its optional SDK/auth is missing."""


class CollectorInputError(ValueError):
    """Offline export is unreadable or malformed."""


@dataclass
class CollectorResult:
    source: str
    mode: str  # "export" | "live"
    facts: list[Fact] = field(default_factory=list)
    records: int = 0
    redaction: RedactionReport = field(default_factory=RedactionReport)
    observed_at: str | None = None
    unresolved: list[dict[str, Any]] = field(default_factory=list)
    raw_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out = {
            "source": self.source,
            "mode": self.mode,
            "records": self.records,
            "observed_at": self.observed_at,
            "facts": [f.to_dict() for f in self.facts],
            "redaction": self.redaction.to_dict(),
            "unresolved": self.unresolved,
            "raw_path": self.raw_path,
        }
        assert_clean(out)
        return out


def read_export(path: str | Path) -> Any:
    p = Path(path)
    try:
        size = p.stat().st_size
    except OSError as exc:
        raise CollectorInputError(f"export unreadable: {p.name}") from exc
    if size > MAX_EXPORT_BYTES:
        raise CollectorInputError(f"export too large: {p.name} ({size} bytes)")
    text = p.read_text(encoding="utf-8-sig")
    if p.suffix.lower() == ".csv":
        return text
    try:
        return json.loads(text)
    except ValueError as exc:
        raise CollectorInputError(f"export is not valid JSON: {p.name}") from exc


def run_pipeline(
    records: Iterable[Mapping[str, Any]],
    *,
    source: str,
    mode: str,
    observed_at: str | None,
    to_facts: Callable[[list[dict[str, Any]], dict[str, Any]], list[Fact]],
    hash_principals: bool = False,
    raw_dir: str | Path | None = None,
) -> CollectorResult:
    raw = [dict(r) for r in records]  # raw artifact: memory only
    report = RedactionReport()
    clean = redact(raw, hash_principals=hash_principals, report=report)
    assert_clean(clean)
    provenance = {"source": source, "mode": mode, "observed_at": observed_at}
    facts = sort_facts(to_facts(clean, provenance))
    assert_clean([f.to_dict() for f in facts])
    result = CollectorResult(source, mode, facts, len(raw), report, observed_at)
    if raw_dir is not None:
        result.raw_path = persist_redacted_raw(clean, raw_dir, source)
    return result


def persist_redacted_raw(clean: Any, raw_dir: str | Path, source: str) -> str:
    assert_clean(clean)
    base = Path(raw_dir)
    base.mkdir(parents=True, exist_ok=True)
    ignore = base / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    name = "".join(c if c.isalnum() or c in "._-" else "_" for c in source) + ".json"
    target = base / name
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(clean, sort_keys=True, indent=1), encoding="utf-8")
    os.replace(tmp, target)
    return target.as_posix()


__all__ = [
    "MAX_EXPORT_BYTES",
    "RAW_DIR",
    "CollectorInputError",
    "CollectorResult",
    "CollectorUnavailable",
    "persist_redacted_raw",
    "read_export",
    "run_pipeline",
]
