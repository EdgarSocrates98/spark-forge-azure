---
sdd: 1
feature: UPSTREAM_FACTS_INTAKE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/UPSTREAM_FACTS_INTAKE/design.md
  sha256: 38d33de39d04ceb1faa2aeca0eb9b3f96d08a8747bd2d33042e58a7d83a54ccd
tasks:
- id: T1
  files: [tests/test_upstream_facts.py]
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_upstream_facts.py
    name: test_forbidden_instruction_key_refused_at_any_depth
- id: T2
  files: [sparkforge_azure/adapters/upstream.py]
  covers: [AC1, AC2]
  test:
    path: tests/test_upstream_facts.py
    name: test_valid_document_passes_with_stamped_provenance
- id: T3
  files:
  - sparkforge_azure/azure/casefile.py
  - sparkforge_azure/fabric/casefile.py
  - sparkforge_azure/stream/casefile.py
  - sparkforge_azure/migration/casefile.py
  - sparkforge_azure/azure/pipeline.py
  - sparkforge_azure/fabric/pipeline.py
  - sparkforge_azure/stream/pipeline.py
  - sparkforge_azure/migration/pipeline.py
  covers: [AC3, AC4]
  test:
    path: tests/test_upstream_facts.py
    name: test_bundle_intake_and_judge_never_fires_on_foreign_kinds
---

# Plan — UPSTREAM_FACTS_INTAKE

T1: contrato de testes (validacao + bounds + integracao bundle).
T2: adapter fail-closed. T3: seam nos 4 dominios + publicacao como evidencia.
