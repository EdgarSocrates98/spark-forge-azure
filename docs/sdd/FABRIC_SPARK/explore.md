---
sdd: 1
feature: FABRIC_SPARK
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Reusar regras Databricks runtime
  tradeoffs:
  - proibido (#57) — runtime matrix e semânticas divergem
- id: A2
  summary: Runtime matrix versionada+sourced (1.3 EOSA Spark 3.5.5/Delta 3.2/Py3.11 vs 2.0 GA Spark 4.1/Delta 4.2/Py3.13), env item, default lakehouse, SJD contract, path relativo
  tradeoffs:
  - fiel à docs
  - precisa de manutenção versionada — mitigado por sources.lock
chosen: A2 — runtime = unresolved sem artifact; default lakehouse modela contexto de path relativo
---

# Explore — FABRIC_SPARK

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
