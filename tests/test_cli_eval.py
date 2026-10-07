"""`python -m sparkforge_azure.evals grade|compare` de ponta a ponta, sobre as fixtures.

A CLI aceita NOMES sob bases fixas -- a suite em `<cwd>/evals/agentic/`, as
execucoes em `RUNS_ROOT`, os baselines em `evals/agentic/<suite>/baselines/`.
Cada teste monta essa geografia num diretorio temporario (`chdir` para um
repositorio falso e `RUNS_ROOT` apontado para outro) e copia as fixtures para
dentro dela, para que a CLI rode exatamente como o operador a roda.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sparkforge_azure.evals import cli

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "host_transcript"
SUITE = "fixtures_suite"


@pytest.fixture
def geografia(tmp_path, monkeypatch):
    repo, runs = tmp_path / "repo", tmp_path / "runs"
    suite_dir = repo / "evals" / "agentic" / SUITE
    shutil.copytree(FIXTURES / "_suite", suite_dir)
    runs.mkdir()
    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli, "RUNS_ROOT", runs)
    return suite_dir, runs


def _json(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def _esperado(caso: str, nome: str) -> dict:
    return json.loads((FIXTURES / caso / "expected" / nome).read_text(encoding="utf-8"))












def _conjuntos(suite_dir: Path, runs: Path, caso: str) -> None:
    shutil.copytree(FIXTURES / caso / "input" / "baseline", suite_dir / "baselines" / "base")
    shutil.copytree(FIXTURES / caso / "input" / "candidate", runs / "cand")












def test_candidate_evaluate_exposes_bundle_and_external_command_sources():
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "candidate",
            "evaluate",
            "--candidate",
            "routing-variant",
            "--bundle",
            "bundle.json",
        ]
    )
    assert args.bundle == "bundle.json"
    assert args.external_command is None

    args = parser.parse_args(
        [
            "candidate",
            "evaluate",
            "--candidate",
            "routing-variant",
            "--evidence",
            "bundle.yaml",
            "--external-command",
            "benchmark_bundle",
        ]
    )
    assert args.bundle == "bundle.yaml"
    assert args.external_command == "benchmark_bundle"
