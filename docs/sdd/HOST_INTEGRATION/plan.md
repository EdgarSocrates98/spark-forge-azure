---
sdd: 1
feature: HOST_INTEGRATION
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/HOST_INTEGRATION/design.md
  sha256: "5025071ffe2a18b083c8e82049e3d63c191772a22666bb0644454640a20d3dbf"
tasks:
  - id: T1
    files:
      - sparkforge_azure/distribution/managed.py
    covers: [AC1, AC2, AC7]
    test:
      path: tests/test_host_integration.py
      name: test_marker_block_coexists_with_user_content
  - id: T2
    files:
      - sparkforge_azure/distribution/hostfiles.py
      - sparkforge_azure/distribution/service.py
      - sparkforge_azure/cli/cmd_distribution.py
    covers: [AC1, AC3, AC4]
    test:
      path: tests/test_host_integration.py
      name: test_mirrors_opt_in_and_ledgered
  - id: T3
    files:
      - sparkforge_azure/distribution/detach.py
    covers: [AC5, AC6]
    test:
      path: tests/test_host_integration.py
      name: test_detach_strips_block_preserves_user_text
  - id: T4
    files:
      - tests/test_architecture_layers.py
      - docs/reference/cli.md
      - docs/portability/HOST_INTEGRATION.md
      - docs/README.md
    covers: [AC1, AC4, AC7]
    test:
      path: tests/test_host_integration.py
      name: test_marker_drift_reported_not_silent
---

# HOST_INTEGRATION — plan

`managed.py` markers primeiro (mecanismo), `hostfiles.py` depois (política),
detach por último (reversão), docs no fim.

## Pontos não-óbvios

- `assess_file` markers compara `owned_key_hashes["block"]` com o sha do
  bloco *extraído* — edição fora dos markers não é drift.
- `strip_marker_block` retorna "" quando só havia o bloco → detach remove
  o arquivo; com conteúdo → reescreve sem a região.
- `_agent_sources()` lê de `_group_dir("agents")` — funciona idêntico em
  source checkout e wheel instalada (o audit de assets já garante o
  dual-mode).
- CLAUDE.md não é criado para hosts ausentes — `monkeypatch` no teste
  cobre o branch sem depender do ambiente.
