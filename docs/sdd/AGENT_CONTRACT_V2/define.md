---
sdd: 1
feature: AGENT_CONTRACT_V2
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_CONTRACT_V2/explore.md
  sha256: 6e8b8292ddc6a72b685e75707bba9babb3cdc2e9c076674d6d443557611e3551
hypothesis:
  claim: O manifest v2 declara family/domain/mission/inputs/outputs/denied_tools/spawn/stop/handoffs/review_policy/evals
    com vocabulario fechado; toda a taxonomia migra preservando invariantes v1
  prediction: validator v2 rejeita manifest sem chaves novas; taxonomia ganha test-engineer e evaluation-specialist
  experiment: pytest tests/test_agent_contract_v2.py
acceptance:
- id: AC1
  statement: manifest v2 exige family, domain, mission, inputs, outputs, denied_tools, spawn.conditions,
    stop.conditions, review_policy, evals
  verified_by:
    kind: test
    ref: tests/test_agent_contract_v2.py::test_v2_required_keys
- id: AC2
  statement: family pertence ao vocabulario fechado dos planos
  verified_by:
    kind: test
    ref: tests/test_agent_contract_v2.py::test_family_closed_vocabulary
- id: AC3
  statement: 'denied_tools vence allowed: tool em ambos falha; pedido de tool fora da allow list falha'
  verified_by:
    kind: test
    ref: tests/test_agent_contract_v2.py::test_denied_tools_win
- id: AC4
  statement: spawn.conditions e stop.conditions usam vocabularios declarados
  verified_by:
    kind: test
    ref: tests/test_agent_contract_v2.py::test_spawn_stop_vocabularies
- id: AC5
  statement: 'invariantes v1 preservadas: handoff DATA_ONLY, sem cloud_write, sem handoff-para-si'
  verified_by:
    kind: test
    ref: tests/test_agent_contract_v2.py::test_v1_invariants_preserved
- id: AC6
  statement: test-engineer e evaluation-specialist entram na taxonomia com manifests completos
  verified_by:
    kind: test
    ref: tests/test_agent_contract_v2.py::test_test_eval_roles_in_taxonomy
success:
- id: SC1
  metric: feature verde offline com ACs cobertos
  source: pytest tests/test_agent_contract_v2.py
out_of_scope:
- o que nao esta na secao do prompt
unknowns: []
change_kinds:
- agent_or_skill
---

# Define — AGENT_CONTRACT_V2

Artefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.
