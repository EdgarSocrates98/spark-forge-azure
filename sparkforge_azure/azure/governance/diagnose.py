"""Multi-layer access diagnosis (sections 29-30): Entra x UC x network x RBAC x ACL.

The chain is evaluated in the order the platform enforces it.  For access that
goes through Unity Catalog the *effective storage identity* is the managed
identity of the storage credential's access connector -- not the end user --
which is exactly why "UC permission exists / storage credential fails" happens.

Outcome:
* ``denied``     -- some layer DENIES; ``root_cause`` is the first denying layer.
* ``unresolved`` -- no layer denies but some layer lacks evidence (UNKNOWN).
* ``allowed``    -- every applicable layer allows.

A missing layer is never assumed to allow (unknown != zero).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sparkforge_azure.azure.governance import layers as L
from sparkforge_azure.azure.governance.model import (
    LayerResult,
    Scenario,
    ScenarioError,
    Verdict,
    parse_abfss,
)
from sparkforge_azure.findings.models import Fact, Finding

CONFLICTS = {
    "rbac_allows_acl_denies": (
        "SFA-GOV-001", "Papel RBAC presente mas sem acesso de dados; ACL do ADLS nega",
    ),
    "identity_valid_network_denies": (
        "SFA-GOV-002", "Identidade e permissões válidas, mas a rede do storage nega",
    ),
    "uc_permission_exists_storage_credential_fails": (
        "SFA-GOV-003", "Privilégio Unity Catalog existe, mas a identidade da storage credential "
                       "não acessa o storage",
    ),
    "workspace_access_exists_catalog_denied": (
        "SFA-GOV-004", "Grants existem, mas o binding de workspace do catálogo nega",
    ),
    "storage_access_exists_external_location_denied": (
        "SFA-GOV-005", "Acesso direto ao storage existe, mas falta privilégio na external location",
    ),
}
ROOT_CAUSE_RULE = ("SFA-GOV-000", "Camada de governança nega o acesso")


@dataclass
class Diagnosis:
    scenario: str
    status: str
    effective_identity: str
    chain: list[LayerResult]
    root_cause: LayerResult | None
    conflicts: list[str]
    facts: list[Fact] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def unresolved(self) -> list[str]:
        return [f"{r.layer}: {r.reason}" for r in self.chain if r.verdict is Verdict.UNKNOWN]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "status": self.status,
            "effective_identity": self.effective_identity,
            "root_cause": self.root_cause.to_dict() if self.root_cause else None,
            "conflicts": self.conflicts,
            "chain": [r.to_dict() for r in self.chain],
            "unresolved": self.unresolved,
            "facts": [f.to_dict() for f in self.facts],
            "findings": [f.to_dict() for f in self.findings],
            "authority": "data_only",
        }


def _groups(sc: Scenario, identity: str) -> list[str]:
    if identity == sc.principal["id"]:
        return [str(g) for g in sc.principal.get("groups") or []]
    info = ((sc.entra or {}).get("principals") or {}).get(identity) or {}
    return [str(g) for g in info.get("groups") or []]


def _storage_layers(sc: Scenario, identity: str, connector: str, url: str) -> list[LayerResult]:
    account_name, container, path = parse_abfss(url)
    account_id = str((sc.adls or {}).get("account_id", "")) or f"storageAccounts/{account_name}"
    scope = L.container_scope(account_id, container)
    groups = _groups(sc, identity)
    out = [L.network_layer(sc.network, sc.compute, connector)]
    rbac, _detail = L.rbac_layer(sc.rbac, identity, groups, scope, sc.operation)
    out.append(rbac)
    if rbac.verdict is Verdict.ALLOW:
        out.append(LayerResult("adls_acl", Verdict.NOT_APPLICABLE,
                               "not evaluated: RBAC data role already grants (ACL cannot restrict)",
                               identity, knowledge_refs=(L.K_ADLS,)))
    else:
        acl = L.acl_layer(sc.adls, identity, groups, path, sc.operation)
        if rbac.verdict is Verdict.UNKNOWN and acl.verdict is Verdict.DENY:
            # RBAC unobserved could still grant: an ACL deny is not conclusive.
            acl = LayerResult("adls_acl", Verdict.UNKNOWN,
                              acl.reason + " -- inconclusive while RBAC is unobserved",
                              identity, knowledge_refs=(L.K_ADLS,))
        out.append(acl)
    return out


def _direct_storage_allows(sc: Scenario) -> bool:
    """Would the END USER reach storage directly (bypassing UC)? Used for conflict C5."""
    url = sc.target.get("url") or sc.target.get("storage_url")
    if not url:
        return False
    res = _storage_layers(sc, str(sc.principal["id"]), "", str(url))
    rb = next(r for r in res if r.layer == "rbac")
    acl = next(r for r in res if r.layer == "adls_acl")
    return rb.verdict is Verdict.ALLOW or acl.verdict is Verdict.ALLOW


def diagnose(raw: Mapping[str, Any] | Scenario) -> Diagnosis:
    sc = raw if isinstance(raw, Scenario) else Scenario.from_dict(raw)
    user = str(sc.principal["id"])
    chain: list[LayerResult] = []
    effective = user
    uc = sc.unity_catalog
    via_uc = uc is not None or sc.target["kind"] in {"table", "volume"}

    if sc.principal.get("enabled") is False:
        chain.append(LayerResult("entra", Verdict.DENY, "principal disabled", user))
    else:
        chain.append(L.entra_layer(sc.entra, user))

    if via_uc:
        uc = uc or {}
        url = str(sc.target.get("url") or sc.target.get("storage_url") or "")
        location = L.covering_location(uc, url) if url else None
        catalog = str(sc.target["table"]).split(".")[0] if sc.target["kind"] == "table" else None
        ws = sc.compute.get("workspace_id")
        chain.append(L.uc_binding_layer(uc, catalog, location if catalog is None else None,
                                        str(ws) if ws else None))
        chain.append(L.uc_privilege_layer(uc, user, _groups(sc, user), sc.target, sc.operation,
                                          location))
        if url:
            mi, connector = L.storage_identity(uc, location)
            if not mi:
                chain.append(LayerResult(
                    "uc_storage_credential",
                    Verdict.DENY if location is not None else Verdict.UNKNOWN,
                    "storage credential / access connector identity not resolvable"
                    if location is not None else "no external location to resolve credential",
                    knowledge_refs=(L.K_UC,)))
            else:
                effective = mi
                chain.append(LayerResult("uc_storage_credential", Verdict.ALLOW,
                                         f"storage reached as access-connector identity {mi}",
                                         mi, knowledge_refs=(L.K_UC,)))
                if sc.entra and mi in (sc.entra.get("principals") or {}):
                    chain.append(L.entra_layer(sc.entra, mi))
                chain.extend(_storage_layers(sc, mi, connector, url))
    else:
        chain.extend(_storage_layers(sc, user, "", str(sc.target["url"])))

    denies = [r for r in chain if r.verdict is Verdict.DENY]
    unknown = [r for r in chain if r.verdict is Verdict.UNKNOWN]
    status = "denied" if denies else ("unresolved" if unknown else "allowed")
    root = denies[0] if denies else None
    conflicts = _conflicts(sc, chain, via_uc)
    diag = Diagnosis(sc.name or "scenario", status, effective, chain, root, conflicts)
    _materialize(diag)
    return diag


def _v(chain: list[LayerResult], layer: str) -> Verdict | None:
    found = [r.verdict for r in chain if r.layer == layer]
    return found[-1] if found else None


def _conflicts(sc: Scenario, chain: list[LayerResult], via_uc: bool) -> list[str]:
    out: list[str] = []
    rbac = next((r for r in reversed(chain) if r.layer == "rbac"), None)
    if (_v(chain, "adls_acl") is Verdict.DENY and rbac is not None
            and "control-plane" in rbac.reason):
        out.append("rbac_allows_acl_denies")
    perms_ok = _v(chain, "rbac") is Verdict.ALLOW or _v(chain, "adls_acl") is Verdict.ALLOW
    if _v(chain, "network") is Verdict.DENY and perms_ok:
        out.append("identity_valid_network_denies")
    if via_uc:
        storage_bad = any(r.verdict is Verdict.DENY for r in chain
                          if r.layer in {"uc_storage_credential", "network", "adls_acl"})
        if _v(chain, "uc_privileges") is Verdict.ALLOW and storage_bad:
            out.append("uc_permission_exists_storage_credential_fails")
        if _v(chain, "uc_binding") is Verdict.DENY and _v(chain, "uc_privileges") is Verdict.ALLOW:
            out.append("workspace_access_exists_catalog_denied")
        if (_v(chain, "uc_privileges") is Verdict.DENY and sc.target["kind"] == "path"
                and _direct_storage_allows(sc)):
            out.append("storage_access_exists_external_location_denied")
    return out


def _materialize(d: Diagnosis) -> None:
    for r in d.chain:
        fact = Fact(
            kind="azure.governance.layer",
            subject={"scenario": d.scenario, "layer": r.layer, "identity": r.identity},
            attrs={"verdict": r.verdict.value, "reason": r.reason},
            provenance={"source": "access_scenario", "extractor": "azure.governance"},
        )
        d.facts.append(fact)
        object.__setattr__(r, "evidence", (fact.id,))
    evidence_all = [f.id for f in d.facts]
    for code in d.conflicts:
        rule_id, title = CONFLICTS[code]
        d.findings.append(_finding(rule_id, title, d, code, evidence_all))
    if d.root_cause is not None and not d.conflicts:
        rule_id, title = ROOT_CAUSE_RULE
        d.findings.append(_finding(rule_id, title, d, "root_cause", list(d.root_cause.evidence)))


def _finding(rule_id: str, title: str, d: Diagnosis, code: str, evidence: list[str]) -> Finding:
    root = d.root_cause
    refs = sorted({k for r in d.chain for k in r.knowledge_refs})
    return Finding(
        rule_id=rule_id,
        title=title,
        severity="P1",
        confidence="high" if not d.unresolved else "medium",
        status="confirmed" if not d.unresolved else "structural",
        subject={"scenario": d.scenario, "conflict": code,
                 "layer": root.layer if root else ""},
        evidence=evidence,
        explanation=(root.reason if root else ""),
        proposed_change=_remedy(code, root),
        validation=["Re-run the scenario after the change; expect status=allowed with the same "
                    "evidence sources."],
        rollback=["Revert the grant/role/network change; no data is modified."],
        sources=[{"knowledge_id": k} for k in refs],
    )


def _remedy(code: str, root: LayerResult | None) -> list[str]:
    layer = root.layer if root else ""
    table = {
        "rbac_allows_acl_denies": "Grant a data-plane role (Storage Blob Data Reader/Contributor) "
                                  "at the right scope, or fix the ACL execute/read bits on the "
                                  "path; control-plane roles never grant data access.",
        "identity_valid_network_denies": "Allow the caller network: private endpoint + linked "
                                         "private DNS zone, firewall subnet/IP rule, or resource "
                                         "instance rule for the access connector.",
        "uc_permission_exists_storage_credential_fails": "Give the access connector managed "
                                                         "identity storage access (e.g. Storage "
                                                         "Blob Data Contributor) and allow it "
                                                         "through the storage network.",
        "workspace_access_exists_catalog_denied": "Bind the workspace to the ISOLATED catalog "
                                                  "or use a bound workspace.",
        "storage_access_exists_external_location_denied": "Grant READ FILES (and WRITE FILES for "
                                                          "writes) on the external location, or "
                                                          "use a governed table.",
    }
    if code in table:
        return [table[code]]
    return [f"Fix the denying layer: {layer}."]


def diagnose_file(path: str) -> Diagnosis:
    import json
    from pathlib import Path

    import yaml

    text = Path(path).read_text(encoding="utf-8")
    raw = json.loads(text) if path.endswith(".json") else yaml.safe_load(text)
    if not isinstance(raw, Mapping):
        raise ScenarioError("scenario file must contain a mapping")
    return diagnose(raw)
