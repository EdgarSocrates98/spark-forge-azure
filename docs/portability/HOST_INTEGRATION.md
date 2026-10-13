# HOST_INTEGRATION — hosts suportados e arquivos gerenciados (W5)

`distribution init` integra o projeto com os hosts sem depender do
checkout de origem (prompt_evo_portable.md §65–§79). Toda escrita é
gerenciada pelo ledger — reversível via `distribution detach`.

## O que `init` escreve

| Arquivo | Modo | Quando |
|---|---|---|
| `.mcp.json` → `mcpServers.sparkforge-azure` | merge (chave possuída) | sempre — entry `sparkforge-azure mcp serve`, binário instalado, nunca path de checkout (§72–§75) |
| `AGENTS.md` | markers (bloco delimitado) | sempre — contrato genérico lido por Codex, Devin e agentes CLI |
| `CLAUDE.md` | markers | arquivo já existe **ou** host `claude` detectado |
| `.claude/agents/custom/*.md`, `.agents/agents/*.md` | file | só com `--with-mirrors` — render do catálogo `agents/` via `agentmanifest.mirrors` (a mesma geração do repo, §66) |

## Markers (§70–§71)

Conteúdo gerenciado em arquivo editável fica entre
`<!-- sparkforge-azure:begin -->` e `<!-- sparkforge-azure:end -->`:

- `init` *upserta* o bloco — conteúdo fora dos markers é byte-preservado.
- `status` reporta bloco removido/alterado como `modified` (drift) —
  nunca reconquista em silêncio.
- `detach` remove só o bloco; arquivo que esvazia é removido, arquivo com
  conteúdo de usuário é preservado.

## Detecção de hosts (§76–§77)

`distribution inspect|doctor` reporta `claude`, `devin`, `codex` como
`available` / `unavailable` / `unproven` — ausência nunca é falha.
Detecção só direciona quais arquivos opcionais aparecem (CLAUDE.md);
não há probing live nem escrita fora do projeto.

## O que não é gerado

- `.devin/`: Devin carrega `AGENTS.md` nativamente — nenhum arquivo
  específico é necessário (auditoria §67).
- Configs de home (`~/.claude`, `~/.codex`): fora de escopo — a integração
  é por-projeto; host global é decisão do usuário.
- MCP clients genéricos: qualquer cliente que leia `.mcp.json` padrão
  está coberto pela mesma chave.

## Reattach

`distribution init` é idempotente: rerun renova blocos e chaves sem tocar
conteúdo de usuário; `project_id` é preservado quando o state sobreviveu.
