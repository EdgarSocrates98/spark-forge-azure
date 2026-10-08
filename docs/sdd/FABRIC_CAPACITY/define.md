---
sdd: 1
feature: FABRIC_CAPACITY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CAPACITY/explore.md
  sha256: "f2e82b2fd12c2d1a85ea8ffe3a5a2903b25d6865a7c2882d940132e725698bf5"
hypothesis:
  claim: Com artifacts de métricas exportados (CapacityMetrics app), o diagnóstico distingue 'job lento por Spark' de 'capacity throttling' e recusa inferir throttling de utilização alta isolada
  prediction: fixture com utilization alta sem throttling events → finding overloaded sem claim de throttling; fixture com CapacityLimitExceeded/delays → capacity; ausência de metrics → unresolved
  experiment: pytest tests/test_fabric_capacity.py
acceptance:
- id: AC1
  statement: 'capacity facts: id, SKU, state, workspace assignments, operations, throttling evidence quando observável'
  verified_by:
    kind: test
    ref: tests/test_fabric_capacity.py::test_capacity_facts
- id: AC2
  statement: high utilization sem evento de throttling/rejeição → overloaded_without_observed_throttling, nunca 'throttled'
  verified_by:
    kind: test
    ref: tests/test_fabric_capacity.py::test_overload_is_not_throttling
- id: AC3
  statement: CapacityLimitExceeded/throttling metrics/delays/rejections → capacity finding
  verified_by:
    kind: test
    ref: tests/test_fabric_capacity.py::test_throttled_with_evidence
- id: AC4
  statement: sem metrics artifact → capacity=unresolved (nunca healthy)
  verified_by:
    kind: test
    ref: tests/test_fabric_capacity.py::test_no_metrics_unresolved
- id: AC5
  statement: slow job + capacity healthy + skew observado → Spark finding, não capacity (root-cause order)
  verified_by:
    kind: test
    ref: tests/test_fabric_capacity.py::test_spark_vs_capacity_attribution
success:
- id: SC1
  metric: cenários capacity/throttling/unresolved verdes sem inferência de threshold
  source: pytest tests/test_fabric_capacity.py
out_of_scope:
- FinOps deep
- live Capacity Metrics API collector (offline export first)
unknowns: []
change_kinds:
- extractor
- rule
- fixture_corpus
---

# Define — FABRIC_CAPACITY

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
