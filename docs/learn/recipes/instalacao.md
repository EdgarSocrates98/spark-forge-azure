# Receita — instalar o spark-forge-azure num projeto

**O quê:** `sparkforge-azure install` grava os ativos gerenciados (`.mcp.json`,
mirrors de skills/agents, bloco nos arquivos de instrução) e emite um recibo
`forge/InstallReceipt/v1` com cada check.
**Por que:** a instalação é o que liga o Forge ao seu host de IA — sem ela,
o MCP não aparece e as skills não são descobertas.
**Quando:** primeira vez no projeto, ou depois de `uninstall`.
**Quando não:** dentro do checkout do próprio repositório (instale num projeto
seu, não no fonte do Forge).

## Passo a passo

```bash
# no diretório do SEU projeto
pip install sparkforge-azure        # ou o extra com mcp: sparkforge-azure[mcp]
sparkforge-azure install --yes
sparkforge-azure install status
```

`--yes` é a aprovação explícita exigida para qualquer escrita — sem ela o
install recusa. Escolha de escopo: `--scope project` (padrão, grava no repo)
| `workspace` (manifesto multi-projeto) | `user` (global na máquina).
Escolha de host: `--host claude|devin|codex|copilot|all` (padrão detectado).

## Interpretação

O recibo lista `checks` por id (`mcp.json`, mirrors, bloco gerenciado…) com
`PASS`/`FAIL`/`NOT_APPLICABLE`. `NOT_APPLICABLE` é honesto — ex. Codex em
escopo projeto não lê `.mcp.json` (`mcp-scope:codex` diz isso e aponta o
caminho: `--scope user` ou `codex mcp add`).

## Verificação

`sparkforge-azure install status` deve voltar `healthy`; o host deve listar o
server `sparkforge-azure` (ex.: `devin mcp list`).

## Limitações

Não testa credencial Azure nem chamada de nuvem — só a integração local.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| recusa sem `--yes` | aprovação obrigatória | rode com `--yes` ou use o wizard da TUI |
| `mcp-scope:codex` NOT_APPLICABLE | Codex 0.160 não lê `.mcp.json` de projeto | `--scope user` ou `codex mcp add` |
| drift reportado | arquivo gerenciado editado à mão | `sparkforge-azure install repair` |
