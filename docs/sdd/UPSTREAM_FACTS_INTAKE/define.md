---
sdd: 1
feature: UPSTREAM_FACTS_INTAKE
phase: define
profile: dev
status: done
hypothesis:
  claim: 'evidencia estrangeira de outro motor Spark Forge (ou do orquestrador)
    entra no case bundle via `upstream.json` com identidade preservada —
    namespace `upstream:`/`upstream.`, provenance `theforge/handoff`, sha do
    artefato gravado no intake — sem nunca disparar regra nativa nem carregar
    instrucao'
  prediction: 'facts upstream aparecem na saida `facts` do run_case com id
    `upstream:*` intacto; nenhum finding cita id upstream como evidence;
    documento com chave imperativa em qualquer profundidade e recusado'
  experiment: pytest tests/test_upstream_facts.py
acceptance:
- id: AC1
  statement: 'read_upstream_facts valida schema, marcas (id upstream:, kind
    upstream., extractor theforge/handoff, attrs.upstream completo), bounds
    (256KiB, 128 facts) e grava artifact_sha256 do documento lido'
  verified_by:
    kind: test
    ref: tests/test_upstream_facts.py::test_valid_document_passes_with_stamped_provenance
- id: AC2
  statement: 'documento com schema errado, fact desmarcado, origem incompleta,
    chave imperativa aninhada ou limites excedidos e recusado com UpstreamError
    nomeado'
  verified_by:
    kind: test
    ref: tests/test_upstream_facts.py::test_forbidden_instruction_key_refused_at_any_depth
- id: AC3
  statement: 'bundle com upstream.json carrega facts estrangeiros; run_case os
    publica em `facts` com identidade intacta e nenhum finding cita id
    `upstream:` — nenhuma regra nativa dispara sobre kind upstream.*'
  verified_by:
    kind: test
    ref: tests/test_upstream_facts.py::test_bundle_intake_and_judge_never_fires_on_foreign_kinds
- id: AC4
  statement: 'upstream.json malformado derruba o bundle com CaseError (exit 2
    nas surfaces), igual a qualquer artefato invalido'
  verified_by:
    kind: test
    ref: tests/test_upstream_facts.py::test_malformed_upstream_doc_is_case_error
success:
- id: SC1
  metric: '4 dominios (access/fabric/stream/migration) aceitam upstream.json;
    8 testes verdes; zero finding referencia id upstream:'
  source: pytest tests/test_upstream_facts.py + testes de pipeline dos 4 dominios
out_of_scope:
- "emissor do documento upstream (lado The Forge/AWS) — este motor so consome"
- "MCP tool dedicada de intake (bundle artifact e o seam; tool fica para consumidor real existir)"
- "traducao de kinds upstream.* para kinds nativos (proibido: launderia)"
unknowns: []
change_kinds:
- extractor
- tool_or_verb
---

# Define — UPSTREAM_FACTS_INTAKE

Adaptacao provider-appropriate do `adapters/upstream.py` do irmao AWS
(schema `sparkforge_azure/upstream-facts/v1`). No AWS o intake entra por
parametro do `analyze_pyspark`; no Azure o seam correto e o case bundle —
`upstream.json` e um artefato do bundle, carregado pelos 4 casefiles,
validado fail-closed e publicado como evidencia na saida do run_case.
