"""SDD ADF_FABRIC_DATA_FACTORY — per-pipeline dimensional verdicts:
unsupported activities block, LS→connection candidates, SHIR manual
review, no blind connection consolidation."""
from __future__ import annotations

from sparkforge_azure.migration import extract, pipelines


def _facts(activities, linked_services=None, irs=None,
           global_parameters=None):
    estate = {"adf_factories": [{
        "id": "adf-1", "name": "adf1",
        "pipelines": [{
            "id": "adf-1/pl/pl1", "name": "pl1",
            "activities": activities,
            "global_parameters": global_parameters or []}],
        "linked_services": linked_services or [],
        "integration_runtimes": irs or [],
    }]}
    return extract.extract_all({"estate": estate},
                               {"estate": "estate.json"})


def _dim(result, name):
    return next(d for d in result["dimensions"] if d["dimension"] == name)


def test_unsupported_activity_blocks():
    """AC1: ExecuteSSISPackage/Custom activity -> unsupported dimension."""
    facts = _facts([{"name": "run_ssis", "type": "ExecuteSSISPackage"}])
    res = pipelines.assess_pipelines(facts)[0]
    dim = _dim(res, "pipeline_activity")
    assert dim["status"] == "unsupported"
    assert dim["evidence"]


def test_global_params_and_linked_services_map():
    """AC2: global parameters -> variable_library candidate; linked
    service -> fabric_connection candidate (never equivalence)."""
    facts = _facts(
        [{"name": "copy1", "type": "Copy", "linked_service": "ls_sql"}],
        linked_services=[{"id": "adf-1/ls/ls_sql", "name": "ls_sql",
                          "type": "AzureSqlDatabase",
                          "auth_kind": "service_principal"}],
        global_parameters=[{"name": "env", "type": "string"}])
    res = pipelines.assess_pipelines(facts)[0]
    kinds = {r["kind"] for r in res["recommendations"]}
    assert "connection_candidate" in kinds
    assert "variable_library_candidate" in kinds
    rec = next(r for r in res["recommendations"]
               if r["kind"] == "connection_candidate")
    assert rec["target_type"] == "fabric_connection"
    assert rec["linked_service"] == "ls_sql"
    auth = _dim(res, "authentication")
    assert auth["status"] == "compatible_with_change"


def test_shir_is_manual_review():
    """AC3: self-hosted IR -> manual_refactor, never auto-mapped."""
    facts = _facts(
        [{"name": "copy_onprem", "type": "Copy",
          "integration_runtime": "shir1"}],
        irs=[{"id": "adf-1/ir/shir1", "name": "shir1",
              "kind": "SelfHosted", "nodes": 2}])
    res = pipelines.assess_pipelines(facts)[0]
    dim = _dim(res, "integration_runtime")
    assert dim["status"] == "manual_refactor"
    assert "gateway" in dim["detail"].lower()


def test_no_blind_connection_consolidation():
    """AC4: two pipelines sharing a linked service whose auth cannot map
    to one Fabric connection -> do_not_consolidate finding."""
    facts = _facts(
        [{"name": "c1", "type": "Copy", "linked_service": "ls_legacy"},
         {"name": "c2", "type": "Copy", "linked_service": "ls_legacy"}],
        linked_services=[{"id": "adf-1/ls/ls_legacy", "name": "ls_legacy",
                          "type": "SqlServer",
                          "auth_kind": "windows_auth"}])
    findings = pipelines.check_connection_sharing(facts)
    assert findings
    assert findings[0]["kind"] == "do_not_consolidate"
    assert len(findings[0]["consumers"]) == 2


def test_unknown_activity_is_unknown_not_compatible():
    facts = _facts([{"name": "exotic", "type": "NewFabricThing2077"}])
    res = pipelines.assess_pipelines(facts)[0]
    assert _dim(res, "pipeline_activity")["status"] == "unknown"
