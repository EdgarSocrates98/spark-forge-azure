---
sdd: 1
feature: COSMOS_DEEP
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/COSMOS_DEEP/plan.md
  sha256: "82ba0cff09be1236e70f3b057afb99ebef52a684e33ad8603bcdef06c03a017f"
tasks:
- id: T1
  status: done
  red:
    command: python scripts/check_knowledge.py --write-index
    exit: 1
  green:
    command: python scripts/check_knowledge.py --write-index
    exit: 0
- id: T2
  status: done
  red:
    command: python scripts/check_skills_agents.py
    exit: 1
  green:
    command: python scripts/check_skills_agents.py
    exit: 0
- id: T3
  status: done
  red:
    command: python -m pytest tests/test_agent_manifests.py tests/test_agent_eval_cases.py tests/test_agent_contract_v2.py -q
    exit: 1
  green:
    command: python -m pytest tests/test_agent_manifests.py tests/test_agent_eval_cases.py tests/test_agent_contract_v2.py -q
    exit: 0
- id: T4
  status: done
  red:
    command: python -m pytest tests/test_skills.py tests/test_knowledgebase.py -q
    exit: 1
  green:
    command: python -m pytest tests/test_skills.py tests/test_knowledgebase.py -q
    exit: 0
claims:
- text: "catalogo fechado registra 24 skills e 21 specialists com mirrors sincronizados"
  evidence_ref: python scripts/check_skills_agents.py (ok:true, errors:[])
- text: "5 docs knowledge/azure/cosmosdb/ VERIFIED com 15 fontes oficiais datadas 2026-11-03"
  evidence_ref: python scripts/check_knowledge.py --write-index (entries:42, violations:[])
- text: "termos cosmos/change feed/partition key/request unit roteam para cosmos-db-specialist"
  evidence_ref: tests/test_agent_eval_cases.py + evals/agents/cosmos-db-specialist.yaml
- text: "docs geradas (reference/skills.md, reference/agents.md, AGENT_INVENTORY, CAPABILITY) refletem o catalogo novo"
  evidence_ref: scripts/gen_skills_doc.py, scripts/gen_agents_doc.py, scripts/gen_agent_inventory.py, scripts/gen_agent_capability.py
change_id: null
---

# Build report — COSMOS_DEEP

Red real: check_knowledge reprovou o formato de `versions` (string vs lista);
check_skills_agents reprovou YAML com `:` virando mapping, eval nao-ancorado e
coordinator com 51 linhas; pytest reprovou `## Fontes` ausente, EXPECTED_IDS
desatualizado e contagens congeladas. Todos resolvidos por ajuste do artefato
ou do teste — nenhum criterio enfraquecido.
