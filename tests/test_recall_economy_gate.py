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
