---
sdd: 1
feature: INTER_FORGE_ENVELOPE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/INTER_FORGE_ENVELOPE/define.md
  sha256: dd662f95bd0337f3930041c52f389a2914ebd9510e0b5d57da302001d675671d
files:
- path: sparkforge_azure/adapters/upstream.py
  action: modify
  reason: ACCEPTED_UPSTREAM_SCHEMAS (intake comum) + write_upstream_facts
    (emissor com as mesmas marcas e o mesmo vocabulario proibido)
- path: tests/test_upstream_facts.py
  action: modify
  reason: contrato dos ACs — schema do irmao aceito, round-trip emit->intake,
    recusas do emissor
decisions:
- id: D1
  choice: intake aceita os dois rotulos de schema (azure + aws) em vez de um
    terceiro rotulo comum — os dois pacotes ja existem e a origem mora em
    attrs.upstream.provider, nao no rotulo
  rejected:
  - schema comum novo (theforge/upstream-facts/v1) — quebraria o intake AWS
    ja publicado, que so aceita o proprio rotulo
  - um schema so compartilhado — misturaria namespaces de pacote
  rollback: voltar a checar igualdade estrita com UPSTREAM_SCHEMA
- id: D2
  choice: consumer_schema default = UPSTREAM_SCHEMA_AWS — o caso de uso real
    e Azure emitindo para o irmao (que so aceita o proprio rotulo)
  rejected:
  - default proprio (emissor para consumo proprio e o caso raro)
  - schema livre (aceitaria envelopes que nenhum intake consome)
  rollback: mudar o default para UPSTREAM_SCHEMA
covers:
- part: inter_forge_envelope
  acceptance: [AC1, AC2, AC3]
---

# Design — INTER_FORGE_ENVELOPE

O emissor reusa `_forbidden_key` do intake: quem empacota nao pode passar
instrucao que o consumidor recusaria — mesma fonte de verdade, um lugar so
para evoluir o vocabulario proibido. O fact emitido e dict (nunca `Fact`
nativo): o id nativo vira sufixo de `upstream:` e `item` em attrs.upstream,
preservando rastreabilidade sem recomputar identidade.
