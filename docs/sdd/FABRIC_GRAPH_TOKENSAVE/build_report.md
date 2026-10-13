---
sdd: 1
feature: FABRIC_GRAPH_TOKENSAVE
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_GRAPH_TOKENSAVE/plan.md
  sha256: "f8ecd1b5143a1adef83e3e0fefdc3eadbc43398b3f6dedc3e2c9f17b946cac41"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_graph.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_graph.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_tokensave.py::test_fabric_benchmark -q", exit: 1}
    green: {command: "python -m pytest tests/test_fabric_tokensave.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_knowledge.py::test_fabric_pack_scoping -q", exit: 1}
    green: {command: "python -m pytest tests/test_fabric_knowledge.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_agentops.py tests/test_fabric_waste.py tests/test_fabric_collectors.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_agentops.py tests/test_fabric_waste.py tests/test_fabric_collectors.py -q", exit: 0}
claims:
  - text: "grafo Fabric tem nos/arestas tipados no layer 'fabric' do registry"
    evidence_ref: "tests/test_fabric_graph.py::test_fabric_graph_nodes_edges"
  - text: "cadeia de shortcut aparece como caminho no grafo"
    evidence_ref: "tests/test_fabric_graph.py::test_shortcut_chain_in_graph"
  - text: "impact queries respondem capacity->workspace e dependents"
    evidence_ref: "tests/test_fabric_graph.py::test_impact_queries"
  - text: "federacao identifica Fabric ids sem confundir com ARM"
    evidence_ref: "tests/test_fabric_graph.py::test_federation_by_fabric_id"
  - text: "benchmark tokensave do caso Fabric mede frontier (recall/latencia/calls), sem score magico"
    evidence_ref: "tests/test_fabric_tokensave.py::test_fabric_benchmark"
  - text: "knowledge scoping por failure layer so carrega packs relevantes"
    evidence_ref: "tests/test_fabric_knowledge.py::test_fabric_pack_scoping"
  - text: "spans fabric.<stage> sao registrados no ledger AgentOps"
    evidence_ref: "tests/test_fabric_agentops.py::test_fabric_stage_spans"
---

# Build Report — FABRIC_GRAPH_TOKENSAVE

Red em worktree base `068b922` (pre-Fabric), green em `feat/cycle3-fabric-deep`. Detalhes no frontmatter.
