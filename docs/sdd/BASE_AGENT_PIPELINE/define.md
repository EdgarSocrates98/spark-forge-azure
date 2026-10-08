---
sdd: 1
feature: BASE_AGENT_PIPELINE
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/BASE_AGENT_PIPELINE/explore.md
  sha256: 728324e4060802027b6112c69bcbda36379c06665789bc0f5a7d8b17f53c95a3
hypothesis:
  claim: BASE_AGENT_PIPELINE declara os 11 estagios §30; plan_pipeline poda condicionais
    por contexto deterministicamente
  prediction: cadeia completa quando tudo necessario; Verifier->Synthesizer direto
    quando evidencia completa + low risk
  experiment: pytest tests/test_agentic_pipeline.py
acceptance:
- id: AC1
  statement: BASE_AGENT_PIPELINE tem os 11 estagios na ordem §30; required = coordinator/inventory/extractor/analyzer/judge/verifier/synthesizer
  verified_by:
    kind: test
    ref: tests/test_agentic_pipeline.py::test_base_pipeline_order
- id: AC2
  statement: plan_pipeline inclui condicionais so quando o contexto pede (specialist_domain,
    needs_review, has_conflict, needs_referee)
  verified_by:
    kind: test
    ref: tests/test_agentic_pipeline.py::test_conditional_branches
- id: AC3
  statement: 'fast-path §32: evidence completa + low risk poda specialist/reviewer/critic/referee'
  verified_by:
    kind: test
    ref: tests/test_agentic_pipeline.py::test_fast_path_skips_optionals
- id: AC4
  statement: todo estagio resolve para um agent real da taxonomia (specialist vira
    o id roteado)
  verified_by:
    kind: test
    ref: tests/test_agentic_pipeline.py::test_stages_resolve_to_real_agents
success:
- id: SC1
  metric: cadeia canonica importavel e deterministica
  source: pytest tests/test_agentic_pipeline.py
out_of_scope:
- executor real da pipeline
- paralelismo
unknowns: []
change_kinds:
- rule
- agent_or_skill
---

# Define — BASE_AGENT_PIPELINE
