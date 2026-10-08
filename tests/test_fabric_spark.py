"""SDD FABRIC_SPARK — runtime matrix, default lakehouse, retry policy."""
from __future__ import annotations

from sparkforge_azure.fabric.diagnose import RUNTIME_MATRIX, evaluate_spark
from sparkforge_azure.fabric.pipeline import run_fabric_case
from sparkforge_azure.findings.models import Fact

FIXTURES = "tests/fixtures/fabric"


def _chain(report):
    return {s["layer"]: s for s in report["diagnosis"]["chain"]}


def test_missing_default_lakehouse():
    r = run_fabric_case(f"{FIXTURES}/f06_sjd_missing_lakehouse")
    assert r["status"] == "denied"
    assert r["failure_layer"] == "spark_job"
    assert _chain(r)["spark_job"]["verdict"] == "deny"


def test_wrong_default_lakehouse():
    r = run_fabric_case(f"{FIXTURES}/f07_sjd_wrong_lakehouse")
    assert _chain(r)["spark_job"]["verdict"] == "deny"
    assert r["failure_layer"] == "spark_job"


def test_runtime_never_guessed():
    """No environment evidence → spark_runtime is UNKNOWN, never assumed."""
    facts = []
    rt, _job = evaluate_spark(facts, {"job": {"id": "j", "kind": "Notebook"}},
                              "spn")
    assert rt.verdict.value == "unknown"
    # And a known runtime beats a mismatched one.
    env = Fact(kind="fabric.environment", subject={"item_id": "e1"},
               attrs={"runtime_version": "1.3", "spark_version": "3.5"})
    rt2, _j2 = evaluate_spark([env], {
        "job": {"id": "j", "kind": "Notebook", "environment_id": "e1",
                "runtime": "2.0"}}, "spn")
    assert rt2.verdict.value == "deny"


def test_runtime_matrix_documented():
    assert RUNTIME_MATRIX["2.0"]["spark"] == "4.1"
    assert RUNTIME_MATRIX["1.3"]["status"] == "eosa_lts"


def test_runtime_mismatch_case():
    r = run_fabric_case(f"{FIXTURES}/f08_runtime_mismatch")
    assert r["failure_layer"] == "spark_runtime"


def test_retry_idempotency_finding():
    """SJD retry enabled without idempotency evidence → SF-FAB-003."""
    facts = [Fact(kind="fabric.spark_job", subject={"item_id": "s"},
                  attrs={"retry_policy_enabled": True,
                        "retry_idempotent_evidence": False})]
    from sparkforge_azure.rules.engine import judge
    from sparkforge_azure.rules.loader import load_catalog
    rules = [r for r in load_catalog() if r["id"] == "SF-FAB-003"]
    findings, _ = judge(facts, rules, runtime={}, return_skipped=True)
    assert findings and findings[0].rule_id == "SF-FAB-003"


def test_notebook_scan_onelake_paths():
    """Fabric notebooks scan: pyspark facts land (repartition/groupBy etc)."""
    r = run_fabric_case(f"{FIXTURES}/f11_slow_spark_healthy_capacity")
    kinds = {f["kind"] for f in r["facts"]}
    assert any(k.startswith("pyspark.") or k.startswith("notebook.")
               for k in kinds)
