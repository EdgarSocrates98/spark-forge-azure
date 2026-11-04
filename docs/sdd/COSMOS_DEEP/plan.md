---
sdd: 1
feature: COSMOS_DEEP
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/COSMOS_DEEP/design.md
  sha256: "55ac617f826ebc9f4ef19f2e5e633fff08b52dc6ab24c49f46d9dfe32392a099"
tasks:
- id: T1
  files: [knowledge/azure/cosmosdb/spark-connector.md, knowledge/azure/cosmosdb/bulk-and-batch.md, knowledge/azure/cosmosdb/change-feed.md, knowledge/azure/cosmosdb/reads-and-tuning.md, knowledge/azure/cosmosdb/model-and-limits.md, knowledge/sources.lock.json, knowledge/query_expansion.yaml, knowledge/packs.yaml, sparkforge_azure/knowledgebase/metadata.py]
  covers: [AC3]
  test:
    path: tests/test_knowledgebase.py
    name: TestRealKnowledgeTree::test_check_script_green
- id: T2
  files: [skills/azure-cosmos-db/SKILL.md, skills/azure-cosmos-db/evals/evals.yaml, sparkforge_azure/skills/model.py]
  covers: [AC1]
  test:
    path: tests/test_skills.py
    name: test_catalogue_has_exactly_24_skills
- id: T3
  files: [agents/cosmos-db-specialist.md, evals/agents/cosmos-db-specialist.yaml, agents/coordinator.md, sparkforge_azure/agentmanifest/model.py, sparkforge_azure/agentmanifest/routing.py]
  covers: [AC2, AC4]
  test:
    path: tests/test_agent_contract_v2.py
    name: test_v2_required_keys
- id: T4
  files: [tests/test_skills.py, scripts/gen_agents_doc.py, docs/README.md, docs/learn/recipes/usar-skills.md, docs/learn/recipes/usar-agents.md, docs/reference/knowledge-packs.md]
  covers: [AC5]
  test:
    path: tests/test_skills.py
    name: test_check_script_summary
---

# Plan — COSMOS_DEEP

T1 corpus -> T2 skill -> T3 specialist+rota -> T4 contagens/docs; regen e
bateria completa como evidencia green no build_report.
