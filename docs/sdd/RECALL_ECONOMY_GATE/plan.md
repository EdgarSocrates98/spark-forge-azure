---
sdd: 1
feature: RECALL_ECONOMY_GATE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/RECALL_ECONOMY_GATE/design.md
  sha256: 6f7611dfa5392205a556263fa0daf4ac0e5abcb4f6cd399f2b618561525af210
tasks:
- id: T1
  files: [tests/test_recall_economy_gate.py]
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_recall_economy_gate.py
    name: test_gold_set_derives_the_declared_floor
- id: T2
  files:
  - fixtures/pyspark/*/expected/facts.json
  - fixtures/pyspark/*/expected/findings.json
  - scripts/check_recall_economy.py
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_recall_economy_gate.py
    name: test_economy_is_measured_or_named_unresolved
---

# Plan — RECALL_ECONOMY_GATE

T1 contrato; T2 corpus + gate. O gate sai verde na primeira execucao porque o
estado medido e honesto (economia unresolved e o resultado correto para
corpus < envelope).
