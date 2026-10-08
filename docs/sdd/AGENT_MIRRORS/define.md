---
sdd: 1
feature: AGENT_MIRRORS
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_MIRRORS/explore.md
  sha256: 14417ef5e60726d45d91e2cfac17846c5731ec38b0c5f4437faa5d9e55d7f522
hypothesis:
  claim: Mirrors de agents gerados deterministicamente em .claude/agents/custom +
    .agents/agents com name prefixado e description=mission
  prediction: check_agent_mirrors detecta missing/stale/orphan igual ao de skills;
    check_skills_agents reporta agent_mirrors_in_sync
  experiment: pytest tests/test_agent_mirrors.py
acceptance:
- id: AC1
  statement: 'render deterministico: name sparkforge-azure-<id>, description=mission,
    header GENERATED, body preservado'
  verified_by:
    kind: test
    ref: tests/test_agent_mirrors.py::test_render_agent_mirror
- id: AC2
  statement: check_agent_mirrors detecta missing/stale/orphan e sync regenera
  verified_by:
    kind: test
    ref: tests/test_agent_mirrors.py::test_agent_mirror_drift_and_sync
- id: AC3
  statement: 'arvore real em sync: 40 mirrors por root'
  verified_by:
    kind: test
    ref: tests/test_agent_mirrors.py::test_real_tree_agent_mirrors_in_sync
- id: AC4
  statement: check_skills_agents reporta agent_mirrors_in_sync
  verified_by:
    kind: test
    ref: tests/test_agent_mirrors.py::test_check_script_reports_agent_mirrors
success:
- id: SC1
  metric: agent_mirrors_in_sync true no strict check
  source: python scripts/check_skills_agents.py --root . --strict
out_of_scope:
- mudar formato do manifest fonte
- registrar agents em host remoto
unknowns: []
change_kinds:
- agent_or_skill
- tool_or_verb
---

# Define — AGENT_MIRRORS
