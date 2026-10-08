---
sdd: 1
feature: FABRIC_CORE
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CORE/plan.md
  sha256: "7f4f03a3e38247be0a51157488e167071fc798178ba52561f6cd0a4346eb6576"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_extractors.py tests/test_fabric_pipeline.py tests/test_fabric_cli.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_extractors.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_extractors.py tests/test_fabric_pipeline.py tests/test_fabric_cli.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_pipeline.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_extractors.py tests/test_fabric_pipeline.py tests/test_fabric_cli.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_cli.py -q", exit: 0}
claims:
  - text: "bundle offline vira facts fabric.* deterministicamente (id de fact estavel, provenance excluida da identidade)"
    evidence_ref: "tests/test_fabric_extractors.py::test_fabric_artifacts_become_facts"
  - text: "topologia SaaS (tenant/capacity/workspace/item) nunca fabrica ARM ids"
    evidence_ref: "tests/test_fabric_extractors.py::test_saas_topology_not_arm"
  - text: "pipeline offline bundle->facts->diagnosis->rules->findings->graph->evidence->receipt roda sem nuvem"
    evidence_ref: "tests/test_fabric_pipeline.py::test_pipeline_end_to_end_offline"
  - text: "evidencia ausente vira UNKNOWN/unresolved, nunca ALLOW inferido"
    evidence_ref: "tests/test_fabric_pipeline.py::test_unknown_never_assumed"
  - text: "sparkforge-azure diagnose fabric --bundle emite o contrato JSON estavel"
    evidence_ref: "tests/test_fabric_cli.py::test_diagnose_fabric_cli_json_contract"
  - text: "diagnose fabric --suite avalia 16 cenarios e reporta pass/fail por cenario"
    evidence_ref: "tests/test_fabric_cli.py::test_diagnose_fabric_suite"
  - text: "collector export+live-injetado redige via boundary compartilhado e classifica falhas"
    evidence_ref: "tests/test_fabric_collectors.py"
---

# Build Report — FABRIC_CORE

Red em worktree base `068b922` (pre-Fabric), green em `feat/cycle3-fabric-deep`. Detalhes no frontmatter.
