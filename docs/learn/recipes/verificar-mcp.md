# Receita — verificar a integração MCP

**O quê:** `sparkforge-azure install mcp-verify` faz o handshake real com o
servidor `sfa_*` — initialize, `tools/list` e uma chamada — e devolve o
resultado como check do recibo.
**Por que:** "o arquivo `.mcp.json` existe" ≠ "o host fala com o server" —
só o handshake prova.
**Quando:** pós-instalação, depois de mexer no `.mcp.json`, ou quando o host
não lista o server.
**Quando não:** para medir o host em si — aí é `sparkforge-azure ai <host>`
(binário, versão, login, integração).

## Passo a passo

```bash
sparkforge-azure install mcp-verify            # handshake real
sparkforge-azure install status                # estado geral da instalação
sparkforge-azure ai all                        # painel dos hosts
sparkforge-azure ai devin --launch             # abre o host (TTY, um host só)
```

## Interpretação

`mcp-verify` PASS significa handshake + tools respondendo; FAIL traz o
motivo (server não sobe, comando errado, timeout). `ai` separa os quatro
sinais: binário, versão, `logged_in` (booleano — a saída de auth nunca entra
no recibo) e integração do repo.

## Verificação

No host instalado, o server `sparkforge-azure` deve aparecer (ex.:
`devin mcp list`) e `sfa_version` responde. 18 tools no catálogo.

## Limitações

Codex CLI 0.160 não lê `.mcp.json` de escopo projeto — o recibo declara
`mcp-scope:codex` `NOT_APPLICABLE`; o caminho é `--scope user` ou
`codex mcp add`. Lançar host nunca acontece via MCP — é fronteira humana.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| handshake recusa `command not found` | `sparkforge-azure` fora do PATH do host | instale no PATH ou aponte o `.mcp.json` |
| Codex não vê o server | limitação do host, não da instalação | `--scope user` / `codex mcp add` |
| `ai` marca NEEDS_LOGIN | host instalado mas deslogado | rode o `login_hint` do recibo (`devin auth login`, …) |
