---
sdd: 1
feature: FORGE_PORTAL
phase: define
profile: dev
status: ready
hypothesis:
  claim: "`sparkforge-azure portal` expõe a UI web local opcional do
    Forge Portal sobre os serviços reais do pacote (install lifecycle,
    host-flow, registry, graphview, docs inventory, mcp_verify) —
    mesmo contrato `forge/PortalApi/1` dos irmãos, sem duplicar engine"
  prediction: "bootstrap responde NOT_INSTALLED em workspace virgem;
    catálogo vem do pacote; plan→confirm→apply executa o lifecycle real
    com ledger; intent ambígua recusa SFA-PORTAL-AMBIGUOUS"
  experiment: pytest tests/test_portal_adapter.py — 18 testes HTTP reais
acceptance:
  - id: AC1
    statement: "GET /bootstrap em workspace virgem descreve a forja
      (forge_id, capabilities) e health NOT_INSTALLED honesto"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_bootstrap_workspace_vazio
  - id: AC2
    statement: "toda chamada /api/v1 exige X-Forge-Session válido —
      token errado recebe 403"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_bootstrap_exige_sessao
  - id: AC3
    statement: "catálogos skills/agents/hosts/docs vêm dos serviços reais
      do pacote — nunca estado fabricado"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_catalogo_skills_e_agents_do_repo
  - id: AC4
    statement: "installation plan→apply exige confirm + plan_token
      assinado; token forjado recusa PORTAL-PLAN-STALE; sem confirm
      recusa PORTAL-CONFIRM; apply real escreve ledger managed"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_install_plan_apply_verified
  - id: AC5
    statement: "intent ambígua recusa SFA-PORTAL-AMBIGUOUS com safe_verbs;
      scope/host inválidos recusam PORTAL-BAD-FIELD"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_task_intencao_ambigua_recusa_nomeada
  - id: AC6
    statement: "tasks seguras (status/doctor/mcp_verify) executam via
      plan→confirm→execute e produzem receipt forge/*; execute sem
      confirm recusa"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_task_doctor_roundtrip
  - id: AC7
    statement: "verbo `portal` entra no parser, na surface.lock (80
      comandos) e na referência cli.md com porquê/quando"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_portal_verb_parseia
  - id: AC8
    statement: "SPA resolvida de portal/assets (clone) ou
      portal_assets packaged (wheel) — index.html existe"
    verified_by:
      kind: test
      ref: tests/test_portal_adapter.py::test_assets_index_resolvido
success:
  - id: SC1
    metric: "0 código de servidor próprio — _forge_portal.py vendored
      byte-identical ao canônico forge-portal"
    source: portal/manifest.json sha256
  - id: SC2
    metric: "0 mutation sem confirm+token; 0 host launch implícito"
    source: tests/test_portal_adapter.py
out_of_scope:
  - páginas especializadas azure (analyze/diagnose UI) — a FASE 5 cobre
    paridade de portal; verticais especializadas são fase posterior
  - host launch automático — boundary TTY/humano mantido
  - bind não-loopback — portal é local-first por contrato
change_kinds:
  - tool_or_verb
  - dependency
  - disk_read
---

# FORGE_PORTAL — define

## Contrato

`sparkforge-azure portal [--no-browser] [--port N] [--root PATH]`:

1. Serve a SPA Forge Portal em `127.0.0.1` com token de sessão.
2. Adapta `forge/PortalApi/1` aos serviços reais: install.service
   (apply/status/doctor/repair/uninstall), distribution.ai (hosts),
   CanonicalRegistry (skills/agents), graphview (views), docs inventory
   (search), mcp_verify (handshake).
3. Toda mutação: plan → plan_token → confirm → execute. Recusas
   nomeadas `SFA-PORTAL-*` / `PORTAL-*`.

## Não-objetivos deliberados

Servidor próprio por forja foi rejeitado — o canônico é vendored
byte-identical (provado por sha256 no manifest de vendor). O portal é
cliente, nunca substitui CLI/TUI/MCP.
