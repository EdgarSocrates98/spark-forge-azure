# Knowledge packs dos verticais

## Vertical Fabric (Cycle 3)

| pack | domínios | failure_layers |
|---|---|---|
| `fabric-core` | `fabric-onelake` | `fabric_workspace`, `item_permission`, `lakehouse` |
| `fabric-spark` | `fabric-data-engineering` | `spark_runtime`, `spark_job`, `delta_perf` |
| `onelake-security` | `fabric-onelake`, `fabric-identity` | `onelake_security` |
| `onelake-shortcuts` | `fabric-onelake`, `fabric-identity` | `shortcut`, `shortcut_auth`, `source_access` |
| `fabric-capacity` | `azure-finops` | `capacity` |
| `fabric-data-factory` | `fabric-data-factory` | `data_factory`, `cross_environment` |

O mesmo compilador `compile_access_knowledge(failure_layer, terms)` seleciona
os packs por `failure_layer` — é genérico aos dois verticais: um caso UC
nunca puxa packs Fabric e vice-versa; `excluded_domains` documenta o que
ficou fora. O report `diagnose fabric` carrega o bloco `knowledge` escopado.

## Vertical de acesso (Cycle 2)

`knowledge/packs.yaml` declara os packs mínimos do vertical
Databricks/Unity Catalog/ADLS (prompt 151). O compilador escopado é
`sparkforge_azure.knowledgebase.vertical.compile_access_knowledge`.

## Packs

| pack | domínios | failure_layers |
|---|---|---|
| `databricks-runtime` | `azure-databricks` | `runtime` |
| `unity-catalog-storage` | `unity-catalog` | `unity_catalog`, `storage_credential`, `external_location`, `workspace_binding` |
| `adls-access` | `azure-adls` | `azure_rbac`, `adls_acl` |
| `azure-identity` | `azure-entra`, `azure-keyvault` | `entra` |
| `azure-network` | `azure-networking` | `network` |
| `delta-performance` | `delta-lake`, `spark-performance` | `delta_perf` |

`crosscut_domains: [governance]` entra em toda seleção — conflitos
multicamada atravessam camadas por definição.

## Escopo determinístico (prompt 152)

`compile_access_knowledge(failure_layer, terms)`:

1. resolve os packs cujo `failure_layers` contém a camada do caso
   (`unresolved`/vazio seleciona todos os packs — ainda dentro do vertical);
2. seleciona entradas só dos domínios desses packs + crosscut, via
   `KnowledgeBase.select` (metadados + expansão determinística, corpos
   ficam em disco);
3. devolve `excluded_domains` — a prova de que domínios fora do vertical
   (`fabric-*`, `azure-synapse`, `azure-data-factory`, …) não foram
   carregados.

O relatório `diagnose` carrega o bloco `knowledge` com o resultado —
uma falha UC nunca puxa material Fabric/Synapse/ADF.

## Expansão de consulta (prompt 153)

`knowledge/query_expansion.yaml` expande `external location denied`
deterministicamente para `storage credential`, `managed identity`,
`adls rbac`, `adls acl`, `workspace binding`, `private endpoint`
(rede) e alvos UC/ADLS/governance — um nível, sem reexpansão.

## Doctor

`sparkforge-azure doctor` inclui a área `live_collectors`: para cada
collector do vertical reporta `module: available|unavailable` e
`live: available|unavailable` (extras SDK), com `missing_sdk`. Nunca
lê credenciais nem chama a nuvem; modo export offline é sempre válido.

## Skill evals (prompt 156)

Cada skill do vertical tem `kind: positive|negative|boundary` em
`skills/<nome>/evals/evals.yaml`: pelo menos um trigger positivo, um
negativo (fora do escopo → handoff) e um caso de fronteira entre
skills adjacentes. O validador (`skills/model.py`) reprova skill do
vertical sem `negative` + `boundary`.
