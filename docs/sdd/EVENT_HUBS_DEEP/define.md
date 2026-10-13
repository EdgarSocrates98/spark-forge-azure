---
sdd: 1
feature: EVENT_HUBS_DEEP
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/EVENT_HUBS_DEEP/explore.md
  sha256: "278433d7709b0bb6dec8b17f9bf83ccd0be30a9417c61535f308195b3c42d7ed"
hypothesis:
  claim: "Um modelo Event Hubs (namespace/hub/partition/consumer group/producer/consumer/auth/network/capture) com fact kinds versionados permite diagnosticar lag e stalls sem confundir availability do servico com progresso do consumer"
  prediction: "bundles streaming produzem facts eh.* tipados; partition skew e throttled_requests viram camadas distintas; source position vs consumer position comparados por particao"
  experiment: pytest tests/test_stream_extractors.py
acceptance:
- id: AC1
  statement: "fact kinds eh.* versionados com provenance; IDs ARM/oficiais como identidade, nunca display name"
  verified_by:
    kind: test
    ref: tests/test_stream_extractors.py::test_eventhubs_artifacts_become_facts
- id: AC2
  statement: "modelo separa namespace/hub/partition/consumer-group sem fundir axes; lag modelado por particao (offset+time)"
  verified_by:
    kind: test
    ref: tests/test_stream_extractors.py::test_partition_positions_modeled
- id: AC3
  statement: "metricas sao time-series com freshness; single point nunca vira trend"
  verified_by:
    kind: test
    ref: tests/test_stream_extractors.py::test_metrics_timeseries_not_point
- id: AC4
  statement: "segredos de connection string/SAS nunca entram em facts (redacao no boundary)"
  verified_by:
    kind: test
    ref: tests/test_stream_extractors.py::test_sas_never_in_facts
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

# Define — EVENT_HUBS_DEEP

Artefato do Cycle 4 (Streaming / Event Hubs + Fabric RTI deep vertical);
ver prompt_evo_cycle4.md.
