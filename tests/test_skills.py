"""Skills system (sections 156-159): contract v1, evals, mirrors and deterministic selection."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest
import yaml

from sparkforge_azure.skills import mirrors
from sparkforge_azure.skills.model import (
    EVAL_KINDS,
    SKILL_NAMES,
    body_cli_refs,
    body_handoff_refs,
    parse_skill,
    validate_knowledge_ref,
    validate_skill_file,
    validate_skills_tree,
    validate_tool_ref,
)
from sparkforge_azure.skills.registry import load_skills, normalize, select_skills

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _all_knowledge_refs(root: Path) -> set[str]:
    refs: set[str] = set()
    for name in SKILL_NAMES:
        refs.update(parse_skill(root / "skills" / name / "SKILL.md").knowledge_refs)
    return refs


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A copy of the real skills tree with every referenced knowledge dir present."""
    shutil.copytree(ROOT / "skills", tmp_path / "skills")
    for ref in _all_knowledge_refs(ROOT):
        (tmp_path / ref).mkdir(parents=True, exist_ok=True)
    return tmp_path


def _edit_front(root: Path, name: str, mutate) -> Path:
    path = root / "skills" / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    _, raw, body = text.split("---", 2)
    data = yaml.safe_load(raw)
    mutate(data)
    new = "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True) + "---" + body
    path.write_text(new, encoding="utf-8")
    return path


def _edit_body(root: Path, name: str, mutate) -> Path:
    path = root / "skills" / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    _, raw, body = text.split("---", 2)
    path.write_text("---" + raw + "---" + mutate(body), encoding="utf-8")
    return path


def _errors(root: Path, name: str = "unity-catalog", **kw) -> list[str]:
    return validate_skill_file(root / "skills" / name / "SKILL.md", root, **kw).errors


# ------------------------------------------------------------------ real tree


def test_catalogue_has_exactly_23_skills():
    # 21 skills de domínio (seção 156) + `analyze-batch-loop`, a skill de método
    # que ancora a análise de lote no extrator pyspark (citada por SF-PY-004),
    # + `delegate-specialists`, a skill de método que ancora a delegação opcional
    # a data-sentinel-forge / forge-doctor-data sob fronteira LOCAL_READ.
    assert len(SKILL_NAMES) == 23 == len(set(SKILL_NAMES))
    found = sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
    assert found == sorted(SKILL_NAMES)


def test_real_tree_validates_with_pending_knowledge():
    rep = validate_skills_tree(ROOT, allow_pending_knowledge=True)
    assert rep.errors == []


def test_real_tree_validates_strict_when_knowledge_present():
    if not (ROOT / "knowledge" / "azure").is_dir():
        pytest.skip("knowledge/azure not written yet")
    rep = validate_skills_tree(ROOT)
    assert rep.errors == []


def test_skills_reference_doc_in_sync():
    # SKILLS_REFERENCE_DOC AC1+AC2: docs/reference/skills.md e gerado e nunca stale.
    script = _load_script("gen_skills_doc")
    doc = ROOT / "docs" / "reference" / "skills.md"
    assert doc.is_file(), "gere com: python scripts/gen_skills_doc.py"
    rendered = script.render(ROOT)
    assert doc.read_text(encoding="utf-8") == rendered, (
        "doc stale — rode python scripts/gen_skills_doc.py"
    )


def test_every_skill_has_negative_and_boundary_evals():
    # SKILL_EVAL_KIND_COVERAGE AC1: toda skill testa trigger negativo e fronteira.
    missing = {}
    for name in SKILL_NAMES:
        eval_path = ROOT / "skills" / name / "evals" / "evals.yaml"
        cases = yaml.safe_load(eval_path.read_text(encoding="utf-8"))["cases"]
        kinds = {c.get("kind", "positive") for c in cases}
        lack = {"negative", "boundary"} - kinds
        if lack:
            missing[name] = sorted(lack)
    assert missing == {}


def test_every_skill_has_statically_checkable_evals():
    for name in SKILL_NAMES:
        data = yaml.safe_load((ROOT / "skills" / name / "evals" / "evals.yaml").read_text("utf-8"))
        assert data["skill"] == name
        assert len(data["cases"]) >= 3
        for case in data["cases"]:
            assert {"id", "prompt", "must_include", "must_not_include",
                    "expected_tools"} <= set(case)
            assert set(case) <= {"id", "prompt", "must_include", "must_not_include",
                                 "expected_tools", "kind"}
            assert case.get("kind", "positive") in EVAL_KINDS


def test_skill_boundaries_are_explicit():
    fabric = parse_skill(ROOT / "skills" / "fabric-data-engineering" / "SKILL.md")
    assert any("Synapse" in d for d in fabric.metadata["does_not"])
    assert any("azure-data-factory" in d for d in fabric.metadata["does_not"])
    uc = parse_skill(ROOT / "skills" / "unity-catalog" / "SKILL.md")
    assert any("Lake Formation" in d for d in uc.metadata["does_not"])


def test_bodies_never_use_aws_cli_and_declare_used_verbs():
    for name in SKILL_NAMES:
        skill = parse_skill(ROOT / "skills" / name / "SKILL.md")
        # every body shows an executable step; which verb depends on the domain
        # (judge only fires on facts a real extractor emits — SKILLS_AGENTS_HARDENING)
        assert body_cli_refs(skill.body)
        assert set(body_cli_refs(skill.body)) <= set(skill.tool_refs)


# ------------------------------------------------------------------ ref validators


@pytest.mark.parametrize(
    "ref",
    ["knowledge/azure/unity-catalog/", "knowledge/spark/", "knowledge/governance/"],
)
def test_valid_knowledge_refs(ref):
    assert validate_knowledge_ref(ref) is None


@pytest.mark.parametrize(
    "ref",
    ["knowledge/spark/aqe.md", "docs/spark/", "knowledge/aws/", "knowledge/azure/glue/",
     "knowledge/azure/", "knowledge/../etc/"],
)
def test_invalid_knowledge_refs(ref):
    assert validate_knowledge_ref(ref) is not None


@pytest.mark.parametrize(
    "ref",
    ["sfa_governance_diagnose", "sparkforge-azure analyze pyspark", "sparkforge-azure judge",
     "sparkforge-azure graph impact", "sparkforge-azure collect workspace-graph",
     "sparkforge-azure offline-bundle", "sparkforge-azure agentops waste"],
)
def test_valid_tool_refs(ref):
    assert validate_tool_ref(ref) is None


@pytest.mark.parametrize(
    "ref",
    ["sparkforge analyze pyspark", "sparkforge_analyze", "sfa_Bad", "sparkforge-azure deploy",
     "sparkforge-azure graph destroy", "sparkforge-azure analyze", "sparkforge-azure judge x",
     "sparkforge-azure lab"],
)
def test_invalid_tool_refs(ref):
    assert validate_tool_ref(ref) is not None


# ------------------------------------------------------------------ negative rules


def test_tree_copy_is_valid_strict(tree):
    assert validate_skills_tree(tree).errors == []


def test_description_too_long(tree):
    _edit_front(tree, "unity-catalog", lambda d: d.update(description="x" * 601))
    assert any("max 600" in e for e in _errors(tree))


def test_contract_version(tree):
    _edit_front(tree, "unity-catalog",
                lambda d: d["metadata"].update(sparkforge_azure_contract="v0"))
    assert any("sparkforge_azure_contract" in e for e in _errors(tree))


@pytest.mark.parametrize("field", ["trigger", "scope", "does", "does_not", "source_authority"])
def test_required_list_field_empty(tree, field):
    _edit_front(tree, "unity-catalog", lambda d: d["metadata"].update({field: []}))
    assert any(f"metadata.{field}" in e for e in _errors(tree))


def test_unknown_metadata_key(tree):
    _edit_front(tree, "unity-catalog", lambda d: d["metadata"].update(extra=["x"]))
    assert any("unknown metadata keys" in e for e in _errors(tree))


def test_name_must_match_directory_and_catalogue(tree):
    _edit_front(tree, "unity-catalog", lambda d: d.update(name="lake-formation"))
    errs = _errors(tree)
    assert any("differs from directory" in e for e in errs)
    assert any("not in the skill catalogue" in e for e in errs)


def test_knowledge_ref_pending_vs_strict(tmp_path):
    shutil.copytree(ROOT / "skills", tmp_path / "skills")
    strict = _errors(tmp_path)
    assert any("does not exist" in e for e in strict)
    rep = validate_skill_file(tmp_path / "skills/unity-catalog/SKILL.md", tmp_path,
                              allow_pending_knowledge=True)
    assert rep.errors == []
    assert "knowledge/azure/unity-catalog/" in rep.pending_knowledge


def test_knowledge_ref_must_be_directory(tree):
    bad = ["knowledge/azure/unity-catalog/a.md"]
    _edit_front(tree, "unity-catalog", lambda d: d["metadata"].update(knowledge_refs=bad))
    assert any("directory path" in e for e in _errors(tree))


def test_tool_ref_aws_cli_rejected(tree):
    _edit_front(tree, "unity-catalog",
                lambda d: d["metadata"]["tool_refs"].append("sparkforge judge"))
    assert any("must be 'sfa_*'" in e for e in _errors(tree))


def test_unknown_source_authority(tree):
    _edit_front(tree, "unity-catalog",
                lambda d: d["metadata"].update(source_authority=["random_blog"]))
    assert any("unknown source_authority" in e for e in _errors(tree))


def test_eval_ref_required_and_existing(tree):
    _edit_front(tree, "unity-catalog",
                lambda d: d["metadata"].update(eval_refs=["skills/unity-catalog/evals/x.yaml"]))
    errs = _errors(tree)
    assert any("eval_refs must include" in e for e in errs)
    assert any("does not exist" in e for e in errs)


def test_body_too_short_and_missing_headings(tree):
    _edit_body(tree, "unity-catalog", lambda b: "\n# curto\n")
    errs = _errors(tree)
    assert any("body has" in e for e in errs)
    assert any("missing heading" in e for e in errs)


def test_body_cli_ref_must_be_declared(tree):
    _edit_body(tree, "unity-catalog", lambda b: b + "\nRode `sparkforge-azure lab run x`.\n")
    assert any("not declared in tool_refs" in e for e in _errors(tree))


def test_body_aws_cli_rejected(tree):
    _edit_body(tree, "unity-catalog", lambda b: b + "\nRode sparkforge analyze pyspark.\n")
    assert any("AWS CLI" in e for e in _errors(tree))


def test_handoff_targets_resolve():
    # AC1+AC2: todo alvo de `## Handoff` é uma skill ou um agent da taxonomia.
    from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS

    valid = set(SKILL_NAMES) | set(ALL_AGENT_IDS)
    bad = sorted(
        (name, target)
        for name in SKILL_NAMES
        for target in body_handoff_refs(parse_skill(ROOT / "skills" / name / "SKILL.md").body)
        if target not in valid
    )
    assert bad == []


def test_handoff_target_unknown_refused(tree):
    # AC3: alvo que não é skill nem agent é recusa nomeada do validador.
    _edit_body(
        tree,
        "unity-catalog",
        lambda b: b.replace("## Handoff\n", "## Handoff\n\n- `bogus-target` — inventado.\n"),
    )
    assert any("handoff target" in e and "bogus-target" in e for e in _errors(tree))


# ------------------------------------------------------------------ evals negatives


def _edit_evals(root: Path, mutate, name: str = "unity-catalog") -> None:
    path = root / "skills" / name / "evals" / "evals.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_evals_need_three_cases(tree):
    _edit_evals(tree, lambda d: d.update(cases=d["cases"][:2]))
    assert any("at least 3" in e for e in _errors(tree))


def test_evals_duplicate_id(tree):
    _edit_evals(tree, lambda d: d["cases"][1].update(id=d["cases"][0]["id"]))
    assert any("duplicate id" in e for e in _errors(tree))


def test_evals_missing_key(tree):
    _edit_evals(tree, lambda d: d["cases"][0].pop("expected_tools"))
    assert any("missing keys" in e for e in _errors(tree))


def test_evals_expected_tools_subset_of_tool_refs(tree):
    _edit_evals(tree, lambda d: d["cases"][0].update(expected_tools=["sfa_unknown"]))
    assert any("expected_tools not in skill tool_refs" in e for e in _errors(tree))


def test_evals_must_include_grounded(tree):
    _edit_evals(tree, lambda d: d["cases"][0].update(must_include=["termo inexistente xyz"]))
    assert any("not grounded" in e for e in _errors(tree))


def test_evals_include_exclude_overlap(tree):
    def mutate(d):
        d["cases"][0]["must_not_include"] = list(d["cases"][0]["must_include"])

    _edit_evals(tree, mutate)
    assert any("overlap" in e for e in _errors(tree))


def test_evals_skill_name_mismatch(tree):
    _edit_evals(tree, lambda d: d.update(skill="iceberg"))
    assert any("'skill' must be" in e for e in _errors(tree))


# ------------------------------------------------------------------ tree-level


def test_tree_missing_and_extra_skill(tree):
    shutil.rmtree(tree / "skills" / "iceberg")
    shutil.copytree(tree / "skills" / "delta-lake", tree / "skills" / "hudi")
    errs = validate_skills_tree(tree).errors
    assert any("missing ['iceberg']" in e for e in errs)
    assert any("unexpected ['hudi']" in e for e in errs)


# ------------------------------------------------------------------ mirrors


def test_real_mirrors_in_sync():
    assert mirrors.check_mirrors(ROOT) == []


def test_render_mirror_is_deterministic_and_prefixed():
    src = (ROOT / "skills" / "delta-lake" / "SKILL.md").read_text(encoding="utf-8")
    a = mirrors.render_mirror(src, "delta-lake")
    assert a == mirrors.render_mirror(src.replace("\n", "\r\n"), "delta-lake")
    assert "\nname: sparkforge-azure-delta-lake\n" in a
    assert "<!-- GENERATED from skills/delta-lake/SKILL.md; do not edit -->" in a
    head, _, rest = a.partition("\n---\n")
    assert rest.startswith("<!-- GENERATED")


def test_mirror_drift_detection_and_sync(tree):
    assert {d.reason for d in mirrors.check_mirrors(tree)} == {"missing"}
    mirrors.sync_mirrors(tree)
    assert mirrors.check_mirrors(tree) == []
    target = tree / ".claude/skills/sparkforge-azure-iceberg/SKILL.md"
    target.write_text(target.read_text(encoding="utf-8") + "edit\n", encoding="utf-8")
    orphan = tree / ".agents/skills/sparkforge-azure-old/SKILL.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("x", encoding="utf-8")
    foreign = tree / ".claude/skills/analyze-batch-loop/SKILL.md"  # AWS skill: untouched
    foreign.parent.mkdir(parents=True)
    foreign.write_text("aws", encoding="utf-8")
    reasons = {(d.path, d.reason) for d in mirrors.check_mirrors(tree)}
    assert (".claude/skills/sparkforge-azure-iceberg/SKILL.md", "stale") in reasons
    assert (".agents/skills/sparkforge-azure-old/SKILL.md", "orphan") in reasons
    script = _load_script("sync_skill_mirrors")
    assert script.main(["--check", "--root", str(tree)]) == 1
    assert script.main(["--root", str(tree)]) == 0
    assert script.main(["--check", "--root", str(tree)]) == 0
    assert not orphan.exists()
    assert foreign.read_text(encoding="utf-8") == "aws"


# ------------------------------------------------------------------ registry


def test_normalize_strips_accents_and_case():
    assert normalize("Migração DO  Synapse!") == " migracao do synapse "


def test_select_skills_is_deterministic_and_capped():
    skills = load_skills(ROOT)
    task = "PERMISSION_DENIED no Unity Catalog ao ler external location no ADLS (abfss)"
    first = select_skills(task, skills)
    assert first == select_skills(task, list(reversed(skills)))
    assert first[0].name == "unity-catalog"
    assert "azure-adls" in [m.name for m in first]
    assert len(select_skills(task, skills, max_skills=1)) == 1
    with pytest.raises(ValueError):
        select_skills(task, skills, max_skills=0)


def test_select_skills_separates_fabric_and_synapse():
    skills = load_skills(ROOT)
    fabric = [m.name for m in select_skills("notebook lento no Fabric Lakehouse", skills)]
    assert fabric[0] == "fabric-data-engineering"
    assert "azure-synapse" not in fabric
    synapse = [m.name for m in select_skills("Spark pool do Synapse em versão antiga", skills)]
    assert synapse[0] == "azure-synapse"


def test_select_skills_no_match():
    assert select_skills("receita de bolo de cenoura", load_skills(ROOT)) == []


def test_check_script_summary(tmp_path):
    script = _load_script("check_skills_agents")
    summary = script.run(ROOT, allow_pending_knowledge=True)
    assert summary["ok"], summary["errors"]
    assert summary["skills"] == 23
    assert summary["agents"] == {"roles": 16, "specialists": 20, "subagents": 4}
    assert script.main(["--root", str(tmp_path)]) == 1
