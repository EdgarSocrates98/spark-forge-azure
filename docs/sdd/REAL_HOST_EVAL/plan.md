---
sdd: 1
feature: REAL_HOST_EVAL
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/REAL_HOST_EVAL/design.md
  sha256: bdecde7f89f81c2fb702b6aafb6d2d3d761203beec066bd21c15b27a78dc9f94
tasks:
- id: T1
  files:
  - tests/test_host_eval.py
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_host_eval.py
    name: test_host_eval_report_shape
- id: T2
  files:
  - sparkforge_azure/agentic/agent_eval.py
  - scripts/run_agent_host_eval.py
  - sparkforge_azure/agentic/freeze.py
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_host_eval.py
    name: test_host_eval_quality_vector
- id: T3
  files:
  - evals/agent_runtime/reports/*.host.json
  covers: [AC2]
  test:
    path: tests/test_host_eval.py
    name: test_host_reports_measured_usage
---

# Plan — REAL_HOST_EVAL

T1 RED: shape/metricas sem chamar host (dry-run do contrato). T2:
`evaluate_case_host` + runner + condicao de freeze. T3: rodada real —
4 spawns via claude_code com opt-in explicito, reports gravados.
