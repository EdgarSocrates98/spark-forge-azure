---
sdd: 1
feature: JOB_VENDAS
phase: build_report
profile: operator
status: done
upstream:
  path: docs/sdd/JOB_VENDAS/plan.md
  sha256: be76f390000ec24cbf7b1e607f33ce4f9cb0c38c0cd52c435bc3049f852b124e
tasks:
  - id: T1
    status: done
    red:
      command: pytest tests/test_job_vendas.py::test_vendas
      exit: 1
    green:
      command: pytest tests/test_job_vendas.py::test_vendas
      exit: 0
claims:
  - text: feature concluida conforme o plan
    evidence_ref: tests/
---

# Build report
