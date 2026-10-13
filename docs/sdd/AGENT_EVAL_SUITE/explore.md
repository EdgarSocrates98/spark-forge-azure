---
sdd: 1
feature: AGENT_EVAL_SUITE
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: 'evals: [tests/x.py] apontando para arquivos que ja existem'
  tradeoffs:
  - rapido
  - fraco — nao e eval por agent, e cobertura indireta
- id: A2
  summary: evals/agents/<id>.yaml com casos route_positive/route_negative executados
    por harness contra route()/explain_route(); roles apontam os testes que as cobrem
  tradeoffs:
  - eval real e regressivo
  - gerado da ROUTING_TABLE = contrato, nao tautologia (detecta regressao de masking/cap)
chosen: A2 — §101-102 pede eval por agent executavel; fleet sai de unevaluated com
  evidencia real
---

# Explore — AGENT_EVAL_SUITE

Os 40 manifests declaram `evals: []` — fleet inteira `unevaluated`. O docstring
de `_eval_coverage` promete "resolvable artifact" mas o codigo so checa lista
nao-vazia (divergencia honesta a fechar). Especialistas ganham casos de rota
executados contra `route()`/`explain_route()`; roles/reviewers/subagents
declaram os testes que ja exercitam seus contratos.
