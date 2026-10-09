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
