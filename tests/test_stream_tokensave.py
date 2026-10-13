"""SDD STREAMING_ECONOMY_OBSERVABILITY — TokenSave on the stream corpus."""
from __future__ import annotations

from sparkforge_azure.tokensave.benchmark import run_benchmark

CORPUS = "evals/token_efficient/stream_case"

TASK = ("Streaming lag crescendo: consumer group cg-orders no hub "
        "ns-01/telemetry parou de avançar — checkpoint, consumer group "
        "ou capacidade do Event Hubs?")
TERMS = ["ns-01", "telemetry", "cg-orders"]


def test_stream_benchmark():
    r = run_benchmark(CORPUS, task=TASK, required_terms=TERMS)
    assert r["baseline"]["bytes"] > 0
    assert r["tokens"] == "unresolved"  # bytes ≠ tokens
    for name, prof in r["profiles"].items():
        assert prof["bytes_read"] <= r["baseline"]["bytes"], name
        assert prof["status"] in {"ok", "partial", "sufficient"}
        assert "level_distribution" in prof
    assert r["profiles"]["economy"]["bytes_avoided"] > 0


def test_stream_corpus_is_self_contained():
    from sparkforge_azure.tokensave.benchmark import corpus_files
    names = {p.name for p in corpus_files(CORPUS)}
    for required in ("case.yaml", "eventhubs.json", "consumer.json",
                     "offsets.json", "query_progress.json",
                     "checkpoint.json"):
        assert required in names, required
