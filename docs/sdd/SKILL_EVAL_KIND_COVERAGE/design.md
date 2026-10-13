---
sdd: 1
feature: SKILL_EVAL_KIND_COVERAGE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/SKILL_EVAL_KIND_COVERAGE/define.md
  sha256: 20e940506a2015748aa0ba52958c4376f6959024e56f70f07932507170d929e6
files:
- path: tests/test_skills.py
  action: modify
  reason: teste na arvore real de cobertura de kinds
- path: skills/analyze-batch-loop/evals/evals.yaml
  action: modify
  reason: negative + boundary
- path: skills/azure-bicep/evals/evals.yaml
  action: modify
  reason: negative + boundary
- path: skills/azure-finops/evals/evals.yaml
  action: modify
  reason: negative + boundary
- path: skills/azure-observability/evals/evals.yaml
  action: modify
  reason: negative + boundary
- path: skills/azure-purview/evals/evals.yaml
  action: modify
  reason: negative + boundary
- path: skills/azure-spark/evals/evals.yaml
  action: modify
  reason: negative + boundary
- path: skills/azure-terraform/evals/evals.yaml
  action: modify
  reason: negative + boundary
- path: skills/iceberg/evals/evals.yaml
  action: modify
  reason: negative + boundary
decisions:
- id: D1
  choice: A2 — teste na arvore real + casos ancorados em dominio adjacente do proprio
    Handoff
  rejected:
  - estender VERTICAL_SKILLS (muda contrato)
  - casos negativos genericos sem alvo real
  rollback: reverter o commit da feature
covers:
- part: eval_kind_coverage
  acceptance:
  - AC1
  - AC2
---

# Design — SKILL_EVAL_KIND_COVERAGE
