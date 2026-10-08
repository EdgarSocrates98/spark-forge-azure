"""SDD MIGRATION_COMPATIBILITY — closed vocabulary, unresolved-first,
score never hides blockers, official-vs-Forge conflicts are REVIEW."""
from __future__ import annotations

from sparkforge_azure.migration import compat, extract
from sparkforge_azure.migration.model import COMPAT_STATUS, READINESS


def _assessment_facts(results):
    return extract.extract_assessment(
        {"tool": "fabric-migration-assistant", "assessed_at":
            "2026-09-15T00:00:00Z", "results": results},
        {"source": "assessment.json"})


def test_dimensions_closed_vocabulary():
    """AC1: every status emitted belongs to COMPAT_STATUS."""
    dims = [
        {"dimension": "pipeline_activity", "status": "compatible"},
        {"dimension": "connector", "status": "compatible_with_change"},
        {"dimension": "authentication", "status": "manual_refactor"},
    ]
    for d in dims:
        assert d["status"] in COMPAT_STATUS
    out = compat.assess_readiness([], dims)
    assert out["readiness"] in READINESS


def test_absence_is_unknown_not_compatible():
    """AC2: no dimension evidence -> UNRESOLVED, never READY."""
    out = compat.assess_readiness([], [])
    assert out["readiness"] == "UNRESOLVED"
    out2 = compat.assess_readiness(
        [], [{"dimension": "connector", "status": "unknown"}])
    assert out2["readiness"] == "UNRESOLVED"


def test_score_never_hides_blockers():
    """AC3: compatible_pct cannot mask unsupported/unknown dimensions."""
    dims = ([{"dimension": f"d{i}", "status": "compatible"}
             for i in range(9)]
            + [{"dimension": "dx", "status": "unsupported"}])
    score = compat.compat_score(dims)
    assert score["blockers"] == 1
    assert score["compatible_pct"] < 100
    assert compat.assess_readiness([], dims)["readiness"] == "BLOCKED"


def test_official_conflict_is_review():
    """AC4: official 'not compatible' vs Forge READY -> REVIEW + conflict,
    never a silent override."""
    facts = _assessment_facts([
        {"asset_id": "adf/pl_x", "official_status": "not compatible"}])
    dims = [{"dimension": "pipeline_activity", "status": "compatible"}]
    out = compat.assess_readiness(facts, dims, asset_key="adf/pl_x")
    assert out["readiness"] == "REVIEW"
    assert out["conflicts"]
    assert out["conflicts"][0]["official"] == "not compatible"
    assert out["conflicts"][0]["forge_internal"] == "READY"


def test_official_states_map_and_unknown_is_unresolved():
    assert compat.map_official("ready") == "READY"
    assert compat.map_official("Needs Review") == "REVIEW"
    assert compat.map_official("coming soon") == "DEFERRED"
    assert compat.map_official("not compatible") == "BLOCKED"
    assert compat.map_official("bogus-label") == "UNRESOLVED"
    assert compat.map_official(None) == "UNRESOLVED"


def test_stale_assessment_flagged():
    facts = _assessment_facts([
        {"asset_id": "a", "official_status": "ready"}])
    stale = extract.extract_assessment(
        {"tool": "t", "assessed_at": "2020-01-01T00:00:00Z",
         "results": [{"asset_id": "a", "official_status": "ready"}]},
        {"source": "assessment.json"})
    out = compat.assess_readiness(
        stale, [{"dimension": "x", "status": "compatible"}],
        asset_key="a")
    assert out["assessment_stale"] is True
    # fresh assessment does not flag
    out2 = compat.assess_readiness(
        facts, [{"dimension": "x", "status": "compatible"}],
        asset_key="a")
    assert out2["assessment_stale"] is False
