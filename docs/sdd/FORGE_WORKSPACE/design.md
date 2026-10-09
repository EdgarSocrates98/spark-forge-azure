---
sdd: 1
feature: FORGE_WORKSPACE
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/FORGE_WORKSPACE/define.md
  sha256: "3712b476938db3ef482a34cd525d5a30dc487a195569cee97f5de9e11b51195f"
files:
  - path: sparkforge_azure/distribution/workspace.py
    action: create
    reason: operações do ForgeWorkspace — discover/init/add/remove/status,
      detect_cycles, reachable(scope)
  - path: sparkforge_azure/cli/cmd_workspace.py
    action: create
    reason: verbos `workspace *` sobre o serviço; recusas como documento refused
  - path: sparkforge_azure/cli/main.py
    action: modify
    reason: registrar cmd_workspace em COMMAND_MODULES
  - path: tests/test_forge_workspace.py
    action: create
    reason: AC1–AC8 — monorepo, multi-repo externo, ciclos, relocação, discover
  - path: docs/reference/cli.md
    action: modify
    reason: seção `sparkforge-azure workspace <op>` (gate docs_surface)
  - path: docs/surface.lock.json
    action: modify
    reason: regen com os 5 verbos novos
  - path: docs/portability/WORKSPACES.md
    action: create
    reason: doc do modelo — manifesto, semântica, locality, verbos
decisions:
  - id: D1
    choice: "`workspace add` auto-inicializa a identidade do alvo quando
      ausente (`initialized_target` reportado) — a declaração explícita do
      usuário é a fronteira que autoriza a escrita no outro repo (§35)."
    rejected:
      - "exigir `distribution init` no alvo antes — atrito sem ganho: o add já
        é a declaração explícita"
      - "não escrever nada no alvo — sem project.yaml o id não existe e o
        workspace não pode referenciá-lo"
    rollback: "remover o projeto do workspace (`remove`) não toca o repo;
      apagar `.sparkforge-azure/project.yaml` do alvo desfaz a identidade"
  - id: D2
    choice: "Paths dentro do root armazenados relativos (relocate com o
      workspace); fora, absolutos — a manifestação explícita é a fronteira,
      `resolve_within` do kernel não é afrouxado."
    rejected:
      - "sempre absolutos — impede a prova de relocação do workspace inteiro
        (§40)"
      - "sempre relativos — `../lib` vira fuga de root sem declaração legível"
    rollback: "normalização é puro mapeamento; reescrever o manifesto é editável"
  - id: D3
    choice: "Ciclo detectado em DFS com in-stack — `dependency_cycle` em
      `workspace status`, `add` reporta `degraded`, `reachable` recusa com
      `error.kind`; nenhuma recursão sem bound existe."
    rejected:
      - "detectar só no load — manifesto com ciclo ficaria ilegível e `status`
        não poderia reportá-lo"
    rollback: "ciclo é estado de manifesto — `remove`/`add` resolvem sem migração"
  - id: D4
    choice: "`reachable(scope)` mora aqui — é a única implementação dos scopes
      e W4 (context) consome sem duplicar o grafo."
    rejected:
      - "duplicar dentro de context/ — dois lugares para a mesma semântica de
        localidade divergem"
    rollback: "o consumo por context é aditivo; mudar scope é mudar este ponto"
  - id: D5
    choice: "Discover sugere por marcadores (`.git`, `pyproject.toml`,
      `project.yaml`) com tetos `MAX_ANCESTORS=24`/`MAX_SUGGESTIONS=32` —
      determinístico, offline, nunca escreve (§24–§27)."
    rejected:
      - "ranking por heurística de conteúdo — LLM-free por spec e ruidoso"
    rollback: "sugestão não tem estado — mudar a política não migra nada"
covers:
  - part: sparkforge_azure/distribution/workspace.py (init/add/remove)
    acceptance: [AC1, AC2, AC3, AC4]
  - part: sparkforge_azure/distribution/workspace.py (detect_cycles/reachable)
    acceptance: [AC5, AC6]
  - part: sparkforge_azure/distribution/workspace.py (discover/status)
    acceptance: [AC7]
  - part: sparkforge_azure/distribution/manifests.py (resolve_declared_path)
    acceptance: [AC8]
  - part: sparkforge_azure/cli/cmd_workspace.py
    acceptance: [AC1, AC2, AC3, AC4, AC5, AC6, AC7]
---

# FORGE_WORKSPACE — design

## O grafo de arestas

`WorkspaceDecl.projects[*].dependencies` é o grafo direcionado declarado.
`detect_cycles` faz DFS iterando ids ordenados — determinístico. `reachable`
usa o mesmo mapa: `direct` expande uma vez, `transitive` fecha, `all`
ignora arestas mas exige manifesto sem ciclo (review explícito).

## Interação com `distribution init`

`workspace init` e `distribution init` são complementares: o primeiro ancora
o *agrupamento*, o segundo a *identidade do projeto*. `workspace init` chama
a mesma `_ensure_project_identity` — um project.yaml por repo, reutilizado
pelos dois.
