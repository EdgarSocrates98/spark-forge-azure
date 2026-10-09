---
sdd: 1
feature: AGENT_VALUE_EVAL
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_VALUE_EVAL/design.md
  sha256: 93bf85a4962b15f0894da917b93e806405bcb248f4d56f04aa3f9a2eedf71d55
tasks:
- id: T1
  files: [tests/test_agent_value_eval.py]
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_agent_value_eval.py
    name: test_value_vector_and_necessity
- id: T2
  files:
  - sparkforge_azure/agentic/agent_eval.py
  - evals/agent_runtime/cases/
  - evals/agent_runtime/expected/
  - evals/agent_runtime/reports/
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_agent_value_eval.py
    name: test_eval_result_format
---

# Plan — AGENT_VALUE_EVAL
