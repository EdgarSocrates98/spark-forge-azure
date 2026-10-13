---
sdd: 1
feature: HOST_PROOF_RECORDED
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/HOST_PROOF_RECORDED/design.md
  sha256: da43c680985eac8322029311dc0d317fe220f443dac71d3094d5ce5a70cfa485
tasks:
- id: T1
  files:
  - tests/test_host_proof.py
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_host_proof.py
    name: test_status_derives_from_artifact
- id: T2
  files:
  - sparkforge_azure/agentic/runtimes/host.py
  - evals/host_proof/claude_code.json
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_host_proof.py
    name: test_registry_reports_proof
---

# Plan — HOST_PROOF_RECORDED

T1 RED: testes contra adapter/registry esperando promocao por artefato.
T2: propriedades `status`/`proof` em `HostCLIAdapter` + transcript gravado
ja produzido pela execucao real anterior (evals/host_proof/claude_code.json).
