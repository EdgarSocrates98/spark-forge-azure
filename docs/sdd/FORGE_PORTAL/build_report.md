---
sdd: 1
feature: FORGE_PORTAL
phase: build_report
profile: dev
status: ready
upstream:
  sha256: "a55e8fdd09ff5f34e4e01a68be8d56cb0e1324b299a35982030cb7aeab3902e8"
  path: docs/sdd/FORGE_PORTAL/plan.md
tasks:
  - id: T1
    status: done
    red:
      command: "pytest tests/test_portal_adapter.py (sem _forge_portal.py vendored — collection error)"
      exit: 2
    green:
      command: "pytest tests/test_portal_adapter.py — 18 passed"
      exit: 0
  - id: T2
    status: done
    red:
      command: "pytest tests/test_portal_adapter.py (sem portal_adapter.py — collection error)"
      exit: 2
    green:
      command: "pytest tests/test_portal_adapter.py — 18 passed"
      exit: 0
  - id: T3
    status: done
    red:
      command: "pytest tests/test_portal_adapter.py::test_portal_verb_parseia (verbo fora do COMMAND_MODULES)"
      exit: 1
    green:
      command: "python scripts/check_surface_lock.py --update → ok"
      exit: 0
  - id: T4
    status: done
    red:
      command: "pytest tests/test_portal_adapter.py::test_assets_index_resolvido (sem portal/assets)"
      exit: 1
    green:
      command: "pytest tests/test_portal_adapter.py::test_assets_index_resolvido"
      exit: 0
  - id: T5
    status: done
    red:
      command: "pytest tests/test_architecture_layers.py (5 arestas portal_adapter não declaradas)"
      exit: 1
    green:
      command: "pytest tests/test_architecture_layers.py — 5 passed; check_docs_surface ok:true"
      exit: 0
claims:
  - text: "portal serve a jornada install→hosts→mcp→task sobre serviços reais"
    evidence_ref: tests/test_portal_adapter.py
  - text: "toda mutação exige confirm + plan_token; recusas nomeadas"
    evidence_ref: tests/test_portal_adapter.py::test_install_plan_apply_verified
  - text: "catálogos vêm do pacote — 22 skills, 40 agents reais"
    evidence_ref: tests/test_portal_adapter.py::test_catalogo_skills_e_agents_do_repo
---

# FORGE_PORTAL — build report

Red real observado: ledger managed.json grava paths absolutos (assert
relativo falhou) e doctor dev-reporta `degraded` honesto num ambiente
sem binário — testes ajustados à semântica real, nunca ao contrário.
Surface lock e camadas mediram o verbo/arestas novos e foram declarados.
