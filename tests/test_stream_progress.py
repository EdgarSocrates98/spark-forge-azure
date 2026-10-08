"""SDD STRUCTURED_STREAMING — progress/lag semantics over query_progress."""
from __future__ import annotations

from sparkforge_azure.stream import extract, progress
from sparkforge_azure.stream.casefile import load_bundle

FIXTURES = "tests/fixtures/stream"


def _facts(case: str):
    b = load_bundle(f"{FIXTURES}/{case}")
    return extract.extract_all(b.artifacts, b.sources)


def test_caught_up_is_not_lag():
    series = progress.progress_series(_facts("s01-caught-up-idle"))
    deficit, _ = progress.sustained_processing_deficit(series)
    assert deficit is False
    assert progress.single_batch_dip(series) is False


def test_sustained_deficit_detected():
    series = progress.progress_series(_facts("s06-sustained-bottleneck"))
    deficit, ev = progress.sustained_processing_deficit(series)
    assert deficit is True and ev


def test_single_batch_dip_is_not_sustained():
    """Prompt §205: one slow batch ≠ sustained lag — separate verdicts."""
    series = progress.progress_series(_facts("s05-single-batch-dip"))
    deficit, _ = progress.sustained_processing_deficit(series)
    assert progress.single_batch_dip(series) is True
    assert deficit is False


def test_stalled_consumer_detected():
    stalled, ev = progress.consumer_stalled(_facts("s02-consumer-stalled"))
    assert stalled is True and ev


def test_partition_skew_quantified():
    skew, measured = progress.partition_skew(_facts("s03-partition-skew"))
    assert skew is True
    assert measured  # carries the skew evidence, not just a bool


def test_progress_events_become_facts():
    """SDD contract name — query_progress vira série de progresso."""
    series = progress.progress_series(_facts("s06-sustained-bottleneck"))
    assert len(series) >= 2
    for f in series:
        assert f.kind == "stream.progress"


def test_single_batch_dip_not_lag():
    """AC2 — dip de batch único não é lag sustentado (contract name)."""
    series = progress.progress_series(_facts("s05-single-batch-dip"))
    deficit, _ = progress.sustained_processing_deficit(series)
    assert progress.single_batch_dip(series) is True
    assert deficit is False


def test_checkpoint_deleted_latest_risk():
    """AC3 — checkpoint ausente + start latest é camada checkpoint."""
    from sparkforge_azure.stream.pipeline import run_stream_case
    r = run_stream_case(f"{FIXTURES}/s08-checkpoint-deleted-latest")
    assert r["failure_layer"] == "checkpoint"
    kinds = {f["rule_id"] for f in r["findings"]}
    assert "SF-STR-LOSS-RISK" in kinds


def test_state_growth_needs_series():
    """AC4 — crescimento de estado exige série de progresso."""
    from sparkforge_azure.stream.pipeline import run_stream_case
    r = run_stream_case(f"{FIXTURES}/s10-state-growth")
    assert r["failure_layer"] in {"state_store", "spark_processing",
                                  "consumer_progress"}
