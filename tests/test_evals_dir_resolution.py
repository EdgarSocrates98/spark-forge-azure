"""Ciclo 12 — resolucao do corpus evals/: workspace > checkout/wheel embutido.

O fallback empacotado (`sparkforge_azure/_data/evals`) so existe dentro de uma
wheel real — aqui verificamos a precedencia e a recusa honesta quando nem o
workspace nem o pacote tem o corpus.
"""

from __future__ import annotations

from sparkforge_azure.evals import cli


def test_workspace_evals_wins(tmp_path, monkeypatch):
    workspace = tmp_path / "ws"
    suite = workspace / "evals" / "agentic" / "debate"
    suite.mkdir(parents=True)
    monkeypatch.chdir(workspace)
    assert cli._suite_dir("debate") == suite


def test_checkout_or_packaged_fallback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # cwd vazio: cai no corpus do checkout (source) ou do _data (wheel).
    resolved = cli._evals_dir()
    assert (resolved / "agentic").is_dir()
    assert cli._suite_dir("debate") == resolved / "agentic" / "debate"


def test_honest_missing_when_neither_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sparkforge_azure.distribution.assets._PKG", tmp_path / "fakepkg")
    monkeypatch.setattr("sparkforge_azure.distribution.assets._REPO", tmp_path / "fakerepo")
    resolved = cli._evals_dir()
    # Recusa honesta: aponta para o workspace, onde um corpus de escrita iria.
    assert resolved == tmp_path / "evals"
    assert not resolved.is_dir()


def test_debate_suite_resolves_through_evals_dir(tmp_path, monkeypatch):
    # `grade` action usa `_evals_dir().joinpath(*DEBATE_SUITE[1:])` — o mesmo
    # path que `_suite_dir("debate")` retorna.
    monkeypatch.chdir(tmp_path)
    assert tmp_path.joinpath(*cli.DEBATE_SUITE).name == "debate" and cli._evals_dir().joinpath(
        *cli.DEBATE_SUITE[1:]
    ) == cli._suite_dir("debate")
