# Instalação portátil — spark-forge-azure

Instala em qualquer diretório/repositório — sem estrutura prévia exigida.

```bash
cd <qualquer-projeto>
sparkforge-azure install                    # escopo projeto (padrão)
sparkforge-azure install --dry-run          # planeja sem escrever
sparkforge-azure install --profile minimal  # só CLI+MCP+marker
sparkforge-azure install --profile full     # skills + agents + todos os hosts
```

O que acontece: assets gerenciados vão para `.agents/`, `.claude/`,
`.devin/`, `.codex/` conforme os hosts detectados; `.mcp.json` ganha uma
entrada gerenciada; `AGENTS.md` recebe um bloco delimitado
`<!-- spark-forge-azure:managed -->` — conteúdo seu nunca é sobrescrito.

Perfis: `minimal` (essencial) · `recommended` (workflow completo, padrão)
· `full` (teto de disclosure — não é autorização extra).

## Recibo e lifecycle

Cada verbo devolve um recibo `forge/InstallReceipt/v1`
(`status: completed|planned|failed`, `checks`, `managed_files` com
`{path, sha256, kind, action}`, `counts`, `context` com bytes medidos)
mais um bloco `lifecycle` `forge/InstallLifecycle/v1` derivado da
evidência: `planned` → `applied` → `verified` → `ready`; `blocked`
quando um gate recusa (aprovação declinada sai `status: failed` + check
`BLOCKED`), `unverified` quando não há prova. `completed` significa "o
writer terminou" — readiness é `lifecycle.state`, nunca o `status`.

## Reinstalação incremental

Todo escritor compara bytes antes de gravar (arquivo, bloco de
marcador, chave JSON, ledger, receipts). Reinstalar a mesma seleção
reescreve **zero** assets (`counts.written: 0`) — só nasce um recibo
datado novo em `.sparkforge-azure/receipts/`.
