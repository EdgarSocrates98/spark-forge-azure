---
sdd: 1
feature: STRUCTURED_STREAMING
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/STRUCTURED_STREAMING/explore.md
  sha256: "055a180da2aa203c4e2e63ea777a8a32bfda7fbdc16bca0906949e888bae141c"
hypothesis:
  claim: "StreamingQueryProgress + checkpoint metadata + config de query permitem classificar stalls (consumer vs checkpoint vs processing vs sink) sem claims de lag falsos"
  prediction: "progress events viram facts stream.*; dip de um batch nao vira sustained lag; checkpoint nao-avancando com source avancando aponta camada checkpoint"
  experiment: pytest tests/test_stream_progress.py
acceptance:
- id: AC1
  statement: "progress events viram facts com batch_id/rates/offsets por particao; query id persistido vs runId por restart"
  verified_by:
    kind: test
    ref: tests/test_stream_progress.py::test_progress_events_become_facts
- id: AC2
  statement: "single-batch processed<input nunca classifica sustained lag; input>process sustentado + backlog growth = spark_processing"
  verified_by:
    kind: test
    ref: tests/test_stream_progress.py::test_single_batch_dip_not_lag
- id: AC3
  statement: "checkpoint deleted + startingOffsets=latest = data-loss RISK finding; behind retention = finding forte"
  verified_by:
    kind: test
    ref: tests/test_stream_progress.py::test_checkpoint_deleted_latest_risk
- id: AC4
  statement: "state store growth so com series; watermark ausente em agregacao = state growth risk, nunca falha garantida"
  verified_by:
    kind: test
    ref: tests/test_stream_progress.py::test_state_growth_needs_series
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

# Define — STRUCTURED_STREAMING

Artefato do Cycle 4 (Streaming / Event Hubs + Fabric RTI deep vertical);
ver prompt_evo_cycle4.md.
