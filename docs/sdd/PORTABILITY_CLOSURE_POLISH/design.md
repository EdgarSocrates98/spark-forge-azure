---
sdd: 1
feature: PORTABILITY_CLOSURE_POLISH
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABILITY_CLOSURE_POLISH/define.md
  sha256: "39e0e8a63ae781ae389a46ef87c61a0b3fea453f99fe6999c88f7250053e8f9a"
files:
  - path: scripts/gen_current_state.py
    action: create
    reason: "AC1 — generator que deriva cada campo de fonte viva; --check
      compara ignorando MAIN_SHA (todo commit muda HEAD, §86)"
  - path: docs/CURRENT_STATE.md
    action: create
    reason: "AC1 — doc gerado com header do-not-hand-edit; nunca editado
      manualmente"
  - path: scripts/check_portability.py
    action: modify
    reason: "AC3 — checks novos: FAILURE_KINDS ⊆ TROUBLESHOOTING, quickstart
      commands ⊆ surface lock, CURRENT_STATE fresco"
  - path: docs/portability/PORTABILITY_OUTCOME.md
    action: modify
    reason: "AC2 — seção 'Post-closure freshness update' com SHAs; snapshot
      de closure preservado"
  - path: docs/portability/PORTABILITY_AUDIT.md
    action: modify
    reason: "nota de supersessão — audit histórico não reescrito"
  - path: docs/portability/WORKSPACES.md
    action: modify
    reason: "distinguir .sparkforge-azure/workspace.yaml (projetos) de
      sparkforge-azure.workspace.yaml (cloud boundary)"
  - path: docs/README.md
    action: modify
    reason: "indexar CURRENT_STATE.md"
  - path: tests/test_distribution.py
    action: modify
    reason: "AC4 — verbo pré-existente verde sem project.yaml"
  - path: docs/claims.lock.json
    action: modify
    reason: "re-stamp final depois de todos os gates verdes (§106)"
  - path: evals/portability/reports/portability-matrix.json
    action: modify
    reason: "relatório commitado estava velho (1 caso); regerado com os 10"
decisions:
  - id: D1
    choice: "CURRENT_STATE.md gerado, nunca editado à mão"
    rejected:
      - "doc manual — drift certo"
      - "gate novo check_portability_docs.py — spec prefere estender o
        existente (§116)"
    rollback: "script é novo; apagar o doc+script reverte"
  - id: D2
    choice: "paridade atual numa seção 'Post-closure freshness update' do
      OUTCOME, com SHAs das três refs amarrados"
    rejected:
      - "reescrever a matriz original no lugar — apaga história"
      - "CURRENT_PARITY.md separado — doc a mais sem ganho (§27–§28)"
    rollback: "seção aditiva; remover a seção reverte"
  - id: D3
    choice: "gate valida presença do kind no troubleshooting, não o texto
      do unlock — kind é contrato, frase pode evoluir (§54)"
    rejected:
      - "validar unlock byte-a-byte — §54 proíbe"
      - "executar comandos do quickstart — §64 proíbe; valida prefixo no
        surface lock"
    rollback: "checks novos falham fechado; remover os blocos reverte"
  - id: D4
    choice: "prova de backward compat = `main([\"version\"]) == 0` sem
      project.yaml (§125–§127)"
    rejected:
      - "depender só dos testes uninitialized de inspect/status/doctor —
        cobrem só verbos de distribuição"
    rollback: "teste aditivo; apagar reverte"
covers:
  - part: scripts/gen_current_state.py + docs/CURRENT_STATE.md
    acceptance: [AC1]
  - part: docs/portability/PORTABILITY_OUTCOME.md (seção post-closure)
    acceptance: [AC2]
  - part: scripts/check_portability.py (3 checks novos)
    acceptance: [AC3]
  - part: tests/test_distribution.py (backward compat)
    acceptance: [AC4]
---

# PORTABILITY_CLOSURE_POLISH — design

Duas frentes: (1) *estado medido* — generator que deriva cada campo de
fonte viva e um doc gerado verificável por `--check`; (2) *paridade* —
recomputada de `origin/main` real das refs (não do audit histórico),
escrita como seção nova datada por SHAs.

Nada toca runtime: só `scripts/` (gates), `tests/` (uma prova de backward
compat) e `docs/`. O freeze permanece frozen por construção.
