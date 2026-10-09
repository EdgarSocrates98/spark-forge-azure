---
sdd: 1
feature: DETACH_HARDENING
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/DETACH_HARDENING/explore.md
  sha256: "4891691de23ed1f67d6fb12a7cfcdf6a1f3570b01806c651136856ce46e07d7f"
hypothesis:
  claim: "Detach sobre o ledger — estado e cache preservados por padrão,
    purge granular por flag, strip de markers, `absent` para assets
    sumidos e `preserved_modified` para trabalho do usuário — é reversível
    e nunca destrutivo por omissão"
  prediction: "detach remove só entradas do ledger; `--purge-state`/
    `--purge-cache` são independentes; `--dry-run` reporta `would_*` sem
    escrever; `distribution init` re-anexa com o mesmo project_id quando o
    estado sobreviveu"
  experiment: pytest tests/test_distribution.py tests/test_host_integration.py
acceptance:
  - id: AC1
    statement: detach sem flags preserva project.yaml/workspace.yaml/ledger
      e devolve state_preserved=True
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_detach_preserves_state_and_reattaches
  - id: AC2
    statement: "--purge-cache remove só cache; --purge-state remove o dir
      de estado; flags independentes"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_detach_cache_preserved_by_default_purged_on_flag
  - id: AC3
    statement: "--dry-run reporta would_remove/would_strip_block/purges
      would_remove:<dir> sem mutar nada"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_detach_dry_run_purge_lists_but_keeps
  - id: AC4
    statement: asset managed ausente vira `absent` no recibo — nunca erro
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_detach_missing_asset_is_absent_not_error
  - id: AC5
    statement: "markers intactos são stripados (só o bloco sai); arquivo
      com conteúdo de usuário sobrevive"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_detach_strips_block_preserves_user_text
  - id: AC6
    statement: "asset managed modificado é preservado com warning — user
      work nunca é revertido"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_detach_modified_managed_file_preserved
  - id: AC7
    statement: "reattach via `distribution init` retoma o mesmo project_id
      quando o estado foi preservado"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_detach_preserves_state_and_reattaches
  - id: AC8
    statement: "chaves com cara de segredo são recusadas no arquivo de
      usuário, --set e layers do resolve_config (config_invalid)"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_user_config_and_set_refuse_secret_keys
success:
  - id: SC1
    metric: "0 deleções fora do ledger; 0 writes em --dry-run; estado
      sobrevive por padrão a qualquer detach"
    source: sparkforge_azure/distribution/detach.py
out_of_scope:
  - "`distribution repair` — `init` idempotente já é o repair (§113)"
  - purge de estado em raízes externas ao projeto — namespace da W3 governa
  - garbage collection/retention de cache — política separada, não detach
change_kinds:
  - tool_or_verb
---

# DETACH_HARDENING — define

## Contrato

`distribution detach [--dry-run] [--purge-state] [--purge-cache]`:

1. Itera o ledger; por entrada decide: state-preserve → `absent` →
   `preserved_modified` → strip markers → excise merge key → remove file.
2. Estado (`project.yaml`, `workspace.yaml`, recibos, ledger) preservado
   por padrão; `--purge-state` remove `.sparkforge-azure`, `--purge-cache`
   remove só `state/cache` — independentes.
3. `--dry-run` reporta `would_*` sem escrever nada.
4. Reattach é `distribution init` — mesmo `project_id` com estado vivo.

## Não-objetivos deliberados

`repair` como verbo separado fica fora: `init` reescreve managed assets,
preserva `modified` e `status`/`doctor` já reportam o drift (§113).
