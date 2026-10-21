"""lf-0029: peer delegation — discovery, governance, exec, handoff, routing.

Every test fakes the specialist surface: PATH scripts written into tmp_path,
injected ``which``/``dist_loader``/``runner`` seams, or a fake ``popen_run``.
The real ``data-sentinel`` and ``forge-doctor-data`` binaries are never
executed — an absent/incompatible specialist is a named refusal, never a
simulated run. Azure specifics covered: AZURE_/ARM_/DATABRICKS_ env
scrubbing, ``--platform databricks`` argv, lakehouse compat argv, and the
explicit boundary that no Azure-cloud verb is declared.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from sparkforge_azure.delegation import governance
from sparkforge_azure.delegation.contracts import (
    DeclaredCapability,
    DelegationRefusal,
    ExecResult,
)
from sparkforge_azure.delegation.discovery import discover_peer
from sparkforge_azure.delegation.env import is_credential_name, safe_env
from sparkforge_azure.delegation.execute import run_governed
from sparkforge_azure.delegation.handoff import (
    HandoffParseError,
    parse_doctor_scan,
    parse_sentinel_report,
)
from sparkforge_azure.delegation.peers import DOCTOR_DATA, SENTINEL, consumer_delegation
from sparkforge_azure.delegation.run import delegate, plan

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

@dataclass
class _FakeProc:
    returncode: int = 0
    stdout: bytes = b""
    stderr: bytes = b""


def _proc(rc: int = 0, out: str = "", err: str = "") -> _FakeProc:
    return _FakeProc(returncode=rc, stdout=out.encode(), stderr=err.encode())


def _no_dist(name: str):
    return None, None


def _no_which(name: str):
    return None


class _FakeDist:
    """An importlib.metadata Distribution stand-in."""

    def __init__(self, meta: dict[str, Any], files_root: Path | None = None):
        self._meta = meta
        self._root = files_root
        self.metadata = meta
        self.version = meta.get("version")
        self.files = meta.get("files", [])

    def locate_file(self, rel: str) -> Path:
        assert self._root is not None
        return self._root / rel


def _dist_loader(meta_by_name: dict[str, dict[str, Any]], root: Path | None = None):
    """Fake ``dist_loader`` — ``meta_by_name`` values use the *normalized*
    shape ``_load_dist`` produces (``name``/``version``/``requires_python``/
    ``files``); ``Name``/``Requires-Python`` accepted as aliases."""
    def load(name: str):
        meta = meta_by_name.get(name)
        if meta is None:
            return None, None
        normalized = {
            "name": meta.get("name") or meta.get("Name") or name,
            "version": meta.get("version"),
            "requires_python": meta.get("requires_python")
                or meta.get("Requires-Python"),
            "files": list(meta.get("files") or []),
        }
        return _FakeDist(meta, root), normalized
    return load


def _write_exe(path: Path, body: str) -> Path:
    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if os.name == "nt":
        shim = path.with_name(path.name + ".cmd")
        shim.write_text(
            f'@echo off\r\n"{sys.executable}" "{path}" %*\r\n', encoding="utf-8"
        )
        return shim
    return path


_SENTINEL_CLI = r'''
import json, sys
argv = sys.argv[1:]
if "--version" in argv:
    print("data-sentinel 1.2.3"); sys.exit(0)
if argv[:2] == ["capabilities", "--descriptors"]:
    print(json.dumps([
        {"capability_id": "sentinel.databricks-logs",
         "provider": "data-sentinel-forge", "version": "1.2.3",
         "description": "log diagnostics",
         "input_types": ["log"], "output_types": ["report"]},
    ])); sys.exit(0)
if argv[:2] == ["lakehouse", "compat"]:
    print(json.dumps({"support_status": "SUPPORTED", "constraints": []})); sys.exit(0)
if argv and argv[0] in ("analyze", "sql", "spark", "lakehouse"):
    print(json.dumps({
        "findings": [{
            "finding_id": "OOM-DRV-1", "severity": "high", "status": "PROBABLE",
            "explanation": "driver memory near limit", "evidence_ids": ["EV-1"],
        }, {
            "finding_id": "SKEW-1", "severity": "medium", "status": "POSSIBLE",
            "explanation": "partition skew suspected", "evidence_ids": [],
        }],
        "limitations": ["sampled logs only"],
    })); sys.exit(0)
sys.exit(2)
'''

_DOCTOR_CLI = r'''
import json, sys
argv = sys.argv[1:]
if "--version" in argv:
    print("forge-doctor-data 0.9.1"); sys.exit(0)
if argv and argv[0] == "scan":
    print(json.dumps({
        "tool": "forge-doctor-data", "version": "0.9.1", "schema_version": "3.0",
        "project": {"path": argv[1] if len(argv) > 1 else "."},
        "summary": {"files": 3, "errors": 1, "warnings": 1},
        "findings": [
            {"id": "DD-SEC-001", "sev": "error", "loc": "jobs/etl.py:12",
             "fp": "ab12cd"},
            {"id": "DD-CFG-010", "sev": "warning", "loc": "conf/spark.yml:4",
             "fp": "ef34ab"},
        ],
    })); sys.exit(1)  # rc 1: findings at/above the exit gate — a result
sys.exit(2)
'''


@pytest.fixture()
def sentinel_cli(tmp_path: Path) -> str:
    return str(_write_exe(tmp_path / "data-sentinel", _SENTINEL_CLI))


@pytest.fixture()
def doctor_cli(tmp_path: Path) -> str:
    return str(_write_exe(tmp_path / "forge-doctor-data", _DOCTOR_CLI))


def _sentinel_injections(cli: str) -> dict[str, Any]:
    # no ``runner``: the fake script answers --version and capabilities
    # --descriptors through the real governed subprocess boundary.
    return {
        "which": lambda name: cli if name == "data-sentinel" else None,
        "dist_loader": _no_dist,
    }


def _doctor_injections(cli: str, *, with_dist: bool = True) -> dict[str, Any]:
    return {
        "which": lambda name: cli if name == "forge-doctor-data" else None,
        "dist_loader": _dist_loader(
            {"forge-doctor-data": {"Name": "forge-doctor-data",
                                   "version": "0.9.1", "files": []}}
        ) if with_dist else _no_dist,
    }


# ---------------------------------------------------------------------------
# Discovery states
# ---------------------------------------------------------------------------

class TestDiscoveryStates:
    def test_not_installed(self, tmp_path: Path):
        entry = discover_peer(
            SENTINEL, probe=True, workspace_root=tmp_path,
            which=_no_which, dist_loader=_no_dist,
        )
        assert entry.state == "NOT_INSTALLED"
        assert entry.checks["handshake"] == "SKIP"

    def test_discovered_without_probe(self, tmp_path: Path):
        loader = _dist_loader(
            {"forge-doctor-data": {"Name": "forge-doctor-data",
                                   "version": "0.9.1", "files": []}}
        )
        entry = discover_peer(
            DOCTOR_DATA, probe=False, workspace_root=tmp_path,
            which=_no_which, dist_loader=loader,
        )
        assert entry.state == "DISCOVERED"
        assert entry.version == "0.9.1"

    def test_verified_via_version_and_descriptors(self, sentinel_cli: str,
                                                  tmp_path: Path):
        entry = discover_peer(
            SENTINEL, probe=True, workspace_root=tmp_path,
            which=lambda n: sentinel_cli if n == "data-sentinel" else None,
            dist_loader=_no_dist,
        )
        assert entry.state == "VERIFIED", entry.notes
        assert entry.checks["health"] == "PASS"
        assert entry.version == "1.2.3"

    def test_verified_doctor_without_descriptor_surface(self, doctor_cli: str,
                                                        tmp_path: Path):
        entry = discover_peer(
            DOCTOR_DATA, probe=True, workspace_root=tmp_path,
            **_doctor_injections(doctor_cli),
        )
        assert entry.state == "VERIFIED", entry.notes
        assert entry.checks["health"] == "PASS"

    def test_incompatible_requires_python(self, tmp_path: Path):
        loader = _dist_loader(
            {"forge-doctor-data": {
                "Name": "forge-doctor-data", "version": "0.9.1",
                "Requires-Python": ">=99.0", "files": []}}
        )
        entry = discover_peer(
            DOCTOR_DATA, probe=True, workspace_root=tmp_path,
            which=_no_which, dist_loader=loader,
        )
        assert entry.state == "INCOMPATIBLE"
        assert any("requires-python" in lim for lim in entry.limitations)

    def test_incompatible_manifest_major_drift(self, tmp_path: Path):
        manifest = {
            "schema": "theforge/SpecialistCapability/v1",
            "specialist": {"id": "forge-doctor-data", "version": "9.0.0"},
            "capabilities": [],
        }
        loader = _dist_loader(
            {"forge-doctor-data": {
                "Name": "forge-doctor-data", "version": "0.9.1",
                "files": ["forge.capabilities.json"]}},
            root=tmp_path,
        )
        (tmp_path / "forge.capabilities.json").write_text(json.dumps(manifest))
        entry = discover_peer(
            DOCTOR_DATA, probe=True, workspace_root=tmp_path,
            which=_no_which, dist_loader=loader,
        )
        assert entry.state == "INCOMPATIBLE", entry.notes

    def test_untrusted_corrupt_manifest(self, tmp_path: Path):
        manifest = {"schema": "wrong/Schema", "specialist": {"id": "x"}}
        loader = _dist_loader(
            {"forge-doctor-data": {
                "Name": "forge-doctor-data", "version": "0.9.1",
                "files": ["forge.capabilities.json"]}},
            root=tmp_path,
        )
        (tmp_path / "forge.capabilities.json").write_text(json.dumps(manifest))
        entry = discover_peer(
            DOCTOR_DATA, probe=True, workspace_root=tmp_path,
            which=_no_which, dist_loader=loader,
        )
        assert entry.state == "UNTRUSTED"
        assert entry.checks["manifest"] == "FAIL"


# ---------------------------------------------------------------------------
# Environment scrubbing — Azure-shaped credentials
# ---------------------------------------------------------------------------

class TestEnvScrubbing:
    def test_azure_credential_names(self):
        for name in ("AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
                     "AZURE_TENANT_ID", "AZURE_STORAGE_KEY",
                     "ARM_CLIENT_ID", "ARM_CLIENT_SECRET",
                     "DATABRICKS_TOKEN", "DATABRICKS_HOST",
                     "EVENTHUB_CONNECTION_STRING", "GITHUB_TOKEN",
                     "MY_API_KEY", "DB_PASSWORD", "HTTPS_PROXY"):
            assert is_credential_name(name), name
        for name in ("PATH", "HOME", "LANG", "TERM"):
            assert not is_credential_name(name), name

    def test_safe_env_strips_azure_credentials(self):
        env = safe_env({
            "PATH": "/usr/bin",
            "AZURE_CLIENT_SECRET": "spn-secret",
            "AZURE_TENANT_ID": "tenant",
            "ARM_SUBSCRIPTION_ID": "sub",
            "DATABRICKS_TOKEN": "dapi123",
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=...",
            "HTTP_PROXY": "http://user:pw@proxy:8080",
            "HOME": "/home/x",
            "SPARKFORGE_AZURE_CONFIG": "x",  # not allowlisted either
        })
        assert env["PATH"] == "/usr/bin"
        assert env["HOME"] == "/home/x"
        for leaked in ("AZURE_CLIENT_SECRET", "AZURE_TENANT_ID",
                       "ARM_SUBSCRIPTION_ID", "DATABRICKS_TOKEN",
                       "AZURE_STORAGE_CONNECTION_STRING", "HTTP_PROXY",
                       "SPARKFORGE_AZURE_CONFIG"):
            assert leaked not in env, leaked

    def test_env_extra_cannot_smuggle_credentials(self):
        result = run_governed(
            ["data-sentinel", "--version"],
            env_extra={"AZURE_CLIENT_SECRET": "x"},
        )
        assert isinstance(result, DelegationRefusal)
        assert result.code == "policy-refusal"

    def test_subprocess_never_sees_credentials(self):
        captured: dict[str, Any] = {}

        def spy(argv, **kw):
            captured["env"] = kw.get("env", {})
            captured["kw"] = kw
            return _proc(out="ok")

        os.environ["AZURE_CLIENT_SECRET"] = "spn-secret-value"  # noqa: S105 — fixture value, never a real secret
        try:
            run_governed(["data-sentinel", "--version"], _popen_run=spy)
        finally:
            del os.environ["AZURE_CLIENT_SECRET"]
        assert "AZURE_CLIENT_SECRET" not in captured["env"]
        assert captured["kw"].get("shell") in (None, False)


# ---------------------------------------------------------------------------
# Governed execution
# ---------------------------------------------------------------------------

class TestRunGoverned:
    def test_never_shell_argv_only(self):
        seen: dict[str, Any] = {}

        def spy(argv, **kw):
            seen["argv"] = argv
            seen["kw"] = kw
            return _proc(out="ok")

        result = run_governed(["x", "--y"], _popen_run=spy)
        assert isinstance(result, ExecResult)
        assert isinstance(seen["argv"], list)
        assert seen["kw"].get("shell") in (None, False)

    def test_timeout_is_named(self):
        def hang(argv, **kw):
            raise subprocess.TimeoutExpired(cmd=argv[0], timeout=1)

        result = run_governed(["slow-cli"], timeout_s=1, _popen_run=hang)
        assert isinstance(result, DelegationRefusal)
        assert result.code == "timeout"

    def test_spawn_failure_provider_absent(self):
        def missing(argv, **kw):
            raise FileNotFoundError(argv[0])

        result = run_governed(["ghost-cli"], _popen_run=missing)
        assert isinstance(result, DelegationRefusal)
        assert result.code == "provider-absent"


# ---------------------------------------------------------------------------
# Handoff parsers — severity/confidence as declared, never promoted
# ---------------------------------------------------------------------------

class TestHandoffParsers:
    def test_sentinel_confidence_rename_no_promotion(self):
        parsed = parse_sentinel_report(json.dumps({
            "findings": [
                {"finding_id": "F1", "severity": "HIGH", "status": "CONFIRMED",
                 "explanation": "a"},
                {"finding_id": "F2", "severity": "MEDIUM", "status": "PROBABLE",
                 "explanation": "b"},
                {"finding_id": "F3", "severity": "LOW", "status": "POSSIBLE",
                 "explanation": "c"},
                {"finding_id": "F4", "severity": "INFO", "status": "UNKNOWN",
                 "explanation": "d"},
            ],
        }))
        conf = {f["id"]: f["confidence"] for f in parsed["findings"]}
        assert conf == {"F1": "CONFIRMED", "F2": "LIKELY",
                        "F3": "POSSIBLE", "F4": "UNKNOWN"}

    def test_possible_never_becomes_confirmed(self):
        parsed = parse_sentinel_report(json.dumps({
            "findings": [{"finding_id": "F", "severity": "info",
                          "status": "POSSIBLE", "explanation": "x"}],
        }))
        assert parsed["findings"][0]["confidence"] == "POSSIBLE"

    def test_sentinel_non_report_json_is_summary_evidence(self):
        parsed = parse_sentinel_report(json.dumps({"support_status": "SUPPORTED"}))
        assert parsed["findings"] == []
        assert parsed["summary_refs"][0]["kind"] == "summary"

    def test_sentinel_invalid_output(self):
        with pytest.raises(HandoffParseError):
            parse_sentinel_report("not json at all")

    def test_doctor_scan_maps_agent_format(self):
        parsed = parse_doctor_scan(json.dumps({
            "tool": "forge-doctor-data", "version": "0.9.1",
            "schema_version": "3.0",
            "summary": {"files": 2, "errors": 1},
            "findings": [
                {"id": "DD-1", "sev": "error", "loc": "a.py:1", "fp": "h1"},
                {"id": "DD-2", "sev": "warning", "loc": "b.py:2", "fp": "h2"},
            ],
        }))
        assert [f["severity"] for f in parsed["findings"]] == ["high", "medium"]
        assert all(f["confidence"] == "UNKNOWN" for f in parsed["findings"])

    def test_doctor_wrong_schema_version_refused(self):
        with pytest.raises(HandoffParseError):
            parse_doctor_scan(json.dumps({"schema_version": "9.9",
                                          "findings": []}))


# ---------------------------------------------------------------------------
# Chain control — cycle prevention
# ---------------------------------------------------------------------------

class TestChainControl:
    def test_revisit_refused(self):
        d = governance.start_chain(
            consumer_delegation(), correlation_id="dl-testchain")
        d = governance.admit_hop(d, "data-sentinel-forge")
        assert not isinstance(d, DelegationRefusal)
        again = governance.admit_hop(d, "data-sentinel-forge")
        assert isinstance(again, DelegationRefusal)
        assert again.code == "cycle-detected"

    def test_reentering_consumer_refused(self):
        # Sentinel → Spark-Azure → Sentinel shape: the consumer is already
        # visited by construction; a hop back to it is a cycle.
        d = governance.start_chain(
            consumer_delegation(), correlation_id="dl-testchain2")
        back = governance.admit_hop(d, "spark-forge-azure")
        assert isinstance(back, DelegationRefusal)
        assert back.code == "cycle-detected"

    def test_hop_budget(self):
        d = governance.start_chain(
            consumer_delegation(), correlation_id="dl-b", max_hops=1)
        d = governance.admit_hop(d, "data-sentinel-forge")
        exhausted = governance.admit_hop(d, "forge-doctor-data")
        assert isinstance(exhausted, DelegationRefusal)
        assert exhausted.code == "budget-exhausted"


# ---------------------------------------------------------------------------
# argv resolution — Azure placeholder semantics
# ---------------------------------------------------------------------------

class TestArgvResolution:
    def test_databricks_platform_is_hardcoded(self):
        argv = governance.resolve_capability_argv(
            ["{cli}", "analyze", "--file", "{target}",
             "--platform", "databricks", "--json", "--no-persist"],
            cli_argv=["data-sentinel"],
            values={"target": "driver.log"},
        )
        assert argv == ["data-sentinel", "analyze", "--file", "driver.log",
                        "--platform", "databricks", "--json", "--no-persist"]

    def test_lakehouse_compat_argv(self):
        argv = governance.resolve_capability_argv(
            ["{cli}", "lakehouse", "compat", "--runtime", "{runtime}",
             "--operation", "{operation}", "--table-format", "{table_format}",
             "--json"],
            cli_argv=["data-sentinel"],
            values={"runtime": "databricks-14.3-lts", "operation": "merge",
                    "table_format": "delta"},
        )
        assert argv == ["data-sentinel", "lakehouse", "compat",
                        "--runtime", "databricks-14.3-lts",
                        "--operation", "merge",
                        "--table-format", "delta", "--json"]

    def test_required_placeholder_missing_refused(self):
        refusal = governance.resolve_capability_argv(
            ["{cli}", "lakehouse", "compat", "--runtime", "{runtime}"],
            cli_argv=["data-sentinel"], values={})
        assert isinstance(refusal, DelegationRefusal)
        assert refusal.code == "invalid-input"

    def test_traversal_in_target_refused(self):
        refusal = governance.resolve_capability_argv(
            ["{cli}", "analyze", "--file", "{target}"],
            cli_argv=["data-sentinel"],
            values={"target": "../../etc/passwd"},
        )
        assert isinstance(refusal, DelegationRefusal)
        assert refusal.code == "invalid-input"

    def test_optional_dialect_drops_flag(self):
        argv = governance.resolve_capability_argv(
            ["{cli}", "spark", "optimize", "--sql", "{target}",
             "--dialect", "{dialect}", "--json"],
            cli_argv=["data-sentinel"],
            values={"target": "q.sql", "dialect": None},
        )
        assert "--dialect" not in argv


# ---------------------------------------------------------------------------
# Caso E — absent specialist → explicit refusal + native fallback
# ---------------------------------------------------------------------------

class TestAbsentSpecialist:
    def test_delegate_absent_never_executes(self, tmp_path: Path):
        payload = delegate(
            "data-sentinel-forge", "sentinel.databricks-logs",
            values={"target": "driver.log"},
            workspace=tmp_path,
            which=_no_which, dist_loader=_no_dist,
            popen_run=lambda *a, **k: pytest.fail("must not spawn"),
        )
        assert payload["status"] == "refused"
        assert payload["refusal"]["code"] == "provider-absent"
        assert payload["fallback"] == "native-analysis"
        assert payload["handoff"] is None
        assert not (tmp_path / ".sparkforge-azure").exists()

    def test_plan_absent_reports_unavailable(self, tmp_path: Path):
        payload = plan(
            "diagnose databricks job oom and data skew",
            workspace=tmp_path, probe=True,
            which=_no_which, dist_loader=_no_dist,
        )
        assert payload["status"] in ("unavailable", "refused")
        codes = {r["code"] for r in payload["refusals"]}
        assert "provider-absent" in codes


# ---------------------------------------------------------------------------
# Caso F — incompatible specialist → explicit block
# ---------------------------------------------------------------------------

class TestIncompatibleSpecialist:
    def test_delegate_incompatible_blocked(self, tmp_path: Path):
        loader = _dist_loader(
            {"forge-doctor-data": {
                "Name": "forge-doctor-data", "version": "0.9.1",
                "Requires-Python": ">=99.0", "files": []}}
        )
        payload = delegate(
            "forge-doctor-data", "doctor.scan-project",
            values={"target": "."},
            workspace=tmp_path,
            which=lambda n: "/x/forge-doctor-data", dist_loader=loader,
            popen_run=lambda *a, **k: pytest.fail("must not spawn"),
        )
        assert payload["status"] == "refused"
        assert payload["refusal"]["code"] == "version-incompatible"


# ---------------------------------------------------------------------------
# Policy gates — Azure boundary: nothing external is declared today
# ---------------------------------------------------------------------------

class TestPolicyGate:
    def test_all_declared_capabilities_are_local_read(self):
        # The Azure boundary: sentinel's cloud verbs are AWS-only, so this
        # forge declares zero EXTERNAL_READ/COST_BEARING capabilities. The
        # gate stays armed anyway — a future cloud verb must enter as
        # external_read explicitly, never slide in silently.
        for spec in (SENTINEL, DOCTOR_DATA):
            for cap in spec.capabilities:
                risks = governance.capability_risks(cap)
                assert risks == frozenset({"LOCAL_READ"}), (cap.id, risks)

    def test_no_aws_verbs_declared(self):
        for cap in SENTINEL.capabilities:
            assert "glue" not in cap.entrypoint, cap.id
            assert "emr" not in cap.entrypoint, cap.id
            assert cap.execution_mode == "local"
            assert not cap.network

    def test_external_read_capability_would_need_grant(self):
        hypothetical = DeclaredCapability(
            id="sentinel.cloud-read",
            entrypoint=["{cli}", "x"],
            execution_mode="remote",
            risk="external_read",
            network=True,
            external_cost="unknown",
        )
        risks = governance.capability_risks(hypothetical)
        gate = governance.gate_capability(risks, authorized=frozenset())
        assert gate.decision == "deny"
        assert set(gate.missing) == {"EXTERNAL_READ", "COST_BEARING"}
        gate = governance.gate_capability(
            risks, authorized={"EXTERNAL_READ", "COST_BEARING"})
        assert gate.decision == "allow"


# ---------------------------------------------------------------------------
# End-to-end delegate → handoff
# ---------------------------------------------------------------------------

class TestDelegateEndToEnd:
    def test_databricks_logs_completed(self, sentinel_cli: str,
                                       tmp_path: Path):
        payload = delegate(
            "data-sentinel-forge", "sentinel.databricks-logs",
            values={"target": "driver.log"},
            workspace=tmp_path,
            **_sentinel_injections(sentinel_cli),
        )
        assert payload["status"] == "completed", payload
        assert "--platform" in payload["argv"]
        assert payload["argv"][payload["argv"].index("--platform") + 1] == "databricks"
        findings = {f["id"]: f for f in payload["findings"]}
        assert findings["OOM-DRV-1"]["confidence"] == "LIKELY"
        assert findings["SKEW-1"]["confidence"] == "POSSIBLE"
        handoff = payload["handoff"]
        assert handoff["schema"] == "theforge/EvidenceHandoff/v1"
        assert handoff["consumer_provider"] == "spark-forge-azure"
        assert handoff["redacted"] is True

    def test_lakehouse_compat_completed(self, sentinel_cli: str,
                                        tmp_path: Path):
        payload = delegate(
            "data-sentinel-forge", "sentinel.lakehouse-compat",
            values={"runtime": "databricks-14.3-lts", "operation": "merge",
                    "table_format": "delta"},
            workspace=tmp_path,
            **_sentinel_injections(sentinel_cli),
        )
        assert payload["status"] == "completed", payload
        assert payload["argv"][:4] == [
            sentinel_cli, "lakehouse", "compat", "--runtime"]

    def test_doctor_scan_completed(self, doctor_cli: str, tmp_path: Path):
        payload = delegate(
            "forge-doctor-data", "doctor.scan-project",
            values={"target": ".", "check": None},
            workspace=tmp_path,
            **_doctor_injections(doctor_cli),
        )
        assert payload["status"] == "completed", payload
        by_id = {f["id"]: f for f in payload["findings"]}
        assert by_id["DD-SEC-001"]["severity"] == "high"
        assert "--check" not in payload["argv"]

    def test_handoff_persisted_under_azure_state_dir(self, sentinel_cli: str,
                                                     tmp_path: Path):
        payload = delegate(
            "data-sentinel-forge", "sentinel.databricks-logs",
            values={"target": "driver.log"},
            workspace=tmp_path,
            **_sentinel_injections(sentinel_cli),
        )
        path = Path(payload["handoff_path"])
        assert path.parent == (
            tmp_path / ".sparkforge-azure" / "delegation" / "handoffs"
        )
        doc = json.loads(path.read_text(encoding="utf-8"))
        from sparkforge_azure.delegation.contracts import EvidenceHandoff, from_dict
        from sparkforge_azure.delegation.governance import verify_integrity
        assert verify_integrity(from_dict(EvidenceHandoff, doc))

    def test_invalid_output_is_named_refusal(self, tmp_path: Path):
        cli = _write_exe(tmp_path / "data-sentinel", r'''
import sys
argv = sys.argv[1:]
if "--version" in argv:
    print("1.0.0"); sys.exit(0)
if argv[:2] == ["capabilities", "--descriptors"]:
    print("[]"); sys.exit(0)
print("this is not a diagnostic report"); sys.exit(0)
''')
        payload = delegate(
            "data-sentinel-forge", "sentinel.databricks-logs",
            values={"target": "x.log"},
            workspace=tmp_path,
            which=lambda n: str(cli) if n == "data-sentinel" else None,
            dist_loader=_no_dist,
        )
        assert payload["status"] == "refused"
        assert payload["refusal"]["code"] == "invalid-output"
        assert payload["handoff"]["status"] == "refused"

    def test_timeout_is_named_failure(self, tmp_path: Path):
        cli = _write_exe(tmp_path / "data-sentinel", r'''
import sys
argv = sys.argv[1:]
if "--version" in argv:
    print("1.0.0"); sys.exit(0)
if argv[:2] == ["capabilities", "--descriptors"]:
    print("[]"); sys.exit(0)
sys.exit(0)
''')

        def hang(argv, **kw):
            raise subprocess.TimeoutExpired(cmd=argv[0], timeout=1)

        payload = delegate(
            "data-sentinel-forge", "sentinel.databricks-logs",
            values={"target": "x.log"},
            workspace=tmp_path,
            which=lambda n: str(cli) if n == "data-sentinel" else None,
            dist_loader=_no_dist,
            popen_run=hang,
        )
        assert payload["status"] == "failed"
        assert payload["handoff"]["error"]["code"] == "timeout"
        assert payload["handoff"]["error"]["retryable"] is True

    def test_capability_not_declared(self, tmp_path: Path):
        payload = delegate(
            "data-sentinel-forge", "sentinel.no-such-cap",
            workspace=tmp_path,
            which=_no_which, dist_loader=_no_dist,
        )
        assert payload["refusal"]["code"] == "capability-absent"

    def test_provider_not_declared(self, tmp_path: Path):
        payload = delegate("some-other-forge", "x.y", workspace=tmp_path)
        assert payload["refusal"]["code"] == "provider-absent"

    def test_cycle_via_chain_refused(self, sentinel_cli: str, tmp_path: Path):
        chained = governance.start_chain(
            consumer_delegation(), correlation_id="dl-cycle")
        chained = governance.admit_hop(chained, "data-sentinel-forge")
        payload = delegate(
            "data-sentinel-forge", "sentinel.databricks-logs",
            values={"target": "x.log"},
            workspace=tmp_path,
            delegation=chained,
            popen_run=lambda *a, **k: pytest.fail("cycle must refuse"),
            **_sentinel_injections(sentinel_cli),
        )
        assert payload["refusal"]["code"] == "cycle-detected"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class TestRouter:
    def test_static_intent_routes_to_doctor(self, doctor_cli: str,
                                            tmp_path: Path):
        payload = plan(
            "static analysis pyspark review antipatterns",
            workspace=tmp_path,
            which=lambda n: doctor_cli if n == "forge-doctor-data" else None,
            dist_loader=_dist_loader(
                {"forge-doctor-data": {"Name": "forge-doctor-data",
                                       "version": "0.9.1", "files": []}}),
        )
        assert payload["status"] == "planned", payload
        assert payload["picks"][0]["provider"] == "forge-doctor-data"
        assert payload["picks"][0]["capability"] == "doctor.scan-project"

    def test_databricks_intent_routes_to_sentinel(self, sentinel_cli: str,
                                                tmp_path: Path):
        payload = plan(
            "diagnose databricks driver log oom and data skew",
            workspace=tmp_path,
            **_sentinel_injections(sentinel_cli),
        )
        assert payload["status"] == "planned", payload
        assert payload["picks"][0]["provider"] == "data-sentinel-forge"
        assert payload["picks"][0]["capability"] == "sentinel.databricks-logs"

    def test_capability_tie_is_ambiguous_never_a_guess(
            self, sentinel_cli: str, tmp_path: Path):
        # "merge operations" hits lakehouse-operation AND lakehouse-compat
        # with the same token score — the router names the tie instead of
        # picking one.
        payload = plan(
            "databricks diagnostics delta lake merge operations",
            workspace=tmp_path,
            **_sentinel_injections(sentinel_cli),
        )
        assert payload["status"] == "ambiguous"
        assert payload["picks"] == []
        assert any(r["code"] == "insufficient-evidence"
                   for r in payload["refusals"])

    def test_no_intent_match_is_unavailable(self, doctor_cli: str,
                                            tmp_path: Path):
        payload = plan(
            "refactor the billing microservice",
            workspace=tmp_path,
            **_doctor_injections(doctor_cli),
        )
        assert payload["status"] == "unavailable"
        assert payload["picks"] == []
        assert payload["unknowns"]
