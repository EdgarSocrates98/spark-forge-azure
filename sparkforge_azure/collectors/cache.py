"""Live-collector cache with explicit freshness (prompts 168-169).

Keyed by ``(resource_id, query)`` — a cached value is only ever returned
with its freshness state: ``fresh`` inside the TTL, ``stale`` past it.
Stale entries are *marked*, never silently served as current; callers
decide whether a stale result may stand in for a live call and any such
use is visible in the collector's ``unresolved``/receipt path.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CacheHit:
    value: Any
    freshness: str  # "fresh" | "stale"
    age_seconds: float
    observed_at: float


@dataclass(slots=True)
class _Entry:
    value: Any
    observed_at: float


class LiveCache:
    """In-memory cache for live collector reads.  Not shared across runs —
    persistence of cloud data is out of scope (raw exports already have
    their own redacted store).
    """

    def __init__(self, ttl_seconds: float = 300.0, clock: Callable[[], float] = time.time):
        self.ttl = max(0.0, ttl_seconds)
        self._clock = clock
        self._entries: dict[tuple[str, str], _Entry] = {}

    @staticmethod
    def key(resource_id: str, query: str) -> tuple[str, str]:
        return (resource_id, query)

    def get(self, resource_id: str, query: str) -> CacheHit | None:
        entry = self._entries.get(self.key(resource_id, query))
        if entry is None:
            return None
        age = self._clock() - entry.observed_at
        return CacheHit(
            entry.value,
            "fresh" if age <= self.ttl else "stale",
            age,
            entry.observed_at,
        )

    def put(self, resource_id: str, query: str, value: Any) -> None:
        self._entries[self.key(resource_id, query)] = _Entry(value, self._clock())

    def get_or_call(
        self,
        resource_id: str,
        query: str,
        fetch: Callable[[], Any],
        *,
        allow_stale: bool = False,
    ) -> tuple[Any, str]:
        """Return ``(value, origin)`` where origin is ``live|fresh|stale``.

        ``stale`` is only returned when ``allow_stale`` — the caller must
        surface it (e.g. ``cache_freshness: stale`` in the result), never
        silently upgrade it to current data.
        """
        hit = self.get(resource_id, query)
        if hit is not None:
            if hit.freshness == "fresh":
                return hit.value, "fresh"
            if allow_stale:
                return hit.value, "stale"
        value = fetch()
        self.put(resource_id, query, value)
        return value, "live"

    def stats(self) -> dict[str, int]:
        now = self._clock()
        fresh = sum(1 for e in self._entries.values() if now - e.observed_at <= self.ttl)
        return {"entries": len(self._entries), "fresh": fresh,
                "stale": len(self._entries) - fresh}


__all__ = ["CacheHit", "LiveCache"]
