---
sdd: 1
feature: MCP_AGENT_ADMIN
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: sem tools novas — CLI ja cobre
  tradeoffs:
  - zero superficie
  - consumidores MCP nao inspecionam a frota
- id: A2
  summary: 'duas tools read-only: sfa_agents_list (inventario+status) e sfa_agents_explain_route
    (explain_route)'
  tradeoffs:
  - minimo util
  - mais 2 entradas no surface lock
chosen: A2 — §147-148 pedem inspecao MCP read-only sem bloat; dois verbos bastam
---

# Explore — MCP_AGENT_ADMIN

A superficie tem 13 tools e nenhuma inspeciona a frota. O prompt pede agent control via MCP *sem* bloat: list + explain_route sao read-only, derivados das mesmas funcoes do CLI (sem logica duplicada).
