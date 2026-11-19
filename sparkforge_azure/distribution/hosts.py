"""Supported agent hosts and their portable integration shape (spec §65–§79).

A host is declared, not probed deeply: ``detect_hosts`` reports
``available`` when the host's CLI is on ``PATH``, ``unavailable`` when it is
not, and never fails on absence (§76–§77). ``unproven`` marks hosts whose
end-to-end integration is declared but not yet verified on this platform;
``unsupported`` is reserved for hosts with no viable config surface.

Integration is *managed*: we only ever write the ``sparkforge-azure`` key of
``.mcp.json`` (Claude project scope) or a delimited managed block in files we
own, and every write is recorded in the managed ledger for detach (§70–§71).
The MCP entry references the installed ``sparkforge-azure`` binary — never a
checkout path (§74–§75).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Literal

HostStatus = Literal["available", "unavailable", "unsupported", "unproven"]

MCP_SERVER_NAME = "sparkforge-azure"
MCP_COMMAND = "sparkforge-azure"
MCP_ARGS = ("mcp", "serve")


@dataclass(frozen=True, slots=True)
class HostSpec:
    name: str
    executable: str
    project_config: str
    config_format: Literal["json"]
    supports_mcp: bool
    verified: bool

    @property
    def managed_key(self) -> str:
        return f"mcpServers.{MCP_SERVER_NAME}"


#: Hosts the lifecycle knows how to describe. Order is display order.
HOSTS: tuple[HostSpec, ...] = (
    HostSpec("claude", "claude", ".mcp.json", "json", True, True),
    HostSpec("devin", "devin", ".mcp.json", "json", True, True),
    HostSpec("codex", "codex", ".mcp.json", "json", True, False),
)


def mcp_entry(*, profile: str | None = None) -> dict[str, object]:
    """The ``mcpServers.sparkforge-azure`` value — installed binary only.

    ``profile`` selects the MCP argv for the Context Gateway execution
    profile (install-2.1): ``economy``/``balanced`` publish the compact
    read-only catalog (``mcp serve --compact``); ``deep``/None keeps the
    full catalog. Unknown profiles are a named error, never a guess."""
    if profile not in (None, "economy", "balanced", "deep"):
        raise ValueError(f"unknown Gateway profile: {profile!r}")
    from sparkforge_azure.install.service import _spec

    argv = _spec().mcp_command
    args = list(argv[1:])
    if profile in ("economy", "balanced"):
        args.append("--compact")
    return {"command": argv[0], "args": args}


def detect_hosts(env_path: str | None = None) -> tuple[dict[str, object], ...]:
    """Detect declared hosts without failing on absence (§76)."""
    out: list[dict[str, object]] = []
    for spec in HOSTS:
        found = shutil.which(spec.executable, path=env_path)
        if not found:
            status: HostStatus = "unavailable"
        elif spec.verified:
            status = "available"
        else:
            status = "unproven"
        out.append(
            {
                "name": spec.name,
                "status": status,
                "executable": found or spec.executable,
                "supports_mcp": spec.supports_mcp,
                "project_config": spec.project_config,
            }
        )
    return tuple(out)


def host_names() -> tuple[str, ...]:
    return tuple(spec.name for spec in HOSTS)


__all__ = [
    "HOSTS",
    "MCP_ARGS",
    "MCP_COMMAND",
    "MCP_SERVER_NAME",
    "HostSpec",
    "HostStatus",
    "detect_hosts",
    "host_names",
    "mcp_entry",
]
