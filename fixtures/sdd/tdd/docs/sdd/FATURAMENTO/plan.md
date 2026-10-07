---
sdd: 1
feature: FATURAMENTO
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/FATURAMENTO/design.md
  sha256: 441016e381d4c98c13dc14a2b16eb1f985c76bdaefaca216664c2f2cf3c49e5e
tasks:
  - id: T1
    files: [src/faturador.py]
    covers: [AC1]
    test:
      path: tests/test_faturamento.py
      name: test_fatura
---

# Plan
