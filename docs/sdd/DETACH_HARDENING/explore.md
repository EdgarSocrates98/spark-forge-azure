---
sdd: 1
feature: DETACH_HARDENING
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: "Endurecer `distribution/detach.py` sobre o ledger da W1 —
      purge granular (state vs cache), markers com strip-não-delete, e
      guarda de chaves secretas nos carriers de config restantes
      (arquivo do usuário, `--set`, layers do resolve)"
    tradeoffs:
      - reutiliza a máquina de drift já provada; nenhum verbo novo
  - id: B
    summary: "Criar `distribution repair` como verbo separado que reescreve
      assets faltantes/íntegros"
    tradeoffs:
      - "proibido pelo spec (§113: avaliar, só criar se init idempotente não
        resolve); init já é o repair — reescreve managed, preserva modified,
        e status/doctor mostram o drift antes"
  - id: C
    summary: Detach destrutivo por padrão (apaga .sparkforge-azure inteiro)
    tradeoffs:
      - "proibido pelo spec (§84–§85: state e cache preservados por default;
        purge só por flag explícita)"
chosen: A
---

# DETACH_HARDENING — explore

O spec (§80–§89) pede detach seguro e reversível. A W1 já entregou o
esqueleto ledger-driven e a W5 adicionou o modo `markers`. Esta onda fecha
o contrato: política explícita de estado/cache, dry-run honesto (inclui os
purges), ausência como `absent` (nunca erro), reattach com o mesmo
`project_id`, e a guarda de segredo nos carriers de config que ainda não a
tinham (`distribution/config.py` — arquivo do usuário via
`SPARKFORGE_AZURE_CONFIG`, `--set` e cada layer do `resolve_config`). A
guarda de manifests já existia em `manifests.py` (`manifest_invalid`) —
mantida como camada, não duplicada.

## Evidência prévia

- `tests/test_distribution.py::test_detach_*` (W1) — preserve/reattach/
  purge/dry-run já verdes.
- `tests/test_host_integration.py::test_detach_strips_block_*` (W5) —
  strip de marker com conteúdo de usuário preservado.
