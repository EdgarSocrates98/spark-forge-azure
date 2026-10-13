---
sdd: 1
feature: AGENT_EVAL_SUITE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_EVAL_SUITE/design.md
  sha256: c74f78cf827ff7111f28223c9a282fba0f361392bc5d89d2e6d64638154c7ee7
tasks:
- id: T1
  files:
  - tests/test_agent_eval_cases.py
  - tests/test_agentic_inventory.py
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_agent_eval_cases.py
    name: test_agent_eval_cases_execute
- id: T2
  files:
  - evals/agents/
  - sparkforge_azure/agentic/inventory.py
  - agents/adf-specialist.md
  - agents/adls-specialist.md
  - agents/analyzer.md
  - agents/azure-databricks-specialist.md
  - agents/bicep-specialist.md
  - agents/coordinator.md
  - agents/cost-reviewer.md
  - agents/critic.md
  - agents/databricks-cost-reviewer.md
  - agents/databricks-performance-reviewer.md
  - agents/databricks-runtime-reviewer.md
  - agents/databricks-uc-reviewer.md
  - agents/delta-specialist.md
  - agents/entra-specialist.md
  - agents/evaluation-specialist.md
  - agents/event-hubs-specialist.md
  - agents/extractor.md
  - agents/fabric-specialist.md
  - agents/finops-specialist.md
  - agents/iceberg-specialist.md
  - agents/inventory.md
  - agents/judge.md
  - agents/migration-reviewer.md
  - agents/migration-specialist.md
  - agents/networking-specialist.md
  - agents/observability-specialist.md
  - agents/onelake-specialist.md
  - agents/performance-reviewer.md
  - agents/purview-specialist.md
  - agents/referee.md
  - agents/reviewer.md
  - agents/security-reviewer.md
  - agents/spark-performance-specialist.md
  - agents/streaming-specialist.md
  - agents/synapse-specialist.md
  - agents/synthesizer.md
  - agents/terraform-specialist.md
  - agents/test-engineer.md
  - agents/unity-catalog-specialist.md
  - agents/verifier.md
  covers:
  - AC1
  - AC3
  - AC4
  test:
    path: tests/test_agent_eval_cases.py
    name: test_agent_eval_cases_execute
---

# Plan — AGENT_EVAL_SUITE
