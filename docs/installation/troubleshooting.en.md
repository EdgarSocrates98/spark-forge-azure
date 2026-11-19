# Troubleshooting — Spark Forge Azure (EN)

| Symptom | Action |
|---|---|
| `command not found: sparkforge-azure` | run `./setup.sh` again; open a **new** terminal (launcher lands on PATH) |
| `FORGE-INSTALL-LOCKED` | another install is running or was interrupted; the lock expires and is recovered automatically — retry |
| `FORGE-INSTALL-PLAN-NOT-APPROVED` | mutations require `--yes` after reviewing `--dry-run` |
| `FORGE-INSTALL-NOT-A-REPO` | project scope needs a `.git` root or `--root` |
| `FORGE-INSTALL-DRIFT` | managed files changed on disk — run `repair` to heal managed regions, keep your edits |
| `FORGE-INSTALL-OWNERSHIP` | files managed by another forge/profile — no silent overwrite; use `--force` only deliberately |
| MCP `FAIL` + `stderr_tail` | missing dependency (e.g. the `mcp` extra) — install it and re-run `mcp-verify` |
| stale/partial install | `uninstall` removes only ledger-owned files; `status`/`doctor` show the truth |
| `lifecycle.state: blocked` | a gate refused — read `checks[].detail` (e.g. `approval: BLOCKED` = declined approval); nothing was written |
| `lifecycle.state: applied` | writes happened but verification did not conclude — run `install doctor`; `applied` ≠ `ready` |
| `lifecycle.state: unverified` | no install evidence at this scope — `install status`/`doctor` report what exists |
| `lifecycle.state: partially_applied` | subset applied (partial drift or mixed batch) — `install repair` converges |
| reinstall rewrote everything | it should not — an identical second run rewrites zero assets; if `counts.written > 0`, the receipt lists which paths changed and why (`managed_files[].action`) |

Português: [troubleshooting.md](troubleshooting.md).
