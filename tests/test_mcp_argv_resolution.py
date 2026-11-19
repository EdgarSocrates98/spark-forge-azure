"""Managed MCP launchers do not depend on the host's PATH."""
import dataclasses
import sys

from sparkforge_azure.distribution.hosts import mcp_entry
from sparkforge_azure.install import service


def test_interpreter_fallback(monkeypatch):
    monkeypatch.setattr(service, "_installation_manifest", lambda: {})
    monkeypatch.setattr(service.shutil, "which", lambda _: None)
    expected = (sys.executable, "-m", "sparkforge_azure", "mcp", "serve")
    assert service._spec().mcp_command == expected
    assert mcp_entry() == {"command": expected[0], "args": list(expected[1:])}
    assert mcp_entry(profile="balanced")["args"] == [*expected[1:], "--compact"]


def test_registered_shim_and_no_mcp(monkeypatch, tmp_path):
    shim = str(tmp_path / "sparkforge-azure")
    monkeypatch.setattr(service, "_installation_manifest", lambda: {"cli": {"shim": shim}})
    spec = service._spec()
    assert spec.mcp_command == (shim, "mcp", "serve")
    assert service._resolved_mcp_command(dataclasses.replace(spec, mcp_command=())) is None


def test_relative_shim_is_not_used(monkeypatch):
    monkeypatch.setattr(service, "_installation_manifest", lambda: {"cli": {"shim": "relative"}})
    assert service._spec().mcp_command[:3] == (sys.executable, "-m", "sparkforge_azure")
