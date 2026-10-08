---
sdd: 1
feature: STREAMING_GRAPHFY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/STREAMING_GRAPHFY/define.md
  sha256: "585d2a553db237c6a2bd674c12af1f925ad77ddadd427124a549eb41fe07a23c"
files:
- path: sparkforge_azure/graph/stream.py
  action: create
  reason: "builder do grafo streaming"
decisions:
- id: D1
  choice: "camada stream no registry de grafos existente (como fabric), nao grafo paralelo"
  rejected:
  - "graph engine separado"
  rollback: "reusar camada azure generica; perde kinds tipados"
covers:
  - {part: graph/stream, acceptance: [AC1, AC2, AC3]}
---

# Design — STREAMING_GRAPHFY
