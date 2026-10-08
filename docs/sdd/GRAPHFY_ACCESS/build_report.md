---
sdd: 1
feature: GRAPHFY_ACCESS
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/GRAPHFY_ACCESS/plan.md
  sha256: "f4d4585dd265778b2ec5447b9204e413ed0a90e414f747db3f62b140b2421e23"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-red-p0c && ../.venv/Scripts/python -m pytest tests/test_access_graph.py::test_access_relations_have_provenance tests/test_access_graph.py::test_no_name_matching_edges tests/test_access_graph_federation.py::test_static_live_merge_and_divergence -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_graph.py tests/test_access_graph_federation.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-red-p0c && ../.venv/Scripts/python -m pytest tests/test_access_queries.py::test_high_value_queries -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_queries.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-red-p0c && ../.venv/Scripts/python -m pytest tests/test_access_pipeline.py::test_evidence_path_from_graph -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_pipeline.py::test_evidence_path_from_graph -q", exit: 0}
claims:
  - text: "facts do vertical viram cadeia de acesso tipada com proveniencia em todo no e aresta (job->cluster->notebook->table->location->credential->identity->role)"
    evidence_ref: "tests/test_access_graph.py::test_access_relations_have_provenance"
  - text: "grafo estatico (bundle) e live (collector) federam por ARM id com observed_by dual e conflito de attrs declarado"
    evidence_ref: "tests/test_access_graph_federation.py"
  - text: "cinco consultas de alto valor respondem bounded e deterministico; alvo ausente e declarado, nao adivinhado"
    evidence_ref: "tests/test_access_queries.py::test_high_value_queries"
  - text: "finding carrega evidence path derivado do grafo: finding -> evidenced_by -> fact node -> artifact"
    evidence_ref: "tests/test_access_pipeline.py::test_evidence_path_from_graph"
  - text: "nenhuma aresta por coincidencia de nome; bindings ausentes viram unresolved com razao nomeada"
    evidence_ref: "tests/test_access_graph.py::test_no_name_matching_edges"
change_id: "feat/cycle2-evolution"
---

# Build Report — GRAPHFY_ACCESS

Reds registrados num worktree da base (`b1caf70`): os tres arquivos de teste
novos falham na coleta (exit 4 — `graph/access`, `graph/access_queries`,
`graph/evidence` e o `azure.pipeline` nao existiam).

- `pytest tests/test_access_graph*.py tests/test_access_queries.py
  tests/test_access_pipeline.py -q` → 11 passed.
- `graph/access.py`: builder em duas passagens (nos depois arestas) porque a
  ordem deterministica dos facts coloca `external_location` antes de
  `storage_credential`. Toda aresta sai de id/url/ARM explicito do fact;
  referencia ausente cai em `graph.unresolved` com razao nomeada.
- `graph/access_queries.py`: cinco consultas bounded (who_can_access,
  jobs_depending_on, what_breaks_if_changed via `impact`, tables_of_credential,
  repo_defining) — resultado nunca e o grafo inteiro; budget e `truncated`
  explicitos; alvo ausente levanta ou declara, nunca adivinha.
- `graph/evidence.py`: caminho `finding -> evidenced_by -> fact -> artifact`
  derivado do grafo; o pipeline injeta `graph_path` em cada `evidence_paths`.
- `graph/live.py`: kinds do vertical (`azure_rbac.*`, `adls.*`,
  `unity_catalog.*`, `databricks.compute`, `notebook.*`) roteiam para o mesmo
  builder — provenance `live` preservada pelo `mode` do fact, entao collector
  e bundle federam no mesmo ARM id.
- `graph/arm.py`: `Microsoft.Databricks/accessConnectors` mapeado para kind
  `identity` (ja estava); scope de assignment vira `kind_for_arm_id` correto
  (storage_account, nao generico `resource`).
- `sparkforge_azure/abfss.py` (novo kernel-leaf): `split_abfss` e a gramatica
  unica; `azure.governance.model.parse_abfss` delega e embrulha em
  `ScenarioError`. Isso elimina a aresta proibida `graph -> azure` — o parser
  vive abaixo de ambos. Arestas novas declaradas: `azure->abfss`,
  `graph->abfss`.
- Filesystem aninhado (`abfss://lake@stg/finance/orders` dentro de
  `loc .../finance`) liga por `part_of` ao prefixo explicito mais longo —
  nunca por similaridade de nome.
- `graph/impact.py`: relacoes de acesso entram em `DEPENDENCY_DIRECTION`
  (todas `reverse` exceto `exposes_identity`/`governs` forward/both) para que
  `what_breaks_if_changed` reuse o traversal bounded existente.
