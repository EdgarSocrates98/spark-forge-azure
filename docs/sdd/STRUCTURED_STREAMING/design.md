---
sdd: 1
feature: STRUCTURED_STREAMING
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/STRUCTURED_STREAMING/define.md
  sha256: "af1d33247606988b9e7ece37e4c61bab63266838064d965ac8b5024b7cd987fc"
files:
- path: sparkforge_azure/stream/progress.py
  action: create
  reason: "StreamingQueryProgress->facts + janelas"
- path: sparkforge_azure/stream/diagnose.py
  action: create
  reason: "cadeia: auth->network->capacity->partition->cg->progress->checkpoint->state->schema->processing->sink"
decisions:
- id: D1
  choice: "lag comparado por particao (source position vs consumer checkpoint) nunca metrica unica"
  rejected:
  - "lag escalar global"
  rollback: "colapsar para lag agregado; perde skew"
- id: D2
  choice: "checkpoint = estado operacional critico com ownership e compatibilidade"
  rejected:
  - "checkpoint como diretorio inerte"
  rollback: "tratar como blob container; perde semantics"
covers:
  - {part: progress+diagnose, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — STRUCTURED_STREAMING
