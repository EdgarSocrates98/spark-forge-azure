"""Contract v2 tests (SDD AGENT_CONTRACT_V2): schema, vocabularies, invariants."""
from __future__ import annotations

import copy
from pathlib import Path

from sparkforge_azure.agentmanifest.model import (
    ADVERSARIAL_CHECKS,
    ALL_AGENT_IDS,
    FAMILIES,
    ROLE_IDS,
    SPAWN_CONDITIONS,
    STOP_CONDITIONS,
    load_manifests,
    validate_agents_tree,
    validate_manifest,
)
from sparkforge_azure.skills.model import split_front_matter

ROOT = Path(__file__).resolve().parents[1]
KNOWN = set(ALL_AGENT_IDS)


def _manifest(agent_id: str) -> tuple[dict, str]:
    _, data, body = split_front_matter(
        (ROOT / "agents" / f"{agent_id}.md").read_text("utf-8"))
    return copy.deepcopy(data), body


def _errs(agent_id: str, mutate) -> list[str]:
    data, body = _manifest(agent_id)
    mutate(data)
    return validate_manifest(data, body, where=agent_id, known_ids=KNOWN,
                             file_stem=agent_id).errors


def test_v2_required_keys() -> None:
    for key in ("family", "domain", "mission", "inputs", "outputs",
                "denied_tools", "spawn", "stop", "review_policy", "evals"):
        errs = _errs("judge", lambda d, k=key: d.pop(k))
        assert any("missing keys" in e for e in errs), key
    errs = _errs("judge", lambda d: d.update(schema_version=1))
    assert any("schema_version" in e for e in errs)


def test_family_closed_vocabulary() -> None:
    manifests = load_manifests(ROOT)
    for m in manifests:
        assert m.family in FAMILIES, m.id
        assert m.domain
    assert any("not in" in e for e in _errs("judge", lambda d: d.update(family="chaos")))
    # a role cannot be a domain agent; a specialist cannot be evidence-plane
    assert any("cannot have family" in e
               for e in _errs("judge", lambda d: d.update(family="domain")))
    assert any("cannot have family" in e
               for e in _errs("adls-specialist", lambda d: d.update(family="control")))


def test_denied_tools_win() -> None:
    errs = _errs("judge", lambda d: d["denied_tools"].append(d["allowed_tools"][0]))
    assert any("denied_tools wins" in e for e in errs)
    # denied entries still must be sfa_* names
    errs = _errs("judge", lambda d: d["denied_tools"].append("not_a_tool"))
    assert any("denied tool" in e for e in errs)


def test_spawn_stop_vocabularies() -> None:
    manifests = load_manifests(ROOT)
    for m in manifests:
        assert set(m.spawn.get("conditions", ())) <= set(SPAWN_CONDITIONS), m.id
        assert set(m.stop.get("conditions", ())) <= set(STOP_CONDITIONS), m.id
        assert isinstance(m.spawn.get("information_gain_threshold"), (int, float))
    assert any("unknown spawn conditions" in e
               for e in _errs("judge", lambda d: d["spawn"].update(conditions=["vibes"])))
    assert any("unknown stop conditions" in e
               for e in _errs("judge", lambda d: d["stop"].update(conditions=["vibes"])))
    assert any("information_gain_threshold" in e
               for e in _errs("judge", lambda d: d["spawn"].update(
                   information_gain_threshold=-1)))


def test_v1_invariants_preserved() -> None:
    manifests = load_manifests(ROOT)
    assert all(m.handoff_mode == "DATA_ONLY" for m in manifests)
    assert all(m.data["risk"] != "cloud_write" for m in manifests)
    for m in manifests:
        assert m.id not in m.handoff_targets, m.id
    # negative paths still refuse
    assert any("DATA_ONLY" in e
               for e in _errs("judge", lambda d: d["handoffs"].update(mode="INSTRUCTIONS")))
    assert any("itself" in e
               for e in _errs("judge", lambda d: d["handoffs"]["allowed_targets"].append("judge")))
    assert any("forbidden" in e
               for e in _errs("adls-specialist", lambda d: d.update(risk="cloud_write")))
    # review_policy vocabulary enforced
    for m in manifests:
        assert m.review_policy.get("adversarial_check") in ADVERSARIAL_CHECKS


def test_test_eval_roles_in_taxonomy() -> None:
    assert "test-engineer" in ROLE_IDS
    assert "evaluation-specialist" in ROLE_IDS
    by_id = {m.id: m for m in load_manifests(ROOT)}
    assert by_id["test-engineer"].family == "test_eval"
    assert by_id["evaluation-specialist"].family == "test_eval"
    assert by_id["test-engineer"].spawn["conditions"] == ["on_gate"]
    # and the whole tree validates clean
    assert validate_agents_tree(ROOT, allow_pending_knowledge=True).errors == []


def test_manifest_accessors_are_single_source() -> None:
    """autonomy.CallPolicy.from_manifest consumes these accessors."""
    by_id = {m.id: m for m in load_manifests(ROOT)}
    m = by_id["judge"]
    assert m.allowed_tools == m.data["allowed_tools"]
    assert m.denied_tools == m.data["denied_tools"]
    assert m.allowed_context_kinds == m.data["allowed_context_kinds"]
    assert m.handoff_targets == m.data["handoffs"]["allowed_targets"]
    assert m.handoff_mode == m.data["handoffs"]["mode"]
