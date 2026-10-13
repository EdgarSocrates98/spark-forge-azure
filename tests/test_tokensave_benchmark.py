"""TokenSave benchmark on the UC/ADLS case corpus (TOKENSAVE_PROOF)."""
from __future__ import annotations

from pathlib import Path

import pytest

from sparkforge_azure.tokensave.benchmark import run_benchmark
from sparkforge_azure.tokensave.engine import TokenSave

CASE_DIR = Path("evals/token_efficient/access_case")


def test_benchmark_profiles_vs_baseline() -> None:
    report = run_benchmark(CASE_DIR)
    base = report["baseline"]["bytes"]
    assert base > 0
    for name in ("economy", "balanced", "deep"):
        run = report["profiles"][name]
        assert run["bytes_read"] < base, name
        assert run["bytes_avoided"] > 0, name
        assert run["status"] == "sufficient", name


def test_metrics_are_measured_not_invented() -> None:
    report = run_benchmark(CASE_DIR)
    for name, run in report["profiles"].items():
        for key in ("level_distribution", "full_read_rate", "index_hit_rate",
                    "cache_hit_rate", "context_reuse_rate", "bytes_read",
                    "bytes_avoided"):
            assert key in run, (name, key)
        assert run["payload_basis"].startswith("len(json.dumps")
    # no provider observation offline -> tokens never a number
    assert report["tokens"] == "unresolved"


def test_stops_at_first_sufficient_level(tmp_path: Path) -> None:
    """L0/L1 covering all required terms must not fire L2/L3/L5/L6."""
    (tmp_path / "uc.json").write_text(
        '{"external_locations": [{"name": "loc_finance"}]}', encoding="utf-8")
    ts = TokenSave(tmp_path, profile_name="balanced")
    res = ts.context("diagnose loc_finance denial", required_terms=["loc_finance"])
    assert res.status == "sufficient"
    assert set(res.levels_used) <= {"L0", "L1"}, res.levels_used
    for rec in ts.ledger.records:
        assert rec.level <= 1, f"L{rec.level} fired after sufficiency: {rec}"


def test_ladder_climbs_only_when_terms_missing(tmp_path: Path) -> None:
    """A term absent from literal text forces deeper levels; L6 never fires."""
    (tmp_path / "uc.json").write_text(
        '{"external_locations": [{"name": "loc_finance"}]}\n' * 80,
        encoding="utf-8")
    ts = TokenSave(tmp_path, profile_name="deep")
    res = ts.context("diagnose loc_finance and qzx_never_exists",
                     required_terms=["loc_finance", "qzx_never_exists"])
    assert res.status == "partial"
    assert "qzx_never_exists" in res.unresolved
    assert ts.ledger.summary()["full_reads"] == 0


def test_full_read_is_rare_and_gated(tmp_path: Path) -> None:
    (tmp_path / "big.py").write_text("x = 1\n" * 500, encoding="utf-8")
    eco = TokenSave(tmp_path, profile_name="economy")
    out = eco.read_full("big.py", reason="need whole file")
    assert out.get("refused") is True and "forbids" in out["reason"]

    deep = TokenSave(tmp_path, profile_name="deep")
    out = deep.read_full("big.py", reason="")
    assert out.get("refused") is True and "reason" in out["reason"]

    out = deep.read_full("big.py", reason="audit the whole module")
    assert out.get("refused") is not True
    rec = deep.ledger.records[-1]
    assert rec.level == 6 and rec.fallback and rec.reason


def test_benchmark_deterministic() -> None:
    a = run_benchmark(CASE_DIR)
    b = run_benchmark(CASE_DIR)
    assert a["baseline"] == b["baseline"]
    for name in a["profiles"]:
        assert a["profiles"][name]["bytes_read"] == b["profiles"][name]["bytes_read"]
        assert a["profiles"][name]["levels_used"] == b["profiles"][name]["levels_used"]


def test_missing_corpus_names_itself(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="case corpus"):
        run_benchmark(tmp_path / "nope")
