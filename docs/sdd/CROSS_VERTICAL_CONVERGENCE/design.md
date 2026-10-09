---
sdd: 1
feature: CROSS_VERTICAL_CONVERGENCE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/CROSS_VERTICAL_CONVERGENCE/define.md
  sha256: "dc1820037f79ae21d7e6fa5493f46968f897dd7be5dc13aec4338ba5e4f66f81"
files:
- path: sparkforge_azure/azure/fingerprint.py
  action: create
  reason: azure_fingerprint(case, facts) — axes de environment.scope +
    compute.workspace_id + target (table/storage account/metastore)
- path: sparkforge_azure/azure/pipeline.py
  action: modify
  reason: case_meta.environment_fingerprint = azure_fingerprint(...) —
    mesma posicao semantica de fabric/stream/migration
- path: sparkforge_azure/migration/pipeline.py
  action: modify
  reason: evidence_paths top-level — _evidence_paths(findings, facts)
    mapeia rule_id -> {facts, files, assets} via provenance.source
- path: evals/convergence/suite.yaml
  action: create
  reason: contrato compartilhado — profiles, shared_result_keys,
    shared_case_meta_keys, shared_receipt_keys, namespaces de fact.kind
- path: evals/convergence/cases/*.yaml
  action: create
  reason: um caso por vertical com required/forbidden findings,
    required_evidence, allowed_unresolved
- path: evals/convergence/runner.py
  action: create
  reason: executor do lab — roda cada caso em cada profile, valida
    contrato, reporta violacoes nomeadas (nunca agregadas a um score)
- path: tests/test_cross_vertical_convergence.py
  action: create
  reason: gate pytest — 20 celulas + contaminacao de dominio/grafo/
    memoria/trust
decisions:
- id: D1
  choice: fingerprint em case_meta (nao top-level) — e onde os outros
    tres verticais emitem; paridade e posicao, nao so presenca
  rejected:
  - emitir nos dois lugares — duplica o dado, cria deriva futura
  - top-level em todos — mudanca desnecessaria em 3 verticais
  rollback: remover o campo de databricks
- id: D2
  choice: evidence_paths de migration derivado dos facts citados nos
    findings (provenance.source -> arquivo) — sem inventar camadas que o
    vertical nao tem (nao ha `layers` nem `notebook_refs`)
  rejected:
  - copiar o formato completo de access (layers/notebook_refs vazios
    seriam ruido — campos ausentes > campos vazios)
  - usar so per_asset — findings citam facts; o caminho correto e
    finding->fact->fonte
  rollback: remover evidence_paths de migration e registrar divergencia
- id: D3
  choice: namespaces de fact.kind medidos nas fixtures reais +
    `upstream.` permitido em todos (fatos estrangeiros preservam
    identidade, nao sao lavados)
  rejected:
  - namespaces teoricos — medi o que os extractors emitem de verdade
  rollback: desativar checagem de namespace no runner
covers:
- part: cross_vertical_convergence
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — CROSS_VERTICAL_CONVERGENCE

Duas correcoes cirurgicas fecham as divergencias medidas no Wave 0, e
o lab torna a convergencia verificavel para sempre:

- `azure/fingerprint.py` espelha `fabric/fingerprint.py`: primeiro
  escritor vence por eixo, conflito real pertence a uma regra
  (SF-ACC-013), nunca resolvido silenciosamente.
- `migration._evidence_paths` mapeia rule_id -> facts -> arquivos de
  proveniencia -> assets. O formato e o do contrato (finding cita
  facts, facts citam fontes), sem forcar campos que o vertical nao tem.
- O runner nao produz score magico: cada violacao e uma linha nomeada
  com caso, profile e campo. `ok` = zero violacoes.
