---
sdd: 1
feature: DETACH_HARDENING
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/DETACH_HARDENING/define.md
  sha256: "6845d22933746eb4ec4c5658594b06ff8e78d55fdbf6b6dfab5c69de2e207cf2"
files:
  - path: sparkforge_azure/distribution/detach.py
    action: modify
    reason: "markers: strip-não-delete; purge granular state/cache; absent
      para missing; preserved_modified com warning; dry-run lista purges"
  - path: sparkforge_azure/distribution/config.py
    action: modify
    reason: "refuse_secret_keys em arquivo de usuário, --set e layers do
      resolve_config (§119–§121); manifests já guardados em manifests.py"
  - path: tests/test_distribution.py
    action: modify
    reason: "AC2, AC3, AC4, AC8 — cache/purge/dry-run/absent/secret-guard"
  - path: docs/portability/DETACH.md
    action: create
    reason: "doc do ciclo detach/reattach + decisão repair (§113)"
  - path: docs/README.md
    action: modify
    reason: indexar DETACH.md
decisions:
  - id: D1
    choice: "STATE_KINDS preservados por padrão; purge_state e purge_cache
      independentes (`state/cache` dentro do state dir)"
    rejected:
      - "um único --purge que apaga tudo — destrutivo por omissão (§84)"
      - "purge por kind individual — granularidade demais para 4 kinds"
    rollback: "flags novas são opt-in; default preserva como antes"
  - id: D2
    choice: "ordem de decisão: state-preservation → missing → modified →
      markers → merge → file; `modified` vence strip/remove"
    rejected:
      - "modified revertido ao blob do ledger — destruiria trabalho do
        usuário (§83)"
    rollback: "ordem é interna; recibo por entrada já registrava ações"
  - id: D3
    choice: "sem verbo `repair` — `init` idempotente cobre (§113)"
    rejected:
      - "verbo separado duplicaria init sem ganho e abriria surface"
    rollback: "documentado em DETACH.md; se surgir gap real, feature nova"
  - id: D4
    choice: "guarda de segredo por nome de chave em TODOS os carriers de
      config — arquivo de usuário, --set, layers do resolve; manifests já
      recusavam via `_refuse_secret_keys`"
    rejected:
      - "só em manifests — deixaria o user config file e --set sem guarda"
    rollback: "guarda nova só recusa o que antes passava — sem migração"
covers:
  - part: sparkforge_azure/distribution/detach.py (purge/absent/markers)
    acceptance: [AC1, AC2, AC3, AC4, AC5, AC6, AC7]
  - part: sparkforge_azure/distribution/config.py (refuse_secret_keys)
    acceptance: [AC8]
---

# DETACH_HARDENING — design

`detach` itera o ledger e classifica por `assess_file`: `missing` →
`absent`; `modified` → `preserved_modified` + warning; markers →
`strip_marker_block` (arquivo que esvazia é removido); merge →
`remove_json_key`; file → unlink. Entradas `STATE_KINDS` saem cedo quando
`purge_state=False`. Purges são `shutil.rmtree` por flag; dry-run emite
`would_remove:<dir>` sem escrever. Ledger re-salvo com o restante —
reattach via `init` retoma o `project_id` do manifesto preservado.

`config.py` ganha `refuse_secret_keys`: regex de nomes de chave com cara
de segredo aplicada ao user config file (`SPARKFORGE_AZURE_CONFIG`), a
`--set` overrides e a cada layer do `resolve_config`. O guarda de
manifesto em `manifests.py` permanece — camadas independentes.
