---
sdd: 1
feature: FORGE_WORKSPACE
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/FORGE_WORKSPACE/explore.md
  sha256: "2e58353b5a9b4de66cd05f210363375451b5469391efa5d52209c8443f728520"
hypothesis:
  claim: Um ForgeWorkspace declarado — manifesto data-only em
    `.sparkforge-azure/workspace.yaml`, ids `sfa-*`, arestas explícitas e
    ciclos como estado de revisão — suporta monorepo, multi-repo e repos
    externos sem ambiguidade e sem escrita fora do que foi declarado
  prediction: "init/add/remove/status/discover cobrem monorepo (paths
    relativos), multi-repo (paths absolutos) e ciclos (`dependency_cycle`)
    determinísticos; mover o diretório do workspace preserva ids e resolução"
  experiment: pytest tests/test_forge_workspace.py — ciclo init→add→remove→
    status→discover + relocação do root inteiro
acceptance:
  - id: AC1
    statement: workspace init cria workspace.yaml com `sfw-*`, registra o
      projeto hospedeiro e é idempotente
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_init_idempotent
  - id: AC2
    statement: "workspace add de filho de monorepo guarda path relativo; add de
      repo fora do root guarda absoluto e marca `external`"
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_add_external_repo_stores_absolute
  - id: AC3
    statement: workspace add é determinístico e idempotente — mesma entrada,
      `kept`; path duplicado com outro id recusa `identity_collision`
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_add_is_deterministic_and_idempotent
  - id: AC4
    statement: workspace remove tira só a declaração e as arestas de entrada —
      o repositório no disco fica intacto
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_remove_is_declaration_only
  - id: AC5
    statement: dependência cíclica é estado explícito `dependency_cycle` em
      status/add e recusa `reachable` por nome — sem recursão infinita
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_cycle_is_explicit_review_state
  - id: AC6
    statement: "reachable implementa os scopes do spec: target=só target;
      direct=target+diretas; transitive=fecho; all=todos os declarados"
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_reachability_scopes
  - id: AC7
    statement: workspace discover sugere candidatos limitados e nunca escreve
      nada — bounded por MAX_ANCESTORS e MAX_SUGGESTIONS
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_discover_suggests_without_writing
  - id: AC8
    statement: mover o diretório do workspace inteiro preserva workspace_id,
      project_ids e resolução de paths relativos
    verified_by:
      kind: test
      ref: tests/test_forge_workspace.py::test_workspace_roundtrip_survives_within_root_move
success:
  - id: SC1
    metric: "workspace discover/init/add/remove/status executáveis na
      superfície travada com docs"
    source: docs/surface.lock.json + docs/reference/cli.md
  - id: SC2
    metric: "0 recusas novas no sdd check e 0 arestas fora de EXCECOES_MEDIDAS"
    source: sparkforge-azure sdd check + tests/test_architecture_layers.py
out_of_scope:
  - context resolve consumindo `reachable` — feature CONTEXT_RESOLUTION (W4)
  - convergência dos schemas antigos `workspace/manifest.py` /
    `graph/workspace.py` — anotada no audit, resolvida na wave de identidade
  - persistência de grafo materializado — já existe em `workspace/graph.py`
    e continua separada
change_kinds:
  - tool_or_verb
---

# FORGE_WORKSPACE — define

## Por que produto, não arquitetura

O spec pede um conceito de produto — "qual conjunto de projetos este
workspace reúne" — implementado como dados declarados + operações sobre
eles. O kernel (`paths`, `durable`) e os engines não mudam; `reachable`
reusa a mesma camada que o contexto vai consumir (W4).

## Fronteras de escrita

`workspace add` escreve no alvo apenas o `project.yaml` portátil quando
ausente — é a ação explícita do comando e é reportada
(`initialized_target`). Nenhum outro arquivo do repo alvo é tocado; `remove`
nunca deleta.
