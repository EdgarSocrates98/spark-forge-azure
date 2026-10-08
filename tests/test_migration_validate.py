"""SDD POST_MIGRATION_VALIDATION — independent dimensions, row-count
equality is not equivalence, perf regression is never a win, wrong
identity fails, no auto-promotion."""
from __future__ import annotations

from sparkforge_azure.migration import extract, validate


def _facts(results):
    return extract.extract_validation(
        {"results": results}, {"source": "validation.json"})


def test_rowcount_equal_metric_differs_fails():
    """AC1: row counts equal but schema differs -> data dim passes while
    schema dim fails; overall is fail.  Equality on one metric is never
    global equivalence."""
    facts = _facts([
        {"asset_id": "tbl1", "dimension": "data", "metric": "row_count",
         "source_value": 1000, "target_value": 1000},
        {"asset_id": "tbl1", "dimension": "schema", "metric": "columns",
         "source_value": "a,b,c", "target_value": "a,b"}])
    out = validate.validate_migration(facts)
    dims = {d["dimension"]: d for d in out["dimensions"]}
    assert dims["data"]["verdict"] == "pass"
    assert dims["schema"]["verdict"] == "fail"
    assert out["overall"] == "fail"


def test_perf_regression_never_win():
    """AC2: target slower than source beyond the band -> fail; never a
    success note."""
    facts = _facts([
        {"asset_id": "nb1", "dimension": "performance",
         "metric": "duration_s", "source_value": 100,
         "target_value": 400}])
    out = validate.validate_migration(facts)
    perf = next(d for d in out["dimensions"]
                if d["dimension"] == "performance")
    assert perf["verdict"] == "fail"
    assert out["overall"] == "fail"


def test_wrong_target_identity_fails():
    """AC3: security dim comparing identity/principal mismatch -> fail."""
    facts = _facts([
        {"asset_id": "pl1", "dimension": "security",
         "metric": "caller_principal",
         "source_value": "sp-source", "target_value": "sp-wrong"}])
    out = validate.validate_migration(facts)
    sec = next(d for d in out["dimensions"]
               if d["dimension"] == "security")
    assert sec["verdict"] == "fail"


def test_no_auto_promotion():
    """AC4: all-pass still requires the evidence bundle — the report
    declares auto_promotion=False and lists unmeasured dimensions."""
    facts = _facts([
        {"asset_id": "pl1", "dimension": "functional",
         "metric": "exit_code", "source_value": 0, "target_value": 0}])
    out = validate.validate_migration(facts)
    assert out["auto_promotion"] is False
    assert "security" in out["unmeasured_dimensions"]
    assert out["overall"] == "review"  # unmeasured dims keep it honest


def test_missing_side_is_unknown():
    facts = _facts([
        {"asset_id": "x", "dimension": "data", "metric": "row_count",
         "source_value": 5, "target_value": None}])
    out = validate.validate_migration(facts)
    assert out["dimensions"][0]["verdict"] == "unknown"
