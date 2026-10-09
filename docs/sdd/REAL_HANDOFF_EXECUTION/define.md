---
sdd: 1
feature: REAL_HANDOFF_EXECUTION
phase: define
profile: dev
status: done
hypothesis:
  claim: 'handoff conecta execucoes reais: cada estagio que completa emite
    AgentHandoff ao proximo; admit_handoff re-filtra pelo plano do receptor
    (§41); confused deputy nunca ganha privilegio (§42); resume por
    fingerprint nao re-roda agente inalterado (§46-47)'
  prediction: run_case com prior receipt pula estagios cujo fingerprint
    (manifest+contexto+runtime) nao mudou; handoff admission gravada no
    case state
  experiment: pytest tests/test_handoff_execution.py
acceptance:
- id: AC1
  statement: estagio completado emite AgentHandoff ao proximo; admission
    ALLOW/DENY gravada em case.state.handoffs com razao
  verified_by:
    kind: test
    ref: tests/test_handoff_execution.py::test_handoff_between_stages
- id: AC2
  statement: 'confused deputy: handoff de specialist pedindo acao
    privilegiada e admitido DATA_ONLY — authority nunca sobe (§42)'
  verified_by:
    kind: test
    ref: tests/test_handoff_execution.py::test_confused_deputy_denied
- id: AC3
  statement: 'resume: run_case(prior=receipt) nao re-executa estagio cujo
    fingerprint nao mudou; mudanca de contexto re-executa (§47)'
  verified_by:
    kind: test
    ref: tests/test_handoff_execution.py::test_resume_skips_unchanged
- id: AC4
  statement: 'fingerprint por estagio §48: agent+role plan+context+runtime;
    deterministico e muda com o contexto'
  verified_by:
    kind: test
    ref: tests/test_handoff_execution.py::test_stage_fingerprint
success:
- id: SC1
  metric: handoffs reais entre estagios com admission nomeada; resume
    deterministico
  source: pytest tests/test_handoff_execution.py
out_of_scope:
- blackboard transport (ja existe como storage)
- nested spawn (§208 desligado)
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — REAL_HANDOFF_EXECUTION
