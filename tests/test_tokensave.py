"""TokenSave: ladder order, sufficiency stop, budgets, policy confinement, ledger truth."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sparkforge_azure.cli.main import main as cli_main
from sparkforge_azure.mcp.tools import authorize, load_all
from sparkforge_azure.tokensave import PROFILES, Level, TokenSave

JOB = '''from pyspark.sql import SparkSession

def read_orders(spark):
    return spark.read.format("delta").load("abfss://raw@acct.dfs.core.windows.net/orders")

def dedupe(df):
    return df.dropDuplicates(["order_id"])

def main():
    spark = SparkSession.builder.getOrCreate()
    out = dedupe(read_orders(spark))
    out.write.format("delta").mode("overwrite").saveAsTable("main.sales.orders")
'''


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / "jobs").mkdir()
    (tmp_path / "jobs" / "orders.py").write_text(JOB, encoding="utf-8")
    (tmp_path / "big.py").write_text("\n".join(f"x{i} = {i}" for i in range(2000)),
                                     encoding="utf-8")
    (tmp_path / ".env").write_text("AZURE_CLIENT_SECRET=supersecret\n", encoding="utf-8")
    (tmp_path / "cert.pem").write_text("-----BEGIN-----\n", encoding="utf-8")
    return tmp_path


def test_profiles_are_monotonic() -> None:
    e, b, d = PROFILES["economy"], PROFILES["balanced"], PROFILES["deep"]
    assert e.budget_bytes < b.budget_bytes < d.budget_bytes
    assert not e.allow_full_read and not b.allow_full_read and d.allow_full_read
    assert not e.allow_debate and d.allow_debate


def test_search_is_literal_and_bounded(repo: Path) -> None:
    ts = TokenSave(repo)
    hits = ts.search("dropDuplicates")
    assert hits == [{"path": "jobs/orders.py", "line": 7,
                     "text": 'return df.dropDuplicates(["order_id"])'}]
    assert ts.ledger.records[-1].level == Level.L1_LITERAL


def test_secrets_are_never_searched_or_read(repo: Path) -> None:
    ts = TokenSave(repo, profile_name="deep")
    assert ts.search("supersecret") == []
    assert ts.read(".env").get("refused")
    assert ts.read_full("cert.pem", reason="test").get("refused")
    assert ts.read("../outside.py").get("refused")


def test_read_is_a_bounded_slice(repo: Path) -> None:
    ts = TokenSave(repo)
    out = ts.read("big.py", 1, 5000)
    assert out["end"] - out["start"] + 1 == PROFILES["economy"].slice_lines
    assert out["truncated"] is True


def test_full_read_is_fallback_only(repo: Path) -> None:
    assert TokenSave(repo).read_full("jobs/orders.py", reason="x")["refused"]
    deep = TokenSave(repo, profile_name="deep")
    assert deep.read_full("jobs/orders.py", reason="")["refused"]
    out = deep.read_full("jobs/orders.py", reason="verifier needs whole job")
    assert "dropDuplicates" in out["text"]
    assert deep.ledger.records[-1].fallback is True


def test_symbols_names_and_ranges_only(repo: Path) -> None:
    ts = TokenSave(repo)
    syms = ts.symbols("jobs/orders.py")
    assert [s["name"] for s in syms] == ["read_orders", "dedupe", "main"]
    assert all("text" not in s for s in syms)


def test_context_stops_at_l1_when_terms_located(repo: Path) -> None:
    ts = TokenSave(repo)
    res = ts.context("where is dropDuplicates applied", required_terms=["dropDuplicates"])
    assert res.status == "sufficient"
    assert res.stop_reason == "STOP_SUFFICIENT"
    assert "L5" not in res.levels_used  # no code body needed: located by L1
    assert res.ledger["full_reads"] == 0


def test_context_exact_ref_is_level_zero(repo: Path) -> None:
    ts = TokenSave(repo)
    res = ts.context("explain jobs/orders.py:7", required_terms=["dropDuplicates"])
    assert res.levels_used[0] == "L0"
    assert res.stop_reason == "STOP_SUFFICIENT"


def test_context_unresolved_is_explicit(repo: Path) -> None:
    res = TokenSave(repo).context("x", required_terms=["nonexistent_symbol_zzz"])
    assert res.status == "partial"
    assert res.unresolved == ["nonexistent_symbol_zzz"]
    assert any(t.get("level") == "L4" and "skipped" in t for t in res.trace) or \
        res.stop_reason == "STOP_NO_GAIN"


def test_repeated_context_is_reused_not_resent(repo: Path) -> None:
    ts = TokenSave(repo)
    ts.search("dedupe")
    first = ts.ledger.total_bytes
    ts.search("dedupe")
    assert ts.ledger.total_bytes == first
    assert ts.ledger.records[-1].cache_hit and ts.ledger.records[-1].reused


def test_ledger_never_claims_tokens(repo: Path) -> None:
    ts = TokenSave(repo)
    ts.search("delta")
    s = ts.ledger.summary()
    assert s["tokens"] is None  # unknown != zero; bytes != tokens
    assert "payload_basis" in s


def test_budget_exhaustion_refuses(repo: Path) -> None:
    ts = TokenSave(repo)
    from sparkforge_azure.tokensave.levels import Profile

    ts.profile = Profile("tiny", Level.L5_SLICE, 10, 5, 1, 0, 2, False, False, False, "economy")
    out = ts.read("jobs/orders.py", 1, 3)
    assert out["refused"] and out["reason"] == "budget exhausted"


def test_cli_and_mcp_surfaces(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(["tokensave", "search", "dropDuplicates", "--root", str(repo)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["result"][0]["line"] == 7 and out["authority"] == "data_only"
    tools = load_all()
    spec = tools["sfa_tokensave_context"]
    assert spec.risk.read_only and authorize(spec).allowed
    res = spec.handler({"task": "dedupe", "root": str(repo), "terms": ["dedupe"]})
    assert res["status"] == "sufficient"


@pytest.mark.parametrize("rev", ["--output=/tmp/x", "-p", "--ext-diff", "HEAD;rm", "a b"])
def test_diff_refuses_option_smuggling(repo: Path, rev: str) -> None:
    out = TokenSave(repo).diff(rev)
    assert out.get("refused") and out["reason"] == "invalid revision"


def test_diff_never_exposes_denied_files(repo: Path) -> None:
    import subprocess

    def git(*a: str) -> None:
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)

    git("init", "-q")
    git("-c", "user.email=t@t", "-c", "user.name=t", "add", "-f", ".")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
    nl = chr(10)
    (repo / ".env").write_text("AZURE_CLIENT_SECRET=rotated-secret" + nl, encoding="utf-8")
    (repo / "jobs" / "orders.py").write_text(JOB + "# change" + nl, encoding="utf-8")
    ts = TokenSave(repo)
    whole = ts.diff("HEAD")
    assert "rotated-secret" not in whole["diff"] and "# change" in whole["diff"]
    assert ts.diff("HEAD", ".env")["refused"]
    assert ts._filter_diff("diff --git a/.env b/.env" + nl + "+X=1" + nl) == ""
