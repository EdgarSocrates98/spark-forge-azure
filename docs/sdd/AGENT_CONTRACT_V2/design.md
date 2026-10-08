---
sdd: 1
feature: AGENT_CONTRACT_V2
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_CONTRACT_V2/define.md
  sha256: f05bf4880954afc7fb3ac66dccbfe229cd77db6b4bd0dbd26f33ac03cf24d1fd
files:
- path: sparkforge_azure/agentmanifest/model.py
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/adf-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/adls-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/analyzer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/azure-databricks-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/bicep-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/coordinator.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/cost-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/critic.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/databricks-cost-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/databricks-performance-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/databricks-runtime-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/databricks-uc-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/delta-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/entra-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/event-hubs-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/extractor.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/fabric-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/finops-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/iceberg-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/inventory.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/judge.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/migration-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/migration-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/networking-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/observability-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/onelake-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/performance-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/purview-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/referee.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/security-reviewer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/spark-performance-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/streaming-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/synapse-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/synthesizer.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/terraform-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/unity-catalog-specialist.md
  action: create
  reason: cycle 6
- path: E:/projetos/spark-forge-azure/agents/verifier.md
  action: create
  reason: cycle 6
- path: tests/test_agent_manifests.py
  action: create
  reason: cycle 6
- path: tests/test_agent_contract_v2.py
  action: create
  reason: cycle 6
decisions:
- id: D1
  choice: A2 — fonte canonica unica; v2 endurece contrato sem fork de diretorio
  rejected:
  - Schema novo paralelo (agents/v2/)
  - Evoluir schema no lugar, chaves novas obrigatorias
  rollback: reverter o commit da feature
covers:
- part: agent_contract_v2
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
  - AC5
  - AC6
---

# Design — AGENT_CONTRACT_V2
