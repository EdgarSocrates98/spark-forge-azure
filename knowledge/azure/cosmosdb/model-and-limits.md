---
id: azure.cosmosdb.model-and-limits
title: Cosmos DB for NoSQL - modelo de RU, partition keys, limites de serviço, throughput control e boas práticas
domain: azure-cosmos-db
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/throughput-control-spark
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/throughput-buckets
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/integrated-cache
    retrieved: 2026-11-03
verified_at: 2026-11-03
versions: {}
status: VERIFIED
preview: false
related: [azure.cosmosdb.spark-connector, azure.cosmosdb.bulk-and-batch, azure.cosmosdb.change-feed, azure.cosmosdb.reads-and-tuning, azure.network.private-link-dns, azure.entra.managed-identity]
---

# Modelo, limites e boas práticas do Cosmos DB for NoSQL

## Modelo de throughput (RU/s)

- Toda operação cobra Request Units; o provisionamento é por contêiner (dedicated) ou por
  banco compartilhado entre contêineres.
- **Limite por partição (lógica e física): 10.000 RU/s** — escalar o contêiner não remove o
  teto por partição; hot partition estrangula em 10K mesmo com 100K+ provisionados.
- Máximo por contêiner/banco: 1.000.000 RU/s (aumento via ticket de suporte).
- Mínimos: 400 RU/s manual por contêiner; 1000 RU/s como max mínimo de autoscale.
  Mínimo efetivo sobe com armazenamento: manual `MAX(400, GB×1, maior RU já provisionado/100)`;
  autoscale `MAX(1000, GB×10, maior max já provisionado/10)`; banco compartilhado soma
  `+100 RU/s` (manual) ou `+1000` (autoscale) por contêiner acima de 25.
- Mínimo por GB armazenado: 1 RU/s (manual).

## Limites de serviço (concepts-limits)

| Recurso | Limite |
|---|---|
| Tamanho máximo de item | 2 MB (JSON UTF-8) |
| Valor de partition key | 2048 bytes (101 sem large partition key) |
| Valor de `id` | 1023 bytes |
| Storage por partição lógica | 20 GB (HPK permite exceder rearchitecting) |
| Request (CRUD/sproc) | 2 MB |
| Response (página de query) | 4 MB |
| Operações por transactional batch | 100 |
| Execução de uma operação/página | 5 s |
| Query SQL | 512 KB, ≤10 JOINs, ≤10 UDFs |

- Query que atinge timeout/tamanho retorna página + continuation token — sem limite
  prático de duração total entre continuações.

## Partition keys (fundação do tuning)

- Escolher PK de alta cardinalidade com distribuição uniforme de RU e storage; o hot
  partition é o modo clássico de falha (429 numa PK com contêiner ocioso).
- 20 GB por partição lógica: keys que crescem sem bound exigem synthetic key ou
  hierarchical partition keys (até 3 níveis) — o aumento temporário do limite via suporte
  **não honra SLA**.
- Para o Spark: partições físicas determinam feed ranges e, por tabela, o paralelismo de
  leitura do conector; carga concentrada em poucas PKs estrangela no limite por partição.

## Throughput control para workloads Spark

Duas camadas oficiais (throughput-control-spark):

- **Throughput buckets server-side — PREVIEW**: exige conector ≥4.43.0 e habilitação do
  preview na conta; até 5 buckets (IDs 1–5) configurados em Scale & Settings no portal;
  `spark.cosmos.throughputControl.enabled=true` + `.name` + `.throughputBucket`. Microsoft
  recomenda buckets onde disponível para ingestão, migração, bulk writes, queries e
  change feed — aplica-se a todo o tráfego no server-side.
- **Throughput control client-side**: grupo nomeado com `targetThroughput` **ou**
  `targetThroughputThreshold` (RU/s alvo vs % do provisionado); uso compartilhado é
  coordenado via contêiner de controle global (`globalControl.database/container`,
  `renewIntervalInMS=5s`, `expireIntervalInMS=11s`, `useDedicatedContainer=true`);
  `priorityLevel` define quem é throttled primeiro — **PREVIEW**.
- Regra prática evidenciada: isolar bulk/CDC de workloads de produção por grupo/bucket
  dedicado; medir RU consumida antes de elevar provisão.

## Integrated cache (dedicated gateway)

- Cache in-memory no dedicated gateway (item cache para point reads + query cache), LRU +
  `MaxIntegratedCacheStaleness`; hit = **0 RU**.
- Beneficia: read-heavy, point reads repetidos, queries repetidas caras, hot PK de leitura.
- **Não** beneficia: write-heavy, reads sem repetição e **change feed**; bulk/transactional
  não popula item cache. Consistência de leitura só Session/Eventual.

## Boas práticas transversais

- **Colocar o cluster Spark na mesma região** da conta Cosmos + `preferredRegionsList`.
- Nunca commitar `accountKey`/client secret; preferir Entra/RBAC de dados
  (`azure.entra.managed-identity`); chave em secret scope.
- Private endpoint exige DNS `privatelink.documents.azure.com` (`azure.network.private-link-dns`);
  `disableTcpConnectionEndpointRediscovery` só para custom domains com PE fora de
  Databricks/Synapse.
- Consistência: default do conector força eventual na leitura — não presumir o nível da
  conta sem declarar `read.consistencyStrategy`.
- Observar o par (métricas Cosmos + estágios Spark): NormalizedRUConsumption, throttles,
  diagnostics `sampled` — tuning sem baseline medido não é tuning, é chute.

## Fontes

- https://learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/throughput-control-spark (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/throughput-buckets (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/integrated-cache (retrieved: 2026-11-03)
