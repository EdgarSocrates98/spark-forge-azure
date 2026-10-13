---
sdd: 1
feature: SKILLS_REFERENCE_DOC
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/SKILLS_REFERENCE_DOC/define.md
  sha256: 262adf9e993ab9c49f7d941b406a7f8485b3df26be8c56a64aa124fb4f1a1863
files:
- path: scripts/gen_skills_doc.py
  action: create
  reason: gera docs/reference/skills.md do corpus
- path: docs/reference/skills.md
  action: create
  reason: catalogo gerado
- path: tests/test_skills.py
  action: modify
  reason: teste de sync (padrao mirrors)
- path: docs/README.md
  action: modify
  reason: indexar o novo doc (gate docs-index)
- path: docs/sdd/README.md
  action: modify
  reason: grill gate mapeado nos campos SDD
- path: docs/reference/cli.md
  action: modify
  reason: sdd check era implementado, nao planejado (stale)
decisions:
- id: D1
  choice: Doc gerada + teste de sync em vez de doc manual
  rejected:
  - doc manual (deriva)
  - verbo novo de CLI (escopo desnecessario)
  rollback: reverter o commit da feature
covers:
- part: skills_reference
  acceptance:
  - AC1
  - AC2
  - AC3
---

# Design — SKILLS_REFERENCE_DOC
