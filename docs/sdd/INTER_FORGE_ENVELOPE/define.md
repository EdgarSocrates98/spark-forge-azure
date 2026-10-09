---
sdd: 1
feature: INTER_FORGE_ENVELOPE
phase: define
profile: dev
status: done
hypothesis:
  claim: '§118 do prompt de paridade: AWS e Azure consomem um envelope de
    handoff COMUM. O intake W1 so aceitava o rotulo azure e nao havia emissor
    — faltava a metade que deixa The Forge rotear evidencia nos dois
    sentidos sem laundering'
  prediction: 'intake aceita sparkforge_aws/upstream-facts/v1 alem do rotulo
    proprio (estrutura identica, proveniencia em attrs.upstream.provider);
    write_upstream_facts embrulha facts locais sob upstream:/upstream. e
    emite o schema do consumidor — round-trip pelo intake prova o contrato'
  experiment: pytest tests/test_upstream_facts.py
acceptance:
- id: AC1
  statement: 'read_upstream_facts aceita documento com schema
    sparkforge_aws/upstream-facts/v1 mantendo as mesmas marcas estrangeiras
    e a mesma rejeicao de chaves de instrucao'
  verified_by:
    kind: test
    ref: tests/test_upstream_facts.py::test_aws_schema_envelope_is_accepted
- id: AC2
  statement: 'write_upstream_facts produz documento que atravessa o proprio
    intake (round-trip): id sob upstream:, kind sob upstream., extractor
    theforge/handoff, attrs.upstream com provider/run_id/node/item'
  verified_by:
    kind: test
    ref: tests/test_upstream_facts.py::test_emitted_doc_round_trips_through_intake
- id: AC3
  statement: 'o emissor recusa chave de instrucao no payload, fact sem
    id/kind, proveniencia vazia e consumer_schema desconhecido — quem emite
    nao empacota o que o intake recusaria'
  verified_by:
    kind: test
    ref: tests/test_upstream_facts.py::test_emitter_refuses_instruction_and_missing_identity
success:
- id: SC1
  metric: 'tests/test_upstream_facts.py verde incluindo round-trip emit->
    intake; nenhum fact emitido perde a marca estrangeira'
  source: pytest tests/test_upstream_facts.py
out_of_scope:
- 'emissor do lado AWS (o sibling e so consumidor hoje; o envelope emitido
  aqui ja e aceito pelo intake dele porque usa o rotulo dele)'
- 'relabelagem automatica de schema (o emissor escolhe explicitamente o
  schema do consumidor)'
unknowns: []
change_kinds:
- tool_or_verb
---

# Define — INTER_FORGE_ENVELOPE

O intake W1 (UPSTREAM_FACTS_INTAKE) trouxe a metade de consumo com o rotulo
proprio. §118 pede envelope COMUM: estrutura identica entre os forges, com a
origem carregada em `attrs.upstream.provider` — nao no rotulo do schema.

Duas mudancas fecham o contrato:

1. `ACCEPTED_UPSTREAM_SCHEMAS` — o intake aceita `sparkforge_aws/upstream-
   facts/v1` alem do proprio. Sem laundering: as marcas `upstream:` /
   `upstream.` / `theforge/handoff` seguem obrigatorias para os dois
   rotulos.
2. `write_upstream_facts` — emissor que embrulha facts locais no envelope.
   Default `consumer_schema=UPSTREAM_SCHEMA_AWS`: o irmao so aceita o
   proprio rotulo, entao quem emite para ele ja sai no envelope certo.
