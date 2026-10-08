---
sdd: 1
feature: AGENT_EVAL_SUITE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_EVAL_SUITE/define.md
  sha256: f8323e7a88cb4ada3f4f3a3b3ffdced8c29c3f59a4d78f7751dd23a8ae0458ed
files:
- path: tests/test_agent_eval_cases.py
  action: create
  reason: harness executavel dos casos
- path: evals/agents/
  action: create
  reason: 20 suites de rota (uma por specialist)
- path: sparkforge_azure/agentic/inventory.py
  action: modify
  reason: _eval_coverage resolve artefatos contra root
- path: tests/test_agentic_inventory.py
  action: modify
  reason: testes de resolucao e frota
- path: agents/adf-specialist.md
  action: modify
  reason: evals declarados
- path: agents/adls-specialist.md
  action: modify
  reason: evals declarados
- path: agents/analyzer.md
  action: modify
  reason: evals declarados
- path: agents/azure-databricks-specialist.md
  action: modify
  reason: evals declarados
- path: agents/bicep-specialist.md
  action: modify
  reason: evals declarados
- path: agents/coordinator.md
  action: modify
  reason: evals declarados
- path: agents/cost-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/critic.md
  action: modify
  reason: evals declarados
- path: agents/databricks-cost-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/databricks-performance-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/databricks-runtime-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/databricks-uc-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/delta-specialist.md
  action: modify
  reason: evals declarados
- path: agents/entra-specialist.md
  action: modify
  reason: evals declarados
- path: agents/evaluation-specialist.md
  action: modify
  reason: evals declarados
- path: agents/event-hubs-specialist.md
  action: modify
  reason: evals declarados
- path: agents/extractor.md
  action: modify
  reason: evals declarados
- path: agents/fabric-specialist.md
  action: modify
  reason: evals declarados
- path: agents/finops-specialist.md
  action: modify
  reason: evals declarados
- path: agents/iceberg-specialist.md
  action: modify
  reason: evals declarados
- path: agents/inventory.md
  action: modify
  reason: evals declarados
- path: agents/judge.md
  action: modify
  reason: evals declarados
- path: agents/migration-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/migration-specialist.md
  action: modify
  reason: evals declarados
- path: agents/networking-specialist.md
  action: modify
  reason: evals declarados
- path: agents/observability-specialist.md
  action: modify
  reason: evals declarados
- path: agents/onelake-specialist.md
  action: modify
  reason: evals declarados
- path: agents/performance-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/purview-specialist.md
  action: modify
  reason: evals declarados
- path: agents/referee.md
  action: modify
  reason: evals declarados
- path: agents/reviewer.md
  action: modify
  reason: evals declarados
- path: agents/security-reviewer.md
  action: modify
  reason: evals declarados
- path: agents/spark-performance-specialist.md
  action: modify
  reason: evals declarados
- path: agents/streaming-specialist.md
  action: modify
  reason: evals declarados
- path: agents/synapse-specialist.md
  action: modify
  reason: evals declarados
- path: agents/synthesizer.md
  action: modify
  reason: evals declarados
- path: agents/terraform-specialist.md
  action: modify
  reason: evals declarados
- path: agents/test-engineer.md
  action: modify
  reason: evals declarados
- path: agents/unity-catalog-specialist.md
  action: modify
  reason: evals declarados
- path: agents/verifier.md
  action: modify
  reason: evals declarados
decisions:
- id: D1
  choice: casos de rota gerados da ROUTING_TABLE + negativos de dominios disjuntos;
    negative exige no_match (nunca below_cap)
  rejected:
  - 'evals: [arquivo de teste] para tudo (nao e eval por agent)'
  - casos a mao (deriva da tabela)
  rollback: reverter o commit da feature
covers:
- part: agent_eval_suite
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — AGENT_EVAL_SUITE
