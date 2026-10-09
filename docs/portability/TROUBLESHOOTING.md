# TROUBLESHOOTING — recusas do lifecycle portável

Todo comando `distribution`/`workspace`/`context` que falha emite um
documento de recusa — nunca um traceback cru (prompt_evo_portable.md
§178–§179):

```json
{"status": "refused",
 "error": {"kind": "<kind>", "detail": "...", "unlock": "..."}}
```

`kind` vem de um vocabulário fechado em
`sparkforge_azure/distribution/errors.py` (`FAILURE_KINDS`). `unlock` é a
menor ação que desbloqueia o comando. Esta tabela documenta cada kind, a
causa típica e a saída — se um unlock impresso divergir daqui, o código é
a verdade (o vocabulario é o contrato; a frase é detalhe).

## Glossário por `kind`

| kind | Causa típica | Desbloqueio |
|---|---|---|
| `project_not_initialized` | `distribution status`/`doctor`/`detach` num repo sem `.sparkforge-azure/project.yaml` | `sparkforge-azure distribution init` na raiz |
| `workspace_not_found` | `workspace *`/`context resolve` sem `workspace.yaml` numa raiz ancestral | `sparkforge-azure workspace init` na raiz compartilhada |
| `manifest_invalid` | `project.yaml`/`workspace.yaml` com YAML inválido, chaves fora do schema, `role` desconhecido, ou chave com cara de segredo (`token`, `password`, `connection_string`, ...) | corrigir o YAML; para segredos: variável de ambiente, nunca literal; identidade corrompida: `distribution init --regen-id` |
| `config_invalid` | config do usuário (`SPARKFORGE_AZURE_CONFIG` ou `--set`) com chave fora do vocabulário (`context.default_scope`, `context.profile`, `host.activation`, `network.mode`, `state.retention`), valor vazio, ou chave com cara de segredo | conferir as chaves conhecidas; segredos só por env var |
| `identity_collision` | `workspace add` numa **cópia** viva de um projeto já declarado (mesmo `sfa-*`, path antigo existe) | `sparkforge-azure distribution init --regen-id` na cópia — ids nunca são fundidos em silêncio |
| `dependency_cycle` | aresta declarada fecha um ciclo no `workspace.yaml` | remover/reorientar a aresta; `workspace status` mostra o ciclo |
| `path_outside_root` | path declarado resolve fora da raiz (traversal `..`, symlink) | declare o caminho real; symlink dentro do repo é recusado de propósito |
| `managed_asset_drift` | arquivo gerenciado (ledger) alterado após o init | nunca é recusa no `init` — `init` reescreve o gerenciado e preserva modificações do usuário; `detach` preserva com warning |
| `host_unavailable` | reservado — ausência de host **não** é falha (`inspect`/`doctor` reportam `unavailable`/`unproven` por host) | instalar o host é opcional; o lifecycle funciona sem |
| `unsupported` | operação/scope/profile fora do conjunto fechado | ajustar o argumento (ex.: `scope: target\|direct\|transitive\|all`) |

## Padrões de sintoma

**`workspace add` recusa um path válido** — quase sempre `identity_collision`
(o diretório foi copiado de um projeto já declarado). Confirmar:
`workspace status` lista o `sfa-*` já registrado; `distribution init
--regen-id` na cópia resolve.

**`context resolve` diz `unresolved`** — path declarado que sumiu do disco.
`unresolved` é reportado, nunca silenciado: ou `workspace add` o novo path
(relocação preserva o `project_id`), ou remover a declaração.

**`detach` não removeu um arquivo meu** — por design: assets modificados
viram `preserved_modified` (warn, nunca revert). `managed.json` registra o
que o init escreveu; o que você editou depois é seu.

**Segredos recusados em config/manifest** — a guarda olha o *nome da
chave*, não o valor: `tokens`, `api_key`, `connection_string` e afins são
recusados estruturalmente. A saída é env var ou secret store do host.

## Diagnóstico rápido

```text
sparkforge-azure distribution inspect    # pacote, assets, hosts — sem escrita
sparkforge-azure distribution status     # drift? managed intactos? missing?
sparkforge-azure distribution doctor     # preflight offline (paths, schema, mirrors)
sparkforge-azure workspace status        # membros, ciclos, paths resolvidos
```

Tudo offline-first: nenhum desses verbos toca a rede ou o HOME real.
