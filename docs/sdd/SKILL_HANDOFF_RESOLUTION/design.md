---
sdd: 1
feature: SKILL_HANDOFF_RESOLUTION
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/SKILL_HANDOFF_RESOLUTION/define.md
  sha256: 1940fcaf3c489203c6b12cfb7b657e4c0ff2d8c17e5dde7deddf34fcd78b9d3f
files:
- path: sparkforge_azure/skills/model.py
  action: modify
  reason: body_handoff_refs + check contra skills ∪ ALL_AGENT_IDS (lazy import; agentmanifest
    ja importa skills)
- path: skills/azure-synapse/SKILL.md
  action: modify
  reason: migration -> migration-specialist
- path: skills/iceberg/SKILL.md
  action: modify
  reason: migration -> migration-specialist
- path: skills/analyze-batch-loop/SKILL.md
  action: modify
  reason: normaliza handoff para formato alvo — desc
- path: tests/test_skills.py
  action: modify
  reason: testes nomeados AC1-AC3
- path: tests/test_architecture_layers.py
  action: modify
  reason: declara aresta skills->agentmanifest (lazy) na medicao
decisions:
- id: D1
  choice: A2 — alvo resolve em skills ∪ ALL_AGENT_IDS (mesmo namespace dos handoff_targets
    dos manifests)
  rejected:
  - handoff so entre skills (security-reviewer e cost-reviewer sao alvos reais)
  - sem validacao
  rollback: reverter o commit da feature
covers:
- part: handoff_resolution
  acceptance:
  - AC1
  - AC2
  - AC3
---

# Design — SKILL_HANDOFF_RESOLUTION
