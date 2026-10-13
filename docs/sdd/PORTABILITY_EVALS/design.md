---
sdd: 1
feature: PORTABILITY_EVALS
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABILITY_EVALS/define.md
  sha256: "82fb1e45af85255de272e5c37fa18dd8abfc2872247efaba7e401b087dd74ee7"
files:
  - path: evals/portability/suite.yaml
    action: create
    reason: "declara os 10 casos §97 + expect + flags §99–§101"
  - path: evals/portability/runner.py
    action: create
    reason: "executa casos em temp dirs via API distribution; HOME/XDG
      falsos; reporta reports/portability-matrix.json"
  - path: scripts/check_portability.py
    action: create
    reason: "gate §188 — assets/schema/docs/mirrors/checkout-dep; --wheel
      é o T3 §194 (uv build → venv temp → lifecycle)"
  - path: docs/portability/PORTABILITY_OUTCOME.md
    action: create
    reason: "outcome brief §200–§204 com scorecard e paridade final"
  - path: docs/guides/SPARKFORGE_AZURE_PORTABLE.md
    action: create
    reason: "quickstart EN §129"
  - path: docs/guides/SPARKFORGE_AZURE_PORTABLE.pt-BR.md
    action: create
    reason: "quickstart pt-BR §129"
  - path: docs/claims.lock.json
    action: modify
    reason: "4 claims novos com proof executável (§189–§190)"
  - path: docs/README.md
    action: modify
    reason: "indexar outcome + quickstarts (gate docs_index)"
decisions:
  - id: D1
    choice: "runner de matriz em evals/ (gate de cenário), não pytest —
      prova integração do ciclo; unit tests já cobrem unidade"
    rejected:
      - "pytest — o spec separa evals/portability/ de tests/"
    rollback: "runner é standalone; nada nos tests depende dele"
  - id: D2
    choice: "uv preferido no wheel gate; pip wheel + venv --with-pip como
      fallback — o venv do repo não tem pip"
    rejected:
      - "pip only — quebraria na máquina atual (venv sem pip module)"
      - "system-site-packages — veria o editable install, falso positivo"
    rollback: "gate é script; nenhuma dependência de produto adicionada"
  - id: D3
    choice: "expects vivem em suite.yaml; runner mapeia id→função e
      compara — spec decide, runner executa"
    rejected:
      - "expects no código — mistura contrato com mecanismo"
    rollback: "yaml novo; sem efeito em código existente"
covers:
  - part: evals/portability/runner.py (10 casos)
    acceptance: [AC1]
  - part: scripts/check_portability.py (gate + --wheel)
    acceptance: [AC2, AC3]
  - part: docs/claims.lock.json + PORTABILITY_OUTCOME.md
    acceptance: [AC4, AC5]
---

# PORTABILITY_EVALS — design

Cada `case_<id>` monta a cena mínima (projetos semeados, workspace,
arestas por id) e devolve observações; `_check` compara com `expect:`.
`_run_isolated` redireciona HOME/USERPROFILE/APPDATA/XDG_CACHE_HOME para
um temp dir e reprova o caso se qualquer arquivo aparecer lá (§99–§100).
O wheel gate usa `uv build` → `uv venv` → `uv pip install` (deps do
projeto: só PyYAML+jsonschema) → subprocess corre init/status/detach/
reattach do pacote instalado, cwd fora do checkout.
