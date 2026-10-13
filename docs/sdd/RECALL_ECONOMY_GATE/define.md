---
sdd: 1
feature: RECALL_ECONOMY_GATE
phase: define
profile: dev
status: done
hypothesis:
  claim: 'o gate recall/economia do ContextPack existe no Azure com o mesmo
    contrato do irmao AWS: recall nominal piso 100% sobre gold set derivado
    de regras, conceitual reportado sem piso, razao de economia recusada
    quando o corpus nao paga o envelope'
  prediction: 'goldset deriva >=12 perguntas dos fixtures pyspark (expected/
    gerado por extrator+judge reais), nominal 12/12, conceitual reportado sem
    piso, economia sai unresolved nomeada com medida que destrava'
  experiment: pytest tests/test_recall_economy_gate.py + execucao do script
acceptance:
- id: AC1
  statement: 'derivar_goldset devolve >=12 perguntas ancoradas em simbolos .py
    de fixtures/pyspark/*/input e o piso declarado e >= 12'
  verified_by:
    kind: test
    ref: tests/test_recall_economy_gate.py::test_gold_set_derives_the_declared_floor
- id: AC2
  statement: 'recall nominal e 100% sobre o gold set, ou cada falha esta em
    SEM_RECALL nomeada — o gate falha nas duas direcoes'
  verified_by:
    kind: test
    ref: tests/test_recall_economy_gate.py::test_nominal_recall_is_total_or_named_failures
- id: AC3
  statement: 'recall conceitual sai reportado sem piso (titulo de regra descreve
    defeito, indice guarda nome)'
  verified_by:
    kind: test
    ref: tests/test_recall_economy_gate.py::test_conceptual_recall_reported_without_floor
- id: AC4
  statement: 'razao de economia sai medida ou unresolved nomeada com a medida
    que a destravaria — nunca numero sobre corpus menor que o envelope'
  verified_by:
    kind: test
    ref: tests/test_recall_economy_gate.py::test_economy_is_measured_or_named_unresolved
success:
- id: SC1
  metric: 'gate exit 0 com nominal 12/12, conceitual 0/12 reportado sem piso,
    economia unresolved nomeada; fixture novo com ancora de simbolo aumenta o
    gold set sem tocar o gate'
  source: python scripts/check_recall_economy.py + pytest tests/test_recall_economy_gate.py
out_of_scope:
- "corpus grande de economia (a razao honesta exige corpus > envelope; medicao
  sobre a arvore do repo fica como follow-up nomeado)"
- "ponte titulo->simbolo para recall conceitual (nao prometido nem no AWS)"
- "piso AWS 27 herdado (nao se copia threshold sem corpus proprio)"
unknowns: []
change_kinds:
- extractor
---

# Define — RECALL_ECONOMY_GATE

Adaptacao do gate AWS. Diferenca honesta: o gold set Azure nao derivava
perguntas (fixtures ancoram stage/file, nao simbolo .py). Em vez de herdar o
piso 27 nem publicar 0/0, o ciclo gerou `expected/facts.json` +
`expected/findings.json` REAIS nas 16 fixtures `fixtures/pyspark/*` —
extrator `pyspark_ast` + judge do catalogo `SF-PY-*`. 12 derivam pergunta.
Envelope fixo medido no Azure: 747 bytes (pack tem chaves extras vs AWS 840).
