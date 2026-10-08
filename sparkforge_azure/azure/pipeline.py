"""Access diagnostic pipeline (offline by default).

    bundle -> casefile -> extractors -> facts -> governance.diagnose
        -> failure_layer -> findings -> trust scan -> receipt -> report

The pipeline never calls Azure.  Live collection is a separate opt-in step
(collectors) that writes the same artifact files a bundle carries.

Every run records one AgentOps span per stage in the shared ledger
(``diagnose.<stage>``), so a CLI or MCP diagnose is inspectable through
``agentops inspect/timeline/critical-path`` like any other vertical.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.trust import TrustEnvelope
from sparkforge_azure.azure import casefile, extract, receipt
from sparkforge_azure.azure.governance.diagnose import diagnose
from sparkforge_azure.azure.governance.model import Verdict, parse_abfss
from sparkforge_azure.facts import notebook_scan
from sparkforge_azure.findings.models import Finding
from sparkforge_azure.graph import Edge, Graph, Node, Provenance, node_id
from sparkforge_azure.graph.access import build_access_graph
from sparkforge_azure.graph.evidence import evidence_paths as graph_evidence_paths
from sparkforge_azure.knowledgebase.vertical import compile_access_knowledge
from sparkforge_azure.observability.context_ledger import shared_ledger
from sparkforge_azure.rules.engine import judge
from sparkforge_azure.rules.loader import load_catalog

PUBLIC_LAYERS = (
    "entra", "workspace_binding", "unity_catalog", "external_location",
    "storage_credential", "network", "azure_rbac", "adls_acl",
    "runtime", "delta_perf", "governance_bypass", "cross_environment",
    "unresolved",
)

_LAYER_MAP = {
    "entra": "entra",
    "uc_binding": "workspace_binding",
    "uc_storage_credential": "storage_credential",
    "network": "network",
    "rbac": "azure_rbac",
    "adls_acl": "adls_acl",
}

# Conflicts whose name is already the truthful layer.  Absent on purpose:
# uc_permission_exists_storage_credential_fails fires for any storage-layer deny
# (network, rbac/acl, credential) so the root cause stays the honest layer.
_CONFLICT_MAP = {
    "rbac_allows_acl_denies": "azure_rbac",
    "identity_valid_network_denies": "network",
    "workspace_access_exists_catalog_denied": "workspace_binding",
    "storage_access_exists_external_location_denied": "external_location",
}

# Layer -> bundle artifact that feeds it.  Used to build evidence paths.
_LAYER_SOURCE = {
    "entra": "entra", "uc_binding": "unity_catalog",
    "uc_privileges": "unity_catalog", "uc_storage_credential": "unity_catalog",
    "network": "network", "rbac": "rbac", "adls_acl": "adls",
}

# UC is only enforced on clusters whose access mode supports it.
_LEGACY_ACCESS_MODES = frozenset({
    "none", "legacy_table_acl", "legacy_passthrough", "legacy_single_user",
})


def _via_uc(bundle: casefile.CaseBundle) -> bool:
    return (bundle.artifacts.get("unity_catalog") is not None
            or bundle.case["target"].get("kind") in {"table", "volume"})


def _runtime_finding(bundle: casefile.CaseBundle,
                     facts: list[Any]) -> Finding | None:
    """Legacy cluster access mode cannot enforce Unity Catalog (SF-ACC-012)."""
    compute = dict(bundle.case.get("compute") or {})
    compute.update(bundle.artifacts.get("compute") or {})
    mode = str(compute.get("data_security_mode", "")).lower()
    if mode not in _LEGACY_ACCESS_MODES or not _via_uc(bundle):
        return None
    evidence = [f.id for f in facts if f.kind == "databricks.compute"]
    if not evidence:
        return None
    return Finding(
        rule_id="SF-ACC-012",
        title="Cluster access mode cannot enforce Unity Catalog",
        severity="P0", confidence="high", status="confirmed",
        subject={"case": bundle.case.get("name", ""), "layer": "runtime"},
        evidence=evidence,
        measured={"data_security_mode": mode},
        explanation=f"Cluster data_security_mode={mode} predates Unity Catalog "
                    "enforcement; UC privileges are never checked on this compute.",
        proposed_change=["Use a UC-capable access mode: USER_ISOLATION (shared) or "
                         "SINGLE_USER."],
        risks=["Jobs may rely on legacy passthrough semantics."],
    )


def _bypass_finding(bundle: casefile.CaseBundle, facts: list[Any],
                    status: str) -> Finding | None:
    """Direct storage access with no UC layer: the workload bypasses governance."""
    if _via_uc(bundle) or status != "allowed":
        return None
    evidence = [f.id for f in facts if f.kind == "notebook.abfss_path"]
    if not evidence:
        evidence = [f.id for f in facts if f.kind == "azure_rbac.assignment"]
    if not evidence:
        return None
    return Finding(
        rule_id="SF-ACC-010",
        title="Storage access bypasses Unity Catalog governance",
        severity="P1", confidence="high", status="confirmed",
        subject={"case": bundle.case.get("name", ""), "layer": "governance_bypass"},
        evidence=evidence or ["f_missing"],
        explanation="The job reaches ADLS directly; no Unity Catalog artifact governs "
                    "this path, so grants, lineage and audit do not apply.",
        proposed_change=["Register the location as a UC external location and access "
                         "through a UC table or the location privilege."],
        risks=["Direct access keeps working after UC adoption unless RBAC/ACLs are "
               "tightened."],
    )


def _delta_finding(bundle: casefile.CaseBundle, facts: list[Any],
                   status: str) -> Finding | None:
    """abfss path hits the storage location of a governed UC table (SF-ACC-011)."""
    if status != "allowed":
        return None
    url = str(bundle.case.get("target", {}).get("url", "")).rstrip("/")
    if not url:
        return None
    for f in facts:
        if f.kind != "unity_catalog.table":
            continue
        loc = str(f.attrs.get("location", "")).rstrip("/")
        if loc and (url == loc or url.startswith(loc + "/")):
            evidence = [f.id] + [g.id for g in facts
                                 if g.kind in {"notebook.abfss_path",
                                               "notebook.delta_op"}]
            return Finding(
                rule_id="SF-ACC-011",
                title="Direct path read of a UC-managed Delta table",
                severity="P2", confidence="high", status="confirmed",
                subject={"case": bundle.case.get("name", ""), "layer": "delta_perf",
                         "table": f.subject.get("name", "")},
                evidence=evidence,
                explanation="The abfss path targets the storage location of UC table "
                            f"{f.subject.get('name')}; path access skips catalog "
                            "privileges, Delta optimizations ordering and audit.",
                proposed_change=["Access the table by name "
                                 f"({f.subject.get('name')}) instead of the abfss path."],
            )
    return None


def _env_mismatch_finding(facts: list[Any],
                          case_name: str) -> Finding | None:
    """SF-ACC-013: environment-scope disagreement across artifacts (193-195).

    Cross-tenant/subscription/workspace evidence must never be merged into
    one authority story — the mismatch is the finding.
    """
    by_key: dict[str, dict[str, set[str]]] = {}
    for f in facts:
        if f.kind != "environment.scope":
            continue
        key = str(f.attrs.get("key"))
        value = str(f.attrs.get("value"))
        src = str(f.subject.get("source", "?"))
        by_key.setdefault(key, {}).setdefault(value, set()).add(src)
    conflicts = {k: v for k, v in by_key.items() if len(v) > 1}
    if not conflicts:
        return None
    evidence = [f.id for f in facts if f.kind == "environment.scope"
                and str(f.attrs.get("key")) in conflicts]
    detail = {k: sorted(v) for k, v in conflicts.items()}
    return Finding(
        rule_id="SF-ACC-013",
        title="Environment mismatch across evidence sources",
        severity="P0", confidence="high", status="confirmed",
        subject={"case": case_name, "layer": "cross_environment"},
        evidence=evidence,
        measured={"conflicting_keys": detail},
        explanation="Artifacts disagree on environment identity "
                    f"{detail}; a metastore/catalog match across tenants or "
                    "workspaces is not the same authority. The bundle cannot "
                    "be trusted as one environment.",
        proposed_change=["Re-collect every artifact against the same tenant, "
                         "subscription and workspace, then re-diagnose."],
        risks=["Findings below this one may mix evidence from different "
               "environments."],
    )


def _failure_layer(bundle: casefile.CaseBundle, diagnosis: Any,
                   extra: list[Finding]) -> str | None:
    """Map the diagnosis to the public failure-layer vocabulary (AC4)."""
    # A cross-environment bundle poisons every layer verdict: report it first.
    if any(f.rule_id == "SF-ACC-013" for f in extra):
        return "cross_environment"
    # A legacy access mode fails before UC evaluation: runtime wins over any
    # layer verdict or conflict the chain produced downstream.
    if any(f.rule_id == "SF-ACC-012" for f in extra):
        return "runtime"
    root = diagnosis.root_cause
    if root is not None:
        for code in diagnosis.conflicts:
            if code in _CONFLICT_MAP:
                # A named conflict tells the truer story than the raw denying
                # layer (e.g. ACL denies *because* no data-plane role exists).
                return _CONFLICT_MAP[code]
        if root.layer == "uc_privileges":
            return ("external_location"
                    if bundle.case["target"].get("kind") == "path" else "unity_catalog")
        return _LAYER_MAP.get(root.layer, root.layer)
    if diagnosis.status == "unresolved":
        return "unresolved"
    for f in extra:
        if f.rule_id == "SF-ACC-011":
            return "delta_perf"
        if f.rule_id == "SF-ACC-010":
            return "governance_bypass"
    return None


def _fact_lookup(facts: list[Any], diagnosis: Any) -> dict[str, Any]:
    """Facts by id: pipeline extractors + the governance engine's own facts."""
    by_id: dict[str, Any] = {f.id: f for f in facts}
    for f in getattr(diagnosis, "facts", None) or []:
        fid = f["id"] if isinstance(f, dict) else f.id
        by_id.setdefault(fid, f)
    return by_id


def _fact_fields(f: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """(subject, attrs, provenance) from a Fact object or its dict form."""
    if isinstance(f, dict):
        return (dict(f.get("subject") or {}), dict(f.get("attrs") or {}),
                dict(f.get("provenance") or {}))
    return dict(f.subject), dict(f.attrs), dict(f.provenance)


def _evidence_paths(bundle: casefile.CaseBundle, diagnosis: Any,
                    facts: list[Any], extra: list[Finding],
                    graph: Graph | None = None) -> dict[str, Any]:
    """finding -> facts -> (layer, bundle file, notebook line).

    When the access graph is built (P0-C), the path is derived from it:
    finding node -> ``evidenced_by`` fact nodes -> provenance sources.
    """
    fact_by_id = _fact_lookup(facts, diagnosis)
    gpaths = graph_evidence_paths(graph) if graph is not None else {}
    paths: dict[str, Any] = {}
    for finding in [*diagnosis.findings, *extra]:
        layers = sorted({r.layer for r in diagnosis.chain})
        files = sorted({bundle.sources[_LAYER_SOURCE[layer]]
                        for layer in layers
                        if _LAYER_SOURCE.get(layer) in bundle.sources})
        notebook_refs = sorted({
            f"{subject.get('file')}:{subject.get('line')}"
            for fid in finding.evidence
            if (f := fact_by_id.get(fid)) is not None
            for subject, _a, _p in [_fact_fields(f)]
            if "file" in subject
        })
        entry = {
            "facts": list(finding.evidence),
            "layers": layers,
            "files": files,
            "notebook_refs": notebook_refs,
        }
        gpath = gpaths.get(node_id("evidence", "finding", finding.rule_id))
        if gpath is not None:
            entry["graph_path"] = gpath
        paths[finding.rule_id] = entry
    return paths


def _access_graph(bundle: casefile.CaseBundle, diagnosis: Any,
                  facts: list[Any], findings: list[Finding]) -> Graph:
    """Full access graph: facts chain + case principal + verdict overlay.

    P0-C: the governed-access chain (job->cluster->notebook->table->location
    ->credential->identity->role) is built by ``graph.access``; this overlay
    adds the diagnosis layer verdicts and finding->fact evidence edges, all
    anchored to the same provenance (the bundle's source files).
    """
    prov = Provenance("artifact", ",".join(sorted(bundle.sources.values())))
    graph = build_access_graph(facts, case=bundle.case)
    principal = str(bundle.case["principal"]["id"])
    p_node = node_id("azure", "identity", principal)
    target = bundle.case["target"]
    if target.get("kind") == "table":
        t_node = node_id("data", "table", str(target["table"]))
    else:
        account, container, path = parse_abfss(str(target.get("url", "")))
        t_node = node_id("azure", "filesystem", f"{account}/{container}{path}")
    fact_by_id = _fact_lookup(facts, diagnosis)
    for r in diagnosis.chain:
        fnode = node_id("evidence", "fact", f"{r.layer}:{r.identity or principal}")
        graph.add_node(Node(fnode, "fact", "evidence",
                            attrs={"layer": r.layer, "verdict": r.verdict.value,
                                   "reason": r.reason}, provenance=prov))
        graph.add_edge(Edge(fnode, f"verdict_{r.verdict.value}", t_node,
                            provenance=prov))
        graph.add_edge(Edge(fnode, "evaluates", p_node, provenance=prov))
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
            key = (subject.get("file") or subject.get("name")
                   or subject.get("securable") or subject.get("layer") or fid)
            src = node_id("evidence", "fact", f"{kind}:{key}")
            graph.add_node(Node(src, "fact", "evidence",
                                attrs={"kind": kind, "source": fprov.get("source")},
                               provenance=Provenance(
                                   "artifact",
                                   str(fprov.get("source") or "bundle"),
                                   fprov.get("observed_at"))))
            graph.add_edge(Edge(n, "evidenced_by", src, provenance=prov))
    return graph


def _trust_scan(bundle: casefile.CaseBundle) -> dict[str, Any]:
    """Scan every raw input at the trust boundary, not only extracted facts.

    Injection-shaped text dropped by extraction is still untrusted input the
    pipeline touched; the envelope covers case + artifacts + notebook bytes.
    """
    parts: list[str] = [json.dumps(bundle.case, sort_keys=True, default=str),
                        json.dumps(bundle.artifacts, sort_keys=True, default=str)]
    for nb in bundle.notebook_files:
        try:
            parts.append(nb.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    payload = "\n".join(parts) or "{}"
    env = TrustEnvelope.external(payload, origin="access.bundle")
    d = env.to_dict()
    d.pop("content", None)
    return {"trust": d["trust"], "instruction_authority": d["instruction_authority"],
            "taint": d["taint"]}


def _access_rules() -> list[dict[str, Any]]:
    return [r for r in load_catalog() if str(r.get("id", "")).startswith("SF-ACC")]


def _record_stage(name: str, start: float, resultado: dict[str, Any]) -> None:
    """One AgentOps span per pipeline stage; record() never touches disk."""
    shared_ledger().record(
        name=f"diagnose.{name}", resultado=resultado, detail_level="stage",
        outcome="ok", start_time=start, channel="diagnose")


def _context_quality(facts: list[Any], diagnosis: Any, findings: list[Finding],
                     evidence_paths: dict[str, Any]) -> dict[str, Any]:
    """selected/used/cited/consumed/required over the decision's evidence.

    `required` is the explicitly required denominator (prompt #111): fact ids
    named by the diagnosis chain verdicts and by finding evidence -- never the
    "everything we happened to select" set. `required_recall` < 1.0 means the
    decision cited evidence the pipeline never produced: an honest gap, not a
    hidden one.
    """
    by_id = _fact_lookup(facts, diagnosis)
    required: set[str] = set()
    for r in getattr(diagnosis, "chain", ()):
        required.update(getattr(r, "evidence", ()) or ())
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


def run_case(root: str | Path, *, profile: str = "balanced") -> dict[str, Any]:
    """Run the full offline pipeline on a case bundle directory."""
    t = time.time()
    bundle = casefile.load_bundle(root)
    _record_stage("load_bundle", t, {"case": str(bundle.case.get("name", ""))})
    t = time.time()
    facts = list(extract.extract_all(bundle.artifacts, bundle.sources))
    merged_compute = dict(bundle.case.get("compute") or {})
    merged_compute.update(bundle.artifacts.get("compute") or {})
    if merged_compute:
        facts += extract.extract_compute(
            merged_compute, {"source": bundle.sources["case"], "mode": "bundle",
                             "observed_at": None})
    _record_stage("extract", t, {"facts": len(facts)})
    t = time.time()
    facts += notebook_scan.scan_paths(bundle.notebook_files, base=bundle.root)
    facts += notebook_scan.skipped_facts(bundle.skipped)
    facts = sorted({f.id: f for f in facts}.values(), key=lambda f: (f.kind, f.id))
    _record_stage("notebook_scan", t, {"facts": len(facts),
                                       "skipped": len(bundle.skipped)})
    t = time.time()
    try:
        diagnosis = diagnose(bundle.to_scenario())
    except Exception as exc:
        raise casefile.CaseError(f"invalid scenario: {exc}") from exc
    _record_stage("diagnose", t, {"status": diagnosis.status,
                                  "layers": len(diagnosis.chain)})

    t = time.time()
    extra = [f for f in (_runtime_finding(bundle, facts),
                         _env_mismatch_finding(facts, bundle.case.get("name", "")),
                         _delta_finding(bundle, facts, diagnosis.status),
                         _bypass_finding(bundle, facts, diagnosis.status))
             if f is not None]
    rule_findings, skipped = judge(
        facts, _access_rules(), runtime={}, return_skipped=True)
    layer = _failure_layer(bundle, diagnosis, extra)
    _record_stage("rules", t, {"findings": len(rule_findings),
                               "skipped": len(skipped)})

    unresolved = [{"layer": r.layer, "reason": r.reason}
                  for r in diagnosis.chain if r.verdict is Verdict.UNKNOWN]
    findings = [*diagnosis.findings, *extra, *rule_findings]
    status = {"allowed": "pass"}.get(diagnosis.status, diagnosis.status)
    if any(f.rule_id == "SF-ACC-012" for f in extra):
        # Legacy access mode denies the access before UC is even consulted.
        status = "denied"
    elif status == "pass" and findings:
        # allowed-but-flagged still exits 1 (findings are blockers by contract)
        status = "findings"

    t = time.time()
    graph = _access_graph(bundle, diagnosis, facts, findings)
    graph_build_ms = round((time.time() - t) * 1000, 3)
    graph_bytes = len(json.dumps(graph.to_dict()))
    _record_stage("graph", t, {"nodes": len(graph.nodes), "edges": len(graph.edges),
                               "build_ms": graph_build_ms,
                               "serialized_bytes": graph_bytes})
    t = time.time()
    paths = _evidence_paths(bundle, diagnosis, facts, extra, graph=graph)
    trust = _trust_scan(bundle)
    _record_stage("evidence_trust", t, {"paths": len(paths), "taint": trust["taint"]})
    return {
        "status": status,
        "case": diagnosis.scenario,
        "case_meta": {
            "name": bundle.case.get("name", diagnosis.scenario),
            "principal": dict(bundle.case.get("principal") or {}),
            "operation": bundle.case.get("operation", ""),
            "target": dict(bundle.case.get("target") or {}),
            "compute": merged_compute,
        },
        "failure_layer": layer,
        "diagnosis": diagnosis.to_dict(),
        "findings": [f.to_dict() for f in findings],
        "rules_skipped": skipped,
        "unresolved": unresolved,
        "facts": [f.to_dict() for f in facts],
        "access_graph": graph.to_dict(),
        "evidence_paths": paths,
        "knowledge": compile_access_knowledge(
            layer, f"{bundle.case.get('name', '')} {layer or 'access'}"),
        "overhead": {"graph": {"nodes": len(graph.nodes), "edges": len(graph.edges),
                               "build_ms": graph_build_ms,
                               "serialized_bytes": graph_bytes}},
        "context_quality": _context_quality(facts, diagnosis, findings, paths),
        "trust": trust,
        "receipt": receipt.build(
            case=diagnosis.scenario, profile=profile,
            tools=["casefile", "extract", "notebook_scan", "governance.diagnose"],
            sources=bundle.sources, facts=len(facts),
            rules=len(findings), findings=len(findings),
            unresolved=unresolved,
        ).to_dict(),
    }


__all__ = ["PUBLIC_LAYERS", "run_case"]
