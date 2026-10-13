---
sdd: 1
feature: AGENTS_REFERENCE_DOC
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENTS_REFERENCE_DOC/define.md
  sha256: 63506e5873257fdaf7e0c8ef31a1145dfc450849ca5d9765c629754da3c52226
files:
- path: scripts/gen_agents_doc.py
  action: create
  reason: gerador do catalogo
- path: docs/reference/agents.md
  action: create
  reason: doc gerada
- path: tests/test_agents_doc.py
  action: create
  reason: sync test
- path: docs/README.md
  action: modify
  reason: index entry
decisions:
- id: D1
  choice: render(root) -> str puro + main() escreve; colunas Agent/Kind/Domain/Autonomy/Evals
  rejected:
  - doc autoral
  - incluir body inteiro (ruido)
  rollback: reverter o commit da feature
covers:
- part: agents_reference_doc
  acceptance:
  - AC1
  - AC2
---

# Design — AGENTS_REFERENCE_DOC
