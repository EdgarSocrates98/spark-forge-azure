---
sdd: 1
feature: DATABRICKS_UC_ADLS
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/DATABRICKS_UC_ADLS/design.md
  sha256: "fbba1d0b95e357610e8703ecbeccb1085ea3dfb3df789a51d02e4879d77589e0"
tasks:
  - id: T1
    files: [sparkforge_azure/azure/casefile.py, sparkforge_azure/azure/extract.py, fixtures/access/]
    covers: [AC1]
    test: {path: tests/test_access_extractors.py, name: test_uc_artifacts_become_facts}
  - id: T2
    files: [sparkforge_azure/facts/notebook_scan.py]
    covers: [AC2]
    test: {path: tests/test_access_extractors.py, name: test_notebook_scan_recognizes_uc_and_adls}
  - id: T3
    files: [sparkforge_azure/azure/pipeline.py, sparkforge_azure/azure/receipt.py, rules/catalog/azure_access.yaml]
    covers: [AC3, AC4]
    test: {path: tests/test_access_pipeline.py, name: test_pipeline_end_to_end_offline}
  - id: T4
    files: [sparkforge_azure/collectors/failure.py, sparkforge_azure/collectors/unity_catalog.py, sparkforge_azure/collectors/azure_rbac.py, sparkforge_azure/collectors/adls_meta.py]
    covers: [AC5]
    test: {path: tests/test_access_collectors.py, name: test_collector_failure_is_unresolved}
  - id: T5
    files: [sparkforge_azure/azure/extract.py]
    covers: [AC6]
    test: {path: tests/test_access_security.py, name: test_tainted_metadata_stays_data_only}
  - id: T6
    files: [sparkforge_azure/cli/cmd_diagnose.py, sparkforge_azure/cli/main.py, sparkforge_azure/mcp/access_tools.py, sparkforge_azure/mcp/tools.py]
    covers: [AC7]
    test: {path: tests/test_access_cli.py, name: test_diagnose_cli_json_contract}
---

# Plan — DATABRICKS_UC_ADLS
