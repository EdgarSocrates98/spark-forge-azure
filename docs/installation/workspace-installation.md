# Instalação em workspace — spark-forge-azure

Monorepo/pasta com vários repositórios:

```bash
cd ~/minha-workspace
theforge install auto --scope workspace
# ou membro explícito (repetível):
theforge install auto --scope workspace --member sub/repo
```

Descoberta: membros são diretórios com `.git` **ou** manifest de
projeto (`forge.json`, `forge.agentic.json`, `pyproject.toml`,
`package.json`) até 2 níveis — diretório sem `.git` conta como membro.
Cada membro mantém seu próprio `.git`, estado e ledger isolados —
nenhum runtime duplicado.

A raiz do workspace recebe o contexto compartilhado (`.forge/context/`,
blocos gerenciados nos hosts) **sem** cunhar
`.sparkforge-azure/project.yaml` — instalar `project`/`workspace` num
membro depois continua permitido e vence pela precedência. Uma
instalação `workspace` bem-sucedida registra o forge em
`~/.forge/installations/spark-forge-azure.json` com os metadados
declarados do `forge.json` (operações, hosts, scopes, `mcp_verify_tool:
sfa_version`).

Precedência: `project > workspace > user` — instalação local do projeto
vence sempre, e conflitos são reportados, nunca sobrescritos.
