---
sdd: 1
feature: AGENT_INVENTORY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_INVENTORY/explore.md
  sha256: df33ce9f869abf550c0100a665103bf776624d65a03ff2f51d7ca1e93bfe65c1
hypothesis:
  claim: Todo agent da taxonomia recebe status do conjunto fechado ready|partial|manifest_only|broken|unevaluated
    por regras deterministicas sobre manifest+role_plan+evals, sem LLM e sem rede
  prediction: agents list cobre 100% da taxonomia; status e funcao pura do estado do repo; doctor reporta
    contagens
  experiment: pytest tests/test_agentic_inventory.py
acceptance:
- id: AC1
  statement: todo agent da taxonomia recebe status do conjunto fechado ready|partial|manifest_only|broken|unevaluated
  verified_by:
    kind: test
    ref: tests/test_agentic_inventory.py::test_every_agent_has_closed_status
- id: AC2
  statement: 'status e deterministico: mesmo repo, mesmo resultado (sem relogio/rede)'
  verified_by:
    kind: test
    ref: tests/test_agentic_inventory.py::test_inventory_is_deterministic
- id: AC3
  statement: agents list e agents inspect <id> cobrem toda a taxonomia e sao read-only
  verified_by:
    kind: test
    ref: tests/test_agentic_inventory.py::test_cli_list_and_inspect_cover_taxonomy
- id: AC4
  statement: agent sem manifest/plano/eval nunca vira ready por default
  verified_by:
    kind: test
    ref: tests/test_agentic_inventory.py::test_missing_artifacts_never_ready
- id: AC5
  statement: doctor agentic_fleet reporta contagens por status sem falhar offline
  verified_by:
    kind: test
    ref: tests/test_agentic_inventory.py::test_doctor_agentic_fleet
success:
- id: SC1
  metric: feature verde offline com ACs cobertos
  source: pytest tests/test_agentic_inventory.py
out_of_scope:
- o que nao esta na secao do prompt
unknowns: []
change_kinds:
- agent_or_skill
- tool_or_verb
---

# Define — AGENT_INVENTORY

Artefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.
