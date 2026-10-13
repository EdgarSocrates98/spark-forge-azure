---
sdd: 1
feature: FABRIC_SPARK
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_SPARK/explore.md
  sha256: "77558bb1fa091497a3743bad9c1fccc27d42ad4c58dc1fc64e84eed646390a16"
hypothesis:
  claim: Runtime matrix sourced + default-lakehouse context + SJD contract permitem diagnosticar 'runtime mismatch', 'missing default lakehouse' e 'relative path resolve errado' deterministicamente
  prediction: fixtures com environment 1.3 vs job requerendo 2.0 produzem spark_runtime; SJD sem defaultLakehouseArtifactId produz lakehouse/spark_job; path relativo com default lakehouse divergente produz
    finding de contexto
  experiment: pytest tests/test_fabric_spark.py
acceptance:
- id: AC1
  statement: runtime matrix versionada e sourced; ausência de artifact → runtime=unresolved
  verified_by:
    kind: test
    ref: tests/test_fabric_spark.py::test_runtime_never_guessed
- id: AC2
  statement: 'SJD facts: executableFile, mainClass, defaultLakehouseArtifactId, additionalLakehouseIds, retryPolicy, environmentArtifactId; default ausente → finding'
  verified_by:
    kind: test
    ref: tests/test_fabric_spark.py::test_missing_default_lakehouse
- id: AC3
  statement: código assumindo lakehouse A com contexto B → finding wrong-default-lakehouse com evidence
  verified_by:
    kind: test
    ref: tests/test_fabric_spark.py::test_wrong_default_lakehouse
- id: AC4
  statement: retryPolicy ativa + efeito colateral não-idempotente observável → risk finding; retry sozinho não é finding
  verified_by:
    kind: test
    ref: tests/test_fabric_spark.py::test_retry_idempotency_finding
- id: AC5
  statement: codeintel reconhece abfss://onelake, mssparkutils, refs de tabela lakehouse
  verified_by:
    kind: test
    ref: tests/test_fabric_spark.py::test_notebook_scan_onelake_paths
success:
- id: SC1
  metric: cenários spark_runtime/spark_job/lakehouse verdes; regras genéricas Spark reusadas sem copiar
  source: pytest tests/test_fabric_spark.py
out_of_scope:
- Native Execution Engine deep
- Spark performance tuning genérico (já coberto)
unknowns: []
change_kinds:
- extractor
- rule
- fixture_corpus
---

# Define — FABRIC_SPARK

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
