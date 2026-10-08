---
sdd: 1
feature: BASE_AGENT_PIPELINE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/BASE_AGENT_PIPELINE/define.md
  sha256: 52814858b319f493c1a37d3f93c6c3eaac25ea5721e3f4e64d6b9c7de3d86a3b
files:
- path: sparkforge_azure/agentic/pipeline.py
  action: create
  reason: cadeia canonica + planner
- path: tests/test_agentic_pipeline.py
  action: create
  reason: contrato §30-32
decisions:
- id: D1
  choice: 'PipelineStage(agent_id|None, required: bool); specialist e slot preenchido
    pelo id roteado'
  rejected:
  - reusar ExecutionGraph (e grafo de evidencias)
  - decisao probabilistica (prompt pede deterministico)
  rollback: reverter o commit da feature
covers:
- part: base_pipeline
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — BASE_AGENT_PIPELINE
