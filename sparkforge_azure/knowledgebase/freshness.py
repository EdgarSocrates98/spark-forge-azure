"""Frescor por entrada de knowledge (secao 162). Deterministico: `today` e injetado.

Precedencia (a primeira que casa vence):

1. status declarado DEPRECATED / CONFLICTED / UNRESOLVED -> honrado como esta;
2. sem fontes                                               -> UNRESOLVED;
3. `verified_at` no futuro em relacao a `today`             -> CONFLICTED;
4. idade > `max_age_days`                                   -> STALE;
5. status declarado STALE                                   -> STALE;
6. caso contrario                                           -> VERIFIED.

O limiar (90 dias por padrao) e convencao do produto, nao fato de fonte; sai
junto do resultado para que quem le saiba que foi escolha.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from sparkforge_azure.knowledgebase.metadata import KnowledgeEntry

DEFAULT_MAX_AGE_DAYS = 90
MAX_AGE_BASIS = "convencao do produto: docs Azure mudam em ciclos mensais; 90 dias = 3 ciclos"

_HONORED = frozenset({"DEPRECATED", "CONFLICTED", "UNRESOLVED"})


@dataclass(frozen=True)
class Freshness:
    id: str
    declared: str
    state: str
    age_days: int
    max_age_days: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "declared": self.declared,
            "state": self.state,
            "age_days": self.age_days,
            "max_age_days": self.max_age_days,
            "reason": self.reason,
        }


def freshness(
    entry: KnowledgeEntry, today: date, max_age_days: int = DEFAULT_MAX_AGE_DAYS
) -> Freshness:
    if max_age_days < 0:
        raise ValueError("max_age_days precisa ser >= 0")
    age = (today - entry.verified_at).days

    def result(state: str, reason: str) -> Freshness:
        return Freshness(entry.id, entry.status, state, age, max_age_days, reason)

    if entry.status in _HONORED:
        return result(entry.status, f"status declarado {entry.status}")
    if not entry.sources:
        return result("UNRESOLVED", "nenhuma fonte citada")
    if age < 0:
        return result("CONFLICTED", "verified_at posterior a data de referencia")
    if age > max_age_days:
        return result("STALE", f"verificado ha {age} dias (> {max_age_days})")
    if entry.status == "STALE":
        return result("STALE", "status declarado STALE")
    return result("VERIFIED", f"verificado ha {age} dias (<= {max_age_days})")


def freshness_report(
    entries: Iterable[KnowledgeEntry],
    today: date,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> dict[str, Any]:
    items = sorted(
        (freshness(e, today, max_age_days) for e in entries), key=lambda f: f.id
    )
    counts: dict[str, int] = {}
    for item in items:
        counts[item.state] = counts.get(item.state, 0) + 1
    return {
        "today": today.isoformat(),
        "max_age_days": max_age_days,
        "max_age_basis": MAX_AGE_BASIS,
        "counts": dict(sorted(counts.items())),
        "entries": [i.to_dict() for i in items],
        "not_fresh": [i.id for i in items if i.state != "VERIFIED"],
    }
