---
sdd: 1
feature: RELOCATABLE_IDENTITY
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/RELOCATABLE_IDENTITY/explore.md
  sha256: "2d65ce04681e35302cf0930804118d105dca2a0aaa8fac36fe718c02c2ea0d61"
hypothesis:
  claim: Identidade gerada persistida + namespaces lógicos por id mantêm
    estado, cache e índices resolvíveis através de relocação, e separam
    cópias deliberadas de merges acidentais
  prediction: mover um projeto preserva `project_id`; copiar um projeto
    declarado gera `identity_collision` até `--regen-id`; state/cache
    compartilhados via env namespaceiam por id sem colisão
  experiment: pytest tests/test_relocatable_identity.py — move, copy, regen,
    relocate, namespaces
acceptance:
  - id: AC1
    statement: mover o diretório do projeto preserva `project_id` e o status
      resolve a nova localização
    verified_by:
      kind: test
      ref: tests/test_relocatable_identity.py::test_project_id_survives_move
  - id: AC2
    statement: "adicionar ao workspace um diretório que copiou um
      `project.yaml` alheio recusa `identity_collision` — a declaração
      original continua apontando para o original"
    verified_by:
      kind: test
      ref: tests/test_relocatable_identity.py::test_copy_is_identity_collision_not_merge
  - id: AC3
    statement: "`distribution init --regen-id` na cópia cunha identidade nova
      e o add passa"
    verified_by:
      kind: test
      ref: tests/test_relocatable_identity.py::test_regen_id_makes_copy_addable
  - id: AC4
    statement: "re-add num path novo cujo antigo sumiu grava `relocated` —
      mesma identidade, nova localização resolvida"
    verified_by:
      kind: test
      ref: tests/test_relocatable_identity.py::test_external_relocation_recorded_not_collided
  - id: AC5
    statement: "state/cache/index namespaces key by `project_id` (e
      `workspace_id` no cache) quando o root é compartilhado via env; layout
      clássico preservado quando o state ancora no projeto"
    verified_by:
      kind: test
      ref: tests/test_relocatable_identity.py::test_state_namespace_isolation
  - id: AC6
    statement: receipts de agentes/contexto carregam `project_id` +
      `workspace_id` + scope via receipt_namespace
    verified_by:
      kind: test
      ref: tests/test_relocatable_identity.py::test_init_receipt_carries_workspace_id
success:
  - id: SC1
    metric: "0 usos de path absoluto como identidade semântica no pacote
      distribution"
    source: sparkforge_azure/distribution/ (identidade sempre sfa-*/sfw-*)
out_of_scope:
  - migração do schema antigo de workspace (graph/workspace.py) — a feature
    nova convive; convergência é decisão separada
  - fingerprints agentic — já digerem contrato+estado, sem path (verificado)
change_kinds:
  - tool_or_verb
---

# RELOCATABLE_IDENTITY — define

## Por que produto, não arquitetura

O spec pede *identidade de produto* relocável — quem esse projeto é não
muda quando ele muda de lugar. É propriedade dos manifests e do serviço,
não do kernel; nada em Facts→Rules→Findings muda.

## Política de cópia/clone explícita (§41–§43)

- **Colisão detectada**: mesmo `project_id` em dois diretórios vivos →
  `identity_collision` com unlock (`init --regen-id` na cópia).
- **Relocação real**: path antigo declarado sumiu → `action: relocated`,
  mesma identidade, nova localização registrada.
- **Regeneração explícita**: `distribution init --regen-id` — única forma de
  cunhar identidade nova numa cópia; registrada no receipt.
