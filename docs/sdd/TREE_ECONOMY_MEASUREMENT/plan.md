---
sdd: 1
feature: TREE_ECONOMY_MEASUREMENT
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/TREE_ECONOMY_MEASUREMENT/design.md
  sha256: "a2370059bcf314ecd7a41b4444cd94571ec94413b42a94395668913a09d43f0c"
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
  - sparkforge_azure/codeintel/context.py
  - scripts/check_recall_economy.py
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_recall_economy_gate.py
    name: test_tree_gold_set_is_derived_and_nonempty
- id: T3
  files:
  - tests/test_codeintel_ranking.py
  covers: [AC4]
  test:
    path: tests/test_codeintel_ranking.py
    name: test_identificador_composto_com_stopword_casa_por_igualdade
---

# Plan — TREE_ECONOMY_MEASUREMENT

T1 contrato (3 testes de gate); T2 implementacao; T3 regressao de
escore (2 testes no ranking). Medicao final: **224/226** nominal,
4.28x contra arquivos, 32.52x contra grep. Os 2 misses sao nomeados e
honestos (`No` e stopword; `collect_live` ambiguo entre 4 collectors).
