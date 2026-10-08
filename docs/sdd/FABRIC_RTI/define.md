---
sdd: 1
feature: FABRIC_RTI
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_RTI/explore.md
  sha256: "4d17c29a1e67927a4956d8f43af8e1d1d2a29f8388eaa122a95a2311ac1d7eef"
hypothesis:
  claim: "RTI e uma cadeia com failure semantics proprias: Real-Time Hub -> Eventstream (source/publish/transform/destination) -> Eventhouse/KQL -> Activator (mapping/evaluation/action)"
  prediction: "eventstream nao-publicado, destination quebrada, ingestion lag e activator mapping/evaluation caem em camadas distintas; rule evaluated != action succeeded"
  experiment: pytest tests/test_stream_rti.py
acceptance:
- id: AC1
  statement: "eventstream facts modelam sources/transforms/destinations/publish_state separadamente"
  verified_by:
    kind: test
    ref: tests/test_stream_rti.py::test_eventstream_facts
- id: AC2
  statement: "destination Eventhouse com erro != source failure; ingestion lag medido por freshness de tabela KQL"
  verified_by:
    kind: test
    ref: tests/test_stream_rti.py::test_destination_vs_source_layers
- id: AC3
  statement: "activator mapping invalido = activator_mapping; KQL queryset stale = activator_evaluation — nunca streaming source issue"
  verified_by:
    kind: test
    ref: tests/test_stream_rti.py::test_activator_mapping_vs_evaluation
- id: AC4
  statement: "rule evaluated nunca afirma business action; action evidence explicita ou unresolved"
  verified_by:
    kind: test
    ref: tests/test_stream_rti.py::test_activator_action_needs_evidence
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

# Define — FABRIC_RTI

Artefato do Cycle 4 (Streaming / Event Hubs + Fabric RTI deep vertical);
ver prompt_evo_cycle4.md.
