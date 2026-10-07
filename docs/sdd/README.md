# SDD — Spec-Driven Development neste repositório

O SDD é o fluxo determinístico de especificação deste projeto: cada mudança
declarada passa por artefatos versionados em `docs/sdd/<FEATURE>/<fase>.md`,
na ordem `explore → define → design → plan → build_report → ship`, e o gate
(`sparkforge_azure.sdd.checks.check`) recusa o que não tiver evidência — cada
falha é uma recusa nomeada com o `unlock` que a destrava.

## Os artefatos

- `docs/sdd/<FEATURE>/explore.md` — o que se sabe e as opções (`approaches`, `chosen`)
- `docs/sdd/<FEATURE>/define.md` — hipótese, critérios `AC*` verificáveis, `success`, `out_of_scope`
- `docs/sdd/<FEATURE>/design.md` — arquivos, decisões com rollback, `covers` dos critérios
- `docs/sdd/<FEATURE>/plan.md` — tarefas `T*` com o teste que falha antes do código
- `docs/sdd/<FEATURE>/build_report.md` — `red`/`green` por tarefa, claims com evidência
- `docs/sdd/<FEATURE>/ship.md` — `hypothesis_outcome`, registros conferidos, `evidence` (operator)

Cada artefato declara `upstream: {path, sha256}` do artefato anterior — o
`text_sha256` do texto normalizado. Editar o upstream sem revisar e regravar o
sha é recusa `upstream_stale`.

## Comandos

- `sdd-define` — skill/verbo que abre uma feature nova (define.md a partir do problema)
- `sparkforge-azure sdd check` — o gate: recusas e lacunas da feature ou do repo
- `sparkforge-azure sdd status` — a fase de cada feature e o que a bloqueia

No sibling AWS o mesmo gate é `sparkforge sdd check`; aqui o binário é
`sparkforge-azure` (os dois projetos coexistem na máquina).

## Os dois perfis

- `dev` — feature com código: tarefa declara `test`, `red` vê o teste falhar
  antes do código, `green` depois.
- `operator` — mudança sem código de produto (config, documento, correção de
  dados): a tarefa prova por `proof` (`funcval`, `fact` ou `finding`) e o build
  registra `change_id` de `change sandbox`, com `evidence` no ship.

## Features deste repo

- `docs/sdd/SDD_EVAL/define.md` — os critérios da suite agentica sobre specs
- `docs/sdd/SDD_MIGRATION/define.md` — os critérios da migração AgentSpec→SDD

## Migração AgentSpec

O processo anterior (AgentSpec) está arquivado em `docs/sdd/archive/agentspec/`
e o plugin desligado em `.claude/settings.json`. O estado local da época
(`.claude/sdd/`) não é versionado — está no `.gitignore`.
