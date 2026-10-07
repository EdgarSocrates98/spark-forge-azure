"""Forge Protocol: AWS-sibling shape stays canonical; API Forge projection validates.

The cross-repo test runs API Forge's own pydantic models in API Forge's own venv
(subprocess), so neither project imports the other (multi-forge RFC).  It is
skipped when the checkout is absent: set SPARKFORGE_AZURE_APIFORGE_REPO.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from sparkforge_azure.protocols import apiforge_compat as compat
from sparkforge_azure.protocols.forge import (
    ForgeCapability,
    ForgeEvidenceBundle,
    ForgeHandoff,
    ForgeHealth,
    ForgeResult,
    ForgeTask,
    ForgeTaskStatus,
)

CAP = ForgeCapability(
    name="azure.governance", domains=("unity-catalog", "adls"), operations=("diagnose",)
)
TASK = ForgeTask(task_type="diagnose", objective="UC external location access denied",
                 inputs={"case": "c1"}, budget={"max_tokens": 4000})
EVID = ForgeEvidenceBundle(facts=("f_1",), findings=("SFA-UC-001",),
                           evidence_refs=("facts.json#f_1",), unresolved=("network",))


def _samples() -> dict[str, object]:
    request = compat.task_request(TASK, capability_id="azure.governance.diagnose")
    return {
        "ForgeCapabilityDescriptor": compat.capability_descriptors(CAP)[0],
        "ForgeTaskRequest": request,
        "ForgeEvidenceBundle": compat.evidence_bundle(
            TASK.id, EVID, hashes={"facts.json#f_1": "a" * 64}
        ),
        "ForgeTaskResult": compat.task_result(
            ForgeResult(task_id=TASK.id, status=ForgeTaskStatus.UNRESOLVED,
                        summary="network layer not observed", evidence=EVID)
        ),
        "ForgeHandoff": compat.handoff(
            ForgeHandoff(task_id=TASK.id, source="spark-forge-azure", target="api-forge",
                         evidence=EVID),
            request=request, handoff_id="h-1",
        ),
        "ForgeHealth": compat.health(
            ForgeHealth(status="ok", version="0.1.0", capabilities=(CAP,),
                        checks={"mcp": "ok", "azure_auth": "absent"})
        ),
    }


def test_canonical_shape_is_aws_sibling_shape() -> None:
    assert set(CAP.to_dict()) == {"name", "version", "domains", "operations", "trust_floor"}
    assert ForgeHandoff(task_id="t", source="a", target="b").to_dict()["authority"] == "DATA_ONLY"


def test_projection_is_deterministic_and_never_invents_status() -> None:
    assert _samples() == _samples()
    health = _samples()["ForgeHealth"]
    assert health["unresolved"] == ["azure_auth"]
    assert health["state"] == "ok"


def test_evidence_never_invents_hashes() -> None:
    out = compat.evidence_bundle(TASK.id, EVID)
    assert out["artifacts"] == []
    assert "unhashed:facts.json#f_1" in out["unresolved"]
    assert compat.risk("something_new") == "external_mutation"


def test_task_id_matches_apiforge_pattern() -> None:
    import re

    tid = compat.task_request(TASK, capability_id="x")["task_id"]
    assert re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", tid)


def _apiforge_python() -> tuple[Path, Path] | None:
    sibling = Path(__file__).resolve().parents[2] / "api-forge"
    repo = Path(os.environ.get("SPARKFORGE_AZURE_APIFORGE_REPO", str(sibling)))
    contract = repo / "src" / "apiforge" / "contracts" / "forge_protocol.py"
    for py in (repo / ".venv" / "Scripts" / "python.exe", repo / ".venv" / "bin" / "python"):
        if py.is_file() and contract.is_file():
            return repo, py
    return None


@pytest.mark.slow
def test_projection_validates_against_apiforge_models(tmp_path: Path) -> None:
    found = _apiforge_python()
    if found is None:
        pytest.skip("API Forge checkout/venv not available")
    repo, py = found
    payload = tmp_path / "samples.json"
    payload.write_text(json.dumps(_samples()), encoding="utf-8")
    script = (
        "import json,sys\n"
        "from apiforge.contracts import forge_protocol as fp\n"
        "data=json.load(open(sys.argv[1],encoding='utf-8'))\n"
        "for name,obj in data.items():\n"
        "    getattr(fp,name).model_validate(obj)\n"
        "print('ok')\n"
    )
    proc = subprocess.run(
        [str(py), "-c", script, str(payload)], capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(repo / "src")}, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip().endswith("ok")
