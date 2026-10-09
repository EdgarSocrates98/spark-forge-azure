# PORTABLE_DISTRIBUTION — lifecycle portável (W1)

O que torna o Spark Forge Azure portável *por instalação*: um pacote
`sparkforge_azure/distribution/` que resolve todos os paths com origem
registrada, mantém identidade de projeto independente de localização,
inventaria os assets empacotados e registra num ledger tudo o que escreve —
o que torna `detach` seguro e reversível.

É camada de produto sobre a arquitetura congelada (§208): reusa `paths`,
`durable` e `doctor`; nenhum kernel ou domínio mudou.

## Verbos

| Verbo | O que faz |
|---|---|
| `distribution inspect [--root R]` | resolve e reporta paths (valor + fonte), identidades, config efetivo com proveniência, inventário de assets com sha256, hosts detectados — sem mutação |
| `distribution init [--root R] [--name N] [--regen-id]` | cria `.sparkforge-azure/project.yaml` (`project_id` `sfa-*`) + chave gerenciada `mcpServers.sparkforge-azure` em `.mcp.json` + ledger + receipt. Idempotente |
| `distribution status [--root R]` | `uninitialized`/`initialized`/`partial`/`drifted`/`broken` + drift por asset |
| `distribution doctor [--root R]` | saúde **offline**, sem auth Azure; hosts ausentes são `unavailable`/`unproven`, nunca falha |
| `distribution detach [--root R] [--dry-run] [--purge-state] [--purge-cache]` | remove apenas o que o ledger registra; state preservado por default; `init` religa |

## Estado local — `.sparkforge-azure/`

```
project.yaml                  identidade relocável
workspace.yaml                ForgeWorkspace (lido aqui; CRUD na W2)
managed.json                  ledger de assets gerenciados
receipt-distribution.json     recibo do último init
cache/                        raiz de cache local
```

`.mcp.json` na raiz é o único arquivo fora do state dir: possuímos apenas a
chave `mcpServers.sparkforge-azure` → `sparkforge-azure mcp serve` (binário
instalado, nunca path de checkout). Chave alheia com valor diferente é
**conflito preservado** — reportado, não sobrescrito.

## Identidade ≠ localização (§38–§43)

`project_id` é um `sfa-<uuid>` gerado uma vez e persistido; mover
`a/projeto` → `b/projeto` mantém o id (paths declarados dentro do workspace
resolvem contra a raiz *atual*). Cópia intencional usa `init --regen-id` —
registrado no receipt, nunca silencioso. O modelo api-forge (`sha256(path)`)
foi rejeitado no audit (D1).

`workspace add` separa os dois casos (W3):

- **Relocação**: o path antigo declarado **não existe mais** → `action:
  relocated`, manifest atualizado para a nova localização, mesma identidade.
- **Cópia/clone**: o path antigo **ainda existe** e o candidato traz o mesmo
  `project_id` → `identity_collision` com unlock
  `distribution init --regen-id` na cópia (ou `workspace remove` na antiga).
  Dois diretórios vivos nunca dividem um `project_id` em silêncio.
- **Path ocupado**: path já declarado por **outro** id → `identity_collision`.

### Namespaces lógicos

Quando `SPARKFORGE_AZURE_STATE_DIR`/`SPARKFORGE_AZURE_CACHE` apontam um root
**compartilhado** (vários projetos), o estado é namespaced pelo id lógico —
nunca pelo path absoluto:

```
<state_root>/projects/<project_id>/…        inclui local/codeintel/graph.sqlite3
<cache_root>/<workspace_id>/projects/<project_id>/…
```

Sem override, o layout clássico `<projeto>/.sparkforge-azure/` é preservado
(root já é por-projeto, namespacing seria redundante). `inspect` reporta os
três (`namespaces.state_dir|cache_dir|codeintel_db`) com o projeto resolvido.

## Paths com fonte registrada (§45)

`resolve_paths` emite valor + `source` ∈ `default|environment|discovery|argument`:

- `SPARKFORGE_AZURE_STATE_DIR` continua soberano (mesmo nome de `paths.state_dir()`).
- `SPARKFORGE_AZURE_CACHE` override de cache; valores `on|off|0|1|true|false`
  são switch de economia, nunca diretório.
- `SPARKFORGE_AZURE_CONFIG` aponta o config de usuário — lido, nunca escrito.
- Sem overrides, state ancora na raiz do projeto descoberta, senão no cwd —
  idêntico ao comportamento anterior (§181).

## Config com precedência (§44–§47)

`defaults < user < workspace < project < cli` — cada chave efetiva carrega a
camada que venceu. Vocabulário fechado (`KNOWN_CONFIG_KEYS`); chave
desconhecida **recusa** em modo estrito e é reportada como `unknown_keys` em
inspect. Nada é ignorado em silêncio.

## Ledger gerenciado (§82, §110)

`managed.json` registra `{path, kind, sha256, mode, owned_keys,
owned_key_hashes, host}` por asset. `mode: merge` grava o sha256 do *valor*
de cada chave possuída — `status` detecta não só chave removida como valor
alterado. Hashes são marcadores de integridade, **não assinaturas** (§108).

## Detach (§80–§89)

Só remove o registrado. `project.yaml`/`workspace.yaml`/receipt são *state* —
preservados por default; `--purge-state`/`--purge-cache` são opt-outs
explícitos. Asset modificado depois do nosso write é trabalho do usuário:
preservado com warning. `--dry-run` reporta sem escrever. Reattach é `init`
idempotente — mesmo `project_id` quando state foi preservado.

## Estados de drift (§111–§112)

`clean` não é emitido separadamente — `initialized` com drift vazio já é o
estado limpo; `partial` = asset gerenciado ausente; `drifted` = modificado;
`broken` = manifest ilegível/inválido; `uninitialized` = nada descoberto.

## Falhas nomeadas (§177–§180)

`{"status":"refused","error":{"kind","detail","unlock?"}}` com `kind` do
vocabulário fechado em `distribution/errors.py`: `workspace_not_found`,
`project_not_initialized`, `identity_collision`, `manifest_invalid`,
`dependency_cycle`, `managed_asset_drift`, `host_unavailable`,
`config_invalid`, `path_outside_root`, `unsupported`.
