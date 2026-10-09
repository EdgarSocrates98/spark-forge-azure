---
sdd: 1
feature: TREE_ECONOMY_MEASUREMENT
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/TREE_ECONOMY_MEASUREMENT/design.md
  sha256: "b949bf9d24586f2fb56db14266004badab219a41c8e28a86de5400ff16435a14"
tasks:
- id: T1
  files: [tests/test_recall_economy_gate.py]
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_recall_economy_gate.py
    name: test_tree_economy_is_measured
- id: T2
  files:
  - sparkforge_azure/economy/goldset.py
  - sparkforge_azure/economy/recall.py
  - sparkforge_azure/codeintel/ranking.py
  - scripts/check_recall_economy.py
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_recall_economy_gate.py
    name: test_tree_gold_set_is_derived_and_nonempty
---

# Plan — TREE_ECONOMY_MEASUREMENT

T1 contrato (3 testes de gate); T2 implementacao — a medicao ja esta
executada e medida: 223/225 nominal, 4.28x contra arquivos, 32.72x
contra grep. Os 2 misses sao nomeados e honestos (`No` e stopword;
`collect_live` ambiguo entre 4 collectors).
