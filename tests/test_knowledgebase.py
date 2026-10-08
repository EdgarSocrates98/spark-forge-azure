"""Base de conhecimento Azure: contrato real de `knowledge/` + metadata + freshness."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from sparkforge_azure.knowledgebase import (
    DOMAINS,
    KnowledgeError,
    freshness,
    freshness_report,
    load_entries,
    load_matrices,
    load_rules,
    validate_front_matter,
    validate_targets,
)
from sparkforge_azure.knowledgebase.metadata import (
    read_front_matter_text,
    split_document,
)

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
TODAY = date(2026, 10, 6)

EXPECTED_IDS = {
    "azure.spark.execution-model",
    "azure.spark.performance-aqe-shuffle-skew",
    "azure.spark.streaming-state-checkpoint",
    "lakehouse.delta-lake",
    "lakehouse.iceberg",
    "lakehouse.open-table-formats",
    "azure.databricks.runtime-and-compute",
    "azure.databricks.workflows",
    "azure.unity-catalog.securable-model",
    "azure.unity-catalog.privileges-and-fgac",
    "azure.unity-catalog.troubleshooting-external-locations",
    "azure.fabric.data-engineering-spark",
    "azure.fabric.onelake-shortcuts",
    "azure.fabric.capacity-and-throttling",
    "azure.fabric.realtime-intelligence",
    "azure.fabric.data-factory",
    "azure.fabric.onelake-security",
    "azure.fabric.workspace-identity",
    "azure.synapse.spark-runtimes",
    "azure.synapse.pipelines-and-linked-services",
    "azure.adf.pipelines-ir-managed-vnet",
    "azure.adls.gen2",
    "azure.eventhubs.kafka-and-spark",
    "azure.purview.unified-catalog-and-lineage",
    "azure.entra.managed-identity",
    "azure.keyvault.secrets-and-rbac",
    "azure.network.private-link-dns",
    "azure.finops.cost-management-and-dbu",
    "azure.observability.monitor-log-analytics",
    "azure.iac.terraform-azurerm",
    "azure.iac.bicep",
    "governance.multi-layer-conflicts",
    "migration.synapse-to-fabric",
    "migration.aws-to-azure-concepts",
    "data-quality.contracts-and-expectations",
    "agentic.evidence-first",
    "spark.streaming.runtime-matrix",
}


def _doc(**overrides) -> dict:
    base = {
        "id": "azure.test.doc",
        "title": "Doc",
        "domain": "azure-adls",
        "authority": "microsoft_official",
        "sources": [{"url": "https://learn.microsoft.com/x", "retrieved": date(2026, 10, 6)}],
        "verified_at": date(2026, 10, 6),
        "versions": {},
        "status": "VERIFIED",
        "preview": False,
        "related": [],
    }
    base.update(overrides)
    return base


def _write(path: Path, front: str, body: str = "# corpo\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{front}---\n{body}", encoding="utf-8")
    return path


FRONT = """id: {id}
title: T
domain: azure-adls
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/x
    retrieved: {verified}
verified_at: {verified}
versions: {{}}
status: VERIFIED
preview: false
related: {related}
"""


def front(entry_id: str, related: str = "[]", verified: str = "2026-10-06") -> str:
    return FRONT.format(id=entry_id, related=related, verified=verified)


# --- arvore real -----------------------------------------------------------


class TestRealKnowledgeTree:
    def test_contract_passes(self):
        entries, errors = load_entries(KNOWLEDGE)
        assert errors == []
        assert {e.id for e in entries} == EXPECTED_IDS

    def test_every_doc_is_fresh_and_sourced(self):
        entries, _ = load_entries(KNOWLEDGE)
        report = freshness_report(entries, TODAY)
        assert report["not_fresh"] == []
        assert all(e.sources for e in entries)
        assert {e.domain for e in entries} <= DOMAINS

    def test_body_line_budget_and_fontes_section(self):
        entries, _ = load_entries(KNOWLEDGE)
        for entry in entries:
            text = (KNOWLEDGE / entry.path).read_text(encoding="utf-8")
            assert 60 <= len(text.splitlines()) <= 200, entry.path
            _, body = split_document(text, entry.path)
            assert "\n## Fontes\n" in body, entry.path
            for url in entry.source_urls:
                assert url in body, (entry.path, url)

    def test_matrices_are_sourced(self):
        matrices, errors = load_matrices(KNOWLEDGE / "matrices")
        assert errors == []
        assert set(matrices) == {
            "databricks-runtime",
            "fabric-runtime",
            "synapse-runtime",
            "eventhubs-tiers",
            "fabric-capacity-throttling",
        }
        assert matrices["databricks-runtime"].get("18 LTS", "spark").value == "4.1.0"
        assert matrices["databricks-runtime"].get("19", "spark").status == "CONFLICTED"
        assert matrices["fabric-runtime"].get("2.0", "spark").value == "4.1.1"

    def test_query_expansion_targets_resolve(self):
        entries, _ = load_entries(KNOWLEDGE)
        rules = load_rules(KNOWLEDGE / "query_expansion.yaml")
        assert len(rules) >= 40
        assert validate_targets(rules, (e.id for e in entries)) == []

    def test_check_script_green(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_knowledge.py"), "--today", "2026-10-06"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        summary = json.loads(proc.stdout)
        assert summary["ok"] is True
        assert summary["entries"] == len(EXPECTED_IDS)


# --- metadata --------------------------------------------------------------


class TestMetadata:
    def test_valid(self):
        entry, errors = validate_front_matter(_doc())
        assert errors == [] and entry is not None
        assert entry.verified_at == date(2026, 10, 6)

    @pytest.mark.parametrize(
        ("override", "fragment"),
        [
            ({"domain": "aws-glue"}, "domain"),
            ({"authority": "blog"}, "authority"),
            ({"status": "OK"}, "status"),
            ({"preview": "no"}, "preview"),
            ({"verified_at": "06/10/2026"}, "verified_at"),
            ({"id": "NoDots"}, "id invalido"),
            ({"sources": []}, "sources"),
            ({"sources": [{"url": "ftp://x", "retrieved": "2026-10-06"}]}, "url"),
            ({"versions": {"dbr": "18"}}, "versions"),
            ({"related": ["azure.test.doc"]}, "proprio id"),
        ],
    )
    def test_rejects(self, override, fragment):
        entry, errors = validate_front_matter(_doc(**override))
        assert entry is None
        assert any(fragment in e for e in errors), errors

    def test_missing_fields(self):
        data = _doc()
        del data["status"]
        entry, errors = validate_front_matter(data)
        assert entry is None and "status" in errors[0]

    def test_internal_allows_empty_sources(self):
        entry, errors = validate_front_matter(_doc(authority="internal", sources=[]))
        assert errors == [] and entry is not None and entry.sources == ()

    def test_bad_front_matter_rejected(self, tmp_path):
        _write(tmp_path / "a.md", "id: [unclosed\n")
        (tmp_path / "b.md").write_text("# sem front matter\n", encoding="utf-8")
        entries, errors = load_entries(tmp_path)
        assert entries == []
        assert any("YAML invalido" in e for e in errors)
        assert any("front matter ausente" in e for e in errors)

    def test_unresolved_related_rejected(self, tmp_path):
        _write(tmp_path / "a.md", front("azure.a.one", related="[azure.missing.doc]"))
        _, errors = load_entries(tmp_path)
        assert any("azure.missing.doc" in e and "nao resolve" in e for e in errors)

    def test_duplicate_ids_rejected(self, tmp_path):
        _write(tmp_path / "a.md", front("azure.a.one"))
        _write(tmp_path / "sub" / "b.md", front("azure.a.one"))
        _, errors = load_entries(tmp_path)
        assert any("duplicado" in e for e in errors)

    def test_index_md_is_not_an_entry(self, tmp_path):
        (tmp_path / "INDEX.md").write_text("# indice\n", encoding="utf-8")
        _write(tmp_path / "a.md", front("azure.a.one"))
        entries, errors = load_entries(tmp_path)
        assert errors == [] and [e.id for e in entries] == ["azure.a.one"]

    def test_front_matter_reader_stops_at_delimiter(self, tmp_path):
        path = tmp_path / "a.md"
        path.write_bytes(front("azure.a.one").join(["---\n", "---\n"]).encode() + b"\xff\xfe bad")
        assert "azure.a.one" in read_front_matter_text(path)

    def test_missing_root_is_error_not_crash(self, tmp_path):
        entries, errors = load_entries(tmp_path / "nope")
        assert entries == [] and "nao e diretorio" in errors[0]

    def test_unterminated_front_matter(self, tmp_path):
        (tmp_path / "a.md").write_text("---\nid: x\n", encoding="utf-8")
        with pytest.raises(KnowledgeError):
            read_front_matter_text(tmp_path / "a.md")


# --- freshness -------------------------------------------------------------


class TestFreshness:
    def _entry(self, **kw):
        entry, errors = validate_front_matter(_doc(**kw))
        assert errors == []
        return entry

    def test_verified_within_window(self):
        f = freshness(self._entry(), date(2027, 1, 4))
        assert f.state == "VERIFIED" and f.age_days == 90

    def test_stale_after_window(self):
        f = freshness(self._entry(), date(2027, 1, 5))
        assert f.state == "STALE" and f.age_days == 91

    def test_custom_max_age(self):
        assert freshness(self._entry(), date(2026, 10, 20), max_age_days=7).state == "STALE"

    @pytest.mark.parametrize("declared", ["DEPRECATED", "CONFLICTED", "UNRESOLVED"])
    def test_declared_status_honored(self, declared):
        assert freshness(self._entry(status=declared), TODAY).state == declared

    def test_declared_stale_honored(self):
        assert freshness(self._entry(status="STALE"), TODAY).state == "STALE"

    def test_no_sources_is_unresolved(self):
        entry = self._entry(authority="internal", sources=[])
        assert freshness(entry, TODAY).state == "UNRESOLVED"

    def test_future_verification_is_conflicted(self):
        assert freshness(self._entry(), date(2026, 10, 1)).state == "CONFLICTED"

    def test_report_is_deterministic(self):
        entries = [self._entry(id="azure.b.x"), self._entry(id="azure.a.x", status="DEPRECATED")]
        r1 = freshness_report(entries, TODAY)
        r2 = freshness_report(list(reversed(entries)), TODAY)
        assert r1 == r2
        assert r1["not_fresh"] == ["azure.a.x"]
        assert r1["counts"] == {"DEPRECATED": 1, "VERIFIED": 1}

    def test_negative_max_age_rejected(self):
        with pytest.raises(ValueError):
            freshness(self._entry(), TODAY, max_age_days=-1)
