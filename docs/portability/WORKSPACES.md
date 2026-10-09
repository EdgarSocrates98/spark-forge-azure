# FORGE_WORKSPACE — agrupamento lógico de projetos (W2)

`ForgeWorkspace` é o agrupamento local/lógico de projetos que a distribuição
portável opera (prompt_evo_portable.md §20–§36). É explicitamente **distinto**
de Azure Workspace, Databricks Workspace e Fabric Workspace — nenhum recurso
de nuvem é tocado, lido ou inferido.

Manifesto: `.sparkforge-azure/workspace.yaml` na raiz do workspace.

## Modelo

```yaml
version: 1
workspace_id: sfw-<uuid24>
name: <nome>
projects:
  - id: sfa-<uuid24>        # identidade portátil do projeto (nunca o path)
    path: app | E:/repos/lib # relativo ao root OU absoluto (externo)
    role: application        # application|data|infra|shared|tests|docs
    dependencies: [sfa-…]    # arestas diretas, declaradas
    optional_dependencies: [sfa-…]
default_target: sfa-<id-do-projeto-hospedeiro>
config: {}                   # camada workspace da precedência de config
```

## Semântica

- **Declarado, não descoberto.** `workspace discover` *sugere* candidatos
  (cwd, ancestrais limitados a `MAX_ANCESTORS=24`, filhos declarados e
  filhos do root, teto de `MAX_SUGGESTIONS=32`); `workspace add` confirma.
  Nenhuma varredura de home, nenhuma inferência de negócio (§26, §33).
- **Externo só quando declarado.** Paths dentro do root são armazenados
  relativos (relocate com o workspace); fora, absolutos — a declaração é a
  fronteira explícita (§35). `resolve_within` do kernel não é afrouxado:
  continua valendo para todo o resto do pacote.
- **Dependências são arestas declaradas.** `dependencies` = direct,
  `optional_dependencies` = optional; `transitive` é derivado em leitura,
  nunca escrito (§30). `workspace remove` remove também arestas de entrada.
- **Ciclos são estado de revisão explícito.** `detect_cycles` (DFS com
  in-stack, limitado ao nº de projetos) alimenta `workspace status`
  (`dependency_cycle`) e recusa `reachable`/`context` por nome —
  `error.kind = dependency_cycle`, nunca recursão infinita (§31–§32).
- **Determinístico.** Projetos ordenados por id; `add` repetido com os
  mesmos argumentos é `kept`; mesma entrada → mesma saída (§34).
- **`remove` nunca deleta repositório** — só a declaração (§36).
- **Identidade ≠ path.** O id do projeto vem do `project.yaml` dele;
  `workspace add` cria a identidade portátil do alvo se ausente
  (`initialized_target: true` — única escrita fora do root, e é a ação
  explícita do comando).

## Locality (base da resolução de contexto — W4)

`reachable(ws, target, scope)` implementa os scopes do spec:

| Scope | Conjunto |
|---|---|
| `target` | só o target |
| `direct` | target + arestas diretas |
| `transitive` | fecho transitivo das arestas |
| `all` | todo projeto declarado (explícito) |

`target` é o default — o workspace inteiro nunca é lido por omissão (§58).

## Verbos

```
workspace discover --root R
workspace init --root R [--name N]
workspace add <path> [--id PID] [--role R] [--depends-on A B] [--optional C]
workspace remove <id>
workspace status
```

Relocação coberta por teste: mover o diretório do workspace inteiro preserva
`workspace_id`, `project_id`s e resolução de paths relativos.
