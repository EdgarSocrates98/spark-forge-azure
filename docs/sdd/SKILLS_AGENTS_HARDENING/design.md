---
sdd: 1
feature: SKILLS_AGENTS_HARDENING
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/SKILLS_AGENTS_HARDENING/define.md
  sha256: "2d850b77800d1a50b297c767bcde4d166430bc5122d0b969620b2eddfd136f9d"
files:
- path: sparkforge_azure/agentmanifest/mirrors.py
  action: modify
  reason: render injeta tools (Read, Grep, Glob [+ Bash]) e description com "Use quando"
- path: sparkforge_azure/agentmanifest/model.py
  action: modify
  reason: validate_manifest recusa does_not que nao seja negacao
- path: agents/adf-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/adls-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/azure-databricks-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/coordinator.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/delta-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/event-hubs-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/fabric-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/iceberg-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/migration-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/networking-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/onelake-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/purview-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/spark-performance-specialist.md
  action: modify
  reason: does_not reescrito como negacao; ganha skill analyze-batch-loop
- path: agents/synapse-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: agents/unity-catalog-specialist.md
  action: modify
  reason: does_not reescrito como negacao
- path: sparkforge_azure/cli/cmd_analyze.py
  action: create
  reason: verbos analyze pyspark, judge, knowledge select sobre motores existentes
- path: sparkforge_azure/cli/main.py
  action: modify
  reason: registra cmd_analyze em COMMAND_MODULES
- path: sparkforge_azure/skills/model.py
  action: modify
  reason: tool_ref de CLI resolve contra command_paths(); planned_tool_refs opcional;
    corpo so cita comando real
- path: skills/analyze-batch-loop/SKILL.md
  action: modify
  reason: Procedimento com comandos reais (sem --kind/--show-skipped inexistentes)
- path: skills/azure-adls/SKILL.md
  action: modify
  reason: comandos reais (collect adls-meta/azure-rbac) e fallback manual
- path: skills/azure-bicep/SKILL.md
  action: modify
  reason: comandos reais (graph build/impact) e fallback manual
- path: skills/azure-data-factory/SKILL.md
  action: modify
  reason: comandos reais (graph build/impact) e fallback manual
- path: skills/azure-databricks/SKILL.md
  action: modify
  reason: collect workspace-graph com --manifest/--export; fallback manual
- path: skills/azure-entra/SKILL.md
  action: modify
  reason: comandos reais (collect azure-rbac) e fallback manual
- path: skills/azure-event-hubs/SKILL.md
  action: modify
  reason: analyze pyspark real; fallback manual para namespace
- path: skills/azure-finops/SKILL.md
  action: modify
  reason: collect workspace-graph correto; fallback manual para custo
- path: skills/azure-networking/SKILL.md
  action: modify
  reason: governance diagnose com arquivo de cenario; fallback manual
- path: skills/azure-observability/SKILL.md
  action: modify
  reason: collect workspace-graph correto; fallback manual para diagnostics
- path: skills/azure-purview/SKILL.md
  action: modify
  reason: graph query com --graph/--neighbors; fallback manual para lineage
- path: skills/azure-spark/SKILL.md
  action: modify
  reason: tokensave search com --root; spark-conf vira fallback manual
- path: skills/azure-synapse/SKILL.md
  action: modify
  reason: graph build com --root; fallback manual para pools/pipelines
- path: skills/azure-terraform/SKILL.md
  action: modify
  reason: comandos reais (graph build/impact) e fallback manual
- path: skills/delta-lake/SKILL.md
  action: modify
  reason: lab run com cenario real; _delta_log vira fallback manual
- path: skills/fabric-data-engineering/SKILL.md
  action: modify
  reason: analyze pyspark + graph build/impact reais; item metadata manual
- path: skills/fabric-onelake/SKILL.md
  action: modify
  reason: governance diagnose com arquivo; fallback manual para shortcuts
- path: skills/fabric-realtime/SKILL.md
  action: modify
  reason: fallback manual para eventstream/item (sem extrator)
- path: skills/iceberg/SKILL.md
  action: modify
  reason: lab run iceberg-small-files real; metadata vira fallback manual
- path: skills/spark-performance/SKILL.md
  action: modify
  reason: lab run spark-skew/verify reais; eventlog vira fallback manual
- path: skills/spark-streaming/SKILL.md
  action: modify
  reason: analyze pyspark + lab run cdc-duplicate-restart; fallback manual
- path: skills/unity-catalog/SKILL.md
  action: modify
  reason: collect unity-catalog + graph query reais; cenario governance arquivo
- path: skills/azure-adls/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais (collect/judge/graph/lab)
- path: skills/azure-bicep/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-data-factory/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-databricks/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais; must_include re-ancorado
- path: skills/azure-entra/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-event-hubs/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais; must_include re-ancorado
- path: skills/azure-finops/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-networking/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-observability/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-purview/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-spark/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-synapse/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/azure-terraform/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/delta-lake/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/fabric-data-engineering/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/fabric-onelake/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/fabric-realtime/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/iceberg/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/spark-performance/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/spark-streaming/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: skills/unity-catalog/evals/evals.yaml
  action: modify
  reason: expected_tools apontam para verbos reais
- path: sparkforge_azure/agentmanifest/routing.py
  action: modify
  reason: scan -> purview scan
- path: tests/test_skills_agents_hardening.py
  action: create
  reason: AC1-AC3, AC5-AC7
- path: tests/test_cli_analyze_judge.py
  action: create
  reason: AC4
- path: docs/surface.lock.json
  action: modify
  reason: regenerado (novos verbos)
- path: docs/reference/cli.md
  action: modify
  reason: documenta os verbos e reduz a lista de planejados
decisions:
- id: D1
  choice: A2 — expor so verbos com motor existente; demais analyze <kind> ficam em
    planned_tool_refs e saem do corpo
  rejected:
  - implementar 30 extratores agora
  - so reescrever skills (judge e analyze pyspark continuariam sem porta)
  rollback: reverter o commit da feature e regenerar mirrors/surface lock
- id: D2
  choice: mirror recebe tools Read, Grep, Glob e Bash apenas quando o manifest declara
    tool sfa_* (toda sfa_* tem verbo de CLI equivalente); Write/Edit/Web/Agent fora
  rejected:
  - nomes MCP do host (servidor nao registrado no projeto; nome nao documentado)
  - manter todas as tools
  rollback: remover a chave tools do render
- id: D3
  choice: knowledge select usa PackRegistry(knowledge/azure) com cache em
    .sparkforge-azure/knowledge-cache (gitignored), nunca dentro de knowledge/
  rejected:
  - cache default ao lado do pack (escreveria no repo)
  rollback: reverter cmd_analyze
covers:
- part: agent_mirrors
  acceptance:
  - AC1
  - AC2
  - AC3
- part: cli_verbs
  acceptance:
  - AC4
- part: skill_refs
  acceptance:
  - AC5
  - AC6
- part: wiring
  acceptance:
  - AC7
---

# Design — SKILLS_AGENTS_HARDENING

Bash em agent read-only e risco residual: o corpo do agent restringe a comandos
`sparkforge-azure` de leitura. Sem servidor MCP registrado, e o menor conjunto que
deixa o agent executar os verbos que o manifest declara.
