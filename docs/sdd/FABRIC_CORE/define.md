---
sdd: 1
feature: FABRIC_CORE
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CORE/explore.md
  sha256: "36ff9271ad2ec72d3c48f80faa790d75595835274d05126c338fb08fcc1b7284"
hypothesis:
  claim: Um modelo de domínio Fabric (tenant/capacity/workspace/item/lakehouse/shortcut/connection/workspace-identity) com fact kinds versionados e extractors determinísticos permite diagnosticar casos
    Fabric offline sem confundir hierarquia SaaS com ARM Azure
  prediction: bundles Fabric offline produzem facts tipados; subscription≠workspace e azure-account≠tenant nunca se fundem; failure layers fabric_* só quando evidence justificar
  experiment: pytest tests/test_fabric_extractors.py tests/test_fabric_pipeline.py
acceptance:
- id: AC1
  statement: fact kinds fabric.* e onelake.* versionados com provenance (source/mode/observed_at) e IDs determinísticos (nunca display name)
  verified_by:
    kind: test
    ref: tests/test_fabric_extractors.py::test_fabric_artifacts_become_facts
- id: AC2
  statement: modelo separa tenant/capacity/workspace/item/lakehouse sem forçar hierarquia ARM; azure subscription nunca vira workspace
  verified_by:
    kind: test
    ref: tests/test_fabric_extractors.py::test_saas_topology_not_arm
- id: AC3
  statement: pipeline artifacts→facts→graph→diagnose→rules→findings→failure_layer→receipt roda offline sobre bundle Fabric
  verified_by:
    kind: test
    ref: tests/test_fabric_pipeline.py::test_pipeline_end_to_end_offline
- id: AC4
  statement: format/runtime/scope sem evidence = unresolved, nunca assumido (Delta não presumido)
  verified_by:
    kind: test
    ref: tests/test_fabric_pipeline.py::test_unknown_never_assumed
- id: AC5
  statement: CLI `sparkforge-azure diagnose fabric --bundle|--suite` + MCP `sfa_diagnose_fabric` expõem a capability
  verified_by:
    kind: test
    ref: tests/test_fabric_cli.py::test_diagnose_fabric_cli_json_contract
success:
- id: SC1
  metric: pipeline Fabric verde offline; failure layer correto por caso; claims novos com prova
  source: pytest tests/test_fabric_*.py
out_of_scope:
- collectors live Fabric
- Data Factory deep
- capacity diagnosis
unknowns: []
change_kinds:
- extractor
- rule
- rule_area
- tool_or_verb
- fixture_corpus
---

# Define — FABRIC_CORE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
