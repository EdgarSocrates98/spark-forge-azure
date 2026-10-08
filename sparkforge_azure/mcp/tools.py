"""Single tool registry shared by MCP and the surface lock.

Every tool declares its risk profile (section 153).  A tool whose risk is not
declared -- or declares a dimension this module does not know -- is DENIED at
authorization time (section 154).  Cloud writes are denied unless the caller
passes an explicit, human-gated authorization (sections 208-209).

Handlers are plain functions ``handler(arguments: dict) -> dict``.  They return
JSON-serialisable data; the MCP envelope wraps it as ``authority=data_only``
(section 125): tool output is data, never instruction.

Tools register from their domain modules via ``@tool(...)``.  The list of
modules that own tools is closed (``TOOL_MODULES``) so the surface is
deterministic and ``load_all()`` is the only import side effect.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

RISK_DIMENSIONS = (
    "read_only",
    "local_write",
    "cloud_read",
    "cloud_write",
    "security_impact",
    "production_impact",
)

Handler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class ToolRisk:
    read_only: bool = False
    local_write: bool = False
    cloud_read: bool = False
    cloud_write: bool = False
    security_impact: bool = False
    production_impact: bool = False

    def __post_init__(self) -> None:
        if self.read_only and (self.local_write or self.cloud_write):
            raise ValueError("read_only tool cannot also write")
        if not any(getattr(self, d) for d in RISK_DIMENSIONS):
            raise ValueError("risk must declare at least one dimension")

    def to_dict(self) -> dict[str, bool]:
        return {d: getattr(self, d) for d in RISK_DIMENSIONS}

    @property
    def mcp_annotations(self) -> dict[str, bool]:
        """MCP ToolAnnotations hints (spec 2025-11-25 / 2026-07-28)."""
        return {
            "readOnlyHint": self.read_only,
            "destructiveHint": self.cloud_write or self.production_impact,
            "idempotentHint": self.read_only,
            "openWorldHint": self.cloud_read or self.cloud_write,
        }


READ_ONLY = ToolRisk(read_only=True)
LOCAL_WRITE = ToolRisk(local_write=True)
CLOUD_READ = ToolRisk(read_only=True, cloud_read=True)


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Mapping[str, Any]
    handler: Handler
    risk: ToolRisk
    domain: str
    compact: bool = False
    output_schema: Mapping[str, Any] | None = None
    tags: tuple[str, ...] = field(default=())

    def declaration(self) -> dict[str, Any]:
        """What ``tools/list`` returns. Deterministic; no handler identity."""
        out: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": dict(self.input_schema),
            "annotations": self.risk.mcp_annotations,
            "_meta": {"sparkforge_azure/risk": self.risk.to_dict(), "domain": self.domain},
        }
        if self.output_schema is not None:
            out["outputSchema"] = dict(self.output_schema)
        return out


TOOLS: dict[str, ToolSpec] = {}

# Closed list of modules that register tools. Adding a tool module is a surface
# change and shows up in the surface lock.
TOOL_MODULES: tuple[str, ...] = (
    "sparkforge_azure.mcp.builtin_tools",
    "sparkforge_azure.mcp.tokensave_tools",
    "sparkforge_azure.mcp.governance_tools",
    "sparkforge_azure.mcp.graph_tools",
)


def tool(
    name: str,
    *,
    description: str,
    input_schema: Mapping[str, Any],
    risk: ToolRisk,
    domain: str,
    compact: bool = False,
    output_schema: Mapping[str, Any] | None = None,
    tags: tuple[str, ...] = (),
) -> Callable[[Handler], Handler]:
    if not name.startswith("sfa_"):
        raise ValueError(f"tool {name!r} must use the sfa_ prefix (multi-forge RFC)")

    def deco(fn: Handler) -> Handler:
        if name in TOOLS and TOOLS[name].handler is not fn:
            raise ValueError(f"duplicate tool {name}")
        TOOLS[name] = ToolSpec(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=fn,
            risk=risk,
            domain=domain,
            compact=compact,
            output_schema=output_schema,
            tags=tuple(tags),
        )
        return fn

    return deco


def load_all() -> dict[str, ToolSpec]:
    for mod in TOOL_MODULES:
        importlib.import_module(mod)
    return dict(sorted(TOOLS.items()))


@dataclass(frozen=True, slots=True)
class Authorization:
    allowed: bool
    reason: str


def authorize(
    spec: ToolSpec | None,
    *,
    allow_local_write: bool = True,
    cloud_read_enabled: bool = False,
    cloud_write_grant: str | None = None,
) -> Authorization:
    """Default-deny gate. ``cloud_write_grant`` must be an explicit human grant id."""
    if spec is None:
        return Authorization(False, "unknown tool: DENY")
    if not isinstance(spec.risk, ToolRisk):
        return Authorization(False, "undeclared risk: DENY")
    risk = spec.risk
    if risk.cloud_write or risk.production_impact:
        if not cloud_write_grant:
            return Authorization(False, "cloud mutation requires explicit human grant: DENY")
    if risk.cloud_read and not cloud_read_enabled:
        return Authorization(False, "cloud read not enabled (offline mode): DENY")
    if risk.local_write and not allow_local_write:
        return Authorization(False, "local write disabled: DENY")
    return Authorization(True, "allowed")


def compact_catalog() -> dict[str, dict[str, Any]]:
    """Compact mode (section 151): the minimal set agents should see by default."""
    return {n: s.declaration() for n, s in load_all().items() if s.compact}


def full_catalog() -> dict[str, dict[str, Any]]:
    return {n: s.declaration() for n, s in load_all().items()}
