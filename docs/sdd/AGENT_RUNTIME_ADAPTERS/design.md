---
sdd: 1
feature: AGENT_RUNTIME_ADAPTERS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_RUNTIME_ADAPTERS/define.md
  sha256: 554e50e28e5496e8d5e8cd5b9506c31aa6f1ef4615bd3648b34fcc87103b0689
files:
- path: sparkforge_azure/agentic/runtimes/__init__.py
  action: create
  reason: pacote de adapters
- path: sparkforge_azure/agentic/runtimes/base.py
  action: create
  reason: ExecutionMode/UsageStatus/RuntimeStatus/SpawnResult v2/protocol
- path: sparkforge_azure/agentic/runtimes/generic.py
  action: create
  reason: adapter generico (floor, INLINE)
- path: sparkforge_azure/agentic/runtimes/playbook.py
  action: create
  reason: adapter playbook — executa roles deterministicas inline
- path: sparkforge_azure/agentic/runtimes/host.py
  action: create
  reason: stubs fail-closed claude_code/devin_cli/devin_desktop/codex
- path: sparkforge_azure/agentic/runtimes/registry.py
  action: create
  reason: registry canonico runtime→adapter→status→proof
- path: tests/test_agentic_runtimes.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: adapters host detectam binario (shutil.which) e sem prova
    retornam runtime_unavailable — ADAPTER_IMPLEMENTED sem fingir spawn
  rejected:
  - adapter fake que retorna "would spawn" (§14 proibe)
  - fingir HOST_PROVEN sem transcript (§9 proibe)
  rollback: remover agentic/runtimes/ + teste
covers:
- part: agent_runtime_adapters
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
  - AC5
---

# Design — AGENT_RUNTIME_ADAPTERS
