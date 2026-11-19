# Troubleshooting — spark-forge-azure

| Sintoma | Ação |
|---|---|
| `command not found: sparkforge-azure` | rode `./setup.sh` de novo; abra terminal novo (launcher no PATH) |
| `FORGE-INSTALL-LOCKED` | outra instalação em curso; se foi interrompida, o lock expira/recupera sozinho |
| `FORGE-INSTALL-PLAN-NOT-APPROVED` | mutações exigem `--yes` (após o `--dry-run`) |
| `FORGE-INSTALL-NOT-A-REPO` | escopo project precisa de `.git` ou `--root` |
| doctor FAIL em mcp-handshake | `sparkforge-azure mcp-verify` mostra stderr_tail — geralmente dependência ausente |
| arquivo seu sumiu? | não deveria — instalação nunca sobrescreve conteúdo do usuário; backups em `<state_dir>/backups/` |
| drift detectado | `sparkforge-azure install repair` restaura regiões gerenciadas mantendo o resto |
| `lifecycle.state: blocked` | um gate recusou — leia `checks[].detail` (ex.: `approval: BLOCKED` = aprovação declinada); nada foi escrito |
| `lifecycle.state: applied` | writes aconteceram mas a verificação não concluiu — rode `install doctor`; `applied` ≠ `ready` |
| `lifecycle.state: unverified` | sem evidência de instalação no escopo — `install status`/`doctor` mostram o que existe |
| `lifecycle.state: partially_applied` | subconjunto aplicado (drift parcial ou batch misto) — `install repair` converge |
| reinstall regravou tudo | não deveria — segunda execução idêntica regrava zero assets; se `counts.written > 0`, o recibo lista quais paths mudaram e por quê (`managed_files[].action`) |
