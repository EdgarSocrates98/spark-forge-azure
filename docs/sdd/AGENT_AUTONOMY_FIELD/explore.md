---
sdd: 1
feature: AGENT_AUTONOMY_FIELD
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: autonomy vive so em autonomy.py (runtime); manifests nao declaram
  tradeoffs:
  - hoje
  - o default BOUNDED §153 nao e contrato — nada trava
- id: A2
  summary: autonomy vira REQUIRED key do v2 com vocab fechado L0-L5; fleet cap <=L2
    enforced por teste
  tradeoffs:
  - §153 vira contrato
  - 40 manifests ganham 1 linha
chosen: A2 — §153-155 pedem o default conservador como contrato, nao convencao
---

# Explore — AGENT_AUTONOMY_FIELD

`autonomy.py` define L0-L5 com perfis, mas nenhum manifest declara nivel — o agente mais privilegiado e indistinguivel do menos. O campo vira obrigatorio no v2 com vocab fechado; L4/L5 ficam fora da frota por decisao declarada.
