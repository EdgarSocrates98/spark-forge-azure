"""A regra fechada que transforma nome de tool em verbo canonico.

A tabela e a Decision 4 do DESIGN do eval harness, e as bordas conhecidas estao
nela de proposito: um teste que so cobre o caminho feliz deixaria a regra mudar
de comportamento na borda sem ninguem ver.
"""
from __future__ import annotations

import pytest

from sparkforge_azure.facts.host_transcript import canonical_verb

PLUGIN = "mcp__plugin_x_sparkforge_azure__sfa_analyze_pyspark"
CADEIA = "cd x && rtk sparkforge-azure analyze pyspark lib/"
UV = "uv run sparkforge-azure rules lookup --rule-id SFA-PY-005"

CASOS = [
    ("mcp__sparkforge_azure__sfa_judge", {}, ("mcp", "judge")),
    # tool do spark-forge-aws (outro forge, prefixo `sparkforge_`) nao e deste canal
    ("mcp__sparkforge__sparkforge_judge", {}, ("other", None)),
    (PLUGIN, {}, ("mcp", "analyze_pyspark")),
    ("mcp__outro__outro_judge", {}, ("other", None)),
    ("Bash", {"command": "sparkforge-azure judge --facts f.json"}, ("bash", "judge")),
    # a CLI `sparkforge` e a do spark-forge-aws
    ("Bash", {"command": "sparkforge judge --facts f.json"}, ("other", None)),
    ("Bash", {"command": CADEIA}, ("bash", "analyze_pyspark")),
    ("Bash", {"command": "python -m sparkforge_azure next-step"}, ("bash", "next_step")),
    ("Bash", {"command": UV}, ("bash", "rules_lookup")),
    ("Bash", {"command": "sparkforge-azure judge facts.json"}, ("bash", "judge")),
    ("Bash", {"command": "ls fixtures/ | head"}, ("other", None)),
    ("Bash", {"command": "echo sparkforge-azure judge"}, ("other", None)),
    ("Bash", {"command": ""}, ("other", None)),
    ("Bash", {}, ("other", None)),
    ("Bash", "nao e dict", ("other", None)),
    ("Read", {"file_path": "sparkforge_azure"}, ("other", None)),
]


@pytest.mark.parametrize("nome, entrada, esperado", CASOS)
def test_tabela_da_decision_4(nome, entrada, esperado):
    assert canonical_verb(nome, entrada) == esperado


def test_borda_conhecida_argumento_so_com_letras_vira_parte_do_verbo():
    """Registrada, nao corrigida: `sparkforge-azure judge cases` vira `judge_cases`.

    O efeito e um falso `missing:[judge]`, VISIVEL no scorecard -- nunca um
    acerto fabricado. Se um dia a regra passar a consultar o parser da CLI para
    resolver isto, este teste muda junto com a decisao, e nao por acidente.
    """
    assert canonical_verb("Bash", {"command": "sparkforge-azure judge cases"}) == (
        "bash",
        "judge_cases",
    )


def test_caminho_absoluto_do_executavel_nao_casa():
    assert canonical_verb("Bash", {"command": "/usr/bin/sparkforge-azure judge"}) == ("other", None)
