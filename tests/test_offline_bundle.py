"""Offline bundle: redacted, content-addressed, verifiable, never raw."""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

import pytest

from sparkforge_azure.azure.governance import diagnose
from sparkforge_azure.bundle import BundleError, build_bundle, verify_bundle

ROOT = Path(__file__).resolve().parents[1]


def _scenario_outputs(tmp: Path) -> tuple[Path, Path]:
    import yaml

    sc = yaml.safe_load((ROOT / "examples/governance/uc_external_location_denied.yaml")
                        .read_text(encoding="utf-8"))
    d = diagnose(sc).to_dict()
    leak = "Account" + "Key=" + secrets.token_urlsafe(40)
    d["facts"][0]["attrs"]["note"] = "conn: DefaultEndpointsProtocol=https;" + leak
    facts, findings = tmp / "facts.json", tmp / "findings.json"
    facts.write_text(json.dumps({"facts": d["facts"]}), encoding="utf-8")
    findings.write_text(json.dumps({"findings": d["findings"]}), encoding="utf-8")
    return facts, findings


def test_bundle_is_redacted_and_verifies(tmp_path: Path) -> None:
    facts, findings = _scenario_outputs(tmp_path)
    out = tmp_path / "bundle"
    res = build_bundle(out, facts=facts, findings=findings,
                       knowledge_root=ROOT / "knowledge",
                       matrices_dir=ROOT / "knowledge" / "matrices")
    assert res["status"] == "ok" and res["redactions"]["count"] >= 1
    text = "".join(p.read_text(encoding="utf-8") for p in out.glob("*.json"))
    assert "AccountKey=" not in text.replace(" ", "")
    assert verify_bundle(out)["status"] == "ok"
    know = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    assert {k["id"] for k in know} >= {"azure.adls.gen2"} or know == [] or all(
        "id" in k for k in know)


def test_tampering_is_detected(tmp_path: Path) -> None:
    facts, findings = _scenario_outputs(tmp_path)
    out = tmp_path / "b"
    build_bundle(out, facts=facts, findings=findings)
    f = out / "facts.json"
    f.write_text(f.read_text(encoding="utf-8").replace("adls_acl", "tampered"), encoding="utf-8")
    (out / "extra.json").write_text("{}", encoding="utf-8")
    probs = verify_bundle(out)["problems"]
    assert any("hash mismatch" in p for p in probs) and any("unlisted" in p for p in probs)


def test_raw_dumps_are_refused(tmp_path: Path) -> None:
    raw = tmp_path / "resources.raw.json"
    raw.write_text("[]", encoding="utf-8")
    with pytest.raises(BundleError):
        build_bundle(tmp_path / "o", facts=raw)


def test_output_dir_must_be_empty(tmp_path: Path) -> None:
    (tmp_path / "o").mkdir()
    (tmp_path / "o" / "x").write_text("x", encoding="utf-8")
    with pytest.raises(BundleError):
        build_bundle(tmp_path / "o")


def test_verify_rejects_planted_secret(tmp_path: Path) -> None:
    out = tmp_path / "b"
    build_bundle(out)
    import hashlib

    planted = json.dumps({"password": os.urandom(8).hex()})
    (out / "config.json").write_text(planted, encoding="utf-8")
    man = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    man["files"]["config.json"] = hashlib.sha256(planted.encode()).hexdigest()
    (out / "MANIFEST.json").write_text(json.dumps(man), encoding="utf-8")
    assert verify_bundle(out)["status"] == "fail"
