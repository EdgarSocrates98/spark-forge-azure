"""Per-session retrieval ledger: what TokenSave put into context, at which level.

Separate from the Token Ledger (section 74): this records *payload bytes and
items* (context), never tokens.  Bytes are not tokens (section 78); an
``estimated_tokens`` figure is only emitted when explicitly requested and is
always labelled ``basis=estimated``.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from sparkforge_azure.tokensave.levels import Level


def payload_bytes(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


@dataclass(frozen=True, slots=True)
class RetrievalRecord:
    primitive: str
    level: int
    payload_bytes: int
    items: int
    cache_hit: bool
    reused: bool
    fallback: bool
    outcome: str  # ok | empty | refused | skipped
    reason: str = ""
    at: float = field(default_factory=time.time)


class RetrievalLedger:
    def __init__(self) -> None:
        self.records: list[RetrievalRecord] = []
        self._seen: set[str] = set()

    def seen(self, key: str) -> bool:
        return key in self._seen

    def mark(self, key: str) -> None:
        self._seen.add(key)

    def add(self, record: RetrievalRecord) -> None:
        self.records.append(record)

    @property
    def total_bytes(self) -> int:
        return sum(r.payload_bytes for r in self.records if not r.reused)

    def summary(self) -> dict[str, Any]:
        by_level: dict[str, int] = {}
        for r in self.records:
            by_level[f"L{r.level}"] = by_level.get(f"L{r.level}", 0) + r.payload_bytes
        calls = len(self.records)
        hits = sum(1 for r in self.records if r.cache_hit)
        return {
            "calls": calls,
            "payload_bytes": self.total_bytes,
            "payload_basis": "len(json.dumps(payload, ensure_ascii=False, sort_keys=True))",
            "bytes_by_level": dict(sorted(by_level.items())),
            "cache_hit_rate": (hits / calls) if calls else None,
            "reuse_count": sum(1 for r in self.records if r.reused),
            "expansion_count": sum(1 for r in self.records if r.level == Level.L3_GRAPH),
            "full_reads": sum(1 for r in self.records if r.level == Level.L6_FULL),
            "refused": sum(1 for r in self.records if r.outcome == "refused"),
            "tokens": None,  # unknown != zero (section 77): provider usage lives elsewhere
        }

    def to_list(self) -> list[dict[str, Any]]:
        return [asdict(r) for r in self.records]

    def mirror_to(self, context_ledger: Any, *, start_time: float | None = None) -> None:
        """Copy records into the ported ``observability.ContextLedger`` (spans)."""
        for r in self.records:
            context_ledger.record(
                name=f"tokensave.{r.primitive}",
                resultado={"items": r.items, "payload_bytes": r.payload_bytes},
                detail_level=f"L{r.level}",
                outcome="ok" if r.outcome in {"ok", "empty"} else r.outcome,
                start_time=start_time or r.at,
                channel="tokensave",
            )
