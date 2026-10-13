---
sdd: 1
feature: PORTABILITY_CLOSURE_POLISH
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABILITY_CLOSURE_POLISH/explore.md
  sha256: "147b952f4f6812d72c2efa5bef79e5a1e9aff26b687adcb087d4744eccfd7622"
hypothesis:
  claim: "As capabilities de portabilidade já estão completas; o risco
    restante é evidência/documentação velha gerando conclusões erradas
    sobre paridade ou estado medido"
  prediction: "depois da reconciliação, toda afirmação de paridade casa com
    os mains atuais, o estado medido é gerado e o gate cobre a frescura"
  experiment: pytest tests/test_distribution.py tests/test_portability_evals.py
acceptance:
  - id: AC1
    statement: "docs/CURRENT_STATE.md é gerado por scripts/gen_current_state.py
      com campos derivados de fonte viva (SHA, versão, claims, skills, agents,
      MCP tools, portabilidade, freeze, REMOTE_CI); --check detecta drift"
    verified_by:
      kind: command
      ref: ".venv/Scripts/python scripts/gen_current_state.py --check"
  - id: AC2
    statement: "PORTABILITY_OUTCOME.md tem seção 'Post-closure freshness
      update' com paridade recomputada dos mains atuais, vereditos
      qualitativos e SHAs amarrados; snapshot de closure preservado"
    verified_by:
      kind: command
      ref: ".venv/Scripts/python scripts/check_docs_index.py && .venv/Scripts/python scripts/check_docs_surface.py"
  - id: AC3
    statement: "check_portability.py cobre FAILURE_KINDS ⊆ TROUBLESHOOTING.md,
      comandos dos quickstarts ⊆ surface lock e frescura de CURRENT_STATE.md"
    verified_by:
      kind: test
      ref: tests/test_portability_evals.py::test_portability_gate_static_ok
  - id: AC4
    statement: "verbos pré-existentes seguem funcionando sem `distribution
      init` — backward compat explícito"
    verified_by:
      kind: test
      ref: tests/test_distribution.py::test_existing_verbs_work_without_distribution_init
success:
  - id: SC1
    metric: "paridade atual recomputada com SHAs; CURRENT_STATE gerado e
      gated; gates verdes; freeze frozen; zero regressão de runtime"
    source: scripts/check_portability.py
out_of_scope:
  - novas capabilities de distribuição/workspace/contexto
  - novos hosts, novas tools MCP, novos agents
  - mudança arquitetural — freeze permanece frozen
change_kinds:
  - claims
  - status_numbers
---

# PORTABILITY_CLOSURE_POLISH — define

Reconciliar docs/evidência com a `main` atual. O outcome guarda o snapshot
de closure; a paridade atual vai numa seção separada e datada por SHA; o
número vivo de testes/claims vem de `CURRENT_STATE.md` gerado — nada é
mantido à mão.
