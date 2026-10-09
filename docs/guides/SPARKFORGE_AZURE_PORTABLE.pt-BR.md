# Spark Forge Azure — Quickstart Portátil

Ciclo completo a partir do `sparkforge-azure` **instalado** — sem o
checkout do código-fonte.

## Instalação

```text
pip install sparkforge-azure          # ou: pipx install sparkforge-azure
sparkforge-azure distribution inspect # pacote, assets, hosts — sem escrita
```

## Projeto único

```text
cd seu-repo
sparkforge-azure distribution init    # grava .sparkforge-azure/, .mcp.json, bloco no AGENTS.md
sparkforge-azure distribution status  # drift? assets gerenciados intactos?
sparkforge-azure distribution doctor  # preflight offline
```

`init` é idempotente — rode de novo para *reparar* assets gerenciados.
Segredos nunca entram em manifestos ou `.mcp.json`; o entry MCP invoca o
binário instalado, nunca um path de checkout.

## Workspace (monorepo / multi-repo)

```text
sparkforge-azure workspace init                 # na raiz compartilhada — sfw-<id>
sparkforge-azure workspace add app              # filho do root → path relativo
sparkforge-azure workspace add ../shared-lib    # fora do root → absoluto, declarado
sparkforge-azure workspace status               # membros, ciclos, drift
```

Dependências são declaradas, nunca inferidas:

```text
sparkforge-azure workspace add app --depends-on <project-id-da-lib>
```

## Contexto limitado

```text
sparkforge-azure context resolve --target app --scope target       # padrão
sparkforge-azure context resolve --target app --scope direct       # + deps diretas
sparkforge-azure context resolve --target app --scope transitive   # o fecho
sparkforge-azure context resolve --scope all                       # só explícito
```

Cada resolve grava um recibo (bytes lidos/evitados, projetos selecionados,
motivo de parada) — nada fora das raízes declaradas é lido.

## Mover / copiar

```text
mv repo ../outro-lugar && sparkforge-azure workspace add ../outro-lugar/repo
# mesmo project_id — o path antigo sumiu → realocação registrada

cp -r repo clone && cd clone && sparkforge-azure distribution init --regen-id
# a cópia precisa cunhar o próprio sfa-<id> antes do `workspace add` aceitar
```

## Detach

```text
sparkforge-azure distribution detach                 # integração fora, estado fica
sparkforge-azure distribution detach --purge-state   # .sparkforge-azure some
sparkforge-azure distribution detach --purge-cache   # só o cache
sparkforge-azure distribution detach --dry-run       # só reporta, sem escrever
sparkforge-azure distribution init                   # reattach — mesmo project_id
```

O que você editou continua seu: arquivos gerenciados e blocos de markers
modificados são preservados com warning — nunca revertidos.

## Economia

Limitado em tudo: TokenSave por projeto (confinado à raiz dele), scope
`target` por padrão, recibos contabilizam cada byte. Barato *e* honesto —
`bytes_avoided` está no recibo e `unresolved` nunca vira zero em silêncio.
