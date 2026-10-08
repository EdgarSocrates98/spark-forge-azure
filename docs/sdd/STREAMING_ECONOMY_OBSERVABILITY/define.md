---
sdd: 1
feature: STREAMING_ECONOMY_OBSERVABILITY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/STREAMING_ECONOMY_OBSERVABILITY/explore.md
  sha256: "7808377a427d6df18613aa4bf6235911c7971045fcef72ae47b51eacc3a971cb"
hypothesis:
  claim: "TokenSave e AgentOps provam economia em streaming: corpus com windowing por query_id/partition/time-range; spans stream.* auditaveis; superficies diagnose stream + sfa_diagnose_stream + doctor"
  prediction: "contexto streaming nao carrega logs inteiros quando janela resolve; suite lab 20+ cenarios verde"
  experiment: pytest tests/test_stream_tokensave.py tests/test_stream_cli.py
acceptance:
- id: AC1
  statement: "CLI diagnose stream --bundle|--suite + MCP sfa_diagnose_stream expoem a capability com contrato JSON"
  verified_by:
    kind: test
    ref: tests/test_stream_cli.py::test_diagnose_stream_cli_json_contract
- id: AC2
  statement: "corpus TokenSave streaming tem janela por query/partition/time; benchmark honesto sem baseline inflado"
  verified_by:
    kind: test
    ref: tests/test_stream_tokensave.py::test_stream_benchmark
- id: AC3
  statement: "knowledge packs stream com vertical:stream nao puxam material UC/lakehouse em caso de lag"
  verified_by:
    kind: test
    ref: tests/test_stream_knowledge.py::test_stream_pack_scoping
- id: AC4
  statement: "doctor streaming_vertical verde; suite fixtures/stream >=20 cenarios contra oraculo expect:"
  verified_by:
    kind: test
    ref: tests/test_stream_suite.py::test_stream_suite_all_cases
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

# Define — STREAMING_ECONOMY_OBSERVABILITY

Artefato do Cycle 4 (Streaming / Event Hubs + Fabric RTI deep vertical);
ver prompt_evo_cycle4.md.
