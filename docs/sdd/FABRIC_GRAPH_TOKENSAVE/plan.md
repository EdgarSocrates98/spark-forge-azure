---
sdd: 1
feature: FABRIC_GRAPH_TOKENSAVE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_GRAPH_TOKENSAVE/design.md
  sha256: "9c7b1459258e208befc2b60ad09647cbda6e55c5e75e2c6586aa06f09096ad46"
tasks:
- id: T1
  files:
  - sparkforge_azure/graph/fabric.py
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_fabric_graph.py
    name: test_fabric_graph_nodes_edges
- id: T2
  files:
  - evals/token_efficient/fabric_case/
  - evals/token_efficient/
  covers:
  - AC5
  test:
    path: tests/test_fabric_tokensave.py
    name: test_fabric_benchmark
- id: T3
  files:
  - knowledge/packs.yaml
  - sparkforge_azure/knowledgebase/vertical.py
  covers:
  - AC6
  test:
    path: tests/test_fabric_knowledge.py
    name: test_fabric_pack_scoping
- id: T4
  files:
  - sparkforge_azure/fabric/pipeline.py
  covers:
  - AC7
  test:
    path: tests/test_fabric_agentops.py
    name: test_fabric_stage_spans
---

# Plan — FABRIC_GRAPH_TOKENSAVE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
