"""Failure taxonomy for collectors.

A collector that cannot observe produces an ``unresolved`` entry carrying a
``failure_class`` -- never a fabricated "resource absent" fact
(unknown != zero, section 77).
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class FailureClass(str, Enum):
    AUTHENTICATION = "authentication"      # 401 / invalid token
    AUTHORIZATION = "authorization"        # 403 / forbidden
    NETWORK = "network"                    # DNS, TLS, timeout, unreachable
    RATE_LIMIT = "rate_limit"              # 429 / throttled
    UNSUPPORTED = "unsupported"            # missing SDK / provider not covered
    INVALID_INPUT = "invalid_input"        # malformed export / bad arguments
    UNKNOWN = "unknown"                    # anything else; still unresolved


_STATUS_MAP = {
    401: FailureClass.AUTHENTICATION,
    403: FailureClass.AUTHORIZATION,
    429: FailureClass.RATE_LIMIT,
}


def classify(exc: BaseException) -> FailureClass:
    """Map an exception to a FailureClass without inspecting secrets."""
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    try:
        if status is not None and int(status) in _STATUS_MAP:
            return _STATUS_MAP[int(status)]
    except (TypeError, ValueError):
        pass
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return FailureClass.NETWORK
    name = type(exc).__name__.lower()
    if "unavailable" in name or "notfound" in name and "module" in name:
        return FailureClass.UNSUPPORTED
    if isinstance(exc, ImportError | ModuleNotFoundError):
        return FailureClass.UNSUPPORTED
    if isinstance(exc, ValueError):
        return FailureClass.INVALID_INPUT
    return FailureClass.UNKNOWN


def unresolved(what: str, exc: BaseException, *, source: str) -> dict[str, Any]:
    """Build the unresolved entry a CollectorResult carries on failure."""
    return {
        "what": what,
        "source": source,
        "failure_class": classify(exc).value,
        "error_type": type(exc).__name__,
        "detail": str(exc)[:200],
    }


__all__ = ["FailureClass", "classify", "unresolved"]
