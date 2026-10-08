"""Access-case memory (prompt #116-120).

Stores UC/ADLS diagnosis cases in the institutional memory
(``agentic.memory``) keyed by an *Azure* environment fingerprint — tenant,
subscription, workspace, DBR/Spark, storage account class, UC metastore —
with no secrets. Records whose ``environment`` score is 0 on retrieval are
returned as ``wrong_environment: true`` and are never auto-reusable (#118):
they surface for human review, they do not decide.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.memory import (
    DecisionMemoryRecord,
    _fingerprint,
    _now,
    classify_memory_candidate,
    persist_memory_candidate,
    retrieve_memory,
)

_ARM_SUBSCRIPTION = re.compile(r"/subscriptions/([^/]+)", re.I)


def _subscription(value: Any) -> str:
    """Subscription GUID from any ARM id in the value; '' when absent."""
    if isinstance(value, str):
        m = _ARM_SUBSCRIPTION.search(value)
        if m:
            return m.group(1)
    if isinstance(value, Mapping):
        for v in value.values():
            found = _subscription(v)
            if found:
                return found
    if isinstance(value, (list, tuple)):
        for v in value:
            found = _subscription(v)
            if found:
                return found
    return ""


def env_fingerprint(report: Mapping[str, Any]) -> dict[str, Any]:
    """Azure environment fingerprint for an access case (prompt #117).

    Built from the case + facts a ``run_case`` report already carries —
    tenant, subscription, workspace, DBR/Spark, storage account kind and UC
    metastore/workspace ids. Absent fields stay absent: a missing fact is not
    a '' that would collide with other environments.
    """
    case = report.get("case_meta") or {}
    compute = dict(case.get("compute") or {})
    facts = report.get("facts") or []
    env: dict[str, Any] = {}
    if compute.get("workspace_id"):
        env["workspace"] = str(compute["workspace_id"])
    for key in ("dbr_version", "databricks_runtime", "runtime_version"):
        if compute.get(key):
            env["dbr"] = str(compute[key])
            break
    if compute.get("spark_version"):
        env["spark"] = str(compute["spark_version"])
    if compute.get("tenant_id"):
        env["tenant"] = str(compute["tenant_id"])
    sub = _subscription(report.get("facts")) or _subscription(case) or _subscription(
        report.get("access_graph"))
    if sub:
        env["subscription"] = sub
    for f in facts:
        attrs = dict(f.get("attrs") or {}) if isinstance(f, dict) else {}
        kind = f.get("kind", "") if isinstance(f, dict) else ""
        if kind == "adls.account":
            for key in ("kind", "sku", "hns"):
                if attrs.get(key):
                    env[f"storage_{key}"] = str(attrs[key])
        if kind == "unity_catalog.catalog" and attrs.get("metastore_id"):
            env.setdefault("uc_metastore", str(attrs["metastore_id"]))
        if kind == "databricks.compute":
            if attrs.get("workspace_url"):
                env.setdefault("workspace_url_host",
                               str(attrs["workspace_url"]).split("/")[2]
                               if "//" in str(attrs["workspace_url"])
                               else str(attrs["workspace_url"]))
            if not env.get("dbr"):
                for key in ("dbr_version", "databricks_runtime", "runtime_version"):
                    if attrs.get(key):
                        env["dbr"] = str(attrs[key])
                        break
            if not env.get("spark") and attrs.get("spark_version"):
                env["spark"] = str(attrs["spark_version"])
    return env


def _problem_text(report: Mapping[str, Any]) -> str:
    case = report.get("case_meta") or {}
    target = case.get("target") or {}
    return (
        f"access:{case.get('operation', '?')}:"
        f"{target.get('kind', '?')}:{target.get('url', target.get('table', '?'))} "
        f"-> {report.get('status', '?')}@{report.get('failure_layer') or 'none'}"
    )


def record_access_case(report: Mapping[str, Any], root: Path | str) -> dict[str, Any]:
    """Persist a diagnosed access case; evidence ids become the record's
    ``decision_evidence`` so unverifiable memory stays quarantined (#114)."""
    env = env_fingerprint(report)
    case = report.get("case_meta") or {}
    evidence: list[str] = []
    for entry in (report.get("evidence_paths") or {}).values():
        if isinstance(entry, Mapping):
            evidence.extend(str(e) for e in entry.get("facts") or ())
    findings = report.get("findings") or []
    decision = ",".join(sorted({f.get("rule_id", "") for f in findings})) or str(
        report.get("failure_layer") or report.get("status"))
    compute = dict(case.get("compute") or {})
    record = DecisionMemoryRecord(
        id=f"acc_{_fingerprint({'p': _problem_text(report), 'e': env, 'd': decision})}",
        case_id=str(case.get("name", "")),
        problem=_problem_text(report),
        problem_fingerprint=_fingerprint(_problem_text(report)),
        environment_fingerprint=_fingerprint(env) if env else "",
        workload_type="azure_databricks_uc_adls_access",
        runtime={
            "dbr": str(compute.get("dbr_version",
                                   compute.get("databricks_runtime", ""))),
            "spark": str(compute.get("spark_version", "")),
            "azure": "databricks+uc+adls",
        },
        spark_version=str(compute.get("spark_version", "")),
        decision=decision,
        decision_evidence=tuple(sorted(set(evidence))),
        outcome=str(report.get("status", "")),
        outcome_evidence=tuple(sorted({
            str(f.get("rule_id")) for f in findings if f.get("rule_id")})),
        confidence="high" if report.get("status") in {"denied", "pass"} else "low",
        created_at=_now(),
        tags=("access", "unity-catalog", "adls"),
    )
    candidate = classify_memory_candidate(record)
    path = persist_memory_candidate(candidate, root)
    return {"recorded": path.as_posix(), "memory": candidate.to_dict(),
            "environment_fingerprint": env}


def retrieve_access_memory(problem: str, env: Mapping[str, Any] | None,
                           root: Path | str) -> dict[str, Any]:
    """Retrieve prior access cases; wrong-environment records are named, never
    silently reused (#118)."""
    fp = _fingerprint(dict(env)) if env else ""
    records = retrieve_memory(
        problem, root, environment_fingerprint=fp,
        workload_type="azure_databricks_uc_adls_access")
    for item in records:
        env_score = float((item.get("retrieval") or {}).get("environment") or 0.0)
        item["wrong_environment"] = bool(fp) and env_score == 0.0
        item["auto_reusable"] = not item["wrong_environment"]
    return {"problem": problem, "environment_fingerprint": dict(env or {}),
            "candidates": records,
            "reusable": sum(1 for r in records if not r["wrong_environment"])}


__all__ = ["env_fingerprint", "record_access_case", "retrieve_access_memory"]
