---
sdd: 1
feature: AGENT_DOD_GATE
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: DoD so no inventario (dims)
  tradeoffs:
  - ja existe
  - dims medem mas nao agrupam por papel nem produzem artefato de capability
- id: A2
  summary: test_agent_dod.py por familia (role/specialist/reviewer/subagent) + agents/CAPABILITY.json
    gerado + gate de novo agent no CONTRIBUTING
  tradeoffs:
  - DoD explicito por papel
  - mais um artefato gerado
chosen: A2 — §217-221 pedem DoD por papel e §137/214 pedem capability manifest
---

# Explore — AGENT_DOD_GATE

O inventario mede dims por agent mas o prompt pede DoD explicito por papel e um capability manifest. O gate de novo agent hoje e tribal — vai para CONTRIBUTING como checklist enforced por teste.
