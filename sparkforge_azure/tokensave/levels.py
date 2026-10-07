"""Retrieval ladder (section 43) and economy profiles (sections 46-49)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Level(IntEnum):
    """Cheapest first. Retrieval stops at the first level that is sufficient."""

    L0_EXACT_REF = 0  # a path:line / node id named in the task itself
    L1_LITERAL = 1  # literal / FTS index lookup
    L2_SYMBOL = 2  # code-intelligence symbols and references
    L3_GRAPH = 3  # bounded graph expansion (callers/callees/impact)
    L4_SEMANTIC = 4  # semantic retrieval -- not available offline (no embeddings)
    L5_SLICE = 5  # bounded artifact slice (line window)
    L6_FULL = 6  # full artifact: FALLBACK ONLY (section 44)


@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    max_level: Level
    budget_bytes: int  # payload bytes, NOT tokens (section 78)
    slice_lines: int  # max lines per L5 slice
    max_slices: int
    max_expansion_depth: int
    max_hits: int
    allow_full_read: bool
    allow_review: bool
    allow_debate: bool
    model_tier: str


PROFILES: dict[str, Profile] = {
    # economy: deterministic tools, TokenSave, cache, compact context, cheap model, no debate
    "economy": Profile("economy", Level.L5_SLICE, 12_000, 40, 3, 1, 8, False, False, False,
                       "economy"),
    "balanced": Profile("balanced", Level.L5_SLICE, 32_000, 80, 6, 2, 16, False, True, False,
                        "balanced"),
    # deep: deeper retrieval, review, debate, powerful model -- still budgeted
    "deep": Profile("deep", Level.L6_FULL, 96_000, 200, 12, 3, 32, True, True, True, "deep"),
}


def profile(name: str) -> Profile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError(
            f"unknown economy profile {name!r}; use one of {sorted(PROFILES)}"
        ) from exc
