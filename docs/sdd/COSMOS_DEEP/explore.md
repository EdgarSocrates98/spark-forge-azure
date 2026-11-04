---
sdd: 1
feature: COSMOS_DEEP
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Cobrir Cosmos dentro das skills azure-spark/spark-streaming existentes, sem skill nem specialist novos
  tradeoffs:
  - menos superficie de catalogo
  - conhecimento Cosmos (RU, partition key, bulk, change feed) diluido em skills genericas — viola o padrao dos verticais deep (event-hubs, fabric)
  - sem dominio proprio o roteamento cai em streaming/performance genericos
- id: A2
  summary: Vertical Cosmos dedicado — dominio knowledge azure-cosmos-db + skill azure-cosmos-db + cosmos-db-specialist + packs + roteamento
  tradeoffs:
  - segue o padrao EVENT_HUBS_DEEP (vertical por servico com evidencia)
  - 5 docs de knowledge ancorados em referencia oficial (Learn + azure-sdk-for-java config reference)
  - "custo — novos registros fechados (SKILL_NAMES, SPECIALIST_DOMAINS, DOMAINS, ROUTING_TABLE) + mirrors + docs geradas"
- id: A3
  summary: Vertical completo com extratores dedicados (analyze cosmos-config/cosmos-account) e regras cosmos.* no catalogo
  tradeoffs:
  - prematuro — nao ha extrator cosmos ainda; registrar como planned_tool_refs mantem a porta aberta sem fingir capability (arquivo != prontidao)
chosen: A2 — vertical com skill/specialist/knowledge/packs/roteamento; extratores ficam planned ate existir implementacao
---

# Explore — COSMOS_DEEP

Pesquisa ancorada em fontes oficiais: Microsoft Learn (tutorial-spark-connector,
throughput-control-spark, change-feed-spark, concepts-limits, integrated-cache,
transactional-batch, throughput-buckets) e azure-sdk-for-java (configuration-reference
do conector Spark 3 + READMEs de compatibilidade por artefato).
