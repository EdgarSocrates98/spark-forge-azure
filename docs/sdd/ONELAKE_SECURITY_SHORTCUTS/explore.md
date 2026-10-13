---
sdd: 1
feature: ONELAKE_SECURITY_SHORTCUTS
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Reusar cadeia UC/RBAC/ACL do Cycle 2 mapeando conceitos
  tradeoffs:
  - 'falso — prompt #28 proíbe; semânticas divergem (grant-only vs RBAC deny)'
- id: A2
  summary: 'Modelo próprio: control plane (workspace roles + item perms) vs data plane (OneLake security roles); shortcut chain com effective identity'
  tradeoffs:
  - fiel à docs MS atuais
  - novo vocabulário — justificado pela divergência real
chosen: A2 — dois planos explícitos; shortcut passthrough/delegated decide effective identity
---

# Explore — ONELAKE_SECURITY_SHORTCUTS

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
