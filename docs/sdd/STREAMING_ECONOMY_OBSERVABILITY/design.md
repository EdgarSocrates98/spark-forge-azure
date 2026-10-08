---
sdd: 1
feature: STREAMING_ECONOMY_OBSERVABILITY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/STREAMING_ECONOMY_OBSERVABILITY/define.md
  sha256: "d97ff99c194aa1c86c4ac468d94898b9d52af20ebe2d00fcae4d04d706d2d84e"
files:
- path: sparkforge_azure/stream/pipeline.py
  action: create
  reason: "run_stream_case end-to-end"
- path: sparkforge_azure/stream/suite.py
  action: create
  reason: "suite runner"
- path: sparkforge_azure/stream/fingerprint.py
  action: create
  reason: "env fingerprint para memory reuse"
- path: sparkforge_azure/cli/cmd_diagnose.py
  action: modify
  reason: "verbo stream"
- path: sparkforge_azure/mcp/tools.py
  action: modify
  reason: "sfa_diagnose_stream"
- path: sparkforge_azure/doctor.py
  action: modify
  reason: "check streaming_vertical"
decisions:
- id: D1
  choice: "diagnose stream como irmao de diagnose fabric; nenhum verbo universal adivinha vertical"
  rejected:
  - "diagnose --vertical flag"
  rollback: "fundir em flag; esconde fronteira de dominio"
- id: D2
  choice: "packs com vertical:stream; delta_perf/cross_environment compartilhados so quando semantics coincidem"
  rejected:
  - "novo silo de knowledge"
  rollback: "marcar packs stream como shared; polui escopo access"
covers:
  - {part: pipeline+surfaces+knowledge, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — STREAMING_ECONOMY_OBSERVABILITY
