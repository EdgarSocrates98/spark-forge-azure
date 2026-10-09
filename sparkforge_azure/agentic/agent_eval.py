"""Empirical agent value — harness A/B (§50-75, §155-172).

Cada case roda as configs §51 sobre o MESMO input (§52):

    A deterministic core only | B + specialist | C + verifier | D full team

Sem host, os custos sao ``unresolved`` (§55) — o que se mede de verdade
aqui e qualidade evidencial por config: findings exigidos cobertos,
proibidos ausentes, evidencia requerida citada, unresolved preservados.
Necessity §59 sai do vetor §57, nunca de um escalar unico.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.agentic.execution import run_case
from sparkforge_azure.agentic.runtime import RuntimeName
from sparkforge_azure.agentmanifest.routing import route

EVAL_DIR = Path("evals/agent_runtime")

NECESSITY = {"ESSENTIAL", "USEFUL", "NEUTRAL", "HARMFUL", "UNRESOLVED"}

#: §51/§156-159 — conjuntos de estagios habilitados por config.
_DETERMINISTIC_SPINE = {
    "coordinator", "inventory", "extractor", "analyzer", "judge",
    "verifier", "synthesizer",
}
CONFIGS: dict[str, dict[str, Any]] = {
    "A": {"allowed_extra": set(), "verifier": False, "team": False},
    "B": {"allowed_extra": {"specialist"}, "verifier": False, "team": False},
    "C": {"allowed_extra": {"specialist"}, "verifier": True, "team": False},
    "D": {"allowed_extra": {"specialist", "reviewer", "critic", "referee"},
          "verifier": True, "team": True},
}


def _allowed_for(config: str, routed: list[str]) -> set[str]:
    allowed = set(_DETERMINISTIC_SPINE)
    cfg = CONFIGS[config]
    if "specialist" in cfg["allowed_extra"]:
        allowed.update(routed)
    if cfg["team"]:
        allowed.update({"reviewer", "critic", "referee"})
    if not cfg["verifier"]:
        allowed.discard("verifier")
    return allowed


@dataclass
class EvalResult:
    """§75 — formato canonico do resultado de uma config."""

    case_id: str
    configuration: str
    runtime: str
    agents: list[str]
    quality: dict[str, Any]
    evidence: list[str]
    unresolved: list[str]
    tokens: dict[str, Any] = field(
        default_factory=lambda: {"status": "unresolved"})
    cost: dict[str, Any] = field(
        default_factory=lambda: {"status": "unresolved"})
    latency_s: float = 0.0
    tool_calls: int = 0
    context_bytes: int = 0
    degraded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "configuration": self.configuration,
            "runtime": self.runtime,
            "agents": self.agents,
            "quality": self.quality,
            "evidence": self.evidence,
            "unresolved": self.unresolved,
            "tokens": self.tokens,
            "cost": self.cost,
            "latency_s": self.latency_s,
            "tool_calls": self.tool_calls,
            "context_bytes": self.context_bytes,
            "degraded": self.degraded,
        }


def _measure_quality(
    receipt, expected: dict[str, Any]
) -> dict[str, Any]:
    produced = set(receipt.state.provisional_findings) | set(
        receipt.state.verified_findings)
    required = {str(r) for r in expected.get("required_findings") or ()}
    forbidden = {str(f) for f in expected.get("forbidden_findings") or ()}
    produced_str = " ".join(sorted(produced))
    req_hit = sorted(r for r in required if any(r in p for p in produced))
    forb_hit = sorted(f for f in forbidden if f in produced_str)
    known_unresolved = [str(u) for u in expected.get("known_unresolved") or ()]
    preserved = [
        u for u in known_unresolved
        if any(u in x for x in receipt.state.unresolved)
    ]
    return {
        "required_findings_hit": len(req_hit),
        "required_findings_total": len(required),
        "forbidden_findings_hit": len(forb_hit),  # deve ser 0
        "forbidden_findings": forb_hit,
        "known_unresolved_preserved": len(preserved),
        "known_unresolved_total": len(known_unresolved),
        "provisional_findings": len(receipt.state.provisional_findings),
    }


def run_eval(
    case: dict[str, Any], expected: dict[str, Any], config: str,
    *, runtime: RuntimeName = RuntimeName.GENERIC,
    root: Path | str = ".",
) -> EvalResult:
    routed = route(str(case.get("task") or ""), max_agents=2)
    t0 = time.time()
    receipt = run_case(
        case, runtime=runtime, root=root,
        allowed=_allowed_for(config, routed),
    )
    latency = time.time() - t0
    return EvalResult(
        case_id=str(case.get("id") or "case"),
        configuration=config,
        runtime=runtime.value,
        agents=[s.agent_id for s in receipt.stages if s.spawn_result],
        quality=_measure_quality(receipt, expected),
        evidence=list(receipt.state.provisional_findings),
        unresolved=list(receipt.state.unresolved),
        latency_s=round(latency, 4),
        context_bytes=len(str(case.get("context") or {}).encode()),
        degraded=receipt.degraded,
    )


def value_vector(
    result: EvalResult, baseline: EvalResult
) -> dict[str, Any]:
    """§57 — vetor canonico; nunca escalar unico."""
    gain = (
        result.quality["required_findings_hit"]
        - baseline.quality["required_findings_hit"]
    )
    evidence_gain = len(result.evidence) - len(baseline.evidence)
    unc_red = (
        len(baseline.unresolved) - len(result.unresolved)
    )
    return {
        "information_gain": max(0, gain),
        "evidence_gain": evidence_gain,
        "uncertainty_reduction": unc_red,
        "decision_impact": "unresolved",
        "quality_delta": gain - result.quality["forbidden_findings_hit"],
        "cost": {"status": "unresolved"},
        "latency_delta_s": round(result.latency_s - baseline.latency_s, 4),
    }


def classify_necessity(vector: dict[str, Any], result: EvalResult) -> str:
    """§59-60 — classificacao honesta do valor do agente."""
    if result.quality["forbidden_findings_hit"] > 0:
        return "HARMFUL"
    if vector["information_gain"] > 0 or vector["evidence_gain"] > 0:
        return "ESSENTIAL" if vector["information_gain"] > 0 else "USEFUL"
    if vector["uncertainty_reduction"] > 0:
        return "USEFUL"
    if result.degraded and vector["latency_delta_s"] > 0:
        return "UNRESOLVED"
    return "NEUTRAL"


def evaluate_case(
    case_path: Path | str, *, root: Path | str = ".",
    runtime: RuntimeName = RuntimeName.GENERIC,
) -> dict[str, Any]:
    """Roda A-D sobre um case e devolve comparacao + baseline A."""
    case_path = Path(case_path)
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    expected_path = (
        Path(root) / EVAL_DIR / "expected" / f"{case['id']}.yaml")
    expected = (
        yaml.safe_load(expected_path.read_text(encoding="utf-8"))
        if expected_path.is_file() else {}
    )
    results = {
        cfg: run_eval(case, expected, cfg, runtime=runtime, root=root)
        for cfg in CONFIGS
    }
    baseline = results["A"]
    vectors = {
        cfg: value_vector(res, baseline) for cfg, res in results.items()
    }
    necessity = {
        cfg: classify_necessity(v, results[cfg])
        for cfg, v in vectors.items()
    }
    return {
        "case_id": case["id"],
        "runtime": runtime.value,
        "results": {c: r.to_dict() for c, r in results.items()},
        "value_vectors": vectors,
        "necessity": necessity,
        "quality_frontier": [
            {"config": c, "quality": r.quality["required_findings_hit"],
             "latency_s": r.latency_s}
            for c, r in results.items()
        ],
    }


# ---------------------------------------------------------------- host eval

_SPECIALIST_SCHEMA_HINT = {
    "kind": "specialist_result",
    "hypotheses": ["<hypothesis about the root cause>"],
    "evidence_refs": ["<evidence reference supporting each hypothesis>"],
    "proposed_findings": ["<concrete finding id or statement>"],
    "unresolved": ["<what could not be determined>"],
    "recommendations": ["<actionable next step>"],
}


def _host_prompt(agent_id: str, case: dict[str, Any]) -> str:
    """Contexto minimo §28: task + unresolved + schema — nunca o transcript."""
    unresolved = "\n".join(
        f"- {u}" for u in case.get("unresolved") or [])
    return (
        "You are the bounded specialist "
        f"`{agent_id}` in a deterministic Azure diagnosis pipeline.\n"
        f"Task: {case.get('task')}\n"
        f"Known unresolved items:\n{unresolved or '- none'}\n"
        "Reply with ONLY a JSON object matching this schema exactly "
        "(no prose, no markdown fence):\n"
        f"{json.dumps(_SPECIALIST_SCHEMA_HINT, indent=0)}"
    )


def _parse_host_structured(agent_id: str, output: str) -> dict[str, Any]:
    """Tenta JSON do modelo; fallback -> parse_freeform (§31, DATA_ONLY)."""
    from sparkforge_azure.agentic.schemas import parse_freeform

    text = (output or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return parse_freeform(agent_id, output)
    if isinstance(parsed, dict):
        return parsed
    return parse_freeform(agent_id, output)


def evaluate_case_host(
    case_path: Path | str, *, root: Path | str = ".",
    runtime: RuntimeName = RuntimeName.CLAUDE_CODE,
) -> dict[str, Any]:
    """§50-75 em host real: config B — core deterministico + 1 specialist.

    O specialist roteado executa de verdade via adapter host; o output e
    DATA_ONLY parseado para o schema, validado, e comparado ao expected.
    Custo/tokens sao medidos do envelope do host — nunca estimados.
    """
    from sparkforge_azure.agentic.runtimes import get_adapter
    from sparkforge_azure.agentic.runtimes.base import AgentSpawnRequestV2
    from sparkforge_azure.agentic.schemas import validate_output

    case_path = Path(case_path)
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    expected_path = (
        Path(root) / EVAL_DIR / "expected" / f"{case['id']}.yaml")
    expected = (
        yaml.safe_load(expected_path.read_text(encoding="utf-8"))
        if expected_path.is_file() else {}
    )
    baseline = run_eval(case, expected, "A", root=root)

    routed = route(str(case.get("task") or ""), max_agents=1)
    specialist = routed[0] if routed else "coordinator"
    adapter = get_adapter(runtime)
    t0 = time.time()
    spawn = adapter.spawn_agent(AgentSpawnRequestV2(
        agent_id=specialist,
        task=_host_prompt(specialist, case),
        timeout_seconds=180,
    ))
    latency = round(time.time() - t0, 3)
    structured = (
        _parse_host_structured(specialist, spawn.output)
        if spawn.status == "completed" else None
    )
    violations = (
        validate_output(specialist, structured)
        if structured is not None
        else ["contract_violation:missing_structured_output"]
    )
    findings = [
        str(f) for f in (structured or {}).get("proposed_findings") or []
    ]

    class _Receipt:  # mede com o mesmo _measure_quality
        class state:  # noqa: D106
            provisional_findings = findings
            verified_findings: list = []
            unresolved = list(
                (structured or {}).get("unresolved") or [])
            handoffs: list = []

    usage = dict(spawn.usage)
    measured = usage.get("status") == "measured"
    result = EvalResult(
        case_id=str(case.get("id") or "case"),
        configuration="B",
        runtime=runtime.value,
        agents=[specialist],
        quality=_measure_quality(_Receipt(), expected),
        evidence=[str(e) for e in
                  (structured or {}).get("evidence_refs") or []],
        unresolved=list((structured or {}).get("unresolved") or []),
        tokens={
            "status": usage.get("status", "unresolved"),
            "input": usage.get("input_tokens"),
            "output": usage.get("output_tokens"),
            "cache_creation_input": usage.get(
                "cache_creation_input_tokens"),
        },
        cost={
            "status": "measured" if usage.get("cost_usd") is not None
            else usage.get("status", "unresolved"),
            "usd": usage.get("cost_usd"),
        },
        latency_s=latency,
        degraded=spawn.status != "completed",
    )
    vector = value_vector(result, baseline)
    return {
        "case_id": case["id"],
        "runtime": runtime.value,
        "specialist": specialist,
        "spawn": spawn.to_dict(),
        "host_usage_measured": measured,
        "schema_violations": violations,
        "result": result.to_dict(),
        "value_vector_vs_A": vector,
        "necessity": classify_necessity(vector, result),
        "baseline_A": baseline.to_dict(),
    }
