"""SDD DATA_ONELAKE — closed strategy vocabulary with evidence, shortcut
as candidate (never forced), retirement prefers copy, HMS split."""
from __future__ import annotations

from sparkforge_azure.migration import data, extract
from sparkforge_azure.migration.model import DATA_STRATEGIES


def _facts(retirement=False, paths=None, tables=None):
    estate = {
        "storage_accounts": [{
            "id": "sa-1", "name": "sa1", "kind": "StorageV2",
            "retirement": retirement,
            "adls_paths": paths if paths is not None else [
                {"path": "fs/delta_tbl", "format": "delta"},
                {"path": "fs/csv_dump", "format": "csv"}]}],
        "synapse_workspaces": [{
            "id": "syn-1", "name": "s1",
            "lake_databases": [{
                "id": "syn-1/ldb/db1", "name": "db1",
                "tables": tables if tables is not None else [
                    {"name": "t_m", "kind": "managed", "format": "delta"},
                    {"name": "t_e", "kind": "external", "format": "delta",
                     "location": "abfss://sa1/fs/e"}]}]}]}
    return extract.extract_all({"estate": estate},
                               {"estate": "estate.json"})


def test_strategy_closed_set_with_evidence():
    """AC1: every recommendation uses the closed strategy set + evidence."""
    recs = data.recommend_data_strategy(_facts())
    assert recs
    for r in recs:
        assert r["strategy"] in DATA_STRATEGIES
        assert r["evidence"], r
        assert r["explanation"]


def test_delta_shortcut_candidate_not_forced():
    """AC2: live Delta path is a *shortcut candidate* — a recommendation
    with reasons, not a mandate."""
    recs = data.recommend_data_strategy(_facts())
    delta = next(r for r in recs if r["asset"].endswith("fs/delta_tbl"))
    assert delta["strategy"] == "shortcut"
    assert delta["target_type"] == "fabric_shortcut"
    assert "nunca mandatorio" in delta["explanation"] or \
        "candidate" in delta["explanation"].lower() or \
        "elegivel" in delta["explanation"]


def test_retirement_prefers_copy():
    """AC3: source retirement -> copy beats shortcut."""
    recs = data.recommend_data_strategy(_facts(retirement=True))
    delta = next(r for r in recs if r["asset"].endswith("fs/delta_tbl"))
    assert delta["strategy"] == "copy"
    assert "retirement" in delta["explanation"]


def test_hms_managed_external_split():
    """AC4: managed vs external tables counted and evidenced separately."""
    hms = data.hms_assessment(_facts())
    assert hms["managed_tables"] == 1
    assert hms["external_tables"] == 1
    assert hms["managed_evidence"] and hms["external_evidence"]
    assert hms["managed_evidence"] != hms["external_evidence"]
