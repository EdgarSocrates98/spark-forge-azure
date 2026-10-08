---
sdd: 1
feature: SKILLS_REFERENCE_DOC
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Catalogo de skills escrito a mao em docs/reference/
  tradeoffs:
  - rapido
  - deriva na primeira mudanca de skill
- id: A2
  summary: scripts/gen_skills_doc.py gera docs/reference/skills.md; teste de sync
    impede drift (padrao mirrors)
  tradeoffs:
  - deterministico
  - uma regeneracao a mais no fluxo
- id: A3
  summary: Doc + grill gate do Loop Factory como disciplina de intake no sdd/README
  tradeoffs:
  - fortalece intake sem mudar contrato
  - doc-only
chosen: A2 + A3 — doc gerada (evidence-backed, sem drift) + grill gate documentado
---

# Explore — SKILLS_REFERENCE_DOC

docs/reference/ cobre cli, knowledge-packs e mcp-tools — mas nao existe
catalogo das 22 skills. A linha Loop Factory (spec e o estado; automate
verificacao, nao decisao) sugere a forma: a doc e gerada do corpus versionado
igual aos mirrors, com teste de sync. O grill gate do Loop Factory mapeia
direto nos campos do SDD (out_of_scope, hypothesis, success) e vira
disciplina de intake documentada em docs/sdd/README.md.
