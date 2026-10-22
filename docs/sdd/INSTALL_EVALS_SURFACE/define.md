---
sdd: 1
feature: INSTALL_EVALS_SURFACE
phase: define
profile: dev
status: done
hypothesis:
  claim: "O corpus de avaliação já existente (evals/*, lab, agentic) pode ser inventariado, classificado nas 4 categorias do §7.1 e exposto pelos ops §7.2 sem reimplementar nenhum runner — basta uma taxonomia declarada + um verbo fino `sparkforge-azure evals`"
  prediction: "o manifesto forge/context/v1 passa a persistir eval_suites classificadas com integrity hash; `evals describe` nunca emite gabarito selado; suites de host recusam EVALS-REQUIRES-HOST em vez de execução sintética"
  experiment: "pytest tests/test_evals_surface.py (22 testes)"
acceptance:
  - id: AC1
    statement: "toda suite declarada carrega kind nas 4 categorias do §7.1 e as 4 estão populadas"
    verified_by: {kind: test, ref: tests/test_evals_surface.py::test_the_four_categories_are_all_populated}
  - id: AC2
    statement: "manifesto persiste eval_suites no shape fechado (id, kind, command) + capabilities.evals.detail com a contagem por categoria"
    verified_by: {kind: test, ref: tests/test_evals_surface.py::test_manifest_eval_suites_are_classified}
  - id: AC3
    statement: "os 6 ops §7.2 (evals.list/describe/run/result + verification.plan/run) aparecem como discovery.commands nomeados; discovery.ops do §6.2 permanece fechado"
    verified_by: {kind: test, ref: tests/test_evals_surface.py::test_manifest_declares_the_7_2_ops_as_commands}
  - id: AC4
    statement: "gabarito selado nunca sai: describe/list/manifest/result emitem metadados + sha256, nunca bytes de expected/ ou baselines"
    verified_by: {kind: test, ref: tests/test_evals_surface.py::test_describe_never_echoes_sealed_answers}
  - id: AC5
    statement: "suites de host recusam EVALS-REQUIRES-HOST e corpus sem runner recusa EVALS-RUNNER-UNAVAILABLE — nunca pass sintético"
    verified_by: {kind: test, ref: tests/test_evals_surface.py::test_evals_run_refuses_suites_that_only_a_host_executes}
  - id: AC6
    statement: "runners determinísticos executam e marcam environment=deterministic, real_environment_proof=false"
    verified_by: {kind: test, ref: tests/test_evals_surface.py::test_evals_run_agent_runtime_recomputes_cases}
  - id: AC7
    statement: "verification.plan/run são invocáveis via verbos reais (`lab plan`, `lab verify`) no fluxo plan->run->evidence do Forge Lab"
    verified_by: {kind: test, ref: tests/test_evals_surface.py::test_cli_verification_ops_exist}
success:
  - id: SC1
    metric: "9 suites classificadas em 4 categorias não-vazias (developer=4, runtime-decision=1, output-verification=1, host-conformance=3)"
    source: "sparkforge_azure/evals/taxonomy.py::kind_counts"
  - id: SC2
    metric: "teste de exposição §7.3: fatias de 40 chars de expected/ e baselines/ ausentes de todo payload de superfície"
    source: "tests/test_evals_surface.py::_fatias_de_resposta"
out_of_scope:
  - "novos runners de avaliação — os existentes são reutilizados (runner.py, gates scripts/, pytest, evaluate_case in-process)"
  - "execução de suites de host pela CLI — recusa nomeada por contrato (executor != avaliador)"
  - "alteração do `_forgecontext.py` canônico — o vocabular discovery.ops do §6.2 é fechado e pertence ao the-forge"
  - "push/PR — fora do escopo do worker"
unknowns:
  - id: U1
    unlock: "n/d — todos os campos são verificáveis por teste offline"
change_kinds: [tool_or_verb]
---

# Define — INSTALL_EVALS_SURFACE (install-2.0 ciclo 5, lf-0038)

A forja já tem infraestrutura nativa de evals — `evals/agentic`,
`evals/agent_runtime`, `evals/agents`, `evals/convergence`,
`evals/host_proof`, `evals/mcp-conformance`, `evals/parity`,
`evals/portability`, `evals/token_efficient`, mais o Forge Lab
(`sparkforge_azure/lab/`). O §7 do install-2.0 pede classificar esse
inventário nas 4 categorias, expor os seis ops conceituais por verbos
reais, selar os gabaritos e marcar prova simulada vs. real — sem
reimplementar runner algum.
