---
sdd: 1
feature: EVENT_HUBS_DEEP
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/EVENT_HUBS_DEEP/define.md
  sha256: "6c4bb2b2263dcbeaa811de7291fb8ba48fa03852d172928bd1920456c33a7ef7"
files:
- path: sparkforge_azure/stream/__init__.py
  action: create
  reason: "pacote do vertical"
- path: sparkforge_azure/stream/model.py
  action: create
  reason: "contratos EH + camadas"
- path: sparkforge_azure/stream/casefile.py
  action: create
  reason: "loader do bundle stream"
- path: sparkforge_azure/stream/extract.py
  action: create
  reason: "artifacts->facts com redacao"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade de hub/namespace; display name vira attr"
  rejected:
  - "name-based identity"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
- id: D2
  choice: "metricas como series temporais com janela+freshness; ponto unico nao e trend"
  rejected:
  - "scalar latest-only"
  rollback: "achatar para ultimo ponto; perde semantica de trend"
covers:
  - {part: model+casefile+extract, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — EVENT_HUBS_DEEP
