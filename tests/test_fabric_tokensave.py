"""SDD FABRIC_GRAPH_TOKENSAVE — TokenSave benchmark on the Fabric corpus."""
from __future__ import annotations

from sparkforge_azure.tokensave.benchmark import run_benchmark

CORPUS = "evals/token_efficient/fabric_case"

TASK = ("Notebook Fabric nao le a tabela via shortcut OneLake em ws-1111 / "
        "lake_sales — shortcut sc-0001 passthrough para ws-2222; e o job "
        "lento: Spark ou capacity cap-0001?")
TERMS = ["sc-0001", "lh-aaaa", "cap-0001", "ws-1111"]


def test_fabric_benchmark():
    r = run_benchmark(CORPUS, task=TASK, required_terms=TERMS)
    assert r["baseline"]["bytes"] > 0
    assert r["tokens"] == "unresolved"  # bytes ≠ tokens; no provider observed
    for name, prof in r["profiles"].items():
        assert prof["bytes_read"] <= r["baseline"]["bytes"], name
        assert prof["status"] in {"ok", "partial", "sufficient"}
        assert "level_distribution" in prof
    # Progressive retrieval must beat the naive baseline on this corpus.
    assert r["profiles"]["economy"]["bytes_avoided"] > 0


def test_fabric_corpus_is_self_contained():
    from sparkforge_azure.tokensave.benchmark import corpus_files
    files = corpus_files(CORPUS)
    names = {p.name for p in files}
    for required in ("workspace.json", "items.json", "onelake_security.json",
                     "shortcuts.json", "capacity.json", "pipelines.json"):
        assert required in names, required
