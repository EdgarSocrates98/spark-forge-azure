---
sdd: 1
feature: GRAPHFY_ACCESS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/GRAPHFY_ACCESS/define.md
  sha256: "1590679379f2a36d35d82f058c23bbfac1445428217175bc22eda06c170cec76"
files:
  - {path: sparkforge_azure/graph/access.py, action: create, reason: "builder: facts de acesso → nós/arestas da cadeia com provenance obrigatória"}
  - {path: sparkforge_azure/graph/access_queries.py, action: create, reason: "consultas de alto valor determinísticas e bounded"}
  - {path: sparkforge_azure/graph/live.py, action: modify, reason: "novos kinds: unity_catalog.storage_credential, external_location, grant, workspace_binding; databricks.notebook; azure.role_assignment"}
  - {path: sparkforge_azure/graph/evidence.py, action: create, reason: "evidence_path via access graph: finding → facts → artefato-fonte"}
  - {path: tests/test_access_graph.py, action: create, reason: "relações + provenance + anti name-matching"}
  - {path: tests/test_access_graph_federation.py, action: create, reason: "static+live merge/divergence/observed_at"}
  - {path: tests/test_access_queries.py, action: create, reason: "5 queries de alto valor"}
decisions:
  - id: D1
    choice: "builder próprio em vez de estender live.py para toda a cadeia; live.py ganha só os kinds novos de recurso"
    rejected: ["tudo em live.py: mistura hierarquia ARM com relações de acesso"]
    rollback: "mover access.py para dentro de live.py"
  - id: D2
    choice: "arestas só de ids/urls literais carregados como atributo do fact"
    rejected: ["match por nome: proibido pelo prompt e pela federation.py"]
    rollback: "n/d"
covers:
  - {part: builder, acceptance: [AC1, AC5]}
  - {part: federation, acceptance: [AC2]}
  - {part: queries, acceptance: [AC3]}
  - {part: pipeline, acceptance: [AC4]}
---

# Design — GRAPHFY_ACCESS

`access.py` lê facts (`unity_catalog.*`, `azure.role_assignment`, `adls.*`,
`databricks.*`, `notebook.*`) e emite a cadeia de acesso. `access_queries.py`
responde as perguntas do prompt como funções bounded sobre o `Graph`.
