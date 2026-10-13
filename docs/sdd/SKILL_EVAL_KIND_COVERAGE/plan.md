---
sdd: 1
feature: SKILL_EVAL_KIND_COVERAGE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/SKILL_EVAL_KIND_COVERAGE/design.md
  sha256: 1874328786508aa75d35e7abe67f3343fd47af6c9d5095badc1e99165a3127fe
tasks:
- id: T1
  files:
  - tests/test_skills.py
  covers:
  - AC1
  test:
    path: tests/test_skills.py
    name: test_every_skill_has_negative_and_boundary_evals
- id: T2
  files:
  - skills/analyze-batch-loop/evals/evals.yaml
  - skills/azure-bicep/evals/evals.yaml
  - skills/azure-finops/evals/evals.yaml
  - skills/azure-observability/evals/evals.yaml
  - skills/azure-purview/evals/evals.yaml
  - skills/azure-spark/evals/evals.yaml
  - skills/azure-terraform/evals/evals.yaml
  - skills/iceberg/evals/evals.yaml
  covers:
  - AC1
  - AC2
  test:
    path: tests/test_skills.py
    name: test_every_skill_has_statically_checkable_evals
---

# Plan — SKILL_EVAL_KIND_COVERAGE
