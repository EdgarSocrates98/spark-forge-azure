"""Base de conhecimento: matrices, expansion, impact, loader e confinamento de caminho."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from sparkforge_azure.knowledgebase import (
    ExpansionError,
    KnowledgeBase,
    KnowledgeError,
    MatrixError,
    expand,
    impact,
    load_entries,
    load_matrices,
    parse_matrix,
    parse_rules,
    validate_matrix,
    validate_targets,
)
from sparkforge_azure.knowledgebase.metadata import KnowledgeEntry

ROOT = Path(__file__).resolve().parents[1]

FRONT = """---
id: {id}
title: {title}
domain: {domain}
authority: microsoft_official
sources:
  - url: {url}
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {{}}
status: VERIFIED
preview: false
related: {related}
---
"""


def doc(root: Path, rel: str, entry_id: str, *, title="T", domain="azure-adls",
        url="https://learn.microsoft.com/x", related="[]", body=b"# corpo\n") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    head = FRONT.format(id=entry_id, title=title, domain=domain, url=url, related=related)
    path.write_bytes(head.encode("utf-8") + body)
    return path


def cell(value="x", source="https://learn.microsoft.com/x", status="VERIFIED"):
    return {"value": value, "source": source, "status": status}


def matrix(**cells):
    return {
        "schema_version": 1,
        "matrix": "m",
        "verified_at": "2026-10-06",
        "rows": [{"key": "k", "values": cells or {"c": cell()}}],
    }


# --- matrices --------------------------------------------------------------


class TestMatrices:
    def test_valid(self):
        m = parse_matrix(matrix(spark=cell("4.1.0")))
        assert m.get("k", "spark").value == "4.1.0"

    def test_cell_without_source_rejected(self):
        bad = cell()
        del bad["source"]
        with pytest.raises(MatrixError) as exc:
            parse_matrix(matrix(spark=bad))
        assert any("source" in e for e in exc.value.errors)

    def test_cell_without_status_rejected(self):
        bad = cell()
        del bad["status"]
        assert any("status" in e for e in validate_matrix(matrix(spark=bad)))

    def test_bad_status_and_non_url(self):
        errors = validate_matrix(matrix(a=cell(status="MAYBE"), b=cell(source="see docs")))
        assert len(errors) == 2

    def test_duplicate_keys_and_schema(self):
        data = matrix()
        data["rows"].append(data["rows"][0])
        data["schema_version"] = 2
        errors = validate_matrix(data)
        assert any("duplicada" in e for e in errors) and any("schema_version" in e for e in errors)

    def test_preview_and_unverified_cells_allowed(self):
        assert validate_matrix(matrix(a=cell(status="PREVIEW"), b=cell(status="UNVERIFIED"))) == []

    def test_load_dir_collects_errors(self, tmp_path):
        (tmp_path / "ok.yaml").write_text(yaml.safe_dump(matrix()), encoding="utf-8")
        bad = matrix()
        bad["matrix"] = "bad"
        del bad["rows"][0]["values"]["c"]["source"]
        (tmp_path / "bad.yaml").write_text(yaml.safe_dump(bad), encoding="utf-8")
        matrices, errors = load_matrices(tmp_path)
        assert list(matrices) == ["m"] and errors


# --- expansion -------------------------------------------------------------

RULES = {
    "schema_version": 1,
    "terms": [
        {
            "term": "external location",
            "aliases": ["external locations"],
            "expands": ["storage credential", "access connector"],
            "targets": ["azure.uc.ext", "unity-catalog"],
        },
        {
            "term": "storage credential",
            "expands": ["managed identity"],
            "targets": ["azure.uc.cred"],
        },
        {"term": "adls", "expands": ["acl"], "targets": ["azure-adls"]},
    ],
}


class TestExpansion:
    def test_expand_and_hits(self):
        rules = parse_rules(RULES)
        exp = expand("Erro na External Location do lake", rules)
        assert exp.matched == ("external location",)
        assert exp.terms == ("external location", "storage credential", "access connector")
        assert exp.ids == ("azure.uc.ext",)
        assert exp.domains == ("unity-catalog",)

    def test_one_level_only(self):
        exp = expand("external location", parse_rules(RULES))
        assert "managed identity" not in exp.terms

    def test_deterministic_and_word_boundary(self):
        rules = parse_rules(RULES)
        a = expand(["adls", "external locations"], rules)
        b = expand(["adls", "external locations"], rules)
        assert a == b and a.matched == ("external location", "adls")
        assert expand("badlsx", rules).matched == ()

    def test_validate_targets(self):
        rules = parse_rules(RULES)
        errors = validate_targets(rules, ["azure.uc.ext"])
        assert errors == [
            "expansao 'storage credential': alvo 'azure.uc.cred' nao e id nem dominio"
        ]

    def test_invalid_rules(self):
        with pytest.raises(ExpansionError):
            parse_rules({"schema_version": 1, "terms": [{"term": "x", "targets": []}]})
        with pytest.raises(ExpansionError):
            parse_rules(
                {"schema_version": 1, "terms": [{"term": "x", "aliases": [403], "targets": ["a"]}]}
            )


# --- impact ----------------------------------------------------------------


def entry(entry_id, related=(), urls=("https://learn.microsoft.com/x",), path=None):
    from datetime import date

    from sparkforge_azure.knowledgebase.metadata import Source

    return KnowledgeEntry(
        id=entry_id, title="t", domain="azure-adls", authority="microsoft_official",
        sources=tuple(Source(u, date(2026, 10, 6)) for u in urls), verified_at=date(2026, 10, 6),
        versions={}, status="VERIFIED", preview=False, related=tuple(related),
        path=path or entry_id.replace(".", "/") + ".md",
    )


class TestImpact:
    def test_tolerates_empty_repo(self, tmp_path):
        report = impact(["azure.a.x"], [entry("azure.a.x")], tmp_path)
        assert report["dependents"] == [] and report["warnings"] == []

    def test_dependents_across_kinds(self, tmp_path):
        entries = [
            entry("azure.a.x", urls=("https://learn.microsoft.com/shared",), path="a/x.md"),
            entry("azure.b.y", related=["azure.a.x"]),
            entry("azure.c.z", related=["azure.b.y"]),
        ]
        (tmp_path / "rules" / "catalog").mkdir(parents=True)
        (tmp_path / "rules" / "catalog" / "r.yaml").write_text(
            yaml.safe_dump({"rules": [
                {"id": "SF-1", "knowledge_refs": ["azure.a.x"]},
                {"id": "SF-2", "sources": [{"url": "https://learn.microsoft.com/shared"}]},
                {"id": "SF-3", "sources": [{"url": "https://github.com/o/r/blob/main/knowledge/a/x.md"}]},
                {"id": "SF-4", "knowledge_refs": ["other"]},
            ]}),
            encoding="utf-8",
        )
        (tmp_path / "skills" / "s1").mkdir(parents=True)
        (tmp_path / "skills" / "s1" / "SKILL.md").write_text(
            "---\nname: s1\nmetadata:\n  knowledge_refs: [azure.a.x]\n---\nbody\n",
            encoding="utf-8",
        )
        (tmp_path / "agents").mkdir()
        (tmp_path / "agents" / "ag.md").write_text(
            "---\nname: ag\nknowledge_refs: azure.a.x\n---\n", encoding="utf-8")
        (tmp_path / "agents" / "broken.md").write_text("no front matter", encoding="utf-8")
        (tmp_path / "evals").mkdir()
        (tmp_path / "evals" / "e.yaml").write_text("refs: [azure.a.x]\n", encoding="utf-8")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "d.md").write_text("ver knowledge/a/x.md\n", encoding="utf-8")

        report = impact(["azure.a.x", "azure.nope.n"], entries, tmp_path)
        kinds = {(d["kind"], d["name"], d["via"]) for d in report["dependents"]}
        assert ("rule", "SF-1", "knowledge_refs") in kinds
        assert ("rule", "SF-2", "sources.url:shared") in kinds
        assert ("rule", "SF-3", "sources.url:path") in kinds
        assert not any(name == "SF-4" for _, name, _ in kinds)
        assert ("skill", "s1", "knowledge_refs") in kinds
        assert ("agent", "ag", "knowledge_refs") in kinds
        assert ("eval", "e", "mention:id") in kinds
        assert ("doc", "d", "mention:path") in kinds
        assert ("knowledge", "azure.b.y", "related") in kinds
        assert ("knowledge", "azure.c.z", "related") in kinds
        assert report["unknown_ids"] == ["azure.nope.n"]

    def test_non_transitive(self, tmp_path):
        entries = [entry("azure.a.x"), entry("azure.b.y", related=["azure.a.x"]),
                   entry("azure.c.z", related=["azure.b.y"])]
        report = impact(["azure.a.x"], entries, tmp_path, transitive=False)
        assert report["affected_knowledge"] == ["azure.a.x", "azure.b.y"]

    def test_unreadable_rule_is_warning(self, tmp_path):
        (tmp_path / "rules" / "catalog").mkdir(parents=True)
        (tmp_path / "rules" / "catalog" / "bad.yaml").write_text("a: [", encoding="utf-8")
        report = impact(["azure.a.x"], [entry("azure.a.x")], tmp_path)
        assert report["warnings"] and report["dependents"] == []


# --- loader ----------------------------------------------------------------


@pytest.fixture
def base(tmp_path):
    root = tmp_path / "kb"
    # corpo com UTF-8 invalido: so a leitura do corpo pode falhar
    doc(root, "uc/ext.md", "azure.uc.ext", title="External locations", domain="unity-catalog",
        body=b"# corpo\n\xff\xfe\xfa invalido\n")
    doc(root, "adls/gen2.md", "azure.adls.gen2", title="ADLS Gen2", related="[azure.uc.ext]")
    doc(root, "spark/perf.md", "azure.spark.perf", title="Skew", domain="spark-performance")
    (root / "query_expansion.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "terms": [{"term": "external location", "expands": ["adls"],
                   "targets": ["azure.uc.ext", "azure-adls"]}],
    }), encoding="utf-8")
    return root


class TestLoader:
    def test_index_reads_only_front_matter(self, base):
        kb = KnowledgeBase(base)
        index = kb.load_index()
        assert set(index) == {"azure.uc.ext", "azure.adls.gen2", "azure.spark.perf"}
        assert kb.errors == []
        with pytest.raises(KnowledgeError, match="UTF-8"):
            kb.load_body("azure.uc.ext")

    def test_select_never_reads_bodies(self, base, monkeypatch):
        kb = KnowledgeBase(base)
        kb.load_index()
        kb.rules()  # o mapa de expansao e metadado, carregado uma vez

        def boom(*_a, **_k):
            raise AssertionError("corpo lido durante select")

        monkeypatch.setattr(Path, "read_text", boom)
        ids = kb.select("falha na external location", limit=2)
        assert ids == ["azure.uc.ext", "azure.adls.gen2"]

    def test_select_domain_filter_and_limit(self, base):
        kb = KnowledgeBase(base)
        assert kb.select("skew", domains=["spark-performance"]) == ["azure.spark.perf"]
        assert kb.select("anything", limit=0) == []

    def test_load_body_one_doc(self, base):
        body = KnowledgeBase(base).load_body("azure.adls.gen2")
        assert body.startswith("# corpo")
        with pytest.raises(KnowledgeError):
            KnowledgeBase(base).load_body("azure.missing.id")


# --- confinamento de caminho ------------------------------------------------


class TestPathConfinement:
    def test_entry_path_escape_refused(self, base, tmp_path):
        outside = tmp_path / "outside.md"
        doc(tmp_path, "outside.md", "azure.out.side")
        kb = KnowledgeBase(base)
        index = kb.load_index()
        evil = entry("azure.evil.one", path="../outside.md")
        index["azure.evil.one"] = evil
        assert outside.exists()
        with pytest.raises(KnowledgeError, match="fora da base"):
            kb.load_body("azure.evil.one")

    def test_root_must_be_directory(self, tmp_path):
        with pytest.raises(KnowledgeError):
            KnowledgeBase(tmp_path / "missing")

    def test_symlink_escape_refused(self, base, tmp_path):
        target = doc(tmp_path / "secret", "s.md", "azure.sec.ret")
        link = base / "linked.md"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            pytest.skip("symlink nao suportado neste ambiente")
        entries, errors = load_entries(base)
        assert "azure.sec.ret" not in {e.id for e in entries}
        assert any("escapa" in e for e in errors)

    def test_check_script_invalid_root_exits_2(self, tmp_path):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_knowledge.py"),
             "--root", str(tmp_path / "nope")],
            capture_output=True, text=True, check=False,
        )
        assert proc.returncode == 2

    def test_check_script_violation_exits_1(self, base):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_knowledge.py"), "--root", str(base)],
            capture_output=True, text=True, check=False,
        )
        assert proc.returncode == 1  # sem INDEX.md e sem matrizes -> violacao
        assert "INDEX.md" in proc.stdout
