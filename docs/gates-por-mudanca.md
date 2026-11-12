# Gates por tipo de mudanca

Todo tipo de mudanca em `sparkforge_azure/sdd/change_kinds.yaml` mapeia para uma
secao DESTE documento. O gate `sparkforge-azure sdd check` le o frontmatter
`change_kinds:` do ship.md da feature e exige que o ship liste cada registro da
secao correspondente — o titulo da secao abaixo e LITERAL; `tests/test_sdd.py`
trava a deriva nos dois sentidos.

Formato de cada secao: que evidencias o ship precisa citar e como produzi-las.

## Acrescentar ou alterar uma REGRA no catálogo

**change_kind:** `rule`

**Registros obrigatorios no ship.md:**

- `rules_catalog_gates` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `manifest_rule_count` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `fixture_kind_coverage` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Dar `runtime_scope` a uma regra — ou seja, **toda regra nova**

**change_kind:** `rule_runtime_scope`

**Registros obrigatorios no ship.md:**

- `runtime_scope_gates` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Critério de domínio: artefato antes de nome

**change_kind:** `domain`

**Registros obrigatorios no ship.md:**

- `domain_criterion` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Acrescentar uma ÁREA nova (`area:` novo num `rules/catalog/*.yaml`)

**change_kind:** `rule_area`

**Registros obrigatorios no ship.md:**

- `routing_yaml` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `coordinator_rule_areas` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Acrescentar ou alterar um EXTRATOR de facts

**change_kind:** `extractor`

**Registros obrigatorios no ship.md:**

- `reachability_lists` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `fixture_kind_coverage` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `snippet_measure` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Mexer no funil de contexto (`sparkforge/codeintel/context.py`, `ranking.py`, `budget.py`)

**change_kind:** `context_funnel`

**Registros obrigatorios no ship.md:**

- `recall_economy_gate` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Acrescentar um CORPUS de fixture novo (`fixtures/<dominio>/`)

**change_kind:** `fixture_corpus`

**Registros obrigatorios no ship.md:**

- `fixture_corpus_gates` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Acrescentar ou alterar um cenário de `evals/holdout/`

**change_kind:** `holdout`

**Registros obrigatorios no ship.md:**

- `holdout_gates` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Editar um documento em `knowledge/`

**change_kind:** `knowledge_doc`

**Registros obrigatorios no ship.md:**

- `offline_manifest` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `sources_lock` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Alterar `knowledge/glue/runtime-matrix.yaml`

**change_kind:** `runtime_matrix`

**Registros obrigatorios no ship.md:**

- `runtime_matrix_gates` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Pontos cegos medidos do extrator de Terraform

**change_kind:** `terraform_blind_spots`

**Registros obrigatorios no ship.md:**

- `terraform_extractor_gates` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Ler dado do disco em código de `sparkforge/`

**change_kind:** `disk_read`

**Registros obrigatorios no ship.md:**

- `verify_wheel` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Alterar dependência: `pyproject.toml`, `requirements.txt`, `locks/` ou os workflows

**change_kind:** `dependency`

**Registros obrigatorios no ship.md:**

- `requirements_mirror` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `hash_locks` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Alterar agent, skill ou seus espelhos

**change_kind:** `agent_or_skill`

**Registros obrigatorios no ship.md:**

- `sync_skills` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `agents_parity` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Acrescentar ou alterar tool, verbo de CLI, agent ou skill: a referência gerada

**change_kind:** `tool_or_verb`

**Registros obrigatorios no ship.md:**

- `surface_lock` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.
- `generated_reference` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Alterar `rules/catalog/routing.yaml`

**change_kind:** `routing`

**Registros obrigatorios no ship.md:**

- `router_gates` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Alterar a tabela *Números correntes* do `STATUS.md`

**change_kind:** `status_numbers`

**Registros obrigatorios no ship.md:**

- `status_numbers_gate` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Alterar `scripts/check_vnext_claims.py`, `docs/claims.lock.json`, ou alegação em `docs/vnext/` ou `docs/harness/`

**change_kind:** `claims`

**Registros obrigatorios no ship.md:**

- `claims_gate` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Alterar o resultado de `call_tool` — campo aditivo no envelope

**change_kind:** `call_tool_envelope`

**Registros obrigatorios no ship.md:**

- `tool_result_parity` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.

## Escrever tabela ou artefato persistente (Delta, Iceberg, OneLake, ADLS Gen2, Parquet)

**change_kind:** `data_persistence`

O `change_kinds` do define declara `data_persistence` quando o job grava
tabela ou artefato persistente — e, no perfil `operator`, o gate também
dispara quando `files` do design ou das tarefas do plan citam `delta`,
`onelake`, `lakehouse`, `iceberg`, `parquet`, `abfss` ou `adls` (num repo de
jobs de dados o nome é sinal de escrita; no `dev` o mesmo nome é código de
ferramenta, e só a declaração conta).
Aí `design` e `plan` respondem, no campo `persistence`, como a mudança trata
cada item do checklist (`sparkforge_azure/sdd/change_kinds.yaml`):
atomicidade, isolamento, consistência, idempotência, concorrência,
versionamento, evolução de schema, chave de negócio, reprocessamento, retry,
snapshot/commit/rollback, recuperação, atualização parcial, testes negativos
e métricas de validação funcional. O design explica, no tratamento de
`snapshot_commit_rollback` e de `partial_update`, como os invariantes se
preservam quando a operação falha entre passos. Item sem tratamento vira
`persistence_undeclared` — lacuna, não recusa, porque a forma correta é
julgamento de domínio.

**Registros obrigatorios no ship.md:**

- `sdd_persistence_check` — evidencia nomeada; produza via `sparkforge-azure sdd check` e cite o artefato/run que a gerou.

Registro ausente ⇒ recusa `change_kind_registry_missing` com unlock apontando esta secao.
