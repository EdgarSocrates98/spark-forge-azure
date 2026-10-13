# Cycle 4 — Outcome Brief (Streaming / Event Hubs / Fabric RTI deep vertical)

`prompt_evo_cycle4.md` implementado em fases/ondas com commit por wave na
branch `feat/cycle4-streaming`.

## STATUS

- Event Hubs streaming diagnosis = **DEEP_LOCAL**
- Structured Streaming diagnosis = **DEEP_LOCAL**
- Fabric RTI vertical = **DEEP_LOCAL**

## SHAs

| Marco | SHA |
|---|---|
| `BASE_SHA` | `86b1910ea809ab7d0d9d86dbdc86a1f769146f6b` (main pós-PR #7) |
| `WAVE0_SDD` | `c0b5890` — 6 sub-SDDs (gate vermelho honesto `test_not_written`) |
| `IMPLEMENTATION_SHA` | `172e768` — vertical stream/ + grafo + regras + lab 22 |
| `HARDENING_SHA` | `c3cb466` — 55 testes + packs + roteamento + corpus TokenSave |
| `FINAL_CODE_SHA` | HEAD de `feat/cycle4-streaming` no merge |
| `FINAL_MAIN_SHA` | commit de merge do PR (post-hoc) |

## P0-A EVENT_HUBS

`stream/model.py` + `extract_eventhubs`: namespace (id ARM, tier,
TU/PU/CU, public_network, kafka_enabled, private_endpoints), hub
(id canônico, partition_count, retention_hours, capture), partições,
consumer groups, `role_assignments` (RBAC — `role`/`auth_mode`/`effect`
preservados; a chave legada `authorization` é tratada como SAS
`authorizationRules` e redigida), métricas como séries temporais
(`eh.metric.points[]`), `eh.throttle` só com throttled>0 medido,
`eh.event` para sinais. Camadas `event_hubs_auth|network|capacity`.

## P0-B STRUCTURED_STREAMING

`stream/progress.py`: série `stream.progress` de
`StreamingQueryProgress`-like dicts; `sustained_processing_deficit`
(deficit + backlog growth), `single_batch_dip` (dip ≠ lag — §205),
`partition_skew`, `consumer_stalled`. `checkpoint` (exists/advancing/
age/owner_query_id/offsets), `state_store` via state_rows na série,
`stream.config` (checkpointLocation, startingOffsets, failOnDataLoss,
outputMode, trigger, watermark), `stream.sink` (idempotent/transactional/
merge_keys).

## P0-C CORRECTNESS

`stream/correctness.py`: `classify_delivery` retorna sempre uma classe de
`DELIVERY_ORDER` — `unresolved` é o default sem evidência; `at_least_once`
exige fonte replayable + checkpoint; `effectively_once` exige sink
idempotente/transactional; `exactly_once_claim_supported` exige
transactional + idempotente + progresso síncrono (async demove).
`schema_compatibility` separa nullable-additive de type-change.
`data_loss_candidates` emite risco/candidato — nunca perda confirmada.

## P0-D FABRIC_RTI

`stream/rti.py`: estágios `eventstream_source|transform|destination|
publish`, `eventhouse_ingestion`, `kql`, `activator_mapping`,
`activator_evaluation` — fail/unknown/pass; ausência de artefato nunca
vira pass (estágio não emitido ou unknown).

## P0-E GRAPHFY

`graph/stream.py` + layer `stream` no registry: kinds `namespace,
eventhub, partition, consumer_group, app, stream_query, checkpoint, sink,
eventstream, es_source, es_transform, es_destination, eventhouse,
activator, activator_rule, connection, identity`. Edges de fluxo/posse/
checkpoint; findings viram nós `finding` + `evidenced_by` (nunca
causalidade inventada — s01 prova).

## P0-F ECONOMY_OBSERVABILITY

- Knowledge: 5 packs `vertical: stream` escopados por failure_layer;
  `cross_environment` resolve por vertical (access→azure-identity,
  stream→eventhubs-core).
- TokenSave: corpus `evals/token_efficient/stream_case` (~12 KB);
  benchmark prova `bytes_avoided > 0`; `tokens` permanece `unresolved`
  (bytes ≠ tokens).
- AgentOps: spans `stream.<stage>` por estágio do pipeline; receipt com
  sources/facts/rules; `context_quality` mede required_recall.
- `stream/fingerprint.py`: fingerprint de ambiente para memória.

## MCP

`sfa_diagnose_stream` (read_only, compact) — bundle → status/
failure_layer/diagnosis/delivery/stream_graph/receipt. Nunca retorna
payloads de eventos. Catálogo: 12 tools.

## CLI

`sparkforge-azure diagnose stream --bundle|--suite [--profile]` — mesmo
contrato dos outros verticais; documentado em `docs/reference/cli.md` e
travado em `surface.lock.json` (46 comandos).

## CONTEXT

Knowledge escopado por `failure_layer` + `vertical`; packs stream nunca
carregam UC/Fabric — `excluded_domains`/vertical provado por teste.

## TRUST

`trust.taint=external` quando bundle carrega `sample_events`
não-confiáveis; `instruction_authority=data_only`; payload hostil (s21)
nunca vira finding nem altera verdict; SAS/JWT/conn-string redigidos no
boundary antes de facts.

## MEMORY

`case_meta.environment_fingerprint` por caso (tenant/namespace/workspace
hash) — memória ancorada a ambiente, não a nomes.

## RECOVERY

Sem cloud mutation; bundle ilegível → `StreamCaseError` → CLI exit 2 /
erro MCP nomeado. Ausência de artefato → `unresolved` com
`artifact`/`artifact_present`.

## KNOWLEDGE

Domínios: `azure-event-hubs`, `spark-streaming`, `fabric-realtime`,
`azure-networking`, `azure-entra`, `azure-finops`, `data-quality`,
`fabric-identity` — todos `VERIFIED` no INDEX com `verified_at` e fonte
oficial.

## SKILLS

Skills existentes `azure-event-hubs`, `spark-streaming`, `fabric-realtime`
cobrem o vertical (sem skill nova — composição); `streaming-specialist`
declara `rule_areas: [SF-STR, SF-RTI]` e recebe AGENT-006.

## LAB

22 cenários `tests/fixtures/stream/s01..s22` — **22 passed / 0 failed**
(`docs/labs/stream.md`). 79 testes `tests/test_stream_*.py`.

## SECURITY

- Redação no boundary de extração (`collectors.redact`); SAS keys nunca
  em facts (`test_sas_never_in_facts`).
- `role_assignments` vs `authorization`: semântica RBAC preservada, SAS
  authorizationRules redigidas (achado real do lab).
- Payloads hostis: sumários/refs apenas; taint external; nenhum payload
  cru no report (`test_no_raw_event_payloads_in_report`).
- Cross-environment: `environment.scope` contraditório → `SF-STR-ENV` P0
  + `cross_environment`.

## CLAIMS

Novas em `docs/claims.lock.json`: `stream-suite-green` (22/22),
`stream-mcp-surface` (`sfa_diagnose_stream` no catálogo) — provas
executáveis, stamped no ancestral.

## SURFACE

`surface.lock.json` regerado: +`diagnose stream` (CLI 45→46),
+`sfa_diagnose_stream` (MCP 11→12). `check_docs_surface` verde — ambos
documentados.

## SUPPLY_CHAIN

Nenhuma dependência nova. Vertical usa só o núcleo existente (PyYAML,
jsonschema).

## TESTS

```
pytest foco stream   79 passed (9 arquivos test_stream_*.py)
stream suite         22 passed / 0 failed
sdd.checks           ok — 17 features, 0 refused
ruff                 clean
surface.lock         ok — sem drift
docs-surface         ok — 46 CLI + 12 MCP cobertos
doctor               streaming_vertical ok
REMOTE_CI            NOT_OBSERVED (quota GitHub — ignorado conforme instruído)
```

## DEFERRED

- Live production load tests (sem cota/credenciais — lab é offline por
  design).
- Catálogo RTI completo de conectores (cobertos: Eventstream
  source/transform/destination/publish, Eventhouse/KQL, Activator).
- Todas as capacidades KQL (ingestion lag + query staleness cobertos;
  otimização de query KQL fica para pack dedicado).
- Streaming FinOps profundo (TU/PU/CU detectados e reportados; análise de
  custo por workload é backlog).

## DEFERRED_EXTERNAL

- Collectors live de Event Hubs/Fabric RTI (ARM/metrics live) — exigem
  credenciais; o contrato `collectors` aceita export injetado.
- Cobertura de CDC/Debezium integrado (schema de envelope reconhecido,
  diagnóstico dedicado é backlog).

## BACKLOG

- Kafka connector matrix por vendor (Confluence/AKS-hosted) além do
  endpoint Kafka do Event Hubs.
- Event Hubs Capture → ADLS como fonte de replay (facts `capture`
  extraídos; diagnosis de replay-path dedicada é backlog).
- Materialized views/continuous KQL como camada própria quando houver
  evidência de caso real.
