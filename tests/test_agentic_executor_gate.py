"""Unidade do Debate ROI Gate (`sparkforge/agentic/executor/gate.py`).

O par real do catalogo (`SF-GRAPH-005` x `SF-LF-001`, so na uniao das duas
fixtures da regra 29) e a base: as variacoes mudam severidade, `kind` ou
evidencia de um finding e conferem o veredito, sem inventar par novo. Onde a
ordem das regras precisa de combinacao que o par real nao tem, o gate e chamado
direto com findings sinteticos.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from sparkforge_azure.agentic.executor import gate
from sparkforge_azure.agentic.executor.run import open_debate_plans, run_executor

RAIZ = Path(__file__).resolve().parents[1]
UNIAO = (
    RAIZ / "fixtures" / "graph" / "import_sem_jar_no_iac" / "expected",
    RAIZ / "fixtures" / "infra_code" / "fgac_com_jar_extra" / "expected",
)
RUNTIME = {"databricks_runtime": "15.4", "spark": "3.5.0"}
BUDGET = {"max_debates": 1, "max_rounds": 3}
POLITICA = {"policy_version": 1, "debate_severities": ["P0", "P1"]}
PLANO = {"participants": [{"agent": "a"}, {"agent": "b"}], "participants_unresolved": []}


def _uniao(overrides: dict[str, dict[str, Any]] | None = None) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    facts: list[dict] = []
    for pasta in UNIAO:
        findings += json.loads((pasta / "findings.json").read_text(encoding="utf-8"))
        facts += json.loads((pasta / "facts.json").read_text(encoding="utf-8"))
    findings = copy.deepcopy(findings)
    for finding in findings:
        for chave, valor in (overrides or {}).get(finding["rule_id"], {}).items():
            if chave == "evidence_append":
                finding["evidence"] = list(finding.get("evidence") or []) + valor
            elif chave == "action":
                finding["action"] = {**finding["action"], **valor}
            else:
                finding[chave] = valor
    return findings, facts


def _gate(overrides: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    findings, facts = _uniao(overrides)
    planos = open_debate_plans(findings, facts, RUNTIME, BUDGET)
    assert len(planos) == 1, planos
    return planos[0]["debate_gate"]


def _resultado(recommendation: str = "experiment", vencedor: str | None = "c1") -> Any:
    return SimpleNamespace(recommendation=recommendation, winning_claim_id=vencedor)


def _finding(rule_id: str, severity: str | None, kind: str) -> dict[str, Any]:
    finding: dict[str, Any] = {"rule_id": rule_id, "action": {"kind": kind}}
    if severity is not None:
        finding["severity"] = severity
    return finding


def _avaliar(findings: list[dict], resultado: Any = None, reversibilidade=None) -> dict:
    return gate.avaliar(
        ("SF-A-001", "SF-B-001"),
        resultado or _resultado(),
        findings,
        [],
        1,
        PLANO,
        politica=POLITICA,
        reversibilidade=reversibilidade or {"k.rev": True, "k.irrev": False},
    )




class TestOrdem:
    def test_irreversivel_decide_mesmo_com_severidade_ausente(self):
        bloco = _avaliar(
            [_finding("SF-A-001", None, "k.rev"), _finding("SF-B-001", "P3", "k.irrev")]
        )
        assert bloco["verdict"] == "debater"
        assert bloco["reasons"] == ["irreversivel:SF-B-001"]
        assert bloco["missing"] == ["severity:SF-A-001"]

    def test_escalate_sai_debater(self):
        bloco = _avaliar(
            [_finding("SF-A-001", "P3", "k.rev"), _finding("SF-B-001", "P3", "k.rev")],
            _resultado("escalate"),
        )
        assert bloco["verdict"] == "debater"
        assert bloco["reasons"] == ["sem_lastro:escalate"]

    def test_sem_claim_vencedora_conta_como_sem_lastro(self):
        bloco = _avaliar(
            [_finding("SF-A-001", "P3", "k.rev"), _finding("SF-B-001", "P3", "k.rev")],
            _resultado("experiment", vencedor=None),
        )
        assert bloco["verdict"] == "debater"
        assert bloco["signals"]["arbitration"] == "sem_vencedor"

    def test_pior_severidade_da_regra_vence(self):
        bloco = _avaliar(
            [
                _finding("SF-A-001", "P3", "k.rev"),
                _finding("SF-A-001", "P1", "k.rev"),
                _finding("SF-B-001", "P3", "k.rev"),
            ]
        )
        assert bloco["signals"]["severity"] == {"SF-A-001": "P1", "SF-B-001": "P3"}
        assert bloco["verdict"] == "debater"

    def test_severidade_fora_de_p0_p3_e_ausente(self):
        bloco = _avaliar(
            [_finding("SF-A-001", "alta", "k.rev"), _finding("SF-B-001", "P3", "k.rev")]
        )
        assert bloco["verdict"] == "unresolved"
        assert bloco["missing"] == ["severity:SF-A-001"]




class TestPolitica:
    def test_politica_do_catalogo_e_valida(self):
        assert gate.load_policy()["debate_severities"] == ["P0", "P1"]

    @pytest.mark.parametrize(
        "doc",
        [
            [],
            {"debate_severities": ["P0"]},
            {"policy_version": 1, "debate_severities": []},
            {"policy_version": 1, "debate_severities": ["P5"]},
        ],
    )
    def test_politica_malformada_recusa_nomeando_o_campo(self, doc):
        with pytest.raises(gate.GatePolicyError, match="debate_gate.yaml"):
            gate.validate_policy(doc)


    def test_reversibilidade_do_catalogo_tem_os_setenta_seis(self):
        mapa = gate.load_reversibility()
        # 76 no AWS; 3 kinds sem sentido Azure sairam (ver provenance de action_kinds.yaml)
        assert len(mapa) == 73
        assert all(isinstance(v, bool) for v in mapa.values())


