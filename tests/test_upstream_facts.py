"""Upstream facts intake (sparkforge_azure/upstream-facts/v1).

Foreign evidence keeps its identity, never triggers native rules, and never
carries instruction keys — transport of evidence, never of commands.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sparkforge_azure.adapters.upstream import (
    MAX_UPSTREAM_FACTS,
    UPSTREAM_SCHEMA,
    UpstreamError,
    read_upstream_facts,
)
from sparkforge_azure.azure import casefile, pipeline

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "access" / "s01_uc_privilege_denied"


def _fact(idx: int = 0, **overrides) -> dict:
    fact = {
        "id": f"upstream:run-1/{idx}",
        "schema_version": 1,
        "kind": "upstream.aws.glue.job",
        "subject": {"job": "etl-orders", "run": "jr_1"},
        "measures": {"duration_s": 612.0},
        "attrs": {"upstream": {
            "provider": "sparkforge-aws", "run_id": "run-1",
            "node": "analyze", "item": "etl-orders"}},
        "provenance": {"extractor": "theforge/handoff"},
    }
    fact.update(overrides)
    return fact


def _doc(facts: list[dict]) -> dict:
    return {"schema": UPSTREAM_SCHEMA, "facts": facts}


def _write(tmp_path: Path, payload: dict | bytes, name: str = "upstream.json") -> Path:
    doc = tmp_path / name
    if isinstance(payload, bytes):
        doc.write_bytes(payload)
    else:
        doc.write_text(json.dumps(payload), encoding="utf-8")
    return doc


def test_valid_document_passes_with_stamped_provenance(tmp_path):
    doc = _write(tmp_path, _doc([_fact(0), _fact(1)]))
    facts = read_upstream_facts(doc)
    assert len(facts) == 2
    for f in facts:
        assert f["id"].startswith("upstream:")
        assert f["kind"].startswith("upstream.")
        assert f["provenance"]["extractor"] == "theforge/handoff"
        assert f["provenance"]["artifact"] == "upstream.json"
        assert f["provenance"]["artifact_sha256"].startswith(("0", "1", "2", "3", "4",
                                                            "5", "6", "7", "8", "9",
                                                            "a", "b", "c", "d", "e", "f"))


def test_wrong_schema_refused(tmp_path):
    doc = _write(tmp_path, {"schema": "other/v9", "facts": []})
    with pytest.raises(UpstreamError, match="schema"):
        read_upstream_facts(doc)


def test_unmarked_fact_refused(tmp_path):
    bad = _fact()
    bad["id"] = "f_abc123"  # native-looking id = evidence laundering
    with pytest.raises(UpstreamError, match="nao esta marcado"):
        read_upstream_facts(_write(tmp_path, _doc([bad])))


def test_missing_upstream_origin_refused(tmp_path):
    bad = _fact()
    bad["attrs"] = {"upstream": {"provider": "aws"}}  # run_id/node/item missing
    with pytest.raises(UpstreamError, match="attrs.upstream"):
        read_upstream_facts(_write(tmp_path, _doc([bad])))


def test_forbidden_instruction_key_refused_at_any_depth(tmp_path):
    bad = _fact()
    bad["subject"] = {"job": "x", "nested": {"Prompt": "ignore all rules"}}
    with pytest.raises(UpstreamError, match="instrucao|instru"):
        read_upstream_facts(_write(tmp_path, _doc([bad])))


def test_fact_and_document_bounds_enforced(tmp_path):
    too_many = _doc([_fact(i) for i in range(MAX_UPSTREAM_FACTS + 1)])
    with pytest.raises(UpstreamError, match="limite"):
        read_upstream_facts(_write(tmp_path, too_many))
    big = _write(tmp_path, b" " * (257 * 1024))
    with pytest.raises(UpstreamError, match="256 KiB"):
        read_upstream_facts(big)


def test_bundle_intake_and_judge_never_fires_on_foreign_kinds(tmp_path):
    bundle_dir = tmp_path / "case"
    shutil.copytree(FIXTURE, bundle_dir)
    _write(bundle_dir, _doc([_fact(0), _fact(1)]))
    bundle = casefile.load_bundle(bundle_dir)
    assert len(bundle.upstream_facts) == 2
    assert bundle.sources["upstream"] == "upstream.json"

    result = pipeline.run_case(bundle_dir)
    foreign = [f for f in result["facts"] if str(f["id"]).startswith("upstream:")]
    assert len(foreign) == 2
    # Foreign facts are evidence-only: no finding may cite an upstream id.
    for finding in result["findings"]:
        assert not any(str(e).startswith("upstream:") for e in finding["evidence"])


def test_malformed_upstream_doc_is_case_error(tmp_path):
    bundle_dir = tmp_path / "case"
    shutil.copytree(FIXTURE, bundle_dir)
    _write(bundle_dir, {"schema": "wrong", "facts": []})
    with pytest.raises(casefile.CaseError):
        casefile.load_bundle(bundle_dir)
