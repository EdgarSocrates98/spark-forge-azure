---
sdd: 1
feature: AGENT_CONTRACT_V2
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_CONTRACT_V2/design.md
  sha256: d3fd2015307ce39f1dbaa3a3c7d87b5176fa2205f977daa216d914a4ee5c383c
tasks:
- id: T1
  files: &id001
  - sparkforge_azure/agentmanifest/model.py
  - E:/projetos/spark-forge-azure/agents/adf-specialist.md
  - E:/projetos/spark-forge-azure/agents/adls-specialist.md
  - E:/projetos/spark-forge-azure/agents/analyzer.md
  - E:/projetos/spark-forge-azure/agents/azure-databricks-specialist.md
  - E:/projetos/spark-forge-azure/agents/bicep-specialist.md
  - E:/projetos/spark-forge-azure/agents/coordinator.md
  - E:/projetos/spark-forge-azure/agents/cost-reviewer.md
  - E:/projetos/spark-forge-azure/agents/critic.md
  - E:/projetos/spark-forge-azure/agents/databricks-cost-reviewer.md
  - E:/projetos/spark-forge-azure/agents/databricks-performance-reviewer.md
  - E:/projetos/spark-forge-azure/agents/databricks-runtime-reviewer.md
  - E:/projetos/spark-forge-azure/agents/databricks-uc-reviewer.md
  - E:/projetos/spark-forge-azure/agents/delta-specialist.md
  - E:/projetos/spark-forge-azure/agents/entra-specialist.md
  - E:/projetos/spark-forge-azure/agents/event-hubs-specialist.md
  - E:/projetos/spark-forge-azure/agents/extractor.md
  - E:/projetos/spark-forge-azure/agents/fabric-specialist.md
  - E:/projetos/spark-forge-azure/agents/finops-specialist.md
  - E:/projetos/spark-forge-azure/agents/iceberg-specialist.md
  - E:/projetos/spark-forge-azure/agents/inventory.md
  - E:/projetos/spark-forge-azure/agents/judge.md
  - E:/projetos/spark-forge-azure/agents/migration-reviewer.md
  - E:/projetos/spark-forge-azure/agents/migration-specialist.md
  - E:/projetos/spark-forge-azure/agents/networking-specialist.md
  - E:/projetos/spark-forge-azure/agents/observability-specialist.md
  - E:/projetos/spark-forge-azure/agents/onelake-specialist.md
  - E:/projetos/spark-forge-azure/agents/performance-reviewer.md
  - E:/projetos/spark-forge-azure/agents/purview-specialist.md
  - E:/projetos/spark-forge-azure/agents/referee.md
  - E:/projetos/spark-forge-azure/agents/reviewer.md
  - E:/projetos/spark-forge-azure/agents/security-reviewer.md
  - E:/projetos/spark-forge-azure/agents/spark-performance-specialist.md
  - E:/projetos/spark-forge-azure/agents/streaming-specialist.md
  - E:/projetos/spark-forge-azure/agents/synapse-specialist.md
  - E:/projetos/spark-forge-azure/agents/synthesizer.md
  - E:/projetos/spark-forge-azure/agents/terraform-specialist.md
  - E:/projetos/spark-forge-azure/agents/unity-catalog-specialist.md
  - E:/projetos/spark-forge-azure/agents/verifier.md
  - tests/test_agent_manifests.py
  - tests/test_agent_contract_v2.py
  covers:
  - AC1
  test:
    path: tests/test_agent_contract_v2.py
    name: test_v2_required_keys
- id: T2
  files: *id001
  covers:
  - AC2
  test:
    path: tests/test_agent_contract_v2.py
    name: test_family_closed_vocabulary
- id: T3
  files: *id001
  covers:
  - AC3
  test:
    path: tests/test_agent_contract_v2.py
    name: test_denied_tools_win
- id: T4
  files: *id001
  covers:
  - AC4
  test:
    path: tests/test_agent_contract_v2.py
    name: test_spawn_stop_vocabularies
- id: T5
  files: *id001
  covers:
  - AC5
  test:
    path: tests/test_agent_contract_v2.py
    name: test_v1_invariants_preserved
- id: T6
  files: *id001
  covers:
  - AC6
  test:
    path: tests/test_agent_contract_v2.py
    name: test_test_eval_roles_in_taxonomy
---

# Plan — AGENT_CONTRACT_V2
