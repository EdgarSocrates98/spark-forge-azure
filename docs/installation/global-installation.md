# Instalação global (escopo user) — spark-forge-azure

Instala uma vez para todos os projetos do usuário:

```bash
sparkforge-azure install --scope user
```

Escreve em `~/.claude/`, `~/.agents/`, `~/.config/<host>/` e config MCP
global. Combinável com instalações de projeto: o nível mais específico
(`project`) sempre prevalece.

O escopo `user` **não** registra runtime de projeto em
`~/.forge/installations/` — só `project`/`workspace` bem-sucedidos o
fazem. Como nos demais escopos, nada é sobrescrito sem posse: arquivo
estrangeiro divergente num caminho gerenciado é preservado e reprova o
install (`preserved_foreign` no recibo, check `foreign-files` FAIL);
idêntico byte-a-byte fica fora do ledger e o uninstall não o remove.
