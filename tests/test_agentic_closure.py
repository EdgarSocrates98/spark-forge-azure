"""Cycle-6 closure — fleet fingerprint determinism + impact graph."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sparkforge_azure.agentic.fingerprint import (
    fingerprint_basis,
    fleet_fingerprint,
)
from sparkforge_azure.agentic.impact import impact_for
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS

REPO = Path(__file__).resolve().parents[1]


def test_fingerprint_deterministic_and_shaped() -> None:
    a = fleet_fingerprint(REPO)
    b = fleet_fingerprint(REPO)
    assert a["fingerprint"] == b["fingerprint"]
    assert a["fingerprint"].startswith("sha256:")
    assert a["agents"] == len(ALL_AGENT_IDS) == 40
    assert a["teams"] == 4
    assert a["routes"] == 20
    # the basis is inspectable — every manifest contributes contract fields
    basis = fingerprint_basis(REPO)
    assert set(basis["manifests"]) == set(ALL_AGENT_IDS)
    assert all("allowed_tools" in m for m in basis["manifests"].values())


def test_fingerprint_drifts_on_contract_change(tmp_path) -> None:
    """A contract mutation must change the hash — that is the whole point."""
    basis = fingerprint_basis(REPO)
    mutated = json.loads(json.dumps(basis))
    mutated["manifests"]["fabric-specialist"]["allowed_tools"] = ["sfa_lab_run"]
    import hashlib
    canon = json.dumps(mutated, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, default=str)
    mutated_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    assert mutated_hash != fleet_fingerprint(REPO)["fingerprint"][7:]


def test_impact_graph_maps_manifest_to_its_tests() -> None:
    rep = impact_for(["agents/fabric-specialist.md"])
    assert rep["agents"] == ["fabric-specialist"]
    assert rep["fleet_wide"] is False
    assert "tests/test_agent_manifests.py" in rep["tests"]
    assert rep["unresolved"] == []


def test_impact_graph_fleet_wide_on_taxonomy() -> None:
    rep = impact_for(["sparkforge_azure/agentmanifest/model.py"])
    assert rep["fleet_wide"] is True
    assert rep["agents"] == sorted(ALL_AGENT_IDS)


def test_impact_graph_unknown_is_unresolved_not_silent() -> None:
    rep = impact_for(["totally/unknown/file.py"])
    assert rep["agents"] == []
    assert rep["unresolved"] == ["impact_unknown:totally/unknown/file.py"]

    # windows-style and ./-prefixed paths normalize
    rep = impact_for([".\\agent-teams\\fabric.yaml"])
    assert rep["unresolved"] == []
    assert "tests/test_agentic_teams.py" in rep["tests"]


def _cli(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", *args],
        capture_output=True, text=True, cwd=REPO)
    return {"code": proc.returncode, "doc": json.loads(proc.stdout)}


def test_agents_fingerprint_and_impact_cli() -> None:
    out = _cli("agents", "fingerprint")
    assert out["code"] == 0
    assert out["doc"]["agents"] == 40
    assert out["doc"]["fingerprint"].startswith("sha256:")

    out = _cli("agents", "impact", "--path", "agents/coordinator.md")
    assert out["code"] == 0
    assert out["doc"]["agents"] == ["coordinator"]

    out = _cli("agents", "impact", "--path", "nope/nada.py")
    assert out["code"] == 1
    assert out["doc"]["status"] == "unresolved"
