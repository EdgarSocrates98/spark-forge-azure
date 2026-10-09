---
sdd: 1
feature: RELOCATABLE_IDENTITY
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/RELOCATABLE_IDENTITY/define.md
  sha256: "380a5df885f92b03f3919ed32502d813e863ba9737001c41aa932586dde9d06f"
files:
  - path: sparkforge_azure/distribution/identity.py
    action: create
    reason: "namespaces lógicos por id — project_state_dir/project_cache_dir/
      codeintel_db/receipt_namespace; único ponto que decide como um root
      compartilhado se torna chave por identidade"
  - path: sparkforge_azure/distribution/workspace.py
    action: modify
    reason: "workspace_add distingue relocated (path antigo sumiu) de
      copy-collision (path antigo existe); resultado carrega
      action/relocated_from"
  - path: sparkforge_azure/distribution/service.py
    action: modify
    reason: "inspect expõe `namespaces`; receipt recebe workspace_id do
      workspace descoberto"
  - path: tests/test_relocatable_identity.py
    action: create
    reason: AC1–AC6 — move, copy-collision, regen, relocated, namespaces
  - path: docs/portability/PORTABLE_DISTRIBUTION.md
    action: modify
    reason: política identidade/cópia/namespace documentada
  - path: docs/portability/WORKSPACES.md
    action: modify
    reason: "semântica de add relocated/collision documentada"
decisions:
  - id: D1
    choice: "Cópia vs relocação se decide pela existência do path antigo
      declarado: `is_dir()` ainda vivo → `identity_collision` (cópia);
      sumiu → `action: relocated`. O estado do filesystem *é* o sinal."
    rejected:
      - "heurística de conteúdo (diff de arquivos) — frágil e cara; a
        pergunta certa é 'a localização antiga ainda vive?', não 'o conteúdo
        é igual?'"
      - "flag `--relocate` no add — adiciona superfície para um caso que o
        filesystem já disambigura"
    rollback: "recusa é read-only; `workspace remove` + `init --regen-id`
      destravam qualquer classificação errada"
  - id: D2
    choice: "Namespacing por id só se aplica a roots que vieram de env
      (`SPARKFORGE_AZURE_STATE_DIR`/`SPARKFORGE_AZURE_CACHE` detectados via
      `paths.env_overrides`). Root ancorado no projeto mantém o layout
      clássico `<projeto>/.sparkforge-azure/`."
    rejected:
      - "namespacing sempre — dobraria a profundidade do layout clássico sem
        ganho (o root já é por-projeto)"
      - "namespacing por hash de path — reintroduz exatamente a dependência
        de localização que a feature remove"
    rollback: "helpers são puros; mudar o critério não migra dados — dirs
      namespaced são criados sob demanda"
  - id: D3
    choice: "`identity.py` em `distribution`, não em pacote novo
      `ports`/`manifest` — o port_manifest.yaml do spec governa ports
      externos; identidade é portabilidade interna."
    rejected:
      - "pacote `identity/` top-level — camada nova para 4 funções; aumenta
        a superfície de importação sem isolar nada"
    rollback: "helpers são leaf-puros; mover depois é refactor mecânico"
covers:
  - part: sparkforge_azure/distribution/identity.py
    acceptance: [AC5, AC6]
  - part: sparkforge_azure/distribution/workspace.py (workspace_add)
    acceptance: [AC2, AC3, AC4]
  - part: sparkforge_azure/distribution/service.py (initialize/status/inspect)
    acceptance: [AC1, AC6]
  - part: sparkforge_azure/distribution/manifests.py (project.yaml persiste id)
    acceptance: [AC1]
---

# RELOCATABLE_IDENTITY — design

## identity.py

API estável: `project_state_dir(paths, project_id)`,
`project_cache_dir(paths, project_id, workspace_id=None)`,
`codeintel_db(paths, project_id)` e `receipt_namespace(project_id,
workspace_id, scope=None)`. Todos puros — resolvem paths, não criam dirs.

## Política add() (workspace.py)

Ordem: path já declarado por outro id → `identity_collision`; mesmo id com
path diferente → `is_dir()` no antigo decide collision vs `relocated`;
caso contrário `added`/`kept`. Sem flags novas na superfície — `--regen-id`
já existe em `distribution init` e é o unlock documentado.

## Fingerprints — já portáteis

`decision/fingerprint.py` digere canonical_json de contrato/estado; nenhum
campo é path. W3 só garante via teste que a identidade textual não deriva
de localização.
