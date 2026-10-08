---
sdd: 1
feature: GRAPHFY_ACCESS
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/GRAPHFY_ACCESS/explore.md
  sha256: "0c6a1084025fc00094776718559ccc3cd29a54e62f4e809e4269f664f87a96e1"
hypothesis:
  claim: "Um builder de grafo de acesso com arestas de proveniência explícita torna o Graphfy parte real da resolução do caso (caminho de evidência e consultas de impacto), não JSON decorativo"
  prediction: "queries de alto valor respondem com nós+provenance determinísticos; merge estático/live do mesmo ARM id unifica e divergência declara conflito"
  experiment: "pytest tests/test_access_graph.py tests/test_access_graph_federation.py"
acceptance:
  - id: AC1
    statement: "builder emite as relações job→uses→cluster, job→executes→notebook, notebook→reads/writes→table, external_location→uses→storage_credential→uses_identity→managed_identity→has_role→assignment, external_location→points_to→path, table→located_at→external_location, todas com provenance"
    verified_by: {kind: test, ref: tests/test_access_graph.py::test_access_relations_have_provenance}
  - id: AC2
    statement: "static+live do mesmo ARM id federam num nó; divergência de atributo cria conflict explícito; live carrega observed_at"
    verified_by: {kind: test, ref: tests/test_access_graph_federation.py::test_static_live_merge_and_divergence}
  - id: AC3
    statement: "consultas 'quem pode acessar storage X', 'jobs dependentes de external location Y', 'o que quebra se Y mudar', 'tabelas dependentes de credential Z' e 'qual repo define R' respondem determinístico e limitado"
    verified_by: {kind: test, ref: tests/test_access_queries.py::test_high_value_queries}
  - id: AC4
    statement: "diagnóstico anexa evidence_path do grafo (finding → facts → artefato-fonte)"
    verified_by: {kind: test, ref: tests/test_access_pipeline.py::test_evidence_path_from_graph}
  - id: AC5
    statement: "nenhuma aresta por coincidência de nome; binding ausente cai em unresolved"
    verified_by: {kind: test, ref: tests/test_access_graph.py::test_no_name_matching_edges}
success:
  - id: SC1
    metric: "grafo de acesso participa do diagnóstico real e as queries de alto valor são determinísticas e bounded"
    source: "pytest tests/test_access_graph*.py tests/test_access_queries.py"
out_of_scope:
  - "ranking semântico por embeddings; expansão automática sem limite"
unknowns: []
change_kinds: [tool_or_verb]
---

# Define — GRAPHFY_ACCESS

Graphfy deixa de ser fundação e vira operação: o diagnóstico carrega caminho de
evidência no grafo e responde as consultas de acesso de alto valor sem mandar o
grafo inteiro para contexto.
