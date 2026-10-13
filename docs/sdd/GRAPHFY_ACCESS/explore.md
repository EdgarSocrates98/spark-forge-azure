---
sdd: 1
feature: GRAPHFY_ACCESS
phase: explore
profile: dev
status: done
approaches:
  - id: A1
    summary: "Builder dedicado `graph/access.py` que converte facts de acesso (UC, RBAC, ADLS, jobs, notebooks) em nós e arestas da cadeia de acesso, com provenance obrigatória por aresta, mais `graph/access_queries.py` com as consultas de alto valor"
    tradeoffs:
      - arestas só de ids explícitos (mesma regra da federação); nada por nome igual
      - queries retornam fatos/nós com caminho de evidência, não texto solto
  - id: A2
    summary: Estender `live_graph_from_facts` com os tipos novos
    tradeoffs:
      - cobre ingestão mas não as relações de acesso nem as consultas
  - id: A3
    summary: Grafo semântico por embeddings
    tradeoffs:
      - o prompt proíbe inferir aresta por similaridade/nome
chosen: A1
---

# Explore — GRAPHFY_ACCESS

## Estado atual (audit)

- `graph/model.py`: `Node`/`Edge`/`Provenance`, ids determinísticos, `merge()`, `conflicts`, `unresolved`, `stats`, fingerprint.
- `graph/live.py`: facts → grafo live (`azure.resource`, `databricks.job`, `databricks.cluster`, `unity_catalog.catalog`) com hierarquia ARM e referências literais em `properties`.
- `graph/federation.py`: merge estático+live por id idêntico apenas, `ambiguous_names`, bindings declarados.
- `graph/query.py`: `find_nodes`, `neighbors`, `shortest_path`, `slice_graph` — determinísticos e limitados.
- `graph/impact.py`: impacto de mudança por categoria.

## O que falta

Relações da cadeia de acesso (job→cluster, job→notebook, notebook→table/path, external_location→storage_credential→managed_identity→role_assignment, external_location→abfss, table→external_location), consultas de alto valor (quem acessa o storage; quais jobs dependem da location; o que quebra se ela mudar; quais tabelas dependem da credential; qual repo define o recurso), prova de federação estático/live no mesmo ARM id com divergência → conflito, e integração do grafo no pipeline de diagnóstico como caminho de evidência.
