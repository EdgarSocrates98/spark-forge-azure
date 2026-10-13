"""Contrato do gate `scripts/check_recall_economy.py`.

O gate decide recall nominal (piso 100%), reporta conceitual sem piso e
recusa publicar razao de economia sobre corpus abaixo do envelope. Os valores
de referencia sao os medidos neste repositorio -- quem mudar o corpus muda o
piso no mesmo commit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_recall_economy.py"


def _report() -> dict:
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_gold_set_derives_the_declared_floor():
    rel = _report()
    assert rel["perguntas"] >= 12
    assert rel["perguntas"] >= rel["piso_de_perguntas"]
    assert rel["goldset"] == "derivado"


def test_nominal_recall_is_total_or_named_failures():
    rel = _report()
    nominal = rel["recall_nominal"]
    assert "unresolved" not in nominal
    assert nominal["passou"] + len(nominal["falhas"]) == nominal["de"]
    # Toda falha nominal precisa estar nomeada em SEM_RECALL no script --
    # o proprio gate falha se uma nao estiver (duas direcoes).
    assert nominal["falhas"] == []


def test_conceptual_recall_reported_without_floor():
    rel = _report()
    conceptual = rel["recall_conceitual"]
    assert "unresolved" not in conceptual
    assert conceptual["piso"] is None
    assert 0 <= conceptual["passou"] <= conceptual["de"]


def test_economy_is_measured_or_named_unresolved():
    rel = _report()
    economia = rel["economia"]
    if "razao_unresolved" in economia:
        # Recusa exige a medida que a destravaria -- nunca razao solta.
        assert economia["medida_que_destravaria"]
        assert economia["envelope_fixo_bytes"] > 0
    else:
        assert economia["contra_arquivos"] > 0
        assert economia["contra_grep"] > 0


# --- Economia na arvore do repositorio (TREE_ECONOMY_MEASUREMENT) -------


def test_tree_gold_set_is_derived_and_nonempty():
    from sparkforge_azure.economy.goldset import derivar_goldset_arvore

    pares = derivar_goldset_arvore()
    # Piso de superficie publica: cair significa que modulos perderam
    # `__all__` ou defs -- derivado, nunca escrito a mao.
    assert len(pares) >= 200
    arquivos = {a for a, _ in pares}
    assert len(arquivos) >= 100  # cobre a arvore, nao um modulo


def test_tree_measurement_has_denominators():
    rel = _report()
    ea = rel["economia_arvore"]
    assert ea.get("erro") is None
    assert ea["perguntas"] >= 200
    assert ea["recall_nominal"]["de"] == ea["perguntas"]
    assert ea["bytes_pack"] > 0 and ea["bytes_arquivos"] > 0


def test_tree_economy_is_measured():
    rel = _report()
    ea = rel["economia_arvore"]
    # A razao que o corpus de fixture nao pode produzir: corpus real
    # excede o envelope, entao o numero e medido, nao unresolved.
    assert ea["contra_arquivos"] > 1
    assert ea["contra_grep"] > 0
    # Recall nominal da arvore e reportado com falhas NOMEADAS -- queda
    # significa que o retrieval perdeu simbolo publico pedido pelo nome.
    r = ea["recall_nominal"]
    # 224/226 medido. Residuais nomeados e legitimos: `codeintel/extract.py::No`
    # (stopword -- a expansao filtra a pergunta inteira) e
    # `collectors/unity_catalog.py::collect_live` (ambiguo -- 4 collectors
    # definem o mesmo nome e o pack carrega um dos irmaos).
    assert r["passou"] >= 224
