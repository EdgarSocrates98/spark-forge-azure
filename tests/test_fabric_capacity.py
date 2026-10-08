"""SDD FABRIC_CAPACITY — utilization != throttling; evidence required."""
from __future__ import annotations

from sparkforge_azure.azure.governance.model import Verdict
from sparkforge_azure.fabric.diagnose import evaluate_capacity
from sparkforge_azure.fabric.pipeline import run_fabric_case
from sparkforge_azure.findings.models import Fact

FIXTURES = "tests/fixtures/fabric"


def test_capacity_facts():
    facts = [Fact(kind="fabric.capacity", subject={"capacity_id": "c1"},
                  attrs={"sku": "F8", "state": "Active",
                         "metric_utilization_percent": 42}),
             Fact(kind="fabric.workspace_capacity",
                  subject={"workspace_id": "w", "capacity_id": "c1"})]
    v = evaluate_capacity(facts, "w", "spn")
    assert v.verdict is Verdict.ALLOW
    assert "no throttling event" in v.reason


def test_overload_is_not_throttling():
    """utilization 120% without a throttling event → NOT denied, and the
    report carries the honest overload finding instead."""
    r = run_fabric_case(f"{FIXTURES}/f09_overload_not_throttled")
    assert r["status"] == "findings"
    stages = {s["layer"]: s["verdict"] for s in r["diagnosis"]["chain"]}
    assert stages["capacity"] == "allow"
    assert any(f["rule_id"] == "SF-FAB-002" for f in r["findings"])
    assert r["failure_layer"] is None


def test_throttled_with_evidence():
    r = run_fabric_case(f"{FIXTURES}/f10_capacity_throttled")
    assert r["status"] == "denied"
    assert r["failure_layer"] == "capacity"
    stages = {s["layer"]: s["verdict"] for s in r["diagnosis"]["chain"]}
    assert stages["capacity"] == "deny"


def test_no_metrics_unresolved():
    facts = [Fact(kind="fabric.capacity", subject={"capacity_id": "c1"},
                  attrs={"sku": "F4"})]
    # capacity exists but no workspace link and no metrics → still resolvable
    # as "no throttling observed" only when linked; unlinked = allow-unknown?
    v = evaluate_capacity(facts, "w", "spn")
    assert v.verdict in (Verdict.UNKNOWN, Verdict.ALLOW)
    # Without any capacity artifact at all → UNKNOWN, never "healthy".
    v2 = evaluate_capacity([], "w", "spn")
    assert v2.verdict is Verdict.UNKNOWN


def test_spark_vs_capacity_attribution():
    """Slow job with healthy capacity + skew in code → Spark findings, no
    capacity claim."""
    r = run_fabric_case(f"{FIXTURES}/f11_slow_spark_healthy_capacity")
    stages = {s["layer"]: s["verdict"] for s in r["diagnosis"]["chain"]}
    assert stages["capacity"] == "allow"
    assert r["failure_layer"] is None
    assert r["status"] == "findings"
    assert any(f["rule_id"].startswith("SF-PY") for f in r["findings"])
