# Receita — abrir o host de IA (`sparkforge-azure ai`)

**O quê:** `sparkforge-azure ai` mede cada host (claude, devin, codex):
binário, versão, login e integração do repo. `--launch` abre o CLI do host
no diretório — CLI+TTY, um host nomeado, nunca via MCP.
**Por que:** antes de delegar, é preciso saber se o host está instalado,
logado e com a integração `healthy` — `ai` responde os três num recibo.
**Quando:** sessão nova, dúvida de login, ou antes de `agents route`.
**Quando não:** para verificar o handshake MCP — isso é
`install mcp-verify` (receita `verificar-mcp`).

## Passo a passo

```bash
sparkforge-azure ai                 # painel dos três hosts
sparkforge-azure ai devin           # um host: state + launch_command
sparkforge-azure ai devin --launch  # abre o devin neste repo (TTY)
```

## Interpretação

Estados por host: `NOT_DETECTED` (binário fora do PATH), `SUPPORTED`
(detectado, integração não-healthy ou sem medida), `NEEDS_LOGIN` (traz
`login_hint` — ex.: `devin auth login`), `READY` (logado + integração
`healthy`), `INTEGRATION_DEGRADED|BROKEN`. `--launch` sem TTY ou com `all`
devolve `launch_refused` + `launch_command` — nunca silêncio.

## Verificação

`READY` = binário + `--version` ok + `logged_in` true + integração
`healthy`. A versão vem do binário real, não de manifesto.

## Limitações

O recibo carrega só o booleano `logged_in` — a saída de `auth status` pode
listar caminhos de credencial e nunca entra no JSON. `sfa_ai` (MCP) expõe só
o painel: lançar é fronteira humana.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| `host_absent` | binário fora do PATH | instale o CLI do host ou corrija o PATH |
| `login_required` | detectado mas deslogado | rode o `login_hint` (`claude auth login`, `devin auth login`, `codex login`) |
| `no_tty` | `--launch` fora de terminal interativo | cole o `launch_command` num terminal seu |
