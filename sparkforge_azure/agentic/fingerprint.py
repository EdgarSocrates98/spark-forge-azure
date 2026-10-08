"""Fleet fingerprint — one deterministic hash over the fleet's contract.

The fingerprint answers "did the agentic contract change?" without reading
diffs: it is ``sha256`` over canonical JSON of every manifest's contract
fields, the routing table, the team files and the closed vocabularies
(context kinds, spawn triggers, handoff modes). Any drift — a tool added, a
context kind removed, a route re-termed — changes the hash and is visible
in review without trusting a summary.

What it is NOT: a quality score, a test result, or proof of behavior. The
fingerprint measures *identity*, not correctness — the SDD gate and the
test suite measure correctness. Both are needed: identity drift with green
tests means the contract moved under a still-valid test set.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.teams import load_teams
from sparkforge_azure.agentmanifest.model import (
    CONTEXT_KINDS,
    load_manifests,
)
from sparkforge_azure.agentmanifest.routing import ROUTING_TABLE

#: The manifest fields that ARE the contract — body prose is deliberately
#: excluded (prose may evolve without contract drift).
CONTRACT_FIELDS: tuple[str, ...] = (
    "kind",
    "family",
    "domain",
    "inputs",
    "outputs",
    "allowed_tools",
    "denied_tools",
    "required_context_kinds",
    "allowed_context_kinds",
    "skills",
    "knowledge_packs",
    "budget",
    "handoffs",
    "handoff_mode",
    "spawn",
    "stop",
    "review_policy",
    "evals",
    "risk",
    "trust_floor",
    "parent",
    "agentops_emit_span",
)


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, default=str)


def _manifest_contract(manifest: Any) -> dict[str, Any]:
    data = manifest.data
    return {k: data.get(k) for k in CONTRACT_FIELDS}


def fingerprint_basis(root: Path | str) -> dict[str, Any]:
    """The full input the hash is computed over — inspectable, never opaque."""
    root = Path(root)
    manifests = {m.id: _manifest_contract(m) for m in load_manifests(root)}
    teams = {t.name: t.to_dict() for t in load_teams(root)}
    return {
        "context_kinds": sorted(CONTEXT_KINDS),
        "manifests": {k: manifests[k] for k in sorted(manifests)},
        "routing": [
            {"specialist": r.specialist, "terms": list(r.terms)}
            for r in ROUTING_TABLE
        ],
        "teams": {k: teams[k] for k in sorted(teams)},
    }


def fleet_fingerprint(root: Path | str) -> dict[str, Any]:
    """The hash plus enough shape to audit what it covers."""
    root = Path(root)
    basis = fingerprint_basis(root)
    digest = hashlib.sha256(_canonical(basis).encode("utf-8")).hexdigest()
    return {
        "fingerprint": f"sha256:{digest}",
        "agents": len(basis["manifests"]),
        "teams": len(basis["teams"]),
        "routes": len(basis["routing"]),
        "context_kinds": len(basis["context_kinds"]),
        "basis_fields": list(CONTRACT_FIELDS),
    }


__all__ = ["CONTRACT_FIELDS", "fingerprint_basis", "fleet_fingerprint"]
