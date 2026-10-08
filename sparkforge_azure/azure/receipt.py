"""Execution receipt for an access diagnosis run.

Required fields per the Cycle 2 spec: case, profile, tools, sources, facts,
rules, findings, agents, budget, unresolved.  The receipt is honest about cost:
offline runs report zero cloud calls and ``cloud_access: false``.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1


@dataclass
class ExecutionReceipt:
    case: str
    profile: str = "balanced"
    tools: list[str] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)
    facts: int = 0
    rules: int = 0
    findings: int = 0
    agents: list[str] = field(default_factory=list)
    budget: dict[str, Any] = field(default_factory=dict)
    unresolved: list[dict[str, Any]] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case": self.case,
            "profile": self.profile,
            "tools": list(self.tools),
            "sources": dict(self.sources),
            "facts": self.facts,
            "rules": self.rules,
            "findings": self.findings,
            "agents": list(self.agents),
            "budget": dict(self.budget),
            "unresolved": list(self.unresolved),
        }


def build(*, case: str, profile: str, tools: Sequence[str],
          sources: Mapping[str, str], facts: int, rules: int,
          findings: int, unresolved: Sequence[Mapping[str, Any]],
          cloud_calls: int = 0) -> ExecutionReceipt:
    return ExecutionReceipt(
        case=case,
        profile=profile,
        tools=sorted(tools),
        sources=dict(sources),
        facts=facts,
        rules=rules,
        findings=findings,
        agents=["extractors", "governance.diagnose", "failure_layer_classifier"],
        budget={"cloud_access": False, "cloud_calls": cloud_calls,
                "profile": profile},
        unresolved=[dict(u) for u in unresolved],
    )


__all__ = ["ExecutionReceipt", "build"]
