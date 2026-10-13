"""Executable per-agent eval cases (SDD AGENT_EVAL_SUITE).

``evals/agents/<id>.yaml`` declares route cases per specialist; this harness
runs them against the real router. ``route_positive`` requires decision
``selected``; ``route_negative`` requires ``no_match`` — ``below_cap`` never
counts as a pass, so an over-matching term cannot hide behind the cap.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from sparkforge_azure.agentmanifest.model import SPECIALIST_IDS
from sparkforge_azure.agentmanifest.routing import explain_route

REPO = Path(__file__).resolve().parents[1]
EVALS_DIR = REPO / "evals" / "agents"


def _suites() -> list[tuple[str, dict]]:
    return [
        (path.name, yaml.safe_load(path.read_text(encoding="utf-8")))
        for path in sorted(EVALS_DIR.glob("*.yaml"))
    ]


def test_agent_eval_cases_execute() -> None:
    suites = _suites()
    assert {s["agent"] for _, s in suites} == set(SPECIALIST_IDS)
    for name, suite in suites:
        agent = suite["agent"]
        kinds = {c["kind"] for c in suite["cases"]}
        assert "route_positive" in kinds, f"{name}: missing route_positive"
        assert "route_negative" in kinds, f"{name}: missing route_negative"
        for case in suite["cases"]:
            decisions = {
                r["specialist"]: r["decision"]
                for r in explain_route(case["prompt"])
            }
            got = decisions[agent]
            expected = (
                "selected" if case["kind"] == "route_positive" else "no_match"
            )
            assert got == expected, (
                f"{name}:{case['id']} expected {expected}, got {got} "
                f"for prompt {case['prompt']!r}"
            )


def test_agent_eval_case_vocabularies() -> None:
    for name, suite in _suites():
        assert suite["agent"] in SPECIALIST_IDS, name
        assert suite["kind"] == "route", name
        for case in suite["cases"]:
            assert case["kind"] in {"route_positive", "route_negative"}, name
            assert case["id"] and case["prompt"], name
