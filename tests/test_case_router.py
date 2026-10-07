from sparkforge_azure.case.router import ROUTING_OPERATORS, next_step
from sparkforge_azure.case.store import new_case, set_gate, set_phase

RUNTIME = {"databricks_runtime": "15.4", "spark": "3.5.0", "python": "3.11", "delta": "3.2.0"}


def case(phase="diagnosis", **over):
    base = set_phase(new_case("c", "2026-07-29T00:00:00Z", RUNTIME), phase)
    for key, value in over.items():
        base[key] = value
    return base


class TestOperators:
    def test_declared_operator_set_is_closed(self):
        assert ROUTING_OPERATORS == frozenset(
            {"equals", "absent", "present", "count_gt", "count_eq", "contains", "any_where"}
        )


class TestIntake:
    def test_missing_runtime_routes_to_diagnose(self):
        step = next_step(case(phase="intake", runtime={}), [])
        assert step["recommended_skill"] == "azure-spark"
        assert step["reason"].startswith("ROUTE-001")

    def test_divergent_runtime_routes_to_diagnose(self):
        divergent = case(phase="intake", runtime=dict(RUNTIME, divergences=["spark: ..."]))
        assert next_step(divergent, [])["reason"].startswith("ROUTE-001")

    def test_no_facts_routes_to_call_graph(self):
        step = next_step(case(phase="inventory"), [])
        assert step["recommended_skill"] == "azure-spark"
        assert step["reason"].startswith("ROUTE-002")




class TestGatesAreAdvisory:
    def test_missing_baseline_is_reported_not_blocking(self):
        ready = set_gate(case(), "dominant_bottleneck_identified", True)
        step = next_step(ready, [])
        assert step["recommended_skill"] == "spark-performance"
        assert "baseline_captured" in step["blocked_by"]

    def test_blocked_by_is_empty_when_gates_satisfied(self):
        ready = set_gate(
            set_gate(case(), "dominant_bottleneck_identified", True), "baseline_captured", True
        )
        assert next_step(ready, [])["blocked_by"] == []


class TestFallback:
    def test_unmatched_state_falls_back_and_says_so(self):
        odd = case(phase="report")
        odd["gates"] = dict.fromkeys(odd["gates"], True)
        step = next_step(odd, [])
        assert step["recommended_skill"] == "azure-spark"
        assert "Nenhuma regra" in step["reason"]


class TestDeterminism:
    def test_same_case_yields_same_step(self):
        assert next_step(case(), ["SF-UI-001", "SF-UI-002"]) == next_step(
            case(), ["SF-UI-002", "SF-UI-001"]
        )

    def test_reason_always_cites_a_rule_id_or_says_fallback(self):
        for findings in ([], ["SF-PY-004"], ["SF-UI-001"], ["SF-ICE-002"]):
            assert next_step(case(), findings)["reason"][:5] in ("ROUTE", "Nenhu")
