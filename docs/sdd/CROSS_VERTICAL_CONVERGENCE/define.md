---
sdd: 1
feature: CROSS_VERTICAL_CONVERGENCE
phase: define
profile: dev
status: done
hypothesis:
  claim: 'os quatro verticais (databricks, fabric, stream, migration)
    divergem no contrato de resultado: a auditoria do Wave 0 mediu que
    databricks nao emite `environment_fingerprint` (os outros tres emitem
    em `case_meta`) e migration nao emite `evidence_paths` (os outros
    tres emitem top-level). Sem um lab que execute os quatro juntos,
    divergencias futuras voltam a ser invisiveis'
  prediction: 'fechar as duas divergencias medidas e executar
    `evals/convergence/` (1 caso x vertical x 5 profiles) produz 20/20
    celulas verdes, com invariantes §20 validados por teste: finding sem
    evidencia, sem segredo no relatorio, trust data_only, namespace de
    facts por vertical, fingerprint deterministico'
  experiment: python evals/convergence/runner.py
acceptance:
- id: AC1
  statement: 'databricks `run_case` emite
    `case_meta.environment_fingerprint` com axes derivados de
    environment.scope + compute + target — mesmo contrato que
    fabric/stream/migration; eixo ausente fica ausente, nunca inventado'
  verified_by:
    kind: test
    ref: tests/test_cross_vertical_convergence.py::test_environment_fingerprint_deterministico
- id: AC2
  statement: 'migration `run_migration_case` emite `evidence_paths`
    top-level mapeando rule_id -> {facts, files, assets} — mesmo
    contrato finding->facts->arquivos dos demais verticais'
  verified_by:
    kind: test
    ref: tests/test_cross_vertical_convergence.py::test_lab_all_cells_pass
- id: AC3
  statement: '`evals/convergence/` roda 1 caso por vertical em 5
    profiles (economy/balanced/deep/deterministic-only/agent-assisted)
    e valida chaves compartilhadas, findings requeridos/proibidos,
    evidencia citada, unresolved permitido — 20 celulas verdes'
  verified_by:
    kind: test
    ref: tests/test_cross_vertical_convergence.py::test_lab_all_cells_pass
- id: AC4
  statement: 'testes de contaminacao: facts nao cruzam namespace entre
    verticais; nos de grafo nao carregam marcador estrangeiro; memoria
    so pontua ambiente quando o fingerprint bate; trust permanece
    data_only nos quatro verticais; caso Fabric/Migration/Stream roteia
    o specialist do proprio vertical, nunca o de outro (§114)'
  verified_by:
    kind: test
    ref: tests/test_cross_vertical_convergence.py::test_contaminacao_de_memoria
success:
- id: SC1
  metric: 'runner reporta ok=true em 20 celulas; nenhum finding sem
    evidencia resolvivel; nenhum fact fora de namespace'
  source: python evals/convergence/runner.py
out_of_scope:
- 'diagnosis/context_quality top-level em migration — semanticamente o
  vertical produz readiness/validation, nao diagnostico de falha;
  registrado como DIFFERENT_BY_DESIGN na matriz'
- 'tornar profile um enum restrito — hoje e string livre no receipt;
  profiles novos nao mudam o contrato, so o recibo'
unknowns: []
change_kinds:
- domain
---

# Define — CROSS_VERTICAL_CONVERGENCE

Wave 0 do ciclo de convergencia mediu duas divergencias reais no
contrato de resultado dos quatro verticais:

1. `environment_fingerprint` — emitido por fabric/stream/migration em
   `case_meta`, ausente em databricks (o vertical mais antigo). Sem ele
   o reuso de memoria nao pode ancorar ambiente no vertical principal.
2. `evidence_paths` — emitido top-level por databricks/fabric/stream,
   ausente em migration. Findings de migracao ja citam facts `f_*`;
   faltava expor o caminho finding -> fact -> arquivo.

A correcao e a contracao do lab `evals/convergence/`: um caso por
vertical, cinco profiles, contrato validado por codigo — divergencia
futura reprova a suite, nao depende de revisao humana lembrar.
