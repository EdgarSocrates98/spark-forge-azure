---
sdd: 1
feature: AGENT_DOD_GATE
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_DOD_GATE/explore.md
  sha256: 9d247dc0a1269118cdbd2e23ba29ee2d4115b1a446037d392894a76bf52b7286
hypothesis:
  claim: DoD verificavel por familia de agent + capability manifest gerado + gate
    de novo agent documentado
  prediction: test_agent_dod.py passa; CAPABILITY.json travado por sync; CONTRIBUTING
    lista o gate
  experiment: pytest tests/test_agent_dod.py
acceptance:
- id: AC1
  statement: todo agent tem os dims core satisfeitos (manifest, role_plan, tool_policy,
    budget, handoff, routing, evals, agentops)
  verified_by:
    kind: test
    ref: tests/test_agent_dod.py::test_core_dod_all_agents
- id: AC2
  statement: 'specialist DoD extra: evals/agents/<id>.yaml existe; reviewers/subagents
    nao entram na ROUTING_TABLE top-level'
  verified_by:
    kind: test
    ref: tests/test_agent_dod.py::test_role_specific_dod
- id: AC3
  statement: agents/CAPABILITY.json gerado deterministicamente e travado por sync
  verified_by:
    kind: test
    ref: tests/test_agent_dod.py::test_capability_manifest_in_sync
- id: AC4
  statement: CONTRIBUTING documenta o gate de novo agent
  verified_by:
    kind: test
    ref: tests/test_agent_dod.py::test_new_agent_gate_documented
success:
- id: SC1
  metric: frota 40/40 ready + capability manifest em sync
  source: pytest + check_skills_agents
out_of_scope:
- mudar semanticas de status
- novo papel
unknowns: []
change_kinds:
- agent_or_skill
- knowledge_doc
---

# Define — AGENT_DOD_GATE
