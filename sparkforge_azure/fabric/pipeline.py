"""Fabric diagnostic pipeline (offline by default).

    bundle -> casefile -> extractors -> facts -> fabric.diagnose
        -> failure_layer -> findings -> trust scan -> receipt -> report

Same contract as ``azure.pipeline.run_case``: never calls Azure, live
collection is a separate opt-in step that writes the same artifact files.
AgentOps spans are ``fabric.<stage>`` (prompt #359-364).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.trust import TrustEnvelope
from sparkforge_azure.azure import receipt
from sparkforge_azure.azure.governance.model import Verdict
from sparkforge_azure.fabric import casefile, diagnose, extract
from sparkforge_azure.fabric.casefile import LAYER_SOURCE
from sparkforge_azure.fabric.fingerprint import fabric_fingerprint
from sparkforge_azure.facts import notebook_scan, pyspark_ast
from sparkforge_azure.findings.models import Finding
from sparkforge_azure.graph import Edge, Graph, Node, Provenance, node_id
from sparkforge_azure.graph.evidence import evidence_paths as graph_evidence_paths
from sparkforge_azure.graph.fabric import build_fabric_graph
from sparkforge_azure.knowledgebase.vertical import compile_access_knowledge
from sparkforge_azure.observability.context_ledger import shared_ledger
from sparkforge_azure.rules.engine import judge
from sparkforge_azure.rules.loader import load_catalog

PUBLIC_LAYERS = (
    "fabric_workspace", "item_permission", "onelake_security", "lakehouse",
    "shortcut", "shortcut_auth", "source_access", "spark_runtime",
    "spark_job", "capacity", "data_factory", "cross_environment",
    "unresolved",
)


def _env_mismatch_finding(facts: list[Any], case_name: str) -> Finding | None:
    """SF-FAB-013: environment-scope disagreement across artifacts."""
    by_key: dict[str, dict[str, set[str]]] = {}
    for f in facts:
        if f.kind != "environment.scope":
            continue
        key = str(f.attrs.get("key"))
        value = str(f.attrs.get("value"))
        src = str(f.subject.get("source", "?"))
        by_key.setdefault(key, {}).setdefault(value, set()).add(src)
    # capacity_id/workspace_id legitimately differ across artifacts — the
    # conflict is per-key *contradiction within the same axis* only.
    conflicts = {k: v for k, v in by_key.items()
                 if len(v) > 1 and k in {"tenant_id", "subscription_id"}}
    if not conflicts:
        return None
    evidence = [f.id for f in facts if f.kind == "environment.scope"
                and str(f.attrs.get("key")) in conflicts]
    detail = {k: sorted(v) for k, v in conflicts.items()}
    return Finding(
        rule_id="SF-FAB-013",
        title="Environment mismatch across evidence sources",
        severity="P0", confidence="high", status="confirmed",
        subject={"case": case_name, "layer": "cross_environment"},
        evidence=evidence,
        measured={"conflicting_keys": detail},
        explanation="Artifacts disagree on environment identity "
                    f"{detail}; evidence from different tenants/subscriptions "
                    "cannot be merged into one authority story.",
        proposed_change=["Re-collect every artifact against the same tenant "
                         "and workspace, then re-diagnose."],
        risks=["Findings may mix evidence from different environments."],
    )


def _capacity_overload_finding(facts: list[Any],
                               case_name: str) -> Finding | None:
    """SF-FAB-002: utilization high WITHOUT throttling evidence — report the
    overload honestly, never call it throttling (AGENTS rule 4)."""
    if not _facts(facts, "fabric.capacity"):
        return None
    if _facts(facts, "fabric.capacity_event"):
        return None  # explicit events are handled by the capacity verdict
    evidence = []
    util = None
    for f in _facts(facts, "fabric.capacity"):
        evidence.append(f.id)
        m = f.attrs.get("metric_utilization_percent")
        if isinstance(m, (int, float)):
            util = m
    if util is None or util < 100:
        return None
    return Finding(
        rule_id="SF-FAB-002",
        title="Capacity overloaded without observed throttling",
        severity="P2", confidence="medium", status="confirmed",
        subject={"case": case_name, "layer": "capacity"},
        evidence=evidence,
        measured={"utilization_percent": util},
        explanation=f"Capacity utilization {util}% is above 100% but no "
                    "throttling event (CapacityLimitExceeded / 429 "
                    "capacity-limit) was observed — bursting/smoothing may be "
                    "absorbing it. High utilization is not throttling evidence.",
        proposed_change=["Pull capacity metrics/events (CapacityLimitExceeded) "
                         "to confirm whether throttling actually occurred."],
        risks=["Sustained overload converts to throttling once smoothing "
               "limits are exceeded."],
    )


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def _fact_lookup(facts: list[Any], diagnosis: Any) -> dict[str, Any]:
    by_id: dict[str, Any] = {f.id: f for f in facts}
    for f in getattr(diagnosis, "facts", None) or []:
        fid = f["id"] if isinstance(f, dict) else f.id
        by_id.setdefault(fid, f)
    return by_id


def _fact_fields(f: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if isinstance(f, dict):
        return (dict(f.get("subject") or {}), dict(f.get("attrs") or {}),
                dict(f.get("provenance") or {}))
    return dict(f.subject), dict(f.attrs), dict(f.provenance)


def _evidence_paths(bundle: casefile.CaseBundle, diagnosis: Any,
                    facts: list[Any], extra: list[Finding],
                    graph: Graph | None = None) -> dict[str, Any]:
    fact_by_id = _fact_lookup(facts, diagnosis)
    gpaths = graph_evidence_paths(graph) if graph is not None else {}
    paths: dict[str, Any] = {}
    for finding in [*diagnosis.findings, *extra]:
        layers = sorted({s.layer for s in diagnosis.chain})
        files = sorted({bundle.sources[LAYER_SOURCE[layer]]
                        for layer in layers
                        if LAYER_SOURCE.get(layer) in bundle.sources})
        notebook_refs = sorted({
            f"{subject.get('file')}:{subject.get('line')}"
            for fid in finding.evidence
            if (f := fact_by_id.get(fid)) is not None
            for subject, _a, _p in [_fact_fields(f)]
            if "file" in subject
        })
        entry = {"facts": list(finding.evidence), "layers": layers,
                 "files": files, "notebook_refs": notebook_refs}
        gpath = gpaths.get(node_id("evidence", "finding", finding.rule_id))
        if gpath is not None:
            entry["graph_path"] = gpath
        paths[finding.rule_id] = entry
    return paths


def _overlay_findings(graph: Graph, findings: list[Finding],
                      fact_by_id: dict[str, Any], prov: Provenance) -> None:
    for finding in findings:
        n = node_id("evidence", "finding", finding.rule_id)
        graph.add_node(Node(n, "finding", "evidence",
                            attrs={"severity": finding.severity,
                                   "title": finding.title}, provenance=prov))
        for fid in finding.evidence:
            f = fact_by_id.get(fid)
            if f is None:
                graph.add_unresolved({"reason": "finding_evidence_not_observed",
                                      "finding": finding.rule_id,
                                      "fact_id": fid})
                continue
            subject, _attrs, fprov = _fact_fields(f)
            kind = f.get("kind") if isinstance(f, dict) else f.kind
            key = (subject.get("file") or subject.get("item_id")
                   or subject.get("name") or subject.get("workspace_id")
                   or fid)
            src = node_id("evidence", "fact", f"{kind}:{key}")
            graph.add_node(Node(src, "fact", "evidence",
                                attrs={"kind": kind,
                                       "source": fprov.get("source")},
                                provenance=Provenance(
                                    "artifact",
                                    str(fprov.get("source") or "bundle"),
                                    fprov.get("observed_at"))))
            graph.add_edge(Edge(n, "evidenced_by", src, provenance=prov))


def _trust_scan(bundle: casefile.CaseBundle) -> dict[str, Any]:
    parts: list[str] = [json.dumps(bundle.case, sort_keys=True, default=str),
                        json.dumps(bundle.artifacts, sort_keys=True, default=str)]
    for nb in bundle.notebook_files:
        try:
            parts.append(nb.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    payload = "\n".join(parts) or "{}"
    env = TrustEnvelope.external(payload, origin="fabric.bundle")
    d = env.to_dict()
    d.pop("content", None)
    return {"trust": d["trust"], "instruction_authority": d["instruction_authority"],
            "taint": d["taint"]}


def _fabric_rules() -> list[dict[str, Any]]:
    """SF-FAB (fabric catalog) + SF-PY (domain-neutral Spark rules — the same
    PySpark AST facts that judge Databricks notebooks judge Fabric ones)."""
    return [r for r in load_catalog()
            if str(r.get("id", "")).startswith(("SF-FAB", "SF-PY"))]


def _record_stage(name: str, start: float, resultado: dict[str, Any],
                  stages: dict[str, dict[str, float]] | None = None) -> float:
    shared_ledger().record(
        name=f"fabric.{name}", resultado=resultado, detail_level="stage",
        outcome="ok", start_time=start, channel="diagnose")
    elapsed = round((time.time() - start) * 1000, 3)
    if stages is not None:
        stages[name] = {"ms": elapsed}
    return elapsed


def _context_quality(facts: list[Any], diagnosis: Any, findings: list[Finding],
                     evidence_paths: dict[str, Any]) -> dict[str, Any]:
    by_id = _fact_lookup(facts, diagnosis)
    required: set[str] = set()
    for s in getattr(diagnosis, "chain", ()):
        required.update(getattr(s, "evidence", ()) or ())
    for f in findings:
        required.update(getattr(f, "evidence", ()) or ())
    cited: set[str] = set()
    for entry in evidence_paths.values():
        if isinstance(entry, dict):
            cited.update(entry.get("facts") or ())
    required_present = required & set(by_id)
    consumed = len(json.dumps(
        [f.to_dict() if hasattr(f, "to_dict") else f for f in facts],
        ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))
    return {
        "selected": len(facts),
        "used": len(required_present),
        "cited": len(cited & set(by_id)),
        "consumed_bytes": consumed,
        "required": len(required),
        "required_present": len(required_present),
        "required_recall": (
            round(len(required_present) / len(required), 4) if required else None
        ),
        "required_basis": "diagnosis.chain.evidence + findings.evidence",
    }


def run_fabric_case(root: str | Path, *, profile: str = "balanced") -> dict[str, Any]:
    """Run the full offline Fabric pipeline on a case bundle directory."""
    stage_ms: dict[str, dict[str, float]] = {}
    t = time.time()
    bundle = casefile.load_bundle(root)
    _record_stage("load_case", t, {"case": str(bundle.case.get("name", ""))},
                  stage_ms)
    t = time.time()
    facts = list(extract.extract_all(bundle.artifacts, bundle.sources))
    _record_stage("extract", t, {"facts": len(facts)}, stage_ms)
    t = time.time()
    facts += notebook_scan.scan_paths(bundle.notebook_files, base=bundle.root)
    facts += notebook_scan.skipped_facts(bundle.skipped)
    for nb in bundle.notebook_files:
        if nb.suffix.lower() != ".py":
            continue
        try:
            facts += pyspark_ast.extract_source(
                nb.read_text(encoding="utf-8", errors="replace"),
                str(nb.relative_to(bundle.root)))
        except OSError:
            continue
    facts = sorted({f.id: f for f in facts}.values(), key=lambda f: (f.kind, f.id))
    _record_stage("notebook_scan", t, {"facts": len(facts),
                                       "skipped": len(bundle.skipped)}, stage_ms)
    t = time.time()
    diagnosis = diagnose.diagnose_fabric(bundle.case, facts)
    _record_stage("diagnose", t, {"status": diagnosis.status,
                                  "layers": len(diagnosis.chain)}, stage_ms)
    t = time.time()
    extra = [f for f in (_env_mismatch_finding(facts, bundle.case.get("name", "")),
                         _capacity_overload_finding(facts, bundle.case.get("name", "")))
             if f is not None]
    rule_findings, skipped = judge(
        facts, _fabric_rules(), runtime={}, return_skipped=True)
    _record_stage("rules", t, {"findings": len(rule_findings),
                               "skipped": len(skipped)}, stage_ms)

    layer = diagnosis.failure_layer
    if any(f.rule_id == "SF-FAB-013" for f in extra):
        layer = "cross_environment"

    unresolved = []
    for s in diagnosis.chain:
        if s.verdict is not Verdict.UNKNOWN:
            continue
        entry: dict[str, Any] = {"layer": s.layer, "reason": s.reason}
        artifact = LAYER_SOURCE.get(s.layer)
        if artifact is not None:
            entry["artifact"] = artifact
            entry["artifact_present"] = artifact in bundle.sources
        unresolved.append(entry)
    findings = [*diagnosis.findings, *extra, *rule_findings]
    status = {"allowed": "pass"}.get(diagnosis.status, diagnosis.status)
    if status == "pass" and findings:
        status = "findings"

    t = time.time()
    graph = build_fabric_graph(facts, case=bundle.case, sources=bundle.sources)
    prov = Provenance("artifact", ",".join(sorted(bundle.sources.values())))
    fact_by_id = _fact_lookup(facts, diagnosis)
    _overlay_findings(graph, findings, fact_by_id, prov)
    graph_build_ms = round((time.time() - t) * 1000, 3)
    graph_bytes = len(json.dumps(graph.to_dict()))
    _record_stage("graph", t, {"nodes": len(graph.nodes), "edges": len(graph.edges),
                               "build_ms": graph_build_ms,
                               "serialized_bytes": graph_bytes}, stage_ms)
    t = time.time()
    paths = _evidence_paths(bundle, diagnosis, facts, extra, graph=graph)
    trust = _trust_scan(bundle)
    _record_stage("evidence_trust", t, {"paths": len(paths), "taint": trust["taint"]},
                  stage_ms)
    return {
        "status": status,
        "case": diagnosis.scenario,
        "case_meta": {
            "name": bundle.case.get("name", diagnosis.scenario),
            "principal": dict(bundle.case.get("principal") or {}),
            "operation": bundle.case.get("operation", ""),
            "target": dict(bundle.case.get("target") or {}),
            # environment fingerprint anchors memory reuse to THIS
            # tenant/capacity/workspace — never silently reused elsewhere.
            "environment_fingerprint": fabric_fingerprint(bundle.case, facts),
        },
        "failure_layer": layer,
        "diagnosis": diagnosis.to_dict(),
        "findings": [f.to_dict() for f in findings],
        "rules_skipped": skipped,
        "unresolved": unresolved,
        "facts": [f.to_dict() for f in facts] + list(bundle.upstream_facts),
        "fabric_graph": graph.to_dict(),
        "evidence_paths": paths,
        "knowledge": compile_access_knowledge(
            layer, f"{bundle.case.get('name', '')} {layer or 'fabric'}",
            vertical="fabric"),
        "overhead": {"graph": {"nodes": len(graph.nodes), "edges": len(graph.edges),
                               "build_ms": graph_build_ms,
                               "serialized_bytes": graph_bytes},
                     "stages": stage_ms},
        "context_quality": _context_quality(facts, diagnosis, findings, paths),
        "trust": trust,
        "receipt": receipt.build(
            case=diagnosis.scenario, profile=profile,
            tools=["casefile", "extract", "notebook_scan", "diagnose_fabric"],
            sources=bundle.sources, facts=len(facts),
            rules=len(findings), findings=len(findings),
            unresolved=unresolved,
        ).to_dict(),
    }


__all__ = ["PUBLIC_LAYERS", "run_fabric_case"]
