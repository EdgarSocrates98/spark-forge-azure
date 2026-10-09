---
sdd: 1
feature: RECALL_ECONOMY_GATE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/RECALL_ECONOMY_GATE/define.md
  sha256: 5b796911eac20f4d75dc6ad8e4684d1549c3e41b7ac799673441ea0656533543
files:
- path: scripts/check_recall_economy.py
  action: create
  reason: gate com piso declarado, SEM_RECALL nas duas direcoes, recusa de
    economia sobre corpus pequeno
- path: fixtures/pyspark/*/expected/{facts,findings}.json
  action: create
  reason: gold set derivavel — gerado por extract_tree+judge reais
- path: tests/test_recall_economy_gate.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: expected/ gerado pelo pipeline real (extrator+judge), nao escrito a
    mao — a segunda verdade copiada e o defeito que o gold set existe para
    evitar
  rejected:
  - gold set escrito a mao (mede a suposicao do autor, nao o sistema)
  - piso 27 herdado do AWS (threshold sem corpus proprio)
  rollback: apagar expected/ + script + testes; piso volta a 0
- id: D2
  choice: resumo de problemas vai para stderr em --json (stdout fica JSON
    puro para consumo de CI)
  rejected:
  - mesmo texto apos o JSON como no AWS (quebra json.loads de quem consome)
  rollback: voltar a imprimir em stdout
covers:
- part: recall_economy_gate
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — RECALL_ECONOMY_GATE

O gate e script puro (stdlib + economy.goldset/recall ja portados). O trabalho
real foi o corpus: `derivar_goldset` so deriva de `fixtures/*/*/input` com
`.py` indexavel + `expected/findings.json` citando facts com subject
file+symbol. As fixtures pyspark ja tinham input; faltava o expected/.
