---
sdd: 1
feature: JOB_VENDAS
phase: plan
profile: operator
status: done
upstream:
  path: docs/sdd/JOB_VENDAS/design.md
  sha256: 1d85c20d0c5225f47d639e206bfbc467a9d7d41ae4165087bdf3576667bceb10
tasks:
  - id: T1
    files: [jobs/vendas.py]
    covers: [AC1]
    test:
      path: tests/test_job_vendas.py
      name: test_vendas
---

# Plan
