---
sdd: 1
feature: FABRIC_CORE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CORE/define.md
  sha256: "386b188589a8927341e3f18acd7310ad5d0f24760bea575d3b4901e120c10fdf"
files:
- path: sparkforge_azure/fabric/__init__.py
  action: create
  reason: pacote do vertical
- path: sparkforge_azure/fabric/extract.py
  action: create
  reason: artifacts→facts com boundary redaction
- path: sparkforge_azure/fabric/model.py
  action: create
  reason: domain contracts + IDs determinísticos
- path: sparkforge_azure/fabric/pipeline.py
  action: create
  reason: diagnose_fabric end-to-end
- path: rules/catalog/fabric.yaml
  action: create
  reason: SF-FAB-* catálogo
- path: sparkforge_azure/fabric/suite.py
  action: create
  reason: suite runner (espelha azure/suite)
decisions:
- id: D1
  choice: IDs oficiais (GUIDs REST) como identidade; displayName vira attr, nunca chave
  rejected:
  - name-based identity
  rollback: "reverter para chave por displayName nos extratores; ids sao triviais de trocar"
- id: D2
  choice: fabric/suite.py próprio reutilizando casefile.load_bundle
  rejected:
  - parametrizar azure/suite — acopla domínios
  rollback: "chamar a suite azure com mapping fabric->azure; dominios desacoplam"
- id: D3
  choice: sfa_diagnose_fabric como tool composicional única (não 1-por-API)
  rejected:
  - estender sfa_diagnose_access com flag — contracts divergentes
  rollback: "expander em tools granulares por endpoint; contrato unico removido"
covers:
  - {part: model+casefile+extract, acceptance: [AC1, AC2]}
  - {part: pipeline+diagnose, acceptance: [AC3, AC4]}
  - {part: cli-mcp, acceptance: [AC5]}
---

# Design — FABRIC_CORE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
