---
sdd: 1
feature: IMPORTACAO
phase: define
profile: dev
status: done
hypothesis:
  claim: a feature melhora o fluxo declarado
  prediction: o criterio de aceite passa no gate
  experiment: rodar o criterio verificado
acceptance:
  - id: AC1
    statement: importa o lote
    verified_by:
      kind: command
      ref: pipeline run --check
success:
  - id: SC1
    metric: criterio verificado pelo gate
    source: relatorio do `check` desta fixture
out_of_scope: []
change_kinds: []
---

# Define
