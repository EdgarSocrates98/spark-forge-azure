---
sdd: 1
feature: COSMOS_DEEP
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/COSMOS_DEEP/define.md
  sha256: "5c23967b7d2f813468f7ddce28e782816915d65c881990a232fadb7b011deaad"
files:
- path: sparkforge_azure/skills/model.py
  action: modify
  reason: SKILL_NAMES + KNOWLEDGE_AZURE_DOMAINS(cosmosdb) + VERTICAL_SKILLS com azure-cosmos-db
- path: sparkforge_azure/agentmanifest/model.py
  action: modify
  reason: SPECIALIST_DOMAINS + cosmos-db (gera cosmos-db-specialist)
- path: sparkforge_azure/agentmanifest/routing.py
  action: modify
  reason: Route cosmos-db-specialist com termos cosmos/change feed/partition key/request unit
- path: sparkforge_azure/knowledgebase/metadata.py
  action: modify
  reason: DOMAINS + azure-cosmos-db
- path: knowledge/azure/cosmosdb/*.md
  action: create
  reason: 5 docs VERIFIED (connector, bulk-and-batch, change-feed, reads-and-tuning, model-and-limits)
- path: knowledge/packs.yaml
  action: modify
  reason: vertical cosmos com 3 packs (cosmos-core, cosmos-spark-connector, cosmos-change-feed)
- path: knowledge/query_expansion.yaml
  action: modify
  reason: termos cosmos/partition key/request unit/change feed/bulk/integrated cache/analytical store
- path: knowledge/sources.lock.json
  action: modify
  reason: fontes oficiais Cosmos com retrieved 2026-11-03
- path: skills/azure-cosmos-db/SKILL.md + evals/evals.yaml
  action: create
  reason: skill contrato v1 + evals positive/negative/boundary
- path: agents/cosmos-db-specialist.md
  action: create
  reason: specialist schema_version 2, read_only, DATA_ONLY, verifier
- path: evals/agents/cosmos-db-specialist.yaml
  action: create
  reason: eval de rota positive/negative
- path: agents/coordinator.md
  action: modify
  reason: allowed_targets + linha da tabela de roteamento Cosmos
- path: tests/test_skills.py
  action: modify
  reason: contagens 23->24 skills e 20->21 specialists
- path: tests/test_knowledgebase.py
  action: modify
  reason: TODAY de referencia e EXPECTED_IDS com os 5 ids cosmosdb
- path: tests/test_agent_manifests.py
  action: modify
  reason: taxonomy counts 20->21 specialists / 40->41 agents
- path: scripts/gen_agents_doc.py
  action: modify
  reason: contagem congelada 40->41 agents no cabecalho gerado
- path: docs/README.md
  action: modify
  reason: contagens congeladas 23->24 skills / 40->41 agents no indice
- path: docs/learn/recipes/usar-skills.md
  action: modify
  reason: contagem 23->24 skills na receita
- path: docs/learn/recipes/usar-agents.md
  action: modify
  reason: contagem 40->41 agents na receita
- path: docs/reference/knowledge-packs.md
  action: modify
  reason: secao do vertical cosmos com os 3 packs
decisions:
- id: D1
  choice: dominio de knowledge `azure-cosmos-db` e pasta `knowledge/azure/cosmosdb/` espelhando `eventhubs`
  rejected: ["reusar dominio azure-spark", "dominio generico 'databases'"]
  rollback: remover entrada de DOMAINS/KNOWLEDGE_AZURE_DOMAINS e pasta
- id: D2
  choice: conector coberto so para API NoSQL/cosmos.oltp; OLAP (Synapse Link) e outras APIs fora
  rejected: ["cobrir cosmos.olap no mesmo vertical", "misturar API for MongoDB"]
  rollback: docs e skill declaram o escopo; ampliar exige nova feature
- id: D3
  choice: extratores cosmos ficam em planned_tool_refs ate existir analyze cosmos-*
  rejected: ["declarar analyze cosmos-config como tool_refs existente"]
  rollback: remover planned_tool_refs do front matter
- id: D4
  choice: roteamento com frases multi-palavra (change feed, partition key, request unit) para nao roubar termos genericos de spark-performance/streaming
  rejected: ["termo solto 'partition'", "termo solto 'bulk'"]
  rollback: remover Route do ROUTING_TABLE e linha do coordinator
covers:
- part: catalogos fechados (skills/agents/domains/routing)
  acceptance: [AC1, AC2, AC4]
- part: corpus knowledge + packs + expansao + sources.lock + INDEX
  acceptance: [AC3]
- part: artefatos gerados (mirrors, docs, CAPABILITY, AGENT_INVENTORY)
  acceptance: [AC5]
---

# Design — COSMOS_DEEP

Mesma topologia do vertical EVENT_HUBS_DEEP: dominio proprio, skill propria,
specialist proprio, packs por failure_layer e rota por frases especificas.
