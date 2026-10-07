"""Deterministic skill registry and selection (no model calls).

Selection scores each skill by how many of its ``trigger`` phrases and ``scope`` terms occur
in the task text (accent- and case-insensitive, word-boundary matching). Ties are broken by
the canonical catalogue order in :data:`SKILL_NAMES`, so the result is a pure function of the
inputs.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from sparkforge_azure.skills.model import (
    SKILL_NAMES,
    Skill,
    discover_skill_files,
    parse_skill,
)

TRIGGER_WEIGHT = 3
SCOPE_WEIGHT = 1


def normalize(text: str) -> str:
    """Lowercase, strip accents and collapse non-alphanumerics to single spaces."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip() + " "


def _contains(haystack: str, phrase: str) -> bool:
    needle = normalize(phrase)
    return needle.strip() != "" and needle in haystack


@dataclass(frozen=True)
class SkillMatch:
    name: str
    score: int
    matched: tuple[str, ...]


def load_skills(root: Path) -> list[Skill]:
    """Parse all skills under ``root/skills`` in canonical order (unknown names last)."""
    skills = [parse_skill(p) for p in discover_skill_files(root)]
    order = {n: i for i, n in enumerate(SKILL_NAMES)}
    return sorted(skills, key=lambda s: (order.get(s.name, len(order)), s.name))


def list_skills(root: Path) -> list[str]:
    return [s.name for s in load_skills(root)]


def score_skill(skill: Skill, task: str) -> SkillMatch:
    hay = normalize(task)
    matched: list[str] = []
    score = 0
    for phrase in skill.trigger:
        if _contains(hay, phrase):
            matched.append(phrase)
            score += TRIGGER_WEIGHT
    for term in skill.scope:
        if _contains(hay, term):
            matched.append(term)
            score += SCOPE_WEIGHT
    return SkillMatch(skill.name, score, tuple(matched))


def select_skills(
    task: str, skills: list[Skill], *, max_skills: int = 3, min_score: int = 1
) -> list[SkillMatch]:
    """Return the best ``max_skills`` matches with ``score >= min_score``; deterministic."""
    if max_skills < 1:
        raise ValueError("max_skills must be >= 1")
    order = {n: i for i, n in enumerate(SKILL_NAMES)}
    matches = [m for m in (score_skill(s, task) for s in skills) if m.score >= min_score]
    matches.sort(key=lambda m: (-m.score, order.get(m.name, len(order)), m.name))
    return matches[:max_skills]
