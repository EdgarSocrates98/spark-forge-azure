---
sdd: 1
feature: HOST_PROOF_RECORDED
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/HOST_PROOF_RECORDED/define.md
  sha256: 3d3b15a26cad94ef6fcf94abab3ede1f6d8fa831804dae895497038d6d770955
files:
- path: sparkforge_azure/agentic/runtimes/host.py
  action: modify
  reason: status/proof derivam de evals/host_proof/<runtime>.json
- path: evals/host_proof/claude_code.json
  action: create
  reason: transcript real do ping minimo via ClaudeCodeAdapter
- path: tests/test_host_proof.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: artefato de prova e a fonte — adapter le o JSON e promove so se
    status==completed e trace_ref sha256 presentes; sem artefato segue
    adapter_implemented
  rejected:
  - flag/env var manual (§9 proibe status sem evidencia)
  - prova compartilhada entre hosts (cada runtime exige transcript proprio)
  rollback: remover leitura de artefato + apagar evals/host_proof/
covers:
- part: host_proof_recorded
  acceptance:
  - AC1
  - AC2
  - AC3
---

# Design — HOST_PROOF_RECORDED

`HostCLIAdapter.status`/`proof` viram propriedades: procuram
`evals/host_proof/<runtime>.json` a partir do repo root (resolvido pelo
proprio modulo). Transcript valido = `status: completed` + `trace_ref`
com prefixo `sha256:`. Qualquer outra forma (ausente, JSON quebrado,
status!=completed, sem trace_ref) => `adapter_implemented`, `proof=None`.
