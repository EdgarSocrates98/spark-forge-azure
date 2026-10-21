---
name: delegate-specialists
description: 'Use quando o caso pedir diagnóstico de runtime sobre artefato exportado
  (log Databricks driver/executor, OOM, skew, shuffle, spill, stall de micro-batch,
  EXPLAIN, SQL pesado, metadata Delta/Unity Catalog, compat runtime×operação×formato)
  ou varredura estática independente do projeto (PySpark/Delta, antipadrões, config,
  deps, segurança, qualidade), ou para decidir SE delegar a data-sentinel-forge ou
  forge-doctor-data em vez dos extratores nativos, consumir um EvidenceHandoff,
  verificar finding do especialista ou revalidar depois de mudança.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - log databricks
  - diagnostico de runtime
  - artefato exportado
  - scan estatico independente
  - delegar especialista
  - evidence handoff
  - revalidar
  scope:
  - delegate discover
  - delegate plan
  - delegate run
  - delegate handoffs
  - data-sentinel
  - forge-doctor-data
  - capabilities declaradas
  - fallback native-analysis
  does:
  - decide quando delegar a data-sentinel-forge ou forge-doctor-data
  - consome EvidenceHandoff persistido em .sparkforge-azure/delegation/handoffs/
  - correlaciona finding do especialista com facts nativos e preserva unresolved
  does_not:
  - não inventa argv nem flag de especialista (só o manifesto declarado)
  - não executa especialista fora da fronteira governada delegate
  - não substitui extratores nativos nem confirma finding por fiat
  knowledge_refs:
  - knowledge/agentic/
  tool_refs:
  - sparkforge-azure delegate discover
  - sparkforge-azure delegate plan
  - sparkforge-azure delegate run
  - sparkforge-azure delegate handoffs
  - sparkforge-azure judge
  eval_refs:
  - skills/delegate-specialists/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---

# Delegate Specialists

Delegação opcional e governada a especialistas irmãos: `data-sentinel-forge`
(diagnóstico de runtime sobre artefato exportado) e `forge-doctor-data` (análise
estática do projeto). Toda capability é `LOCAL_READ` — nada chama a Azure;
especialista ausente degrada para `native-analysis`, nunca execução simulada.

## Procedimento

1. `sparkforge-azure delegate discover` — estados reais por especialista:
   `VERIFIED` executa; `DISCOVERED`/`NOT_INSTALLED`/`UNTRUSTED`/`INCOMPATIBLE`
   voltam como recusa nomeada. Não presuma presença; leia o estado.
2. `sparkforge-azure delegate plan "<intenção>"` — roteamento determinístico
   para a capability declarada, com justificativa e recusas, sem executar.
   As capabilities saem do manifesto declarado, nunca da memória.
3. `sparkforge-azure delegate run <provider> <capability> --target <artefato>`
   — executa sob fronteira governada (argv fixo, env saneada de credenciais
   `AZURE_*`/`ARM_*`/`DATABRICKS_*`, timeout, caps de saída, gate de risco
   `--authorize`).
4. `sparkforge-azure delegate handoffs` — lista os `EvidenceHandoff` selados
   (SHA-256) persistidos em `.sparkforge-azure/delegation/handoffs/`.
5. Correlacione findings do handoff com facts nativos e `sparkforge-azure judge`;
   divergência vira `unresolved`, não média.

## Pontos de decisão

- Log Databricks/OOM/skew/spill/stall de streaming → `sentinel.databricks-logs`.
- EXPLAIN físico → `sentinel.spark-explain`; SQL pesado → `sentinel.sql-analyze`
  ou `sentinel.sql-optimize`.
- Metadata Delta/Unity Catalog, MERGE, grants, compat → `sentinel.delta-metadata`,
  `sentinel.lakehouse-operation`, `sentinel.lakehouse-access`, `sentinel.lakehouse-compat`.
- Scan estático PySpark/Delta/config/deps/segurança → `doctor.scan-project`.
- Artefato já respondido por extrator nativo (`analyze pyspark`, `judge`) → não delegue.
- Especialista não `VERIFIED` → recusa nomeada é a resposta; não force.
- Revalidar após mudança → novo `delegate run`, nunca reler handoff velho.

## Não concluir sem evidência

- Finding do especialista é evidência externa: cite `handoff` e `run_id`,
  nunca o promova a `CONFIRMED` quando veio `POSSIBLE`/`UNKNOWN`.
- `status`/`limitations` do handoff fazem parte da evidência — reporte-os.
- Ausência de finding é ausência de proxy, não prova de correção.
- Recusa nomeada (`provider-absent`, `policy-refusal`, `cycle-detected`,
  `budget-exhausted`, `timeout`, `invalid-output`, `insufficient-evidence`)
  não é "serviço quebrado" — é estado.

## Handoff

- `spark-performance` — skew, spill, OOM com event log nativo.
- `delta-lake` — layout de arquivos e MERGE.
- `spark-streaming` — semântica de streaming e micro-batch.
- `azure-databricks` — plataforma Databricks, jobs e clusters.
