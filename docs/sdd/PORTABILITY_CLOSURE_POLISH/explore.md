---
sdd: 1
feature: PORTABILITY_CLOSURE_POLISH
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: "Reconciliação evidence-first: `gen_current_state.py` deriva o
      estado medido (SHA, claims, contagens, freeze, matriz de evals); paridade
      recomputada dos `origin/main` atuais de AWS/api-forge; outcome ganha
      seção pós-closure preservando o snapshot; gates estendidos, não
      multiplicados"
    tradeoffs:
      - nenhum doc manual novo como fonte de verdade — CURRENT_STATE é gerado
      - gates existentes cobrem a frescura (check_portability estendido)
  - id: B
    summary: Novo doc CURRENT_PARITY.md + novo gate check_portability_docs.py
    tradeoffs:
      - "proliferam documentos/gates sem valor — §27–§28 preferem CURRENT_STATE
        + seção no outcome; §116 prefere estender o gate existente"
  - id: C
    summary: Reescrever os outcome/audit históricos com os números atuais
    tradeoffs:
      - "proibido (§5): snapshot de closure é histórico — distinguir
        Closure Snapshot de Current Measured State"
chosen: A
---

# PORTABILITY_CLOSURE_POLISH — explore

A wave de portabilidade está tecnicamente completa (PR #22 mergeado). O
risco restante não é código — é **evidência e documentação ficando velhas**:
o outcome diz que AWS não tem portable distribution (não é mais verdade —
`origin/main 904b40e` tem `sparkforge_aws/distribution`, `workspace/portable`,
`context resolve` e `integrate`+`detach` de nível usuário) e o report de
evals estava stale no disco (1 caso em vez de 10).

Trabalho = reconciliação pós-congelamento (§90): recomputar paridade do
código atual com SHAs amarrados, criar o estado medido canônico como
artefato *gerado*, fechar a validação de kinds/comandos no gate existente,
e estampar claims por último.
