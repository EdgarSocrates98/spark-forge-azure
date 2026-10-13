# Instalação global (escopo user) — spark-forge-azure

Instala uma vez para todos os projetos do usuário:

```bash
sparkforge-azure install --scope user
```

Escreve em `~/.claude/`, `~/.agents/`, `~/.config/<host>/` e config MCP
global. Combinável com instalações de projeto: o nível mais específico
(`project`) sempre prevalece.
