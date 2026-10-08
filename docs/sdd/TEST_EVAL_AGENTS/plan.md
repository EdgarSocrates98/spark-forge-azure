---
sdd: 1
feature: TEST_EVAL_AGENTS
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/TEST_EVAL_AGENTS/design.md
  sha256: d6c206bb6af3c889463d6ee9c3ab8203873a90b36a68fe049008f06e687a4cc3
tasks:
- id: T1
  files: &id001
  - agents/test-engineer.md
  - agents/evaluation-specialist.md
  - sparkforge_azure/agentmanifest/model.py
  - sparkforge_azure/agentic/evalplane.py
  - tests/test_agentic_test_eval.py
  covers:
  - AC1
  test:
    path: tests/test_agentic_test_eval.py
    name: test_new_roles_validate_v2
- id: T2
  files: *id001
  covers:
  - AC2
  test:
    path: tests/test_agentic_test_eval.py
    name: test_test_engineer_tool_policy
- id: T3
  files: *id001
  covers:
  - AC3
  test:
    path: tests/test_agentic_test_eval.py
    name: test_eval_specialist_context_policy
- id: T4
  files: *id001
  covers:
  - AC4
  test:
    path: tests/test_agentic_test_eval.py
    name: test_spawn_by_trigger_not_domain
---

# Plan — TEST_EVAL_AGENTS
