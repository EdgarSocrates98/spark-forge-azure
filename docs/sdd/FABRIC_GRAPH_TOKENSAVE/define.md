---
sdd: 1
feature: FABRIC_GRAPH_TOKENSAVE
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_GRAPH_TOKENSAVE/explore.md
  sha256: "2db854afb02bae331df6490eaec89e2db1c1873333ee423b864ec5dbc07386fb"
hypothesis:
  claim: Node kinds Fabric no Graphfy existente + benchmark TokenSave + knowledge compiler escopado + spans fabric.* provam a mesma economia/evidência do vertical Databricks sem duplicar subsistemas
  prediction: impact queries (notebooks→lakehouse, items→shortcut, workspace→capacity) respondem; benchmark resolve caso 'notebook não lê tabela via shortcut' com required_recall=1.0 e bytes economizados;
    tokens=unresolved offline
  experiment: pytest tests/test_fabric_graph.py tests/test_fabric_tokensave.py
acceptance:
- id: AC1
  statement: node kinds fabric_*/onelake_* + edges workspace→capacity, contains, uses, invokes, writes_to, points_to, authenticates_via, member_of, grants — só com provenance explícita
  verified_by:
    kind: test
    ref: tests/test_fabric_graph.py::test_fabric_graph_nodes_edges
- id: AC2
  statement: cadeia notebook→lakehouse→shortcut→target construída; evidence paths derivam do grafo
  verified_by:
    kind: test
    ref: tests/test_fabric_graph.py::test_shortcut_chain_in_graph
- id: AC3
  statement: impact queries respondem as 5 perguntas do prompt (notebooks-usam-lakehouse, pipelines-invocam-notebook, items-dependem-shortcut, workspace-usa-capacity, impacto-de-mudança)
  verified_by:
    kind: test
    ref: tests/test_fabric_graph.py::test_impact_queries
- id: AC4
  statement: federation static+live por ID oficial com attr_conflicts preservado
  verified_by:
    kind: test
    ref: tests/test_fabric_graph.py::test_federation_by_fabric_id
- id: AC5
  statement: benchmark Fabric mede baseline/economy/balanced/deep com required_recall, bytes, calls, latency; tokens=unresolved
  verified_by:
    kind: test
    ref: tests/test_fabric_tokensave.py::test_fabric_benchmark
- id: AC6
  statement: knowledge packs fabric-* compilam por failure_layer; caso shortcut não carrega databricks/synapse/adf/purview
  verified_by:
    kind: test
    ref: tests/test_fabric_knowledge.py::test_fabric_pack_scoping
- id: AC7
  statement: spans fabric.* por estágio no ledger; overhead.stages no report
  verified_by:
    kind: test
    ref: tests/test_fabric_agentops.py::test_fabric_stage_spans
success:
- id: SC1
  metric: grafo no hot path + benchmark honesto + conftest limpo
  source: pytest tests/test_fabric_*.py
out_of_scope:
- live Fabric API collectors deep
- Tier-3 transcripts
unknowns: []
change_kinds:
- extractor
- rule
- fixture_corpus
---

# Define — FABRIC_GRAPH_TOKENSAVE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
