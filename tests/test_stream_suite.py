"""SDD STREAMING_ECONOMY_OBSERVABILITY — stream lab suite oracle."""
from __future__ import annotations

from sparkforge_azure.stream.suite import run_stream_suite

FIXTURES = "tests/fixtures/stream"


def test_stream_suite_all_cases():
    r = run_stream_suite(FIXTURES)
    assert r["failed"] == 0, [c["case"] for c in r["cases"]
                             if c["verdict"] == "fail"]
    assert r["passed"] >= 22
    assert r["status"] == "pass"
