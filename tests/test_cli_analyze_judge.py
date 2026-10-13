"""SDD SKILLS_AGENTS_HARDENING AC4 — verbos com motor existente na CLI.

``analyze pyspark`` → facts; ``judge`` → findings com rule_id + evidence;
``knowledge select`` → claims do pack. Tudo offline, JSON no stdout.
"""
from __future__ import annotations

import json
from pathlib import Path

from sparkforge_azure.cli.main import main

LOOP_JOB = """\
from pyspark.sql import functions as F
dates = [r["dt"] for r in spark.table("raw.events").select("dt").distinct().collect()]
for dt in dates:
    batch = spark.table("raw.events").filter(F.col("dt") == dt)
    batch.write.format("delta").mode("append").saveAsTable("silver.events")
"""


def _run(capsys, argv: list[str]) -> tuple[int, dict]:
    capsys.readouterr()
    code = main(argv)
    return code, json.loads(capsys.readouterr().out)


def test_ac4_analyze_judge_knowledge_roundtrip(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    job = tmp_path / "job.py"
    job.write_text(LOOP_JOB, encoding="utf-8")
    facts = tmp_path / "facts.json"

    code, out = _run(capsys, ["analyze", "pyspark", "--path", str(job), "--out", str(facts)])
    assert code == 0
    assert out["count"] == len(out["facts"]) > 0
    assert any(f["kind"] == "pyspark.loop" for f in out["facts"])
    assert json.loads(facts.read_text(encoding="utf-8"))["facts"] == out["facts"]

    code, out = _run(capsys, ["judge", "--facts", str(facts)])
    assert code == 1  # findings emitidos
    ids = {f["rule_id"] for f in out["findings"]}
    assert "SF-PY-004" in ids
    assert all(f["evidence"] for f in out["findings"])
    assert all("reason" in s for s in out["skipped"])

    code, out = _run(capsys, ["knowledge", "select", "--domain", "unity-catalog",
                              "--query", "USE SCHEMA", "--limit", "3"])
    assert code == 0
    assert 0 < len(out["claims"]) <= 3
    assert (tmp_path / "state" / "knowledge-cache").is_dir()  # cache fora de knowledge/


def test_ac4_refusals(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    code, out = _run(capsys, ["analyze", "pyspark", "--path", str(tmp_path / "nope.py")])
    assert code == 2 and out["status"] == "refused"
    bad = tmp_path / "facts.json"
    bad.write_text("{}", encoding="utf-8")
    code, out = _run(capsys, ["judge", "--facts", str(bad)])
    assert code == 2 and out["status"] == "refused"
    code, out = _run(capsys, ["knowledge", "select", "--domain", "nao-existe"])
    assert code == 2 and out["status"] == "refused"


def test_judge_accepts_collector_envelope(tmp_path: Path, capsys, monkeypatch) -> None:
    """`collect <kind> --facts` emite `fact_list`; judge lê o mesmo envelope."""
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    env = tmp_path / "collected.json"
    env.write_text(json.dumps({"fact_list": [
        {"kind": "pyspark.loop", "subject": {"path": "job.py", "line": 3},
         "attrs": {"contains_write": True}},
    ]}), encoding="utf-8")
    code, out = _run(capsys, ["judge", "--facts", str(env)])
    assert code == 1
    assert "SF-PY-004" in {f["rule_id"] for f in out["findings"]}
