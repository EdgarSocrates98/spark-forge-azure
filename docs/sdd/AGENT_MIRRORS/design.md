---
sdd: 1
feature: AGENT_MIRRORS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_MIRRORS/define.md
  sha256: 359464a069e4cdf19d37eefe947ac03a798e846a185616185e662996612bd3db
files:
- path: sparkforge_azure/agentmanifest/mirrors.py
  action: create
  reason: render/check/sync espelhando skills.mirrors
- path: scripts/sync_agent_mirrors.py
  action: create
  reason: verb de sync paralelo a sync_skill_mirrors
- path: scripts/check_skills_agents.py
  action: modify
  reason: agent_mirrors_in_sync no rollup
- path: tests/test_agent_mirrors.py
  action: create
  reason: contrato dos mirrors
- path: .claude/agents/custom/
  action: create
  reason: root de mirror Claude
- path: .agents/agents/
  action: create
  reason: root de mirror agents neutro
decisions:
- id: D1
  choice: file-per-agent (convencao .claude/agents/custom/<n>.md), nao dir-per-agent
    como skills
  rejected:
  - copiar manifest verbatim (host exige name/description)
  - editar agents/*.md em cada host (deriva)
  rollback: reverter o commit da feature
covers:
- part: agent_mirrors
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — AGENT_MIRRORS
