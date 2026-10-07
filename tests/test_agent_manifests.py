"""Agent / specialist manifests (sections 94-99) and coordinator routing (sections 97/107)."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

from sparkforge_azure.agentmanifest import routing
from sparkforge_azure.agentmanifest.model import (
    ALL_AGENT_IDS,
    ROLE_IDS,
    SPECIALIST_IDS,
    SUBAGENT_IDS,
    load_manifests,
    parse_manifest,
    validate_agents_tree,
    validate_manifest,
)
from sparkforge_azure.skills.model import split_front_matter

ROOT = Path(__file__).resolve().parents[1]
KNOWN = set(ALL_AGENT_IDS)


def _manifest(agent_id: str) -> tuple[dict, str]:
    _, data, body = split_front_matter((ROOT / "agents" / f"{agent_id}.md").read_text("utf-8"))
    return copy.deepcopy(data), body


def _errs(agent_id: str, mutate=None, body_mutate=None) -> list[str]:
    data, body = _manifest(agent_id)
    if mutate:
        mutate(data)
    if body_mutate:
        body = body_mutate(body)
    return validate_manifest(data, body, where=agent_id, known_ids=KNOWN,
                             file_stem=agent_id).errors


# ------------------------------------------------------------------ real tree


def test_taxonomy_counts():
    assert len(ROLE_IDS) == 14
    assert len(SPECIALIST_IDS) == 20
    assert len(SUBAGENT_IDS) == 4
    assert len(set(ALL_AGENT_IDS)) == 38
    found = sorted(p.stem for p in (ROOT / "agents").glob("*.md"))
    assert found == sorted(ALL_AGENT_IDS)


def test_real_tree_validates_with_pending_knowledge():
    assert validate_agents_tree(ROOT, allow_pending_knowledge=True).errors == []


def test_real_tree_validates_strict_when_knowledge_present():
    if not (ROOT / "knowledge" / "azure").is_dir():
        pytest.skip("knowledge/azure not written yet")
    assert validate_agents_tree(ROOT).errors == []


def test_manifest_semantics():
    by_id = {m.id: m for m in load_manifests(ROOT)}
    assert all(m.data["handoff_mode"] == "DATA_ONLY" for m in by_id.values())
    assert all(m.data["risk"] != "cloud_write" for m in by_id.values())
    for sid in SUBAGENT_IDS:
        assert by_id[sid].data["parent"] == "azure-databricks-specialist"
    assert set(by_id["synthesizer"].data["allowed_context"]) <= {"finding", "evidence",
                                                                  "unresolved"}
    assert by_id["coordinator"].data["skills"] == []
    assert by_id["extractor"].data["required_context"] == ["artifact"]
    assert set(by_id["judge"].data["required_context"]) == {"fact", "rule"}


# ------------------------------------------------------------------ negative rules


@pytest.mark.parametrize("risk", ["cloud_write"])
def test_cloud_write_forbidden(risk):
    assert any("forbidden" in e for e in _errs("adls-specialist", lambda d: d.update(risk=risk)))


def test_unknown_risk():
    assert any("not in" in e for e in _errs("adls-specialist", lambda d: d.update(risk="root")))


@pytest.mark.parametrize("value", [0, -1, True, "8"])
def test_budget_must_be_positive_int(value):
    errs = _errs("judge", lambda d: d["budget"].update(max_tool_calls=value))
    assert any("budget.max_tool_calls" in e for e in errs)


def test_budget_tier_keys_and_ceiling():
    assert any("model_tier" in e
               for e in _errs("judge", lambda d: d["budget"].update(model_tier="ultra")))
    assert any("exactly" in e for e in _errs("judge", lambda d: d["budget"].pop("max_model_calls")))
    assert any("exceeds" in e
               for e in _errs("judge", lambda d: d["budget"].update(max_context_tokens=10**6)))


def test_handoff_targets_must_resolve():
    errs = _errs("judge", lambda d: d["handoff_targets"].append("lake-formation-specialist"))
    assert any("does not resolve" in e for e in errs)
    errs = _errs("judge", lambda d: d["handoff_targets"].append("judge"))
    assert any("itself" in e for e in errs)


def test_handoff_mode_data_only():
    errs = _errs("judge", lambda d: d.update(handoff_mode="INSTRUCTIONS"))
    assert any("DATA_ONLY" in e for e in errs)


def test_subagent_requires_specialist_parent():
    sid = "databricks-uc-reviewer"
    assert any("must declare a parent" in e for e in _errs(sid, lambda d: d.update(parent=None)))
    assert any("existing specialist" in e for e in _errs(sid, lambda d: d.update(parent="judge")))
    errs = _errs(sid, lambda d: d.update(parent="fabric-specialist"))
    assert any("parent must be" in e for e in errs)


def test_only_subagents_have_parent():
    errs = _errs("delta-specialist", lambda d: d.update(parent="azure-databricks-specialist"))
    assert any("only subagents" in e for e in errs)


def test_allowed_context_superset_of_required():
    errs = _errs("judge", lambda d: d.update(allowed_context=["fact"]))
    assert any("must include required_context" in e for e in errs)
    errs = _errs("judge", lambda d: d["allowed_context"].append("vibes"))
    assert any("unknown context kinds" in e for e in errs)


def test_synthesizer_only_verified_inputs():
    errs = _errs("synthesizer", lambda d: d["allowed_context"].append("code"))
    assert any("synthesizer may only use" in e for e in errs)


def test_coordinator_never_replaces_specialist():
    errs = _errs("coordinator", lambda d: d.update(skills=["unity-catalog"]))
    assert any("never replaces" in e for e in errs)
    errs = _errs("coordinator", body_mutate=lambda b: b.replace("`iceberg-specialist`", "`x`"))
    assert any("routing table does not mention" in e for e in errs)


def test_unknown_skill_and_tool_names():
    assert any("unknown skill" in e
               for e in _errs("delta-specialist", lambda d: d["skills"].append("hudi")))
    assert any("'sfa_*'" in e
               for e in _errs("delta-specialist", lambda d: d["tools"].append("sparkforge_judge")))


def test_specialist_needs_skill():
    assert any("at least one skill" in e
               for e in _errs("delta-specialist", lambda d: d.update(skills=[])))


def test_kind_and_id_rules():
    assert any("must have kind" in e for e in _errs("judge", lambda d: d.update(kind="specialist")))
    assert any("not in the agent taxonomy" in e
               for e in _errs("judge", lambda d: d.update(id="oracle")))
    assert any("differs from file name" in e
               for e in _errs("judge", lambda d: d.update(id="verifier")))


def test_missing_and_unknown_keys():
    assert any("missing keys" in e for e in _errs("judge", lambda d: d.pop("trust_floor")))
    assert any("unknown keys" in e for e in _errs("judge", lambda d: d.update(model="gpt")))
    assert any("trust_floor" in e for e in _errs("judge", lambda d: d.update(trust_floor="MAYBE")))


def test_body_length_bounds():
    assert any("body has" in e for e in _errs("judge", body_mutate=lambda b: "# x\n"))
    assert any("body has" in e for e in _errs("judge", body_mutate=lambda b: b + "x\n" * 60))


def test_knowledge_ref_strict_vs_pending(tmp_path):
    shutil.copytree(ROOT / "agents", tmp_path / "agents")
    strict = validate_agents_tree(tmp_path)
    assert any("does not exist" in e for e in strict.errors)
    pending = validate_agents_tree(tmp_path, allow_pending_knowledge=True)
    assert pending.errors == []
    assert "knowledge/agentic/" in pending.pending_knowledge


def test_tree_missing_and_extra_agent(tmp_path):
    shutil.copytree(ROOT / "agents", tmp_path / "agents")
    (tmp_path / "agents" / "critic.md").unlink()
    shutil.copy(tmp_path / "agents" / "judge.md", tmp_path / "agents" / "oracle.md")
    errs = validate_agents_tree(tmp_path, allow_pending_knowledge=True).errors
    assert any("missing ['critic']" in e for e in errs)
    assert any("unexpected ['oracle']" in e for e in errs)
    # critic is a role name, so handoffs to it still resolve; no cascading errors
    assert not any("does not resolve" in e for e in errs)


# ------------------------------------------------------------------ routing


def test_routing_table_matches_specialists_and_coordinator_body():
    assert tuple(r.specialist for r in routing.ROUTING_TABLE) == SPECIALIST_IDS
    body = parse_manifest(ROOT / "agents" / "coordinator.md").body
    assert routing.render_routing_table() in body


def test_route_minimal_and_ordered():
    q = "PERMISSION_DENIED no Unity Catalog lendo ADLS via abfss atrás de private endpoint"
    assert routing.route(q) == [
        "unity-catalog-specialist", "adls-specialist", "networking-specialist"
    ]


def test_route_is_deterministic():
    terms = ["delta merge lento", "skew no shuffle", "custo dbu"]
    a = routing.route(terms, max_agents=5)
    assert a == routing.route(list(reversed(terms)), max_agents=5)
    assert a == routing.route(terms, max_agents=5)
    assert set(a) == {"delta-specialist", "spark-performance-specialist", "finops-specialist"}


def test_route_cap_and_bounds():
    everything = " ".join(t for r in routing.ROUTING_TABLE for t in r.terms)
    assert len(routing.route(everything)) == routing.DEFAULT_MAX_AGENTS
    assert len(routing.route(everything, max_agents=5)) == 5
    for bad in (0, 6):
        with pytest.raises(ValueError):
            routing.route("delta", max_agents=bad)


def test_route_longest_match_masks_shorter():
    assert routing.route("pipeline do Fabric Data Factory falhando") == ["fabric-specialist"]
    assert routing.route("pipeline do Azure Data Factory falhando") == ["adf-specialist"]
    assert routing.route("event hubs partition count") == ["event-hubs-specialist"]


def test_route_no_match_returns_empty():
    assert routing.route("receita de bolo") == []


def test_route_targets_are_manifests():
    by_id = {m.id for m in load_manifests(ROOT)}
    assert {r.specialist for r in routing.ROUTING_TABLE} <= by_id
