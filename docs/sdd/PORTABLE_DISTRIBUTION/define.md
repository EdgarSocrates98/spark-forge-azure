---
sdd: 1
feature: PORTABLE_DISTRIBUTION
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABLE_DISTRIBUTION/explore.md
  sha256: "3b5089e78d2bff95f30847638215426a1b8edf4f637ff9db80a52ff45f41cbb4"
hypothesis:
  claim: Um pacote `distribution/` com manifests gerenciados, ledger de assets e
    resolução de paths com origem registrada torna o Spark Forge Azure operável
    de forma portável — instalado, inicializável, inspecionável e desanexável
    sem depender do checkout — sem redesenhar a arquitetura
  prediction: "`distribution init` num diretório vazio cria identidade
    `sfa-*` + `.mcp.json` gerenciado; `inspect` em wheel instalada resolve o
    mesmo contrato; `detach` reverte apenas o registrado; 0 falhas novas no
    suite existente"
  experiment: pytest tests/test_distribution.py + ciclo init→detach→init em
    diretório temporário; prova de wheel fica para a feature PORTABILITY_PROOFS
acceptance:
  - id: AC1
    statement: "distribution inspect num diretório sem init retorna status ok
      com project/workspace None e nunca falha"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_inspect_uninitialized_is_ok
  - id: AC2
    statement: "`distribution init` cria project.yaml com `sfa-*` + entrada
      gerenciada `mcpServers.sparkforge-azure` em .mcp.json apontando para o
      binário instalado, e todo write vai para o ledger"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_init_writes_identity_and_mcp
  - id: AC3
    statement: init é idempotente — segunda execução mantém o mesmo project_id
      e reporta `kept`; `--regen-id` cunha identidade nova registrada
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_init_is_idempotent
  - id: AC4
    statement: "`distribution status` classifica uninitialized/initialized/
      partial/drifted/broken — asset removido → partial, asset modificado →
      drifted, manifest inválido → broken"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_status_broken_manifest
  - id: AC5
    statement: "`distribution detach` remove apenas assets gerenciados,
      preserva state por default, honra --dry-run e `init` religa com o mesmo
      project_id"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_detach_preserves_state_and_reattaches
  - id: AC6
    statement: config efetivo segue defaults < user < workspace < project <
      cli com origem por chave; chave desconhecida recusa em strict e é
      reportada fora dele
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_config_precedence_and_sources
  - id: AC7
    statement: manifests recusam chaves com cara de segredo e chaves
      desconhecidas — nunca ignoram silenciosamente
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_manifest_refuses_secret_like_keys
  - id: AC8
    statement: detecção de host nunca falha por ausência — ausente vira
      `unavailable`, não-verificado vira `unproven`; doctor é offline e nunca
      pede auth Azure
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_doctor_offline_and_uninitialized
  - id: AC9
    statement: "SPARKFORGE_AZURE_STATE_DIR e SPARKFORGE_AZURE_CACHE override
      resolvem com source `environment`; valores de switch (off/0/false) não
      viram diretório"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_state_dir_env_override
success:
  - id: SC1
    metric: "distribution inspect/init/status/doctor/detach executáveis e
      documentados na superfície travada"
    source: docs/surface.lock.json + docs/reference/cli.md
  - id: SC2
    metric: "0 arestas de import novas fora de EXCECOES_MEDIDAS"
    source: tests/test_architecture_layers.py
out_of_scope:
  - ciclo de vida do ForgeWorkspace (discover/init/add/status) — feature
    FORGE_WORKSPACE (W2)
  - resolução de contexto target/direct/transitive/all — CONTEXT_RESOLUTION (W4)
  - instalação per-host além de `.mcp.json` projeto-scope — HOST_PORTABILITY (W5)
  - prova de wheel instalada fora do checkout e evals/portability — W7
change_kinds:
  - tool_or_verb
---

# PORTABLE_DISTRIBUTION — define

## Por que produto, não arquitetura

O prompt pede portabilidade como *propriedade do produto*: o pacote instalado
funciona em qualquer diretório, identidade não depende de path, e o que o
lifecycle escreve pode ser revertido. Nada disso muda Facts→Rules→Findings,
o kernel L0/L1 ou as superfícies — é uma camada nova sobre a arquitetura
congelada (§208), não uma reorganização dela.

## Recusas nomeadas

Todo erro de lifecycle sai como `{"status":"refused","error":{"kind":...}}`
com `kind` do vocabulário fechado em `distribution/errors.py` (§177–§180):
nunca traceback, nunca `error` solto.
