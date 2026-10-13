---
sdd: 1
feature: FORGE_PORTAL
phase: design
profile: dev
status: ready
upstream:
  sha256: "aa511c1b682edcefb18c05261860ae5b5e45d511e6084e99abc7cf8d38502447"
  path: docs/sdd/FORGE_PORTAL/define.md
files:
  - path: sparkforge_azure/portal_adapter.py
    action: create
    reason: "adapter forge/PortalApi/1 → serviços reais azure (install,
      distribution.ai, registry, graphview, docs, mcp_verify)"
  - path: sparkforge_azure/cli/cmd_portal.py
    action: create
    reason: "verbo portal no padrão argparse COMMAND_MODULES com
      rationale no docstring"
  - path: sparkforge_azure/cli/main.py
    action: modify
    reason: "registrar cmd_portal no COMMAND_MODULES"
  - path: sparkforge_azure/_forge_portal.py
    action: create
    reason: "servidor portal vendored byte-identical (stdlib http.server)"
  - path: portal/assets/
    action: create
    reason: "SPA vendored com manifest sha256 — distribuição clone+wheel"
  - path: pyproject.toml
    action: modify
    reason: "force-include portal/assets → portal_assets no wheel;
      sdist; per-file-ignore do vendored"
  - path: tests/test_portal_adapter.py
    action: create
    reason: "AC1–AC8 — HTTP real contra servidor efêmero"
  - path: tests/test_architecture_layers.py
    action: modify
    reason: "declarar arestas portal_adapter→serviços como superfície L7"
  - path: docs/reference/cli.md
    action: modify
    reason: "seção portal com porquê/quando — gate docs_surface"
  - path: docs/surface.lock.json
    action: modify
    reason: "surface lock regenerado — 80 comandos"
decisions:
  - id: D1
    choice: "Servidor + SPA vendored byte-identical do forge-portal
      canônico, provado por portal/manifest.json sha256 — arquitetura
      replica, domínio não copia"
    rejected:
      - "servidor próprio por forja — três implementações de sessão/
        token divergiriam em semanas"
      - "dependência de pacote compartilhado — forja é instalável
        standalone; vendor é o mecanismo aprovado dos irmãos"
    rollback: "remover _forge_portal.py + portal/assets + verbo"
  - id: D2
    choice: "portal_adapter top-level como superfície L7 ao lado de
      cli/mcp — arestas declaradas no gate de camadas"
    rejected:
      - "subpackage portal/ — um módulo de adaptação não justifica
        pacote; irmãos usam top-level"
    rollback: "mover para cli/ e redeclarar arestas"
  - id: D3
    choice: "intent ambígua vira SFA-PORTAL-AMBIGUOUS com safe_verbs —
      o portal nunca executa heurística em cima de texto livre"
    rejected:
      - "best-effort fuzzy match — executaria o verbo errado com
        confiança falsa"
    rollback: "trocar o ramo `_plan_task` desconhecido por best-effort —
      reversível no adapter"
covers:
  - part: sparkforge_azure/portal_adapter.py
    acceptance: [AC1, AC2, AC3, AC4, AC5, AC6]
  - part: sparkforge_azure/cli/cmd_portal.py + cli/main.py
    acceptance: [AC7]
  - part: portal/assets + pyproject force-include
    acceptance: [AC8]
  - part: docs/reference/cli.md + surface.lock.json
    acceptance: [AC7]
---

# FORGE_PORTAL — design

O adapter é a única peça com lógica azure: mapeia operações do contrato
para os serviços já testados do pacote e traduz seus documentos
`forge/*` para o envelope do portal. Nada de regra de negócio nova —
orquestração e tradução de envelope apenas.
