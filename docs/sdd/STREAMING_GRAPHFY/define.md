---
sdd: 1
feature: STREAMING_GRAPHFY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/STREAMING_GRAPHFY/explore.md
  sha256: "715d2e2cd18dd82ce395551daa21c8670e10419cd1226753974cd64249fb741d"
hypothesis:
  claim: "O grafo streaming modela flow (producer->hub->partition->cg->query->sink e source->eventstream->destination->eventhouse->activator) + state (checkpoint) + ownership sem inventar causalidade"
  prediction: "evidence_paths incluem graph_path para findings; impact query responde quem consome hub X"
  experiment: pytest tests/test_stream_graph.py
acceptance:
- id: AC1
  statement: "nos stream/rti com kinds dedicados; edges flow/reads_from/writes_to/checkpoints/monitors com provenance"
  verified_by:
    kind: test
    ref: tests/test_stream_graph.py::test_stream_graph_nodes_edges
- id: AC2
  statement: "findings viram nos evidence no grafo com arestas aos facts citados (overlay como fabric)"
  verified_by:
    kind: test
    ref: tests/test_stream_graph.py::test_finding_overlay_in_graph
- id: AC3
  statement: "grafo nunca cria causalidade sem evidencia — aresta causal so quando finding a sustenta"
  verified_by:
    kind: test
    ref: tests/test_stream_graph.py::test_no_invented_causality
success:
- id: SC1
  metric: pipeline streaming verde offline; failure layer correto por caso; claims novos com prova
  source: pytest tests/test_stream_*.py
out_of_scope:
- collectors live Event Hubs/RTI
- ADF/Synapse migration (Cycle 5)
- exactly-once marketing claims
unknowns: []
change_kinds:
- extractor
- rule
- rule_area
- tool_or_verb
- fixture_corpus
---

# Define — STREAMING_GRAPHFY

Artefato do Cycle 4 (Streaming / Event Hubs + Fabric RTI deep vertical);
ver prompt_evo_cycle4.md.
