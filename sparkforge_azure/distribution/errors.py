"""Structured failure kinds for the portable lifecycle (spec section 178).

Portable commands never leak a raw traceback as product output (section 179):
a failure is a refusal document ``{"status": "refused", "error": {...}}`` that
the CLI layer serializes. ``PortableError`` carries the closed vocabulary of
``kind`` values plus ``detail`` and an ``unlock`` telling the operator the
smallest action that unblocks the command.
"""

from __future__ import annotations

from typing import Any

#: Closed failure vocabulary (prompt_evo_portable.md section 178). New kinds
#: are added here, never invented at the call site.
FAILURE_KINDS: frozenset[str] = frozenset(
    {
        "workspace_not_found",
        "project_not_initialized",
        "identity_collision",
        "manifest_invalid",
        "dependency_cycle",
        "managed_asset_drift",
        "host_unavailable",
        "config_invalid",
        "path_outside_root",
        "unsupported",
    }
)


class PortableError(Exception):
    """A named, structured refusal inside the portable lifecycle."""

    def __init__(self, kind: str, detail: str, *, unlock: str | None = None) -> None:
        if kind not in FAILURE_KINDS:
            raise ValueError(f"unknown failure kind: {kind!r}")
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
        self.unlock = unlock

    def to_error(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": self.kind, "detail": self.detail}
        if self.unlock:
            out["unlock"] = self.unlock
        return out


def refused_document(exc: PortableError) -> dict[str, Any]:
    """The JSON document a refused portable command emits."""
    return {"status": "refused", "error": exc.to_error()}


__all__ = ["FAILURE_KINDS", "PortableError", "refused_document"]
