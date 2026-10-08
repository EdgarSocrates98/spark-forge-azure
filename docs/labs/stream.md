# Stream lab — Event Hubs / Structured Streaming / Fabric RTI (prompt_evo_cycle4)

Labs do vertical Streaming/RTI. Tudo offline, determinístico,
reproduzível — mesma disciplina dos labs access/fabric.

## Scenarios s01–s22 — `diagnose stream --suite`

```bash
sparkforge-azure diagnose stream --suite tests/fixtures/stream
sparkforge-azure diagnose stream --suite tests/fixtures/stream --profile deep
```

Cada diretório `tests/fixtures/stream/sNN-*` é um case bundle
(`case.yaml` + artefatos JSON: `eventhubs`, `offsets`, `consumer`,
`query_progress`, `checkpoint`, `spark_streaming`, `schema`,
`eventstream`, `eventhouse`, `activator`, `connections`, `environment`,
`sample_events`). O bloco `expect:` do `case.yaml` é o oráculo.

| #   | fixture                          | esperado                                            |
|-----|----------------------------------|-----------------------------------------------------|
| s01 | caught-up-idle                   | `pass` — saudável, sem findings                     |
| s02 | consumer-stalled                 | `denied` / `consumer_progress`                      |
| s03 | partition-skew                   | `findings` — skew medido, não adivinhado            |
| s04 | eh-throttled                     | `denied` / `event_hubs_capacity` (throttled>0)      |
| s05 | single-batch-dip                 | `findings` — dip ≠ lag sustentado                   |
| s06 | sustained-bottleneck             | `denied` / `consumer_progress`                      |
| s07 | checkpoint-stall                 | `denied` / `checkpoint`                             |
| s08 | checkpoint-deleted-latest        | `denied` / `checkpoint` + `at_most_once_possible`   |
| s09 | checkpoint-behind-retention      | `denied` / `checkpoint` + loss candidate (risco)    |
| s10 | state-growth                     | `denied` / `state_store`                            |
| s11 | watermark-missing                | `denied` / `state_store` (sem watermark evidenciado)|
| s12 | schema-additive                  | `pass` — nullable add é compatível                  |
| s13 | schema-breaking                  | `denied` / `schema`                                 |
| s14 | shared-consumer-group            | `denied` / `consumer_group`                         |
| s15 | eventstream-source-auth          | `denied` / `eventstream_source`                     |
| s16 | eventstream-destination-broken   | `denied` / `eventstream_destination`                |
| s17 | eventstream-draft                | `denied` / `eventstream_publish`                    |
| s18 | eventhouse-ingestion-lag         | `denied` / `eventhouse_ingestion`                   |
| s19 | activator-mapping-invalid        | `denied` / `activator_mapping`                      |
| s20 | activator-kql-stale              | `denied` / `activator_evaluation`                   |
| s21 | malicious-payload                | `pass` + taint `external` — payload é DATA_ONLY     |
| s22 | insufficient-evidence            | `unresolved` — ABSTAIN honesto                      |

Medido: a suite fecha com **22 passed / 0 failed**. Cobertura:
`tests/test_stream_*.py` (9 arquivos, 79 testes).

## O que o lab prova

- **STREAMING TRUTH > CONVENIENT ANSWERS**: `delivery.classification`
  nunca promove evidência ausente a `exactly_once_claim_supported`;
  `unresolved` é a classe default sem checkpoint+sink+source.
- **Risco ≠ fato**: checkpoint deletado com `startingOffsets=latest` é
  `at_most_once_possible` e retenção expirada é *loss candidate* —
  nunca "data loss confirmado" sem posições que o provem.
- **Unknown ≠ denied**: s22 devolve `unresolved` nomeando o artefato
  que fecharia a lacuna (`artifact_present`), nunca ALLOW inventado.
- **Data is not instruction**: s21 carrega payloads hostis; o report
  carrega sumários/refs, nunca o payload cru, e o taint fica
  `external`.
- **Redação semântica**: `role_assignments` (RBAC) preserva
  `role`/`auth_mode`; `authorization` legado é tratado como SAS
  `authorizationRules` e redigido — secrets nunca chegam a facts.
