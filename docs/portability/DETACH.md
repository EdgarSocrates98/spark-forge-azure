# DETACH — desanexar com segurança e reverter (W6)

`sparkforge-azure distribution detach` desfaz exatamente o que o ledger
registrou — e nada mais (prompt_evo_portable.md §80–§89). O objetivo é que
remover a integração nunca custe trabalho do usuário.

## Modelo

Toda escrita de `distribution init` fica registrada em
`.sparkforge-azure/managed-ledger.json` com `path`, `kind`, `mode`,
`sha256` (arquivo) ou `owned_keys` + `key_shas` (merge) ou
`block_sha256` (markers). Detach percorre o ledger e decide por entrada:

| Estado atual | Ação |
|---|---|
| `missing` | `absent` — só sai do ledger; nunca é erro |
| `modified` | `preserved_modified` + warning — conteúdo alterado depois da nossa escrita é trabalho do usuário (§83, §85) |
| `markers` íntegro | `stripped_block` — só o bloco `<!-- sparkforge-azure:* -->` sai; arquivo que esvazia é removido |
| `merge` íntegro | `removed_keys` — a chave possuída (`mcpServers.sparkforge-azure`) é excisada; arquivo que esvazia é removido |
| `file` íntegro | `removed` — deletado (mirrors, configs totalmente nossas) |

Conteúdo fora dos markers e chaves não-possuídas em arquivos merge são
byte-preservados. Um `.mcp.json` cujo entry `sparkforge-azure` foi
editado pelo usuário é preservado inteiro — o diff do valor da chave
demarca propriedade.

## Política de estado (§84–§85)

`project.yaml`, `workspace.yaml`, recibos e o próprio ledger são *estado*
— preservados por padrão, nunca deletados implicitamente:

```text
sparkforge-azure distribution detach                    # remove integração, mantém estado
sparkforge-azure distribution detach --purge-state      # remove .sparkforge-azure inteiro
sparkforge-azure distribution detach --purge-cache      # remove só .sparkforge-azure/cache
sparkforge-azure distribution detach --dry-run          # reporta ações sem escrever
```

`--purge-state` e `--purge-cache` são independentes: purgar cache não
apaga identidade. `--dry-run` lista `would_*` actions e `would_remove:<dir>`
em `purged` sem tocar o disco.

## Reattach (§88)

```text
sparkforge-azure distribution init
```

Idempotente: com estado preservado, o **mesmo `project_id`** é retomado
(o manifesto sobreviveu ao detach) e os assets são reescritos do zero.
Depois de `--purge-state`, `init` gera uma identidade nova — é o
comportamento desejado para um projeto que foi "desadotado".

## `repair` — decisão (§113)

Não existe verbo `repair`. `distribution init` **é** o repair: reescreve
assets managed faltantes/íntegros, preserva `modified` como trabalho do
usuário, e `status`/`doctor` apontam o drift antes. Um verbo separado
duplicaria a idempotência sem ganho — a decisão é registrada aqui e em
`docs/sdd/DETACH_HARDENING/design.md` (out_of_scope).

## Segurança

- Nada fora do ledger é tocado; entradas do ledger fora do root não são
  seguidas (paths gravados são relativos ao projeto).
- `scan_repository`/`resolve_within` já recusam symlinks e escapes —
  detach opera sobre os mesmos roots autorizados.
- Nenhum prompt, segredo ou valor de config é movido — detach só lida
  com arquivos de integração e diretórios de estado.
