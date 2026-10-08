---
sdd: 1
feature: SYNAPSE_FABRIC_SPARK
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/SYNAPSE_FABRIC_SPARK/explore.md
  sha256: "8e1de68f12deff97849a8fdcf4b05135cd8841f35a749bea7ceafdea96950474"
hypothesis:
  claim: "Notebooks Synapse sao varridos por padroes de refactor oficiais (mssparkutils->notebookutils, synapsesql->delta, spark.catalog.* nao suportados, paths /user/trusted-service-user) e pool->environment/config/library gaps viram findings tipados"
  prediction: "cada padrao detectado vira finding com arquivo+linha+pattern; pool diff nao forca 1:1 de compute; notebook inteiro nunca e auto-rewritten"
  experiment: pytest tests/test_migration_spark.py
acceptance:
- id: AC1
  statement: "patterns oficiais de refactor detectados por ocorrencia com evidence (mssparkutils, synapsesql, catalog API, linked-service paths)"
  verified_by:
    kind: test
    ref: tests/test_migration_spark.py::test_refactor_patterns_detected
- id: AC2
  statement: "spark config custom classificada (supported/change/unsupported) sem mapear compute 1:1"
  verified_by:
    kind: test
    ref: tests/test_migration_spark.py::test_spark_config_classified
- id: AC3
  statement: "library sem compatibilidade provada e REVIEW/UNRESOLVED, nunca unsupported inventado"
  verified_by:
    kind: test
    ref: tests/test_migration_spark.py::test_library_unknown_is_review
- id: AC4
  statement: "notebook dependency graph alimenta blast radius"
  verified_by:
    kind: test
    ref: tests/test_migration_spark.py::test_notebook_dependency_graph
success:
- id: SC1
  metric: pipeline migration verde offline; readiness correto por caso; claims novos com prova
  source: pytest tests/test_migration_*.py
out_of_scope:
- auto-rewrite seguro de trechos; Scala/Java deep; notebook ipynb->fabric converter
unknowns: []
change_kinds:
- extractor
- rule
---

# Define — SYNAPSE_FABRIC_SPARK

Artefato do Cycle 5 (ADF/Synapse -> Fabric migration vertical); ver prompt_evo_cycle5.md.
