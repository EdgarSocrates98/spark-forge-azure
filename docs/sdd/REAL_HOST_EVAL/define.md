---
sdd: 1
feature: REAL_HOST_EVAL
phase: define
profile: dev
status: done
hypothesis:
  claim: 'com claude_code host_proven, o harness A/B ganha sinal empirico
    real: 1 spawn de specialist por vertical produz vector §57 com
    cost=measured, nao unresolved'
  prediction: 'evals/agent_runtime/reports/<case>.host.json por case registra
    specialist real: output vira provisional via parse_freeform/JSON, quality
    mede required_findings cobertos, necessity sai do vocab §59'
  experiment: pytest tests/test_host_eval.py + 4 reports host gravados
acceptance:
- id: AC1
  statement: 'evaluate_case_host(case, runtime=claude_code) roda config B
    real: spawn do specialist roteado, output DATA_ONLY parseado, schema
    validado, custo medido do envelope'
  verified_by:
    kind: test
    ref: tests/test_host_eval.py::test_host_eval_report_shape
- id: AC2
  statement: 'report <case>.host.json carrega tokens/cost MEASURED do
    envelope claude — nunca estimado; latent_s real; trace_ref do spawn'
  verified_by:
    kind: test
    ref: tests/test_host_eval.py::test_host_reports_measured_usage
- id: AC3
  statement: 'host report reusa _measure_quality + value_vector do harness:
    required/forbidden/unresolved comparados ao expected do case; necessity
    ∈ vocab §59 — nunca promovido sem evidencia'
  verified_by:
    kind: test
    ref: tests/test_host_eval.py::test_host_eval_quality_vector
success:
- id: SC1
  metric: '4 reports <case>.host.json com cost.status=measured; freeze
    critical_specialists_evaluated passa a met com evidencia nomeada'
  source: pytest tests/test_host_eval.py + evaluate_freeze()
out_of_scope:
- eval completo A-D em host (cada config = N spawns; B e o minimo honesto)
- verifier/reviewer em host (deterministico inline ja cobre; §221-226)
- auto-remocao de agent por resultado (§61 proibe)
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — REAL_HOST_EVAL

Com `claude_code` `host_proven`, o eval deixa de ser simulado: uma execucao
real do specialist roteado por case (config B = core + specialist). O output
do host e DATA_ONLY — parseado para `specialist_result`, validado por schema,
promovido a provisional (§31-32). Custo/tokens vem medidos do envelope — a
primeira medida empirica real de custo de agente do projeto.
