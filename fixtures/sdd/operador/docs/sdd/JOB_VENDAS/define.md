---
sdd: 1
feature: JOB_VENDAS
phase: define
profile: operator
status: done
hypothesis:
  claim: a feature melhora o fluxo declarado
  prediction: o criterio de aceite passa no gate
  experiment: rodar o criterio verificado
acceptance:
  - id: AC1
    statement: o job de vendas roda
    verified_by:
      kind: command
      ref: job run --check
success:
  - id: SC1
    metric: criterio verificado pelo gate
    source: relatorio do `check` desta fixture
out_of_scope: []
change_kinds: []
case_id: case-2026-09-28-job
---

# Define
