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
