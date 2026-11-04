---
sdd: 1
feature: COSMOS_DEEP
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/COSMOS_DEEP/explore.md
  sha256: "23b30bdabe4c200989783aa8d376e09480d38e1c4811670f5fcf8c7199779aa1"
hypothesis:
  claim: "Um vertical Cosmos DB for NoSQL (dominio de knowledge + skill + specialist + packs + rota) permite responder bulk/batch, CDC/change feed, leitura, RU/throughput e boas praticas do conector Spark com evidencia oficial versionada, sem inflar skills genericas"
  prediction: "check_skills_agents/check_knowledge verdes com 24 skills e 21 specialists; roteamento de termos cosmos/change feed/partition key/RU chega ao cosmos-db-specialist; evals positive/negative/boundary da skill passam na validacao"
  experiment: python scripts/check_skills_agents.py && python scripts/check_knowledge.py && python -m pytest tests/test_skills.py tests/test_agent_contract_v2.py tests/test_agent_eval_cases.py -q
acceptance:
- id: AC1
  statement: "skill azure-cosmos-db registrada em SKILL_NAMES/VERTICAL_SKILLS, contrato v1 valido, evals com positive+negative+boundary"
  verified_by:
    kind: command
    ref: python scripts/check_skills_agents.py
- id: AC2
  statement: "cosmos-db-specialist registrado em SPECIALIST_DOMAINS com manifest schema_version 2 valido (read_only, DATA_ONLY, verifier)"
  guard: "o node nunca foi visto vermelho isolado: manifest e catalogo nasceram na mesma mudanca; o red real da feature esta em check_skills_agents (4 erros de contrato incluindo o `does` do proprio agente)"
  verified_by:
    kind: test
    ref: tests/test_agent_contract_v2.py::test_v2_required_keys
- id: AC3
  statement: "5 docs knowledge/azure/cosmosdb/ VERIFIED com fontes oficiais datadas; INDEX regerado; dominio azure-cosmos-db em DOMAINS"
  verified_by:
    kind: command
    ref: python scripts/check_knowledge.py --write-index
- id: AC4
  statement: "roteamento de termos cosmos/change feed/partition key/request unit para cosmos-db-specialist no coordinator e ROUTING_TABLE; eval de rota positive/negative"
  guard: "o node nunca foi visto vermelho isolado: os casos de rota foram escritos verdes de primeira; o red real da feature esta em check_skills_agents e nos contratos de catalogo"
  verified_by:
    kind: test
    ref: tests/test_agent_eval_cases.py::test_agent_eval_cases_execute
- id: AC5
  statement: "mirrors .claude/.agents, docs geradas (agents.md, skills.md, AGENT_INVENTORY, CAPABILITY.json) sincronizadas com o catalogo de 24 skills / 41 agents"
  verified_by:
    kind: command
    ref: python scripts/check_skills_agents.py
success:
- id: SC1
  metric: bateria de verificacao do repo verde; termos Cosmos roteam ao specialist; nenhum claim sem fonte nos docs
  source: python scripts/check_skills_agents.py && python scripts/check_knowledge.py
out_of_scope:
- extratores dedicados (analyze cosmos-config / cosmos-account) — ficam planned_tool_refs
- regras cosmos.* no catalogo de regras — proxima wave com extrator
- coletores live Cosmos (cloud read) — sem mutacao nem leitura de conta real
- conector OLAP do Azure Synapse Link e APIs nao-NoSQL (Mongo/Cassandra/Gremlin/Table)
unknowns: []
change_kinds:
- knowledge_doc
- agent_or_skill
- domain
- routing
---

# Define — COSMOS_DEEP

Vertical Cosmos DB for NoSQL deep: knowledge ancorado na referencia oficial
de configuracao do conector Spark 3 + Microsoft Learn; skill e specialist
seguem o padrao EVENT_HUBS_DEEP; extratores dedicados ficam planned.
