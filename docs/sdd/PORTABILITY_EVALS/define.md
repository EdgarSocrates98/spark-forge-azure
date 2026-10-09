---
sdd: 1
feature: PORTABILITY_EVALS
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABILITY_EVALS/explore.md
  sha256: "1b1c051e74b2a7c222b6bd2731dca823c81489aaa04c7403b6006d60d006b478"
hypothesis:
  claim: "Uma matriz de 10 casos dirigida por suite.yaml, com HOME/XDG
    redirecionados e um gate que inclui wheel instalado fora do checkout,
    prova §199 (lifecycle/workspace/relocation/multi-repo/scopes/wheel-only/
    host/detach) sem tocar o HOME real"
  prediction: "os 10 casos reportam ok; check_portability --wheel reporta
    `portability gate: ok`; nenhum caso escreve fora do temp root"
  experiment: "python evals/portability/runner.py && python
    scripts/check_portability.py --wheel"
acceptance:
  - id: AC1
    statement: "os 10 casos do §97 existem e passam via runner em temp dirs
      com HOME falso"
    verified_by:
      kind: command
      ref: "python evals/portability/runner.py — saída `portability: ok`"
  - id: AC2
    statement: "check_portability cobre §188: assets sha256, schema
      workspace, docs indexadas, sem checkout dep, mirrors (no --wheel)"
    verified_by:
      kind: command
      ref: "python scripts/check_portability.py — `portability gate: ok`"
  - id: AC3
    statement: "T3 wheel: build+install em venv temp fora do checkout roda
      init/status/detach/reattach"
    verified_by:
      kind: command
      ref: "python scripts/check_portability.py --wheel — gate ok"
  - id: AC4
    statement: "claims §189 só com prova executável: wheel, relocation,
      multi-repo-context, detach-safe"
    verified_by:
      kind: command
      ref: "python scripts/check_claims.py --static — textos no outcome doc"
  - id: AC5
    statement: "PORTABILITY_OUTCOME.md tem os campos §201 e scorecard
      PROVEN/PARTIAL/DEFERRED (§202)"
    verified_by:
      kind: command
      ref: "python scripts/check_portability.py — docs check inclui outcome"
success:
  - id: SC1
    metric: "0 writes em HOME real; 10/10 casos ok; wheel gate ok"
    source: evals/portability/runner.py + scripts/check_portability.py
out_of_scope:
  - T4 host real novo — reuso de evals/host_proof/claude_code.json (§196)
  - CI remoto — sem quota no momento do merge; gates locais cobrem
  - cross-OS real (Linux runner) — paths testados via semântica; §98
change_kinds:
  - claims
  - tool_or_verb
---

# PORTABILITY_EVALS — define

## Contrato

1. `evals/portability/suite.yaml` declara os 10 casos + expect + flags de
   isolamento; `runner.py` executa e emite `reports/portability-matrix.json`.
2. `scripts/check_portability.py` é o gate §188: assets, schema, docs,
   checkout-dep sempre; mirrors + wheel com `--wheel` (T3, §194).
3. `docs/portability/PORTABILITY_OUTCOME.md` fecha com §201/§202/§204.
4. 4 claims novos só com prova executável (§189–§192).

## Não-objetivos deliberados

Sem prova de host real nova: §196 diz reusar a existente. CI remoto fica
PARTIAL — o dono autorizou merge com CI vermelho por quota.
