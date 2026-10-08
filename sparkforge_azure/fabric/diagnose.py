"""Fabric access/operation diagnosis — deterministic chain evaluation.

Chain order mirrors the operational authority chain researched against
current MS Learn (SDDs ONELAKE_SECURITY_SHORTCUTS / FABRIC_SPARK /
FABRIC_CAPACITY)::

    fabric_workspace → item_permission → onelake_security
      → shortcut → shortcut_auth → source_access
      → lakehouse → spark_runtime → spark_job
      → capacity → data_factory → cross_environment

Each stage emits a ``StageVerdict`` (ALLOW / DENY / UNKNOWN /
NOT_EVALUATED).  ``UNKNOWN`` never means ALLOW: the failure layer is the
first DENY, or ``unresolved`` when the chain cannot be completed.  Missing
evidence is recorded as an unresolved entry naming the artifact that would
close it — never silently converted into a verdict.

Shortcut semantics (current docs):
  * ``passthrough`` — caller identity authorized at the target; only
    same-tenant OneLake→OneLake may default to it.
  * ``delegated`` — a configured connection or workspace identity carries
    authorization to the target; required for cross-tenant and external.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sparkforge_azure.azure.governance.model import Verdict
from sparkforge_azure.fabric.model import (
    DATA_PLANE_BYPASS_ROLES,
    SHORTCUT_AUTH_DELEGATED,
    SHORTCUT_AUTH_PASSTHROUGH,
)
from sparkforge_azure.findings.models import Finding


@dataclass
class StageVerdict:
    layer: str
    verdict: Verdict
    identity: str
    reason: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"layer": self.layer, "verdict": self.verdict.value,
                "identity": self.identity, "reason": self.reason,
                "evidence": self.evidence}


@dataclass
class FabricDiagnosis:
    status: str                     # allowed | denied | unresolved
    failure_layer: str | None
    chain: list[StageVerdict]
    findings: list[Finding]
    conflicts: list[str]
    scenario: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "failure_layer": self.failure_layer,
                "chain": [s.to_dict() for s in self.chain],
                "findings": [f.to_dict() for f in self.findings],
                "conflicts": self.conflicts, "scenario": self.scenario}


def _facts_by_kind(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def _principal_role(facts: list[Any], workspace_id: str,
                    principal: str) -> tuple[str | None, list[str]]:
    """Workspace role of ``principal``; returns (role, evidence fact ids)."""
    ev: list[str] = []
    for f in _facts_by_kind(facts, "fabric.workspace_role"):
        ev.append(f.id)
        if (str(f.subject.get("workspace_id")) == workspace_id
                and str(f.subject.get("principal")) == principal):
            return str(f.attrs.get("role") or ""), [f.id]
    return None, ev


def _workspace_identity(facts: list[Any],
                        workspace_id: str) -> tuple[str | None, list[str]]:
    for f in _facts_by_kind(facts, "fabric.workspace_identity"):
        if str(f.subject.get("workspace_id")) == workspace_id:
            return str(f.subject.get("principal_id") or ""), [f.id]
    return None, []


def _workspace_has_identity(facts: list[Any]) -> bool:
    return bool(_facts_by_kind(facts, "fabric.workspace"))


def _target_item(facts: list[Any], target: Mapping[str, Any]) -> tuple[
        str | None, str | None]:
    """(item_id, item_type) the case targets."""
    if target.get("item_id"):
        iid = str(target["item_id"])
        for f in _facts_by_kind(facts, "fabric.item"):
            if str(f.subject.get("item_id")) == iid:
                return iid, str(f.subject.get("type") or "")
        return iid, None
    if target.get("lakehouse_id"):
        return str(target["lakehouse_id"]), "Lakehouse"
    return None, None


def _scope_covers(scopes: list[Any], table: str | None,
                  path: str | None) -> bool:
    """Grant-model scope check: no scopes = item-wide grant; else at least
    one scope must cover the requested table/folder (prefix containment)."""
    if not scopes:
        return True
    for scope in scopes:
        if not isinstance(scope, Mapping):
            continue
        st = str(scope.get("type", ""))
        spath = str(scope.get("path", "")).rstrip("/")
        if st == "table" and table and (
                scope.get("table") == table or
                (spath and str(scope.get("table", "")).endswith(table))):
            return True
        if st in {"folder", "files"} and path and (
                path == spath or path.startswith(spath + "/")):
            return True
        if st == "item":
            return True
    return False


def _rls_cls_blocks(role: Mapping[str, Any], op: str) -> str | None:
    """Row/column filters on a role: RLS restricts, CLS blocks columns.

    Both are engine-aware — we return the restriction label so the finding
    can say *where* filtering applies, never claim filtering happened.
    """
    if role.get("row_filter"):
        return "rls_restricts_rows"
    if role.get("column_filter") and op == "read":
        return "cls_restricts_columns"
    return None


def evaluate_workspace(facts: list[Any], case: Mapping[str, Any],
                       workspace_id: str) -> StageVerdict:
    principal = str(case.get("principal", {}).get("id", ""))
    ptype = str(case.get("principal", {}).get("type", ""))
    if not _workspace_has_identity(facts):
        return StageVerdict("fabric_workspace", Verdict.UNKNOWN, principal,
                            "workspace artifact absent")
    if ptype == "workspace_identity":
        ws_id, ev = _workspace_identity(facts, workspace_id)
        if ws_id and ws_id == principal:
            return StageVerdict("fabric_workspace", Verdict.ALLOW, principal,
                                "workspace identity attached to workspace", ev)
        return StageVerdict("fabric_workspace", Verdict.DENY, principal,
                            "workspace identity not attached to this workspace",
                            ev)
    role, ev = _principal_role(facts, workspace_id, principal)
    if role:
        return StageVerdict("fabric_workspace", Verdict.ALLOW, principal,
                            f"workspace role {role}", ev)
    return StageVerdict("fabric_workspace", Verdict.DENY, principal,
                        "principal absent from workspace roles", ev)


def evaluate_item(facts: list[Any], case: Mapping[str, Any],
                  workspace_id: str, ws_role: str | None) -> StageVerdict:
    """Item (control-plane) permission.

    Workspace roles carry implicit item access: Admin/Member/Contributor get
    read+write; Viewer gets read.  A Viewer attempting a write is denied at
    this layer — the workspace stage already established presence.
    """
    principal = str(case.get("principal", {}).get("id", ""))
    op = str(case.get("operation", "read"))
    item_id, _itype = _target_item(facts, case.get("target") or {})
    if ws_role in {"Admin", "Member", "Contributor"}:
        return StageVerdict("item_permission", Verdict.ALLOW, principal,
                            f"workspace role {ws_role} grants item access")
    if ws_role == "Viewer":
        if op == "read":
            return StageVerdict("item_permission", Verdict.ALLOW, principal,
                                "workspace Viewer role grants item read")
        return StageVerdict("item_permission", Verdict.DENY, principal,
                            f"Viewer cannot {op} items")
    if item_id is None:
        return StageVerdict("item_permission", Verdict.NOT_APPLICABLE,
                            principal, "no item in target")
    for f in _facts_by_kind(facts, "fabric.item"):
        if str(f.subject.get("item_id")) != item_id:
            continue
        perms = f.attrs.get("permissions") or {}
        granted = perms.get(principal) or []
        if isinstance(granted, str):
            granted = [granted]
        if granted:
            return StageVerdict("item_permission", Verdict.ALLOW, principal,
                                f"item permission {sorted(granted)}", [f.id])
        return StageVerdict("item_permission", Verdict.DENY, principal,
                            "no item permission recorded for principal",
                            [f.id])
    return StageVerdict("item_permission", Verdict.UNKNOWN, principal,
                        f"item {item_id} absent from items artifact")


def evaluate_onelake(facts: list[Any], case: Mapping[str, Any],
                     ws_role: str | None,
                     item_id: str | None) -> tuple[StageVerdict, list[str]]:
    """Data-plane: OneLake security roles.  Grant-only model — absence of a
    grant is a DENY, never an inferred allow."""
    principal = str(case.get("principal", {}).get("id", ""))
    op = str(case.get("operation", "read"))
    target = case.get("target") or {}
    restrictions: list[str] = []
    if str(target.get("kind")) not in {"table", "path"}:
        return (StageVerdict("onelake_security", Verdict.NOT_APPLICABLE,
                             principal, "target is not a data-plane object"),
                restrictions)
    if ws_role in DATA_PLANE_BYPASS_ROLES:
        return (StageVerdict("onelake_security", Verdict.ALLOW, principal,
                             f"workspace role {ws_role} has data-plane access"),
                restrictions)
    roles = [f for f in _facts_by_kind(facts, "onelake.security_role")
             if str(f.subject.get("item_id")) == (item_id or "")]
    if item_id is None:
        return (StageVerdict("onelake_security", Verdict.NOT_APPLICABLE,
                             principal, "no data-plane item in target"),
                restrictions)
    if not roles:
        if _facts_by_kind(facts, "onelake.security_role"):
            return (StageVerdict("onelake_security", Verdict.UNKNOWN, principal,
                                 "no OneLake role observed on target item"),
                    restrictions)
        return (StageVerdict("onelake_security", Verdict.UNKNOWN, principal,
                             "onelake_security artifact absent"), restrictions)
    needed = "Read" if op == "read" else "ReadWrite"
    for f in roles:
        role_name = str(f.subject.get("role"))
        members = [str(m) for m in (f.attrs.get("members") or [])]
        if principal not in members:
            continue
        perms = [str(p) for p in (f.attrs.get("permissions") or [])]
        if needed not in perms and "ReadWrite" not in perms:
            continue
        if _scope_covers(f.attrs.get("scopes") or [],
                         target.get("table"), target.get("path")):
            restr = _rls_cls_blocks(
                {"row_filter": f.attrs.get("row_filter"),
                 "column_filter": f.attrs.get("column_filter")}, op)
            if restr:
                restrictions.append(f"{role_name}:{restr}")
            return (StageVerdict("onelake_security", Verdict.ALLOW, principal,
                                 f"role {role_name} grants {needed}", [f.id]),
                    restrictions)
    return (StageVerdict("onelake_security", Verdict.DENY, principal,
                         "no OneLake role grant covers this operation",
                         [f.id for f in roles]), restrictions)


def evaluate_shortcut(facts: list[Any], case: Mapping[str, Any],
                      item_id: str | None) -> tuple[StageVerdict, Mapping[str, Any] | None]:
    """Does the target path/table traverse a shortcut?"""
    principal = str(case.get("principal", {}).get("id", ""))
    target = case.get("target") or {}
    tpath = str(target.get("path") or "")
    ttable = str(target.get("table") or "")
    candidates = _facts_by_kind(facts, "fabric.shortcut")
    if item_id:
        candidates = [f for f in candidates
                      if str(f.subject.get("lakehouse_id")) == item_id]
    for f in candidates:
        spath = str(f.attrs.get("path", "")).rstrip("/")
        if not spath:
            continue
        hit = (tpath and (tpath == spath or tpath.startswith(spath + "/"))) or \
              (ttable and spath.split("/")[-1] == ttable)
        if hit:
            return StageVerdict("shortcut", Verdict.ALLOW, principal,
                                f"target resolves through shortcut {spath}",
                                [f.id]), f.attrs
    if not candidates:
        return StageVerdict("shortcut", Verdict.NOT_APPLICABLE, principal,
                            "no shortcuts on target item"), None
    return StageVerdict("shortcut", Verdict.NOT_APPLICABLE, principal,
                        "target does not traverse a shortcut"), None


def evaluate_shortcut_auth(facts: list[Any], case: Mapping[str, Any],
                           shortcut: Mapping[str, Any] | None,
                           ws_id: str) -> tuple[StageVerdict, str | None]:
    """Auth chain → effective identity.  Returns (verdict, effective_id)."""
    principal = str(case.get("principal", {}).get("id", ""))
    if shortcut is None:
        return StageVerdict("shortcut_auth", Verdict.NOT_APPLICABLE, principal,
                            "not through a shortcut"), None
    mode = str(shortcut.get("auth_mode", ""))
    if mode == SHORTCUT_AUTH_PASSTHROUGH:
        return StageVerdict("shortcut_auth", Verdict.ALLOW, principal,
                            "passthrough: caller identity authorizes"), principal
    if mode == SHORTCUT_AUTH_DELEGATED:
        cid = str(shortcut.get("connection_id", ""))
        if shortcut.get("workspace_identity"):
            wi, ev = _workspace_identity(facts, ws_id)
            if wi:
                return StageVerdict(
                    "shortcut_auth", Verdict.ALLOW, principal,
                    "delegated via workspace identity", ev), wi
            return StageVerdict("shortcut_auth", Verdict.UNKNOWN, principal,
                                "delegated via workspace identity but none "
                                "observed"), None
        for f in _facts_by_kind(facts, "fabric.connection"):
            if str(f.subject.get("connection_id")) == cid:
                eff = str(f.attrs.get("identity") or f"conn:{cid}")
                return StageVerdict(
                    "shortcut_auth", Verdict.ALLOW, principal,
                    f"delegated via connection {cid}", [f.id]), eff
        return StageVerdict("shortcut_auth", Verdict.UNKNOWN, principal,
                            f"connection {cid or '?'} absent from artifact"), None
    return StageVerdict("shortcut_auth", Verdict.UNKNOWN, principal,
                        f"auth_mode {mode or 'missing'} not observed"), None


def evaluate_source_access(facts: list[Any], case: Mapping[str, Any],
                           shortcut: Mapping[str, Any] | None,
                           effective_id: str | None) -> StageVerdict:
    """Is the effective identity authorized on the shortcut target?

    Passthrough OneLake→OneLake: re-evaluate the *caller* against the target
    workspace/item roles.  Delegated: evidence must show the connection /
    workspace identity reaching the target — absence of evidence is
    UNKNOWN, never DENY-inferred.
    """
    principal = str(case.get("principal", {}).get("id", ""))
    if shortcut is None:
        return StageVerdict("source_access", Verdict.NOT_APPLICABLE, principal,
                            "not through a shortcut")
    if effective_id is None:
        return StageVerdict("source_access", Verdict.UNKNOWN, principal,
                            "effective identity unresolved")
    tgt_ws = str(shortcut.get("target_workspace_id", ""))
    mode = str(shortcut.get("auth_mode", ""))
    if mode == SHORTCUT_AUTH_PASSTHROUGH and tgt_ws:
        role, ev = _principal_role(facts, tgt_ws, effective_id)
        if role:
            return StageVerdict("source_access", Verdict.ALLOW, effective_id,
                                f"caller has role {role} on target workspace",
                                ev)
        return StageVerdict("source_access", Verdict.DENY, effective_id,
                            "caller absent from target workspace roles", ev)
    # Delegated: the connection carries the effective identity; evidence of
    # target authorization is the connection's observed reachability and,
    # for OneLake→OneLake delegated, the identity's role on the target.
    for f in _facts_by_kind(facts, "fabric.connection"):
        cid = str(f.subject.get("connection_id"))
        if effective_id in {f"conn:{cid}", str(f.attrs.get("identity") or "")}:
            ev = [f.id]
            if str(f.attrs.get("last_test", "")) == "failed":
                return StageVerdict("source_access", Verdict.DENY, effective_id,
                                    "connection test failed at target", ev)
            if f.attrs.get("last_test") == "ok" or f.attrs.get("authorized"):
                return StageVerdict("source_access", Verdict.ALLOW,
                                    effective_id,
                                    "connection authorized at target", ev)
            if tgt_ws:
                role, rev = _principal_role(facts, tgt_ws, effective_id)
                ev += rev
                if role:
                    return StageVerdict(
                        "source_access", Verdict.ALLOW, effective_id,
                        f"delegated identity has role {role} on target", ev)
                return StageVerdict(
                    "source_access", Verdict.DENY, effective_id,
                    "delegated identity absent from target workspace", ev)
            return StageVerdict("source_access", Verdict.UNKNOWN, effective_id,
                                "connection exists; target authorization "
                                "not evidenced", ev)
    if not tgt_ws:
        return StageVerdict("source_access", Verdict.UNKNOWN, effective_id,
                            "shortcut target metadata missing")
    return StageVerdict("source_access", Verdict.UNKNOWN, effective_id,
                        "target authorization not evidenced")


def evaluate_lakehouse(facts: list[Any], item_id: str | None,
                       operation: str, principal: str) -> StageVerdict:
    """The lakehouse item must exist for table/path targets to resolve."""
    if item_id is None:
        return StageVerdict("lakehouse", Verdict.NOT_APPLICABLE, principal,
                            "no lakehouse in target")
    for f in _facts_by_kind(facts, "fabric.lakehouse"):
        if str(f.subject.get("item_id")) == item_id:
            return StageVerdict("lakehouse", Verdict.ALLOW, principal,
                                f"lakehouse {item_id} observed", [f.id])
    return StageVerdict("lakehouse", Verdict.UNKNOWN, principal,
                        f"lakehouse {item_id} absent from artifacts")


#: Fabric runtime matrix (current docs, Runtime 2.0 GA / 1.3 EOSA).
RUNTIME_MATRIX = {
    "1.3": {"spark": "3.5", "python": "3.11", "delta": "3.2",
            "status": "eosa_lts"},
    "2.0": {"spark": "4.1", "python": "3.13", "delta": "4.2",
            "status": "ga"},
}


def evaluate_spark(facts: list[Any], case: Mapping[str, Any],
                   principal: str) -> tuple[StageVerdict, StageVerdict]:
    """(spark_runtime, spark_job) — evaluated when the case names a compute
    context (notebook / spark job definition)."""
    job = case.get("job") or {}
    env_id = str(job.get("environment_id", "")
                   or case.get("target", {}).get("environment_id", ""))
    wanted_runtime = str(job.get("runtime") or "")
    runtime_v = StageVerdict("spark_runtime", Verdict.NOT_APPLICABLE, principal,
                             "no compute context in case")
    job_v = StageVerdict("spark_job", Verdict.NOT_APPLICABLE, principal,
                         "no job/notebook in case")
    if not job:
        return runtime_v, job_v
    # Runtime: environment artifact declares the runtime; a requested runtime
    # different from the environment's is a mismatch.
    envs = _facts_by_kind(facts, "fabric.environment")
    env = None
    for f in envs:
        if env_id and str(f.subject.get("item_id")) == env_id:
            env = f
    if env is None and envs and not env_id:
        env = envs[0]
    if env is not None:
        rv = str(env.attrs.get("runtime_version", ""))
        if wanted_runtime and rv and rv != wanted_runtime:
            runtime_v = StageVerdict(
                "spark_runtime", Verdict.DENY, principal,
                f"environment runtime {rv} != job runtime {wanted_runtime}",
                [env.id])
        elif rv:
            runtime_v = StageVerdict(
                "spark_runtime", Verdict.ALLOW, principal,
                f"runtime {rv} observed", [env.id])
        else:
            runtime_v = StageVerdict(
                "spark_runtime", Verdict.UNKNOWN, principal,
                "environment lacks runtime version", [env.id])
    elif job:
        runtime_v = StageVerdict("spark_runtime", Verdict.UNKNOWN, principal,
                                 "environment artifact absent")
    # Job: SparkJobDefinition requires default_lakehouse per current docs.
    default_lh = str(job.get("default_lakehouse_id")
                     or job.get("defaultLakehouseArtifactId") or "")
    if job.get("kind") == "SparkJobDefinition" or job.get("main_file"):
        if not default_lh:
            job_v = StageVerdict(
                "spark_job", Verdict.DENY, principal,
                "SparkJobDefinition without default lakehouse")
        else:
            ok = any(str(f.subject.get("item_id")) == default_lh
                     for f in _facts_by_kind(facts, "fabric.lakehouse"))
            job_v = StageVerdict(
                "spark_job",
                Verdict.ALLOW if ok else Verdict.DENY, principal,
                f"default lakehouse {default_lh} "
                + ("observed" if ok else "absent from artifacts"))
    elif job:
        job_v = StageVerdict("spark_job", Verdict.ALLOW, principal,
                             "notebook/job context observed")
    return runtime_v, job_v


def evaluate_capacity(facts: list[Any], workspace_id: str,
                      principal: str) -> StageVerdict:
    """Capacity state: throttling is ONLY claimed on explicit evidence —
    a ``CapacityLimitExceeded``/throttling event.  High utilization without
    that evidence is reported as overload, not throttling (AGENTS rule 4/8).
    """
    caps = _facts_by_kind(facts, "fabric.capacity")
    if not caps:
        return StageVerdict("capacity", Verdict.UNKNOWN, principal,
                            "capacity artifact absent")
    cap_ids = {
        str(f.subject.get("capacity_id"))
        for f in _facts_by_kind(facts, "fabric.workspace_capacity")
        if str(f.subject.get("workspace_id")) == workspace_id}
    candidates = [c for c in caps
                  if not cap_ids or str(c.subject.get("capacity_id")) in cap_ids]
    if not candidates:
        return StageVerdict("capacity", Verdict.UNKNOWN, principal,
                            "workspace capacity link not observed")
    for c in candidates:
        cid = str(c.subject.get("capacity_id"))
        for e in _facts_by_kind(facts, "fabric.capacity_event"):
            if str(e.subject.get("capacity_id")) != cid:
                continue
            etype = str(e.subject.get("type"))
            if "CapacityLimitExceeded" in etype or "Throttle" in etype:
                return StageVerdict("capacity", Verdict.DENY, principal,
                                    f"{etype} observed on {cid}",
                                    [c.id, e.id])
        if str(c.attrs.get("state", "")).lower() in {"suspended", "disabled"}:
            return StageVerdict("capacity", Verdict.DENY, principal,
                                f"capacity {cid} {c.attrs['state']}", [c.id])
    ev_ids = [c.id for c in candidates]
    return StageVerdict("capacity", Verdict.ALLOW, principal,
                        "no throttling event observed", ev_ids)


def evaluate_data_factory(facts: list[Any], case: Mapping[str, Any],
                          workspace_id: str, principal: str) -> StageVerdict:
    """Pipeline context seam (P1): activities referencing notebooks in a
    different workspace than the pipeline are flagged cross-environment."""
    pipes = _facts_by_kind(facts, "fabric.pipeline")
    if not pipes:
        return StageVerdict("data_factory", Verdict.NOT_APPLICABLE, principal,
                            "no pipeline in bundle")
    ev: list[str] = []
    for act in _facts_by_kind(facts, "fabric.pipeline_activity"):
        ev.append(act.id)
        ref_ws = str(act.attrs.get("reference_workspace_id", ""))
        if ref_ws and ref_ws != workspace_id:
            return StageVerdict(
                "data_factory", Verdict.DENY, principal,
                f"activity {act.subject.get('name')} references workspace "
                f"{ref_ws} != pipeline workspace {workspace_id}", ev)
    return StageVerdict("data_factory", Verdict.ALLOW, principal,
                        "pipeline activities consistent with workspace", ev)


def diagnose_fabric(case: Mapping[str, Any],
                    facts: list[Any]) -> FabricDiagnosis:
    """Evaluate the Fabric authority chain for a case."""
    principal = str(case.get("principal", {}).get("id", ""))
    target = case.get("target") or {}
    workspace_id = str(target.get("workspace_id")
                       or case.get("workspace_id") or "")
    chain: list[StageVerdict] = []
    findings: list[Finding] = []
    conflicts: list[str] = []

    ws = evaluate_workspace(facts, case, workspace_id)
    chain.append(ws)
    role = None
    if ws.verdict is Verdict.ALLOW:
        for f in _facts_by_kind(facts, "fabric.workspace_role"):
            if (str(f.subject.get("workspace_id")) == workspace_id
                    and str(f.subject.get("principal")) == principal):
                role = str(f.attrs.get("role") or "")
        if str(case.get("principal", {}).get("type")) == "workspace_identity":
            role = "Member"  # attached identity operates with member-level perms
    item_id, _itype = _target_item(facts, target)
    item = (evaluate_item(facts, case, workspace_id, role)
            if ws.verdict is Verdict.ALLOW else
            StageVerdict("item_permission", Verdict.NOT_APPLICABLE, principal,
                         "workspace stage not allowed"))
    chain.append(item)
    ol, restrictions = (evaluate_onelake(facts, case, role, item_id)
                        if item.verdict in {Verdict.ALLOW, Verdict.NOT_APPLICABLE}
                        else (StageVerdict("onelake_security",
                                           Verdict.NOT_APPLICABLE, principal,
                                           "item stage denied"), []))
    chain.append(ol)
    sc_v, sc_attrs = evaluate_shortcut(facts, case, item_id)
    chain.append(sc_v)
    sa_v, eff = evaluate_shortcut_auth(facts, case, sc_attrs, workspace_id)
    chain.append(sa_v)
    chain.append(evaluate_source_access(facts, case, sc_attrs, eff))
    data_target = str(target.get("kind")) in {"table", "path"}
    lh = (evaluate_lakehouse(facts, item_id,
                             str(case.get("operation", "read")), principal)
          if data_target else
          StageVerdict("lakehouse", Verdict.NOT_APPLICABLE, principal,
                       "target is not a lakehouse data object"))
    chain.append(lh)
    rt, job = evaluate_spark(facts, case, principal)
    chain.extend([rt, job])
    chain.append(evaluate_capacity(facts, workspace_id, principal))
    chain.append(evaluate_data_factory(facts, case, workspace_id, principal))

    # Control-plane allow + data-plane deny is the signature split; record it
    # as a named conflict rather than hiding it in the chain.
    if (item.verdict is Verdict.ALLOW and ol.verdict is Verdict.DENY):
        conflicts.append("item_access_exists_onelake_denies")

    denied = next((s for s in chain if s.verdict is Verdict.DENY), None)
    unknown = [s for s in chain if s.verdict is Verdict.UNKNOWN]
    if denied:
        status = "denied"
        failure_layer = denied.layer
    elif unknown:
        status = "unresolved"
        failure_layer = "unresolved"
    else:
        status = "allowed"
        failure_layer = None
    return FabricDiagnosis(status=status, failure_layer=failure_layer,
                           chain=chain, findings=findings,
                           conflicts=conflicts,
                           scenario=str(case.get("name", "")))


__all__ = ["FabricDiagnosis", "RUNTIME_MATRIX", "StageVerdict",
           "diagnose_fabric"]
