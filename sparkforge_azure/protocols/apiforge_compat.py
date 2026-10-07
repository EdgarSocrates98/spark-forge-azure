"""Deterministic translation of Forge Protocol envelopes to the API Forge wire shape.

Spark Forge AWS and API Forge publish *different* Forge Protocol shapes
(docs/architecture/SHARED-PRIMITIVES.md).  This repository keeps the AWS
sibling shape as canonical (``protocols.forge``, ported COPY_SAFE) and offers
this one-way projection so The Forger / API Forge can consume Azure envelopes
without either Forge changing its contract (sections 187, 191).

Rules:
* pure functions, no I/O, no pydantic dependency (API Forge validates its side);
* nothing is invented: fields API Forge requires that the canonical shape lacks
  are filled from explicit arguments or left as API Forge defaults;
* ``authority`` stays DATA_ONLY -- translation never increases authority.
"""

from __future__ import annotations

import re
from typing import Any

from sparkforge_azure.protocols.forge import (
    ForgeCapability,
    ForgeEvidenceBundle,
    ForgeHandoff,
    ForgeHealth,
    ForgeResult,
    ForgeTask,
    ForgeTaskStatus,
)

ENGINE = "spark-forge-azure"
PROTOCOL_VERSION = "forge-protocol/v1"

# API Forge ForgeResultStatus = ok|review|blocked|failed|unresolved. A result
# that is still accepted/running is not final: it needs review, never "ok".
_RESULT_STATUS = {
    ForgeTaskStatus.SUCCEEDED: "ok",
    ForgeTaskStatus.FAILED: "failed",
    ForgeTaskStatus.BLOCKED: "blocked",
    ForgeTaskStatus.UNRESOLVED: "unresolved",
    ForgeTaskStatus.ACCEPTED: "review",
    ForgeTaskStatus.RUNNING: "review",
}

# Our risk vocabulary (mcp.tools.RISK_DIMENSIONS) -> API Forge CapabilityRisk.
# Conservative: a cloud read carries tenant data, so it is "sensitive".
_RISK = {
    "read_only": "read_only",
    "local_write": "local_reversible",
    "cloud_read": "sensitive",
    "security_impact": "sensitive",
    "cloud_write": "external_mutation",
    "production_impact": "external_mutation",
}

# API Forge Budgets = {max_calls, max_rounds, deadline} (extra keys forbidden).
_BUDGET_KEYS = {"max_calls": "max_calls", "max_tool_calls": "max_calls",
                "max_rounds": "max_rounds", "deadline": "deadline"}


def risk(value: str) -> str:
    """Unknown risk maps to the most restrictive class, never to read_only."""
    return _RISK.get(value, "external_mutation")


def _budgets(budget: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    mapped = {_BUDGET_KEYS[k]: v for k, v in budget.items() if k in _BUDGET_KEYS}
    rest = {k: v for k, v in budget.items() if k not in _BUDGET_KEYS}
    return mapped, rest


def _slug(value: str) -> str:
    """API Forge task ids: ``^[a-z0-9][a-z0-9-]{1,62}$``."""
    slug = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    slug = slug or "task"
    if len(slug) < 2:
        slug = f"{slug}-t"
    return slug[:63]


def capability_descriptors(
    cap: ForgeCapability, *, state: str = "supported", risk: str = "read_only"
) -> list[dict[str, Any]]:
    """One API Forge descriptor per operation (API Forge is operation-granular)."""
    ops = cap.operations or (cap.name,)
    return [
        {
            "schema": "apiforge/forge-capability-descriptor/v1",
            "capability_id": f"{cap.name}.{op}" if op != cap.name else cap.name,
            "operation": op,
            "state": state,
            "risk": globals()["risk"](risk),
            "surfaces": [],
            "evidence": [],
            "limitations": [f"domains={','.join(cap.domains)}"] if cap.domains else [],
        }
        for op in ops
    ]


def task_request(task: ForgeTask, *, capability_id: str) -> dict[str, Any]:
    budgets, unmapped = _budgets(dict(task.budget))
    inputs = dict(task.inputs)
    if unmapped:
        # Preserved, not dropped: budgets API Forge cannot express travel as data.
        inputs["sparkforge_azure_budget"] = unmapped
    return {
        "schema": "apiforge/forge-task-request/v1",
        "task_id": _slug(task.id),
        "capability_id": capability_id,
        "intent": task.objective,
        "inputs": inputs,
        "budgets": budgets,
        "risk": risk(task.risk),
        "origin_engine": ENGINE,
        "requested_by": task.requested_by,
    }


def evidence_bundle(
    task_id: str, bundle: ForgeEvidenceBundle, *, hashes: dict[str, str] | None = None
) -> dict[str, Any]:
    """API Forge artifacts are content-addressed (sha256 required).

    A ref is emitted as an artifact only when its sha256 is supplied; otherwise it
    is reported as ``unhashed:<ref>`` in ``unresolved`` -- a hash is never invented.
    """
    hashes = hashes or {}
    artifacts: list[dict[str, Any]] = []
    unresolved = list(bundle.unresolved)
    for kind, refs in (("evidence_ref", bundle.evidence_refs), ("finding", bundle.findings),
                       ("fact", bundle.facts)):
        for ref in refs:
            if ref in hashes:
                artifacts.append({"path": ref, "sha256": hashes[ref], "kind": kind})
            else:
                unresolved.append(f"unhashed:{ref}")
    return {
        "schema": "apiforge/forge-evidence-bundle/v1",
        "task_id": _slug(task_id),
        "artifacts": artifacts,
        "unresolved": unresolved,
    }


def task_result(result: ForgeResult) -> dict[str, Any]:
    return {
        "schema": "apiforge/forge-task-result/v1",
        "task_id": _slug(result.task_id),
        "status": _RESULT_STATUS[result.status],
        "payload": {"summary": result.summary, "metrics": dict(result.metrics),
                    "rollback": result.rollback},
        "evidence": list(result.evidence.evidence_refs),
        "gaps": list(result.evidence.unresolved),
        "limitations": [],
        "error_code": None,
    }


def handoff(h: ForgeHandoff, *, request: dict[str, Any], handoff_id: str) -> dict[str, Any]:
    return {
        "schema": "apiforge/forge-handoff/v1",
        "handoff_id": handoff_id,
        "task_id": _slug(h.task_id),
        "from_engine": h.source,
        "to_engine": h.target,
        "request": request,
        "evidence_refs": list(h.evidence.evidence_refs),
        "context_refs": [],
        "delivery": "prepared",
        "unresolved": list(h.evidence.unresolved),
    }


def health(h: ForgeHealth) -> dict[str, Any]:
    state = "ok" if h.status == "ok" else "degraded"
    return {
        "schema": "apiforge/forge-health/v1",
        "engine": ENGINE,
        "protocol_version": PROTOCOL_VERSION,
        "state": state,
        "capabilities": len(h.capabilities),
        "tasks_by_state": {},
        "unresolved": sorted(k for k, v in h.checks.items() if v != "ok"),
    }
