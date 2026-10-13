# Graphfy — o grafo semântico/de workspace da Forge

> Seções 54–67, 68, 173–179, 283. Camada **L3** (ADR-0001). Collectors são **L6**.

**Graphfy é o grafo semântico/de workspace da Forge.** É infraestrutura para recuperação,
análise de impacto, expansão de contexto, entendimento de workspace, ligação de conhecimento
e análise de mudança — **não** é visualização. Stdlib + PyYAML; nenhum SDK de nuvem.

Código: `sparkforge_azure/graph/` (grafo) e `sparkforge_azure/collectors/` (observação
read-only que alimenta o grafo live).

## Modelo (`graph/model.py`)

- `Node(id, kind, layer, attrs, provenance)` e `Edge(source, relation, target, attrs, provenance)`.
- `Provenance(kind, source, observed_at)` com `kind ∈ static | live | artifact | knowledge`.
- IDs determinísticos `layer:kind:chave`; recurso Azure é `azure:<ARM id em minúsculas>` —
  o *kind* fica **fora** do id, para que a mesma ARM id vista no manifesto e no Resource Graph
  seja **um** nó.
- Serialização JSON canônica (chaves e listas ordenadas) + `fingerprint()` SHA-256.
- `Graph`: `add_node`/`add_edge`/`merge`/`neighbors`/`subgraph`. Merge só por id idêntico;
  conflito de kind vai para `unresolved`; conflito de atributo é registrado
  (`attr_conflicts`), nunca sobrescrito em silêncio; proveniências extras em `observed_by`.

### Camadas e kinds

| Camada | Kinds (contrato) | Extensões documentadas |
|---|---|---|
| code | file, symbol, function, class, import, test, config | repository |
| data | dataset, table, column, pipeline, notebook, job, stream, checkpoint | cluster |
| azure | tenant, subscription, resource_group, workspace, storage_account, filesystem, databricks_workspace, unity_catalog, adf, fabric_workspace, event_hub, purview, network, identity | fabric_capacity, key_vault, resource |
| knowledge | knowledge, rule, skill, agent, eval, finding | domain, boundary |
| evidence | fact, finding, evidence, decision, receipt, trace | — |
| fabric | tenant, capacity, workspace, item, lakehouse, notebook, spark_job, environment, pipeline, pipeline_activity, shortcut, connection, workspace_identity, identity | onelake_table, onelake_path, onelake_role, external_target |
| stream | namespace, eventhub, partition, consumer_group, app, stream_query, checkpoint, sink, eventstream, es_source, es_transform, es_destination, eventhouse, activator, activator_rule | connection, identity |
| migration | adf_factory, synapse_workspace, pipeline, activity, dataset, linked_service, trigger, integration_runtime, global_parameter, synapse_notebook, spark_pool, spark_job, lake_database, table, library, spark_config, adls_path, storage_account | fabric_workspace, fabric_pipeline, fabric_connection, fabric_notebook, fabric_environment, fabric_lakehouse, fabric_shortcut, variable_library, fabric_item, assessment_result, recommendation, wave, identity |

As três últimas camadas são os planos SaaS dos verticais: `fabric` separada
do ARM `azure` (workspace Fabric não é recurso ARM), `stream` com semântica
temporal (causalidade só quando um finding a sustenta), `migration` com
arestas `migrates_to{status}` e auth source/target em nós separados.

## Fontes do grafo

| Fonte | Módulo | Proveniência |
|---|---|---|
| Repositório (arquivos, imports, testes, configs, Terraform `resource`, notebooks Databricks) | `semantic.py` | static |
| Code Intelligence (`codeintel.index.indexar`) para símbolos e chamadas; fallback `ast` | `semantic.py` | static |
| Manifesto de workspace (repos, relações, recursos declarados, bindings, domínios, fronteiras) | `workspace.py` | static |
| Observação autorizada (facts de collectors, já redigidos) | `live.py` | live |
| Fragmentos de artefato (`workspace.federated.GraphFragment`) | `adapters.py` | artifact |
| Knowledge (`knowledge/**/*.md`), skills (`skills/*/SKILL.md`), agents (`agents/*.md`) | `adapters.py` | knowledge |

## Manifesto `sparkforge-azure.workspace.yaml` (§66)

```yaml
schema_version: 1
workspace: contoso-lakehouse
repositories:            # path relativo, sem "..", sem absoluto, sem symlink
  - {name: terraform, path: terraform, role: terraform}   # roles: terraform|bicep|databricks|adf|fabric|synapse|shared|app|docs
relationships:
  - {source: databricks, relation: depends_on, target: terraform}
cloud_resources:         # id explícito obrigatório; forma da ARM id validada
  - {name: lake, kind: storage_account, arm_id: /subscriptions/<guid>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<n>}
  - {name: analytics, arm_id: ..., databricks_workspace_id: "1234567890123456", workspace_url: https://adb-....azuredatabricks.net}
  - {name: sales-fabric, fabric_workspace_id: <guid>}
bindings:                # recurso do repo -> recurso declarado (nome lógico ou ARM id)
  - {repository: terraform, address: azurerm_storage_account.lake, target: lake}
domains:    [{name: sales, repositories: [databricks], cloud_resources: [lake]}]
boundaries: [{name: fabric-isolado, source: fabric, target: terraform, allowed: false}]
```

Exemplo completo e sintético: `examples/workspace/` (multi-repo `/terraform /databricks /adf
/fabric /shared`). Nada é descoberto: repositório não declarado não é varrido.

## Regra de composição (§64) — inegociável

`federation.federate(static, live, artifact, knowledge, bindings=...)`:

1. **Nós só se unificam por id idêntico** (ARM id, id de workspace Databricks, GUID Fabric,
   caminho de repositório, id de knowledge).
2. **Arestas entre grafos só vêm de binding declarado ou referência verificada** — id
   explícito carregado como atributo (`databricks_workspace_id` → `same_as`) ou ARM id
   literal dentro de `properties` (ex.: `privateLinkServiceId` → `references`).
3. **Nome parecido ou igual nunca liga nada.** Dois `stshared` em assinaturas diferentes
   continuam dois nós; aparecem em `ambiguous_names` com `linked: false`.
4. Candidato sem ligação vai para `unresolved` com motivo: `unbound_iac_resource` (com
   `name_candidates` só para o humano), `binding_source_not_found`,
   `binding_target_undeclared`, `binding_endpoint_missing`, `dangling_reference`,
   `declared_not_observed`, `boundary_violation`.

## Consultas e impacto

- `query.py`: `find_nodes` (kind/layer/attrs), `neighbors` (filtro de relação e direção),
  `shortest_path` (BFS limitada), `slice_graph` (fatia limitada por orçamento de nós —
  minimalidade de contexto).
- `impact.py` (§54): dado arquivo/símbolo/id de knowledge/node id, percorre dependentes com
  limite de profundidade e agrupa em `symbols, callers, tests, configs, rules, skills, agents,
  knowledge, resources, data, files` + `unresolved`. Resolução de entrada é **exata**
  (caminho `repo/path`, `path`, id) — basename sozinho não resolve.

## Persistência (`store.py`)

`.sparkforge-azure/graph/{graph.json,index.json,repos/<repo>.json}`. Rebuild incremental:
só o repositório cujo fingerprint de conteúdo mudou é reconstruído. `load_graph` confere o
fingerprint gravado e recusa arquivo adulterado.

## Collectors read-only (§173–179)

Pipeline: API Azure **ou** export offline → raw (memória) → **redação** → `assert_clean` →
facts (`azure.resource`, `databricks.job|cluster`, `unity_catalog.catalog`, `azure.cost`,
`azure.log_analytics.row`) → nós live.

- `redact.py`: JWT, bearer, `AccountKey=`, `SharedAccessKey=`, `SharedAccessSignature`,
  `Password=`, `sig=` de SAS, client secret, PEM, senha em URL, chave de storage, valores sob
  chaves sensíveis e cópias em base64 disso tudo; hash salgado opcional de principal ids.
  `assert_clean` roda antes de qualquer escrita/retorno e lista só caminhos, nunca valores.
- `resource_graph.py`: KQL `Resources | project id, name, type, location, resourceGroup,
  subscriptionId, tenantId, properties`, paginação por skip token; `from_export(path)` é o
  caminho padrão (sem auth).
- `databricks.py`, `cost.py`, `monitor.py`: `from_export` real + método live preguiçoso;
  extra ausente → `CollectorUnavailable` com dica de instalação. Custo ausente é `None`
  (Unknown ≠ Zero).
- `auth.py`: DefaultAzureCredential, Azure CLI, Managed Identity, Service Principal (segredo
  só por env), Workload Identity, via `require_azure_identity()` preguiçoso. Importar
  `collectors` não importa SDK algum (teste checa `sys.modules`).
- Read-only por construção: cada classe expõe só `collect(...)`; teste AST proíbe verbos
  mutantes (`begin_create`, `create_or_update`, `delete`, `update`, `put`, `post`, ...).
- `workspace_graph.py`: grafo live escopado às assinaturas declaradas no manifesto;
  observação fora do escopo é descartada e contada.
- Raw só é gravado se pedido, já redigido, em `.sparkforge-azure/raw/` com `.gitignore` `*`.
  Fixtures em `fixtures/azure/` são **sintéticos** e sem material secreto; os testes injetam
  segredos falsos gerados em runtime numa cópia temporária para provar a redação.

## CLI e MCP

| Superfície | Módulo | Risco |
|---|---|---|
| `graph build --root R [--manifest M] [--out O]` | `cli/cmd_graph.py` | offline |
| `graph query --graph G --kind K \| --layer L \| --neighbors ID \| --path A B` | `cli/cmd_graph.py` | offline |
| `graph impact --graph G --changed X...` | `cli/cmd_graph.py` | offline |
| `graph federate --static G [--live G] [--artifact G] [--knowledge-root R]` | `cli/cmd_graph.py` | offline |
| `collect workspace-graph --manifest M [--export E] [--live]` | `cli/cmd_collect.py` | offline; `--live` lê Azure |
| `collect resource-graph --export E` | `cli/cmd_collect.py` | offline |
| `sfa_graph_query` | `mcp/graph_tools.py` | READ_ONLY |
| `sfa_graph_impact` (compact) | `mcp/graph_tools.py` | READ_ONLY |
| `sfa_collect_workspace_graph` | `mcp/graph_tools.py` | CLOUD_READ (negada sem cloud read habilitado) |

Exit codes: 0 ok · 1 resultado `unresolved` · 2 entrada recusada. Leitura de nuvem exige
`--live` explícito; sem ele o comando usa export ou recusa.
