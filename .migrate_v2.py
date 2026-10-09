"""Migrate agents/*.md frontmatter v1 -> v2 (Cycle 6, AGENT_CONTRACT_V2).

v1 keys                 v2 keys
id                      id
kind                    kind
role                    mission   (v1 'role' text IS the mission)
does                    does
does_not                does_not
required_context        required_context_kinds
allowed_context         allowed_context_kinds
tools                   allowed_tools
skills                  skills
knowledge_refs          knowledge_packs
budget{...}             budget{context,tools,model_calls,model_tier,time,handoffs}
handoff_targets         handoffs.allowed_targets
handoff_mode            handoffs.mode
risk                    risk
trust_floor             trust_floor
parent                  parent
rule_areas              rule_areas (optional)
                        + schema_version: 2, family, domain, role, inputs,
                          outputs, denied_tools, spawn, stop, review_policy,
                          evals, agentops_emit_span

Also writes agents/test-engineer.md and agents/evaluation-specialist.md
(AC6 — they must exist in the taxonomy for v2 validation).
"""
from __future__ import annotations

import io
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
AGENTS = ROOT / "agents"

FAMILY = {
    "coordinator": "control",
    "inventory": "evidence", "extractor": "evidence", "analyzer": "evidence",
    "judge": "evidence", "verifier": "evidence", "synthesizer": "evidence",
    "reviewer": "review", "security-reviewer": "review", "cost-reviewer": "review",
    "performance-reviewer": "review", "migration-reviewer": "review",
    "critic": "adversarial", "referee": "adversarial",
    "test-engineer": "test_eval", "evaluation-specialist": "test_eval",
}
SPAWN = {
    "coordinator": ["always"],
    "inventory": ["always"], "extractor": ["always"], "analyzer": ["always"],
    "judge": ["always"], "verifier": ["always"], "synthesizer": ["always"],
    "reviewer": ["on_finding_review"], "security-reviewer": ["on_finding_review"],
    "cost-reviewer": ["on_finding_review"], "performance-reviewer": ["on_finding_review"],
    "migration-reviewer": ["on_finding_review"],
    "critic": ["on_disagreement"], "referee": ["on_conflict"],
    "test-engineer": ["on_gate"], "evaluation-specialist": ["on_gate"],
}
STOP = {
    "coordinator": ["on_budget_exhausted"],
    "inventory": ["on_artifacts_exhausted", "on_budget_exhausted"],
    "extractor": ["on_artifacts_exhausted", "on_budget_exhausted"],
    "analyzer": ["on_unknowns_resolved", "on_budget_exhausted"],
    "judge": ["on_verdict", "on_budget_exhausted"],
    "verifier": ["on_verdict", "on_budget_exhausted"],
    "synthesizer": ["on_synthesis_emitted"],
    "reviewer": ["on_findings_reviewed", "on_no_disagreement"],
    "security-reviewer": ["on_findings_reviewed", "on_no_disagreement"],
    "cost-reviewer": ["on_findings_reviewed", "on_no_disagreement"],
    "performance-reviewer": ["on_findings_reviewed", "on_no_disagreement"],
    "migration-reviewer": ["on_findings_reviewed", "on_no_disagreement"],
    "critic": ["on_no_disagreement"], "referee": ["on_verdict"],
    "test-engineer": ["on_eval_complete"], "evaluation-specialist": ["on_eval_complete"],
}
INPUTS = {
    "coordinator": ["task", "finding", "evidence", "unresolved", "handoff"],
    "inventory": ["artifact", "code", "knowledge"],
    "extractor": ["artifact", "tool_output"],
    "analyzer": ["fact", "evidence", "knowledge"],
    "judge": ["fact", "rule"],
    "verifier": ["fact", "evidence", "tool_output"],
    "synthesizer": ["finding", "evidence", "unresolved"],
    "reviewer": ["finding", "evidence"],
    "security-reviewer": ["finding", "evidence"],
    "cost-reviewer": ["finding", "evidence"],
    "performance-reviewer": ["finding", "evidence"],
    "migration-reviewer": ["finding", "evidence"],
    "critic": ["finding", "evidence"], "referee": ["finding", "evidence"],
    "test-engineer": ["code", "artifact", "finding"],
    "evaluation-specialist": ["fact", "evidence", "memory"],
}
OUTPUTS = {
    "coordinator": ["route", "handoff"],
    "inventory": ["fact"], "extractor": ["fact"],
    "analyzer": ["evidence", "hypothesis"],
    "judge": ["verdict"], "verifier": ["evidence", "verdict"],
    "synthesizer": ["report", "unresolved"],
    "reviewer": ["review", "recommendations"],
    "security-reviewer": ["review", "recommendations"],
    "cost-reviewer": ["review", "recommendations"],
    "performance-reviewer": ["review", "recommendations"],
    "migration-reviewer": ["review", "recommendations"],
    "critic": ["objections"], "referee": ["decision"],
    "test-engineer": ["review", "recommendations"],
    "evaluation-specialist": ["report", "recommendations"],
}
GAIN = {  # information_gain_threshold
    "coordinator": 0.0,
    "inventory": 0.0, "extractor": 0.0, "analyzer": 0.0,
    "judge": 0.0, "verifier": 0.0, "synthesizer": 0.0,
    "reviewer": 0.1, "security-reviewer": 0.1, "cost-reviewer": 0.1,
    "performance-reviewer": 0.1, "migration-reviewer": 0.1,
    "critic": 0.2, "referee": 0.2,
    "test-engineer": 0.1, "evaluation-specialist": 0.1,
}
TIME = {
    "coordinator": 60, "inventory": 120, "extractor": 120, "analyzer": 120,
    "judge": 120, "verifier": 120, "synthesizer": 120,
    "reviewer": 90, "security-reviewer": 90, "cost-reviewer": 90,
    "performance-reviewer": 90, "migration-reviewer": 90,
    "critic": 90, "referee": 90,
    "test-engineer": 180, "evaluation-specialist": 180,
}
NEEDS_VERIFIER = {"extractor", "analyzer", "judge"}


def dump(data: dict) -> str:
    buf = io.StringIO()
    yaml.safe_dump(data, buf, sort_keys=False, allow_unicode=True, width=100)
    return buf.getvalue()


def split(text: str) -> tuple[dict, str]:
    assert text.startswith("---\n"), "no frontmatter"
    end = text.index("\n---\n", 3)
    return yaml.safe_load(text[4:end]), text[end + 5:]


def migrate(path: Path) -> None:
    old, body = split(path.read_text(encoding="utf-8"))
    aid = old["id"]
    kind = old["kind"]
    family = FAMILY.get(aid)
    if family is None:
        if kind == "specialist":
            family = "domain"
        elif kind == "subagent":
            family = "review"
        else:
            raise SystemExit(f"no family for {aid}")
    if kind == "specialist":
        domain = aid[: -len("-specialist")]
        spawn = ["on_domain_match"]
        stop = ["on_unknowns_resolved", "on_budget_exhausted"]
        inputs = ["handoff", "fact", "evidence", "knowledge", "unresolved"]
        outputs = ["finding", "recommendations", "unresolved"]
        gain, time, needs_verifier = 0.2, 180, True
    elif kind == "subagent":
        domain = "databricks"
        spawn = ["on_parent_spawn"]
        stop = ["on_findings_reviewed"]
        inputs = ["handoff", "finding"]
        outputs = ["review", "recommendations"]
        gain, time, needs_verifier = 0.3, 90, False
    else:
        domain = family
        spawn, stop = SPAWN[aid], STOP[aid]
        inputs, outputs = INPUTS[aid], OUTPUTS[aid]
        gain, time = GAIN[aid], TIME[aid]
        needs_verifier = aid in NEEDS_VERIFIER

    budget_old = old["budget"]
    targets = old["handoff_targets"]
    new = {
        "schema_version": 2,
        "id": aid,
        "kind": kind,
        "family": family,
        "domain": domain,
        "role": aid,
        "mission": old["role"],
        "does": old["does"],
        "does_not": old["does_not"],
        "inputs": inputs,
        "outputs": outputs,
        "allowed_tools": old["tools"],
        "denied_tools": [],
        "required_context_kinds": old["required_context"],
        "allowed_context_kinds": old["allowed_context"],
        "knowledge_packs": old["knowledge_refs"],
        "skills": old["skills"],
        "trust_floor": old["trust_floor"],
        "budget": {
            "context": budget_old["max_context_tokens"],
            "tools": budget_old["max_tool_calls"],
            "model_calls": budget_old["max_model_calls"],
            "model_tier": budget_old["model_tier"],
            "time": time,
            "handoffs": min(len(targets), 8) if kind != "subagent" else 1,
        },
        "spawn": {
            "conditions": spawn,
            "information_gain_threshold": gain,
        },
        "stop": {"conditions": stop},
        "handoffs": {"allowed_targets": targets, "mode": old["handoff_mode"]},
        "review_policy": {
            "requires_verifier": needs_verifier,
            "adversarial_check": "on_conflict" if needs_verifier else "never",
        },
        "evals": [],
        "agentops_emit_span": True,
        "risk": old["risk"],
        "parent": old["parent"],
    }
    if "rule_areas" in old:
        new["rule_areas"] = old["rule_areas"]
    path.write_text("---\n" + dump(new) + "---\n" + body, encoding="utf-8", newline="")
    print(f"migrated {aid}")


def write_new_role(aid: str, data: dict, body: str) -> None:
    (AGENTS / f"{aid}.md").write_text(
        "---\n" + dump(data) + "---\n" + body, encoding="utf-8", newline="")
    print(f"created {aid}")


TE = {
    "schema_version": 2, "id": "test-engineer", "kind": "role",
    "family": "test_eval", "domain": "test_eval", "role": "test-engineer",
    "mission": "Audita a cobertura de testes do caso: encontra testes negativos, de fronteira e de "
               "contrato ausentes; nunca escreve código de produção.",
    "does": [
        "mapear critérios verificáveis sem teste correspondente",
        "detectar drift entre contrato e implementação",
        "apontar caminhos de falha sem cobertura negativa",
    ],
    "does_not": [
        "não escreve nem corrige código de produção",
        "não promove hipótese sem evidência de teste",
        "não executa mutação em nuvem",
    ],
    "inputs": ["code", "artifact", "finding"],
    "outputs": ["review", "recommendations"],
    "allowed_tools": ["sfa_tokensave_read", "sfa_tokensave_symbols"],
    "denied_tools": [],
    "required_context_kinds": ["code"],
    "allowed_context_kinds": ["code", "artifact", "fact", "finding", "rule", "unresolved"],
    "knowledge_packs": ["knowledge/agentic/"],
    "skills": [],
    "trust_floor": "USER_INPUT",
    "budget": {"context": 8000, "tools": 8, "model_calls": 2,
               "model_tier": "balanced", "time": 180, "handoffs": 2},
    "spawn": {"conditions": ["on_gate"], "information_gain_threshold": 0.1},
    "stop": {"conditions": ["on_eval_complete"]},
    "handoffs": {"allowed_targets": ["verifier", "coordinator"], "mode": "DATA_ONLY"},
    "review_policy": {"requires_verifier": False, "adversarial_check": "never"},
    "evals": [],
    "agentops_emit_span": True,
    "risk": "read_only",
    "parent": None,
}
TE_BODY = """
# Test Engineer

## Missão

Garantir que todo critério verificável tenha teste correspondente — incluindo
caminhos de falha e fronteiras — sem tocar em código de produção.

## Procedimento de evidência

1. Enumerar critérios verificáveis do caso (contratos, acceptance, regras).
2. Cruzar com a superfície de testes via TokenSave; listar lacunas.
3. Classificar cada lacuna: negativa ausente, fronteira ausente, contrato derivado.
4. Emitir `review` com a lista priorizada; nunca a correção.

## Condições de parada

- `on_eval_complete`: todas as lacunas enumeradas e classificadas.

## Recusar

- Recusar escrever implementação: a saída é diagnóstico de cobertura.
- Recusar teste fraco que apenas repete o caminho feliz.
- Recusar escopo fora do caso em análise.
"""

ES = {
    "schema_version": 2, "id": "evaluation-specialist", "kind": "role",
    "family": "test_eval", "domain": "test_eval", "role": "evaluation-specialist",
    "mission": "Mede se um agent acrescenta valor: ganho de informação, custo e qualidade "
               "por perfil (economy/balanced/deep); recomenda rebaixar, fundir ou remover.",
    "does": [
        "comparar saída com e sem um agent no mesmo caso",
        "medir custo vs. ganho de informação por agent",
        "avaliar recall de bloqueadores e taxa de falso-positivo",
    ],
    "does_not": [
        "não responde o mérito técnico do caso (não é specialist)",
        "não decide remoção sozinho — recomenda ao coordinator",
        "não usa estimativa de token sem telemetria real",
    ],
    "inputs": ["fact", "evidence", "memory"],
    "outputs": ["report", "recommendations"],
    "allowed_tools": ["sfa_agentops_inspect"],
    "denied_tools": [],
    "required_context_kinds": ["fact", "evidence"],
    "allowed_context_kinds": ["fact", "evidence", "finding", "memory", "unresolved"],
    "knowledge_packs": ["knowledge/agentic/"],
    "skills": [],
    "trust_floor": "USER_INPUT",
    "budget": {"context": 8000, "tools": 6, "model_calls": 2,
               "model_tier": "balanced", "time": 180, "handoffs": 2},
    "spawn": {"conditions": ["on_gate"], "information_gain_threshold": 0.1},
    "stop": {"conditions": ["on_eval_complete"]},
    "handoffs": {"allowed_targets": ["coordinator", "synthesizer"], "mode": "DATA_ONLY"},
    "review_policy": {"requires_verifier": False, "adversarial_check": "never"},
    "evals": [],
    "agentops_emit_span": True,
    "risk": "read_only",
    "parent": None,
}
ES_BODY = """
# Evaluation Specialist

## Missão

Responder, com dados e não opinião, se um agent merece existir: o que ele
acrescenta em informação por unidade de custo, e se um perfil mais barato
atinge o mesmo resultado.

## Procedimento de evidência

1. Rodar o mesmo caso com e sem o agent avaliado (lab controlado).
2. Medir ganho de informação, redução de unresolved, decisão alterada e custo.
3. Comparar perfis economy/balanced/deep; registrar a fronteira de qualidade.
4. Emitir `report` com recomendação: manter, rebaixar perfil, fundir ou remover.

## Condições de parada

- `on_eval_complete`: métricas emitidas com baseline do mesmo caso.

## Recusar

- Recusar conclusão sem baseline comparável ("parece redundante" não é dado).
- Recusar medir token por estimativa de caracteres — só telemetria real.
- Recusar avaliar agent fora do escopo declarado.
"""


def main() -> None:
    write_new_role("test-engineer", TE, TE_BODY)
    write_new_role("evaluation-specialist", ES, ES_BODY)
    for path in sorted(AGENTS.glob("*.md")):
        if path.stem in {"test-engineer", "evaluation-specialist"}:
            continue
        migrate(path)
    print("done")


if __name__ == "__main__":
    main()
