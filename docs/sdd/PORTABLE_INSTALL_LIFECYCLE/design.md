---
sdd: 1
feature: PORTABLE_INSTALL_LIFECYCLE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/PORTABLE_INSTALL_LIFECYCLE/define.md
  sha256: "df17fc3da3e58b81b983fc47c15b437296ec53c811b524bc83c0f7d3f396839d"
files:
  - {path: sparkforge_azure/install/service.py, action: create, reason: "ciclo de vida forge/* sobre o ledger do distribution; profiles e escopos"}
  - {path: sparkforge_azure/install/__init__.py, action: create, reason: "pacote"}
  - {path: sparkforge_azure/cli/cmd_install.py, action: create, reason: "verbo install com op posicional (apply default)"}
  - {path: sparkforge_azure/_installkit.py, action: create, reason: "engine compartilhado vendored (byte-identical com stamp) — locks, escopo, handshake MCP, registry"}
  - {path: sparkforge_azure/cli/main.py, action: modify, reason: "registrar cmd_install + estender exit-0 set com statuses forge/*"}
  - {path: pyproject.toml, action: modify, reason: "per-file-ignore ruff p/ fonte vendored"}
  - {path: tests/test_install_lifecycle.py, action: create, reason: "prova as 8 ACs"}
  - {path: docs/reference/cli.md, action: modify, reason: "documentar o verbo (gate docs_surface)"}
  - {path: docs/surface.lock.json, action: modify, reason: "lock regenerado com install (gate surface_lock)"}
decisions:
  - id: D1
    choice: "adapter sobre distribution.service/ledger em vez de portar o kit de ledger do installkit"
    rejected: ["dois ledgers: drift conflitante, estado duplicado .sparkforge-azure + .forge no mesmo target"]
    rollback: "deletar install/ + cmd_install + entrada em COMMAND_MODULES"
  - id: D2
    choice: "espelhos de skills escritos por _install_skill_mirrors com render_mirror + record_file no mesmo ledger"
    rejected: ["espelhos fora do ledger: detach não removeria, drift invisível"]
    rollback: "n/d"
  - id: D3
    choice: "install usa op posicional (install status) em vez de subparser aninhado"
    rejected: ["install status como subparser: verboso, diverge da UX dos irmãos sem ganho"]
    rollback: "n/d"
  - id: D4
    choice: "FileNotFoundError no handshake MCP vira BLOCKED (incompleto), não FAIL (defeito) — fix no canonical do the-forge re-vendored a todos"
    rejected: ["FAIL para CLI ausente: teste e doctor quebrariam em checkout sem instalação, reportando defeito onde não há"]
    rollback: "n/d"
covers:
  - {part: install/service.py + cmd_install.py, acceptance: [AC1, AC2, AC3, AC4, AC5, AC6, AC7]}
  - {part: cli/main.py + surface.lock + cli.md, acceptance: [AC8]}
---

# Design — PORTABLE_INSTALL_LIFECYCLE

`install` delega toda a mecânica de ownership ao que o repo já prova:
`distribution.initialize` (apply), `assess_ledger` (drift), `detach`
(uninstall), `install_host_assets` (escopo user). O installkit vendored
supre o que falta: resolução de escopo, lock não-bloqueante, handshake
MCP, recibos/saúde `forge/*`, registry `~/.forge`.
