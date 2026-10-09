---
sdd: 1
feature: HOST_PROOF_RECORDED
phase: define
profile: dev
status: done
hypothesis:
  claim: 'host_proven deixa de ser aspiracao: evals/host_proof/<runtime>.json
    grava o transcript real; adapter promove status por artefato, nunca por flag'
  prediction: claude_code passa a host_proven com proof=path do transcript;
    demais hosts seguem adapter_implemented ate prova propria
  experiment: pytest tests/test_host_proof.py
acceptance:
- id: AC1
  statement: 'artefato de prova: evals/host_proof/<runtime>.json gravado por
    execucao real contem status=completed, trace_ref sha256 e proof_kind'
  verified_by:
    kind: test
    ref: tests/test_host_proof.py::test_proof_artifact_schema
- id: AC2
  statement: 'HostCLIAdapter.status deriva do artefato: transcript valido ->
    host_proven; ausente/invalido -> adapter_implemented; prova corrompida
    nunca promove'
  verified_by:
    kind: test
    ref: tests/test_host_proof.py::test_status_derives_from_artifact
- id: AC3
  statement: 'registry reporta proof=path do artefato; freeze passa a ver
    claude_code host_proven — e NENHUM outro host sem transcript proprio'
  verified_by:
    kind: test
    ref: tests/test_host_proof.py::test_registry_reports_proof
success:
- id: SC1
  metric: 'runtime_registry()["claude_code"].status == host_proven com proof
    apontando para evals/host_proof/claude_code.json; freeze
    host_execution_proven=met'
  source: pytest tests/test_host_proof.py
out_of_scope:
- provar devin/devin_desktop/codex (exige transcript proprio por runtime)
- rodar o eval completo A-D em host real (W2 cobre specialist vertical)
- parse do envelope claude --output-format json (fica no adapter do W2)
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — HOST_PROOF_RECORDED

§9/§88: `host_proven` so existe com transcript real gravado. O artefato e a
prova — `evals/host_proof/<runtime>.json` contem o SpawnResultV2 completo de
uma execucao real (`status=completed`, `trace_ref` sha256, `proof_kind`).
O adapter le o artefato para derivar status: prova valida promove, prova
ausente/corrompida nunca promove. Status continua sendo evidencia, nunca
declaracao.
