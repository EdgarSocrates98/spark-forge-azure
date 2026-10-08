---
sdd: 1
feature: AGENTOPS_AGENT
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENTOPS_AGENT/explore.md
  sha256: 556c64dd939f695908ecdbb0922af33da5ba6da61e777f5647b960c87a5c2055
hypothesis:
  claim: Cada execucao de agent emite AgentSpan com campos §56 (tokens None=unresolved nunca estimado
    de chars); cada case emite AgentExecutionReceipt com considered/spawned/skipped/reasons/budgets/stop
  prediction: waste detector marca agent spawnado sem ganho; receipt lista skipped com reason
  experiment: pytest tests/test_agentic_spans.py
acceptance:
- id: AC1
  statement: AgentSpan carrega agent_id/family/case_id/spawn_reason/context/tokens/cost/stop_reason; tokens
    desconhecidos sao None, nunca 0 nem estimativa de chars
  verified_by:
    kind: test
    ref: tests/test_agentic_spans.py::test_agent_span_fields_and_unknown_tokens
- id: AC2
  statement: AgentExecutionReceipt lista agents considered/spawned/skipped com reasons, handoffs, budgets,
    stop reason
  verified_by:
    kind: test
    ref: tests/test_agentic_spans.py::test_execution_receipt_shape
- id: AC3
  statement: 'waste detector: spawned sem facts/findings/unresolved_resolved e sem decision_changed ->
    waste'
  verified_by:
    kind: test
    ref: tests/test_agentic_spans.py::test_waste_detector
- id: AC4
  statement: agentops report agrega value vector por agent sem score magico
  verified_by:
    kind: test
    ref: tests/test_agentic_spans.py::test_agentops_report_value_vector
success:
- id: SC1
  metric: feature verde offline com ACs cobertos
  source: pytest tests/test_agentic_spans.py
out_of_scope:
- o que nao esta na secao do prompt
unknowns: []
change_kinds:
- agent_or_skill
- tool_or_verb
---

# Define — AGENTOPS_AGENT

Artefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.
