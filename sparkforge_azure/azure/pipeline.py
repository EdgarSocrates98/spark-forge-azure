"""Access diagnostic pipeline (offline by default).

    bundle -> casefile -> extractors -> facts -> governance.diagnose
        -> failure_layer -> findings -> trust scan -> receipt -> report

The pipeline never calls Azure.  Live collection is a separate opt-in step
(collectors) that writes the same artifact files a bundle carries.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.trust import TrustEnvelope
from sparkforge_azure.azure import casefile, extract, receipt
from sparkforge_azure.azure.governance.diagnose import diagnose
from sparkforge_azure.azure.governance.model import Verdict, parse_abfss
from sparkforge_azure.facts import notebook_scan
from sparkforge_azure.findings.models import Finding
from sparkforge_azure.graph import Edge, Graph, Node, Provenance, node_id
from sparkforge_azure.rules.engine import judge
from sparkforge_azure.rules.loader import load_catalog

PUBLIC_LAYERS = (
    "entra", "workspace_binding", "unity_catalog", "external_location",
    "storage_credential", "network", "azure_rbac", "adls_acl",
    "runtime", "delta_perf", "governance_bypass", "unresolved",
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


def _failure_layer(bundle: casefile.CaseBundle, diagnosis: Any,
                   extra: list[Finding]) -> str | None:
    """Map the diagnosis to the public failure-layer vocabulary (AC4)."""
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


def _evidence_paths(bundle: casefile.CaseBundle, diagnosis: Any,
                    facts: list[Any], extra: list[Finding]) -> dict[str, Any]:
    """finding -> facts -> (layer, bundle file, notebook line)."""
    fact_by_id = {f.id: f for f in facts}
    paths: dict[str, Any] = {}
    for finding in [*diagnosis.findings, *extra]:
        layers = sorted({r.layer for r in diagnosis.chain})
        files = sorted({bundle.sources[_LAYER_SOURCE[layer]]
                        for layer in layers
                        if _LAYER_SOURCE.get(layer) in bundle.sources})
        notebook_refs = sorted({
            f"{f.subject.get('file')}:{f.subject.get('line')}"
            for fid in finding.evidence
            if (f := fact_by_id.get(fid)) is not None and "file" in f.subject
        })
        paths[finding.rule_id] = {
            "facts": list(finding.evidence),
            "layers": layers,
            "files": files,
            "notebook_refs": notebook_refs,
        }
    return paths


def _access_graph(bundle: casefile.CaseBundle, diagnosis: Any,
                  facts: list[Any], findings: list[Finding]) -> dict[str, Any]:
    """Minimal access graph: principal -> layers -> target, findings -> facts.

    P0-C (GRAPHFY_ACCESS) expands this into the full federated access graph;
    here the graph exists so every finding already carries a structural
    evidence path instead of a bare list of ids.
    """
    prov = Provenance("artifact", ",".join(sorted(bundle.sources.values())))
    graph = Graph()
    principal = str(bundle.case["principal"]["id"])
    p_node = node_id("azure", "identity", principal)
    graph.add_node(Node(p_node, "identity", "azure",
                        attrs={"principal_type": bundle.case["principal"].get("type")},
                        provenance=prov))
    target = bundle.case["target"]
    if target.get("kind") == "table":
        t_node = node_id("data", "table", str(target["table"]))
        graph.add_node(Node(t_node, "table", "data", provenance=prov))
    else:
        account, container, path = parse_abfss(str(target.get("url", "")))
        t_node = node_id("azure", "filesystem", f"{account}/{container}{path}")
        graph.add_node(Node(t_node, "filesystem", "azure",
                            attrs={"account": account, "container": container},
                            provenance=prov))
    graph.add_edge(Edge(p_node, "accesses", t_node,
                        attrs={"operation": bundle.case["operation"]},
                        provenance=prov))
    fact_by_id = {f.id: f for f in facts}
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
                continue
            key = (f.subject.get("file") or f.subject.get("name")
                   or f.subject.get("securable") or f.id)
            src = node_id("evidence", "fact", f"{f.kind}:{key}")
            graph.add_node(Node(src, "fact", "evidence",
                                attrs={"kind": f.kind}, provenance=prov))
            graph.add_edge(Edge(n, "evidenced_by", src, provenance=prov))
    return graph.to_dict()


def _trust_scan(facts: list[Any]) -> dict[str, Any]:
    """Wrap all extracted metadata as data; injection-shaped text -> suspicious."""
    payload = json.dumps([f.attrs for f in facts], sort_keys=True, default=str)
    env = TrustEnvelope.external(payload or "{}", origin="access.bundle")
    d = env.to_dict()
    d.pop("content", None)
    return {"trust": d["trust"], "instruction_authority": d["instruction_authority"],
            "taint": d["taint"]}


def _access_rules() -> list[dict[str, Any]]:
    return [r for r in load_catalog() if str(r.get("id", "")).startswith("SF-ACC")]


def run_case(root: str | Path, *, profile: str = "balanced") -> dict[str, Any]:
    """Run the full offline pipeline on a case bundle directory."""
    bundle = casefile.load_bundle(root)
    facts = list(extract.extract_all(bundle.artifacts, bundle.sources))
    merged_compute = dict(bundle.case.get("compute") or {})
    merged_compute.update(bundle.artifacts.get("compute") or {})
    if merged_compute:
        facts += extract.extract_compute(
            merged_compute, {"source": bundle.sources["case"], "mode": "bundle",
                             "observed_at": None})
    facts += notebook_scan.scan_paths(bundle.notebook_files, base=bundle.root)
    facts += notebook_scan.skipped_facts(bundle.skipped)
    facts = sorted({f.id: f for f in facts}.values(), key=lambda f: (f.kind, f.id))
    try:
        diagnosis = diagnose(bundle.to_scenario())
    except Exception as exc:
        raise casefile.CaseError(f"invalid scenario: {exc}") from exc

    extra = [f for f in (_runtime_finding(bundle, facts),
                         _delta_finding(bundle, facts, diagnosis.status),
                         _bypass_finding(bundle, facts, diagnosis.status))
             if f is not None]
    rule_findings, skipped = judge(
        facts, _access_rules(), runtime={}, return_skipped=True)
    layer = _failure_layer(bundle, diagnosis, extra)

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

    return {
        "status": status,
        "case": diagnosis.scenario,
        "failure_layer": layer,
        "diagnosis": diagnosis.to_dict(),
        "findings": [f.to_dict() for f in findings],
        "rules_skipped": skipped,
        "unresolved": unresolved,
        "facts": [f.to_dict() for f in facts],
        "access_graph": _access_graph(bundle, diagnosis, facts, findings),
        "evidence_paths": _evidence_paths(bundle, diagnosis, facts, extra),
        "trust": _trust_scan(facts),
        "receipt": receipt.build(
            case=diagnosis.scenario, profile=profile,
            tools=["casefile", "extract", "notebook_scan", "governance.diagnose"],
            sources=bundle.sources, facts=len(facts),
            rules=len(findings), findings=len(findings),
            unresolved=unresolved,
        ).to_dict(),
    }


__all__ = ["PUBLIC_LAYERS", "run_case"]
