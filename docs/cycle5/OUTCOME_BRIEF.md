# Cycle 5 — Outcome Brief (ADF/Synapse → Fabric migration vertical)

`prompt_evo_cycle5.md` implementado em fases/ondas com commit por wave na
branch `feat/cycle5-migration`.

## STATUS

- Migration assessment (ADF/Synapse → Fabric) = **DEEP_LOCAL**

Não é tradução automática de serviços: é avaliação dirigida por evidência.
"ADF = Fabric Data Factory" é candidato-alvo, nunca equivalência semântica.

## SHAs

| Marco | SHA |
|---|---|
| `BASE_SHA` | `61367a5ffebc5dff6206b5a3dfd455217819f1f9` (main pós-PR #8) |
| `WAVE0_SDD` | `6e74262` — 7 sub-SDDs (gate vermelho honesto `test_not_written`) |
| `IMPLEMENTATION_SHA` | `ab84215` — vertical migration/ + grafo + regras + lab 22 + CLI/MCP |
| `HARDENING_SHA` | closure — build_reports red→green, claims, docs |
| `FINAL_CODE_SHA` | HEAD de `feat/cycle5-migration` no merge |
| `FINAL_MAIN_SHA` | commit de merge do PR (post-hoc) |

## P0-A MIGRATION_INVENTORY

`migration/extract.py` + `inventory.py`: facts tipados `adf.*`/
`synapse.*`/`fabric.*` com IDs canônicos (ARM ids quando presentes), arestas
de dependência tipadas (`contains/uses/reads/writes/invokes/depends_on/
runs_on/references`), `estate_summary()` por readiness. Assessment ausente
nunca vira `READY` — fica `UNRESOLVED`. Segredos de linked services
redigidos no boundary (`[REDACTED:*]`). Display names são atributos; o ID
canônico é a identidade.

## P0-B MIGRATION_COMPATIBILITY

`migration/compat.py`: vocabulário fechado `compatible /
compatible_with_change / manual_refactor / unsupported / preview /
unknown`, dims fechadas (pipeline_activity, connector, authentication,
integration_runtime, network, parameter, trigger, expression, notebook,
spark_runtime, library, spark_config, storage_path, catalog_api,
git_integration, deployment). Rollup worst-of; `unknown` nunca promove.
Scores auxiliares nunca escondem blocker/manual. Status oficial Microsoft
(`ready / needs review / coming soon / not compatible`) é evidência
externa mapeada para `READY/REVIEW/DEFERRED/BLOCKED` — divergência
oficial-vs-Forge gera `conflicts[]` e degrada para `REVIEW`; assessment
stale é flagged.

## P0-C ADF_FABRIC_DATA_FACTORY

`migration/pipelines.py`: classificação por atividade
(compatible/compatible_with_change/manual_refactor/unsupported),
`global_parameter` com identidade composta `pipeline#name`, linked services
→ candidato `fabric_connection` (nunca consolidação cega — shared LS com
auth incompatível vira finding `SF-MIG-CONN`), SHIR/managed VNet →
`MANUAL`, triggers/expressions como dims próprias.

## P0-D SYNAPSE_FABRIC_SPARK

`migration/spark.py`: padrões de refactor em notebooks (`mssparkutils`,
`synapsesql`, `spark.catalog.*`, paths `synapse:`/`abfss:`), classificação
de `spark_config` (passthrough/review/unsupported), compatibilidade de
libraries com `unknown` explícito, grafo de dependência de notebooks
(`%run`/`notebook.run`/`notebooks.run` resolvidos path↔name), distinção
explícita Synapse≠Fabric no modelo.

## P0-E DATA_ONELAKE

`migration/data.py`: estratégia fechada `retain/shortcut/copy/hybrid`.
Shortcut é candidato mediado por evidência (ADLS Gen2 + Delta + identidade
alvo observada), nunca recomendação automática; evidência de retirement da
fonte força `copy`. HMS managed vs external tratados separadamente.

## P0-F MIGRATION_PLANNER

`migration/planner.py`: waves topológicas sobre o multimap de
dependências (um asset com N deps mantém as N arestas); ciclo →
`plan.status=REVIEW` sem ordem fabricada; blocker upstream compartilhado
aparece em `shared_blockers`; **toda** wave carrega `rollback` explícito +
`data_divergence_policy`. Congelamento/ordem vêm só de evidência.

## P0-G POST_MIGRATION_VALIDATION

`migration/validate.py`: dims `functional, data, schema, dq, performance,
security, lineage, cost, orchestration`. `fail` em qualquer dim →
`overall=fail`. Row-count igual não sobrepõe divergência de métrica de
negócio (`data` vs `dq` separados). Regressão de performance não é
escondida por sucesso funcional. Identidade alvo errada → security fail.
Dims ausentes → `unmeasured_dimensions` + `overall=review` — nunca
auto-promoção para production-ready.

## GRAPHFY

`graph/migration.py` + layer `migration` no registry: nós de estate
source (adf_factory, pipeline, activity, dataset, linked_service, trigger,
integration_runtime, synapse_*, lake_database, table, adls_path,
storage_account) + alvos `fabric_*` + `recommendation`/`wave`/`identity`.
Edges tipados + `migrates_to{status}` + `schedules`; endpoint ausente →
`graph.unresolved` (nunca nó inventado). Graph é serialização — a camada
não importa o domínio (convenção stream/fabric).

## TOKENSAVE / ECONOMY

Report inclui `context` com bytes/estágios medidos (estate size, graph
build, assessment time) — economia medida, não declarada. `tokens`
permanece `unresolved` (bytes ≠ tokens).

## MCP

`sfa_assess_migration` (read_only, compact) — bundle → status/readiness/
compat/conflicts/plan(waves, blockers)/validation/unresolved. Projeção
compacta — nunca despeja o estate inteiro. Catálogo: 13 tools.

## CLI

`sparkforge-azure migration inventory|assess|plan|validate
--bundle|--suite [--profile]` — documentado em `docs/reference/cli.md` e
travado em `surface.lock.json` (50 comandos).

## AGENTOPS

Spans `migration.load|inventory|graph|assess|compatibility|plan|
validate|verify|report` no ledger; receipt com facts/rules citações.
Rota AGENT-007 → `migration-specialist` declara `rule_areas: [SF-MIG]`.

## CONTEXT

Knowledge escopado por `vertical="migration"` — 5 packs
(`migration-inventory|adf|spark|data|plan`); packs de migração nunca
carregam access/stream/fab e vice-versa (prova em
`test_knowledge_vertical`).

## TRUST

`instruction_authority=data_only`; artefatos de assessment/plan do
usuário são evidência externa, nunca autoridade; metadados hostis (s22)
ficam `DATA_ONLY` — não viram finding nem alteram readiness; segredos de
linked service redigidos antes de Facts.

## MEMORY

`migration/fingerprint.py`: fingerprint de estate (hash de tipos/contagens
+ identity classes) — memória ancorada a ambiente, não a display names.

## RECOVERY

Sem cloud mutation (live collection é opt-in e read-only por contrato);
bundle ilegível → `MigrationCaseError` → CLI exit 2 / erro MCP nomeado;
evidência ausente → `UNRESOLVED`, nunca síntese.

## KNOWLEDGE

Domínios `migration`, `azure-data-factory`, `azure-synapse`,
`fabric-data-factory`, `fabric-onelake`, `fabric-data-engineering` —
entradas `VERIFIED` no INDEX com `verified_at` e fonte oficial.

## SKILLS

`azure-data-factory` e `azure-synapse` promovidas a `VERTICAL_SKILLS` —
evals positive+negative+boundary ancorados nos SKILL.md.

## LAB

22 cenários `tests/fixtures/migration/` — **22 passed / 0 failed**
(`docs/labs/migration.md`). 46 testes `tests/test_migration_*.py`
focados (9 arquivos), incl. ciclo de dependência, conflito oficial,
assessment stale, payload malicioso, evidência insuficiente.

## SECURITY

- Redação no boundary; `SENSITIVE_KEY` casa `authorizationRules`/`password`
  — `role`/`auth_mode` preservados como semântica.
- Source identity e target identity são nós/facts separados — wrong
  target identity falha `security` na validação.
- Sem cloud write; secrets nunca em Facts (`test_secrets_redacted_*`).

## CLAIMS

Novas em `docs/claims.lock.json`: `migration-suite-green` (≥22 passed,
0 failed), `migration-mcp-surface` (`sfa_assess_migration` no catálogo);
`mcp-tools-12`→`mcp-tools-13`; `suite-green` restampado com o count real
do HEAD. Provas executáveis, stamped no ancestral.

## SURFACE

`surface.lock.json` regerado: +4 verbos `migration *` (CLI 46→50),
+`sfa_assess_migration` (MCP 12→13). `check_docs_surface` verde.

## SUPPLY_CHAIN

Nenhuma dependência nova. Vertical usa só o núcleo (PyYAML, jsonschema).

## TESTS

```
pytest foco migration  46 passed (9 arquivos test_migration_*.py)
migration suite        22 passed / 0 failed
sdd check              7/7 features ok, 0 refused (red→green real,
                       worktree .tmp-mig-red @ 61367a5, exit 2)
ruff                   clean
surface.lock           ok — sem drift
docs-surface           ok — 50 CLI + 13 MCP cobertos
doctor                 migration_vertical ok — 6 regras SF-MIG, 22 fixtures
REMOTE_CI              NOT_OBSERVED (quota GitHub — ignorado conforme instruído)
```

## DEFERRED

- Cobertura de atividade/conector long tail (o vocabulário fecha o que o
  lab mede; novos tipos caem em `unknown`/manual por design).
- Otimização de custo pós-migração (dim `cost` mede regressão declarada;
  modelagem FinOps de capacidade alvo é backlog).
- Diff visual de notebooks Synapse→Fabric (padrões detectados; rewriter
  assistido é backlog).

## DEFERRED_EXTERNAL

- Coletor live ADF/Synapse (ARM export/activity runs) — exige credenciais;
  o contrato aceita `estate.json` exportado.
- Migration Assistant oficial como fonte live (o produto consome export
  de assessment; execução da ferramenta Microsoft fica fora do processo).
