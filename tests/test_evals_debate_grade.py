"""`sparkforge_azure.evals.debate_grade` sobre desfechos SINTETICOS (AT-013).

O grader so le arquivo: o `result.json` que `scripts/run_debate.py` grava por
caso, o `debate_facts.jsonl` copiado do estado do debate e os transcripts
`<n>-<lado>.jsonl`. Aqui cada teste monta essa geografia a mao -- nenhum modelo,
nenhum debate de verdade (o placar sobre debates reais da suite mora em
`tests/test_debate_suite.py`).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from sparkforge_azure.evals import cli
from sparkforge_azure.evals.debate_grade import (
    DEBATE_FACTS_FILE,
    GRADE_FILE,
    OUTCOMES,
    RESULT_FILE,
    DebateGradeError,
    grade_case,
    grade_debate_run,
    load_expected,
    outcome_of,
    suite_cases,
)

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS = ROOT / "fixtures" / "host_transcript"
COM_USAGE = TRANSCRIPTS / "correct_mcp" / "input" / "q-mcp.jsonl"
SEM_USAGE = TRANSCRIPTS / "no_usage" / "input" / "q-alt.jsonl"
REGRAS = ["SF-GRAPH-005", "SF-LF-001"]


def _gabarito(outcome: str = "winner", winner: str | None = "SF-LF-001", **extra: Any) -> dict:
    return {
        "schema_version": 1,
        "rules": REGRAS,
        "outcome": outcome,
        "winner": winner,
        "decided_by": {"kind": "lakeformation.grant", "attr": "is_iam_allowed_principals",
                       "value": False},
        **extra,
    }


def _done(vencedor: str | None, refs: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": "done",
        "outcome": "winner" if vencedor else "unresolved",
        "winner_rule": vencedor,
        "closed_by": "consensus",
        "rounds_completed": 3,
        "referee": {"upheld": True},
        "decision": {"evidence_refs": refs or []},
    }


def _caso(
    base: Path,
    done: dict[str, Any] | None,
    tentativas: list[str] = (),
    status: str = "done",
    facts: list[dict[str, Any]] = (),
) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    resultado = {
        "status": status,
        "done": done,
        "attempts": [{"n": i + 1, "status": s} for i, s in enumerate(tentativas)],
    }
    (base / RESULT_FILE).write_text(json.dumps(resultado), encoding="utf-8")
    if facts:
        (base / DEBATE_FACTS_FILE).write_text(
            "".join(json.dumps(f) + "\n" for f in facts), encoding="utf-8"
        )
    return base


def _grant(fact_id: str, iam: bool) -> dict[str, Any]:
    return {
        "extractor": "lakeformation-grants",
        "path": "artifacts/x.json",
        "fact": {"id": fact_id, "kind": "lakeformation.grant",
                 "attrs": {"is_iam_allowed_principals": iam}},
    }


# --------------------------------------------------------------------------
# outcome
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("gabarito", "eleito", "esperado"),
    [
        (_gabarito(), "SF-LF-001", "correct_winner"),
        (_gabarito(), "SF-GRAPH-005", "wrong_winner"),
        (_gabarito(), None, "missed_resolution"),
        (_gabarito("unresolved", None), None, "correct_unresolved"),
        (_gabarito("unresolved", None), "SF-LF-001", "false_resolution"),
    ],
)
def test_os_cinco_desfechos(gabarito, eleito, esperado):
    assert outcome_of(gabarito, _done(eleito)) == esperado


def test_os_desfechos_publicados_sao_exatamente_os_cinco():
    assert set(OUTCOMES) == {
        "correct_winner",
        "wrong_winner",
        "missed_resolution",
        "correct_unresolved",
        "false_resolution",
    }


# --------------------------------------------------------------------------
# gabarito
# --------------------------------------------------------------------------


def _grava_gabarito(pasta: Path, dado: dict) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "expected.yaml").write_text(yaml.safe_dump(dado), encoding="utf-8")
    return pasta


@pytest.mark.parametrize(
    "dado",
    [
        _gabarito(winner="SF-OUTRA-001"),
        _gabarito("unresolved", "SF-LF-001"),
        _gabarito("talvez", None),
        {**_gabarito(), "decided_by": {}},
        {**_gabarito(), "rules": ["SF-LF-001", "SF-LF-001"]},
        {**_gabarito(), "schema_version": 2},
    ],
)
def test_gabarito_malformado_e_recusado(dado, tmp_path):
    with pytest.raises(DebateGradeError):
        load_expected(_grava_gabarito(tmp_path / "c", dado))




# --------------------------------------------------------------------------
# um caso
# --------------------------------------------------------------------------


def test_sem_result_e_ungraded_e_nao_desfecho(tmp_path):
    (tmp_path / "c").mkdir()
    linha = grade_case("c", _gabarito(), tmp_path / "c")
    assert linha["status"] == "ungraded"
    assert linha["reason"] == "result_not_found"
    assert "outcome" not in linha


def test_debate_que_nao_fechou_e_ungraded_com_a_razao_do_driver(tmp_path):
    caso = _caso(tmp_path / "c", None, ["no_json_block"] * 3, status="aborted")
    linha = grade_case("c", _gabarito(), caso)
    assert linha["status"] == "ungraded"
    assert linha["outcome"] is None
    assert linha["reason"] == "aborted"
    assert linha["refused_submissions"] == 3


def test_recusa_conta_no_json_block_e_nao_conta_falha_de_host_nem_passe(tmp_path):
    tentativas = ["accepted", "refused", "no_json_block", "host_failed", "driver_pass"]
    linha = grade_case("c", _gabarito(), _caso(tmp_path / "c", _done("SF-LF-001"), tentativas))
    assert linha["status"] == "graded"
    assert linha["rounds"] == 3
    assert (linha["refused_submissions"], linha["host_failures"], linha["driver_passes"]) == (
        2,
        1,
        1,
    )
    # o passe do driver nao e chamada ao host: quatro turnos esperados, zero achados
    assert linha["cost"]["turns_expected"] == 4
    assert linha["cost"]["transcripts_found"] == 0


def test_fact_decisivo_extraido_e_citado(tmp_path):
    facts = [_grant("f_certo", iam=False), _grant("f_errado", iam=True)]
    caso = _caso(tmp_path / "c", _done("SF-LF-001", ["claim_x", "f_certo"]), facts=facts)
    assert grade_case("c", _gabarito(), caso)["decisive_fact"] == {
        "kind": "lakeformation.grant",
        "extracted": True,
        "cited_by_decision": True,
    }


def test_fact_do_kind_certo_com_atributo_errado_nao_e_o_decisivo(tmp_path):
    """Casa por `kind` E por `attr == value`: o grant de IAM_ALLOWED_PRINCIPALS
    nao sustenta a vitoria do Lake Formation, mesmo citado."""
    caso = _caso(
        tmp_path / "c", _done("SF-LF-001", ["f_errado"]), facts=[_grant("f_errado", iam=True)]
    )
    decisivo = grade_case("c", _gabarito(), caso)["decisive_fact"]
    assert decisivo["extracted"] is False
    assert decisivo["cited_by_decision"] is False








# --------------------------------------------------------------------------
# a execucao inteira
# --------------------------------------------------------------------------


def _suite(base: Path) -> Path:
    _grava_gabarito(base / "vence", _gabarito())
    _grava_gabarito(base / "empata", _gabarito("unresolved", None))
    _grava_gabarito(base / "fora", _gabarito())
    (base / "uniao").mkdir()  # sem expected.yaml: nao e caso
    return base


def _chaves(valor: Any, prefixo: str = "") -> list[str]:
    if isinstance(valor, dict):
        saida = []
        for chave, filho in valor.items():
            caminho = f"{prefixo}.{chave}" if prefixo else chave
            saida.append(caminho)
            saida.extend(_chaves(filho, caminho))
        return saida
    if isinstance(valor, list):
        return [c for item in valor for c in _chaves(item, prefixo)]
    return []






# --------------------------------------------------------------------------
# CLI: `python -m sparkforge_azure.evals debate --run <nome>`
# --------------------------------------------------------------------------


@pytest.fixture
def geografia(tmp_path, monkeypatch):
    repo, runs = tmp_path / "repo", tmp_path / "runs"
    _suite(repo / "evals" / "agentic" / "debate")
    runs.mkdir()
    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli, "DEBATE_RUNS_ROOT", runs)
    return runs


def test_cli_grava_grade_json_dentro_da_execucao(geografia, capsys):
    _caso(geografia / "debate-1" / "vence", _done("SF-LF-001"), ["accepted"])
    assert cli.main(["debate", "--run", "debate-1"]) == 0
    impresso = json.loads(capsys.readouterr().out)
    gravado = json.loads((geografia / "debate-1" / GRADE_FILE).read_text(encoding="utf-8"))
    assert impresso == gravado
    assert gravado["totals"]["outcomes"]["correct_winner"] == 1


@pytest.mark.parametrize("nome", ["../fora", "a/b", "..", "."])
def test_cli_recusa_caminho_no_lugar_de_nome(nome, geografia, capsys):
    assert cli.main(["debate", "--run", nome]) == 2
    assert "NOME" in capsys.readouterr().err


def test_cli_recusa_execucao_ausente(geografia, capsys):
    assert cli.main(["debate", "--run", "nao-existe"]) == 2
    assert "ausente" in capsys.readouterr().err
