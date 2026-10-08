"""Collector recovery (prompt #121-125).

Maps a collector failure onto the agentic ``RecoveryPolicy`` taxonomy:

    authentication  -> security_refusal   (credentials are wrong; retry won't fix)
    authorization   -> policy_conflict    (escalate: missing permission)
    network         -> transient_host     (retry)
    rate_limit      -> transient_host     (retry — bounded by max_attempts)
    unsupported     -> provider_unavailable (retry, then replan to offline)
    invalid_input   -> invalid_input      (refuse)
    unknown         -> tool_failure       (replan)

Retry happens only for transient classes (#122).  When the policy says stop
and an offline export exists, the collector falls back to it with
``status: degraded`` and a receipt naming the fallback — no hidden fallback
(#124-125).  With no offline artifact the failure surfaces as ``unresolved``
carrying the ``failure_class``; a collector that cannot observe never
fabricates an "absent" fact.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sparkforge_azure.agentic.recovery import RecoveryPolicy
from sparkforge_azure.collectors import failure as cf

# Collector FailureClass -> agentic RecoveryPolicy FailureClass.
_TO_POLICY = {
    cf.FailureClass.AUTHENTICATION: "security_refusal",
    cf.FailureClass.AUTHORIZATION: "policy_conflict",
    cf.FailureClass.NETWORK: "transient_host",
    cf.FailureClass.RATE_LIMIT: "transient_host",
    cf.FailureClass.UNSUPPORTED: "provider_unavailable",
    cf.FailureClass.INVALID_INPUT: "invalid_input",
    cf.FailureClass.UNKNOWN: "tool_failure",
}

_TRANSIENT = {cf.FailureClass.NETWORK, cf.FailureClass.RATE_LIMIT,
              cf.FailureClass.UNSUPPORTED}


def _strategy_fingerprint(exc: BaseException, *, attempt: int) -> str:
    """Fingerprint per attempt for transient retries: retrying the same call
    *is* the strategy here — pinning the fingerprint would make the policy's
    repeated-strategy STOP fire before a legitimate bounded retry.  For
    terminal classes the fingerprint is irrelevant (they break out anyway).
    """
    import hashlib

    raw = f"{cf.classify(exc).value}:{type(exc).__name__}:{attempt}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def collect_with_recovery(
    collect_live: Callable[..., Any],
    *,
    kwargs: dict[str, Any] | None = None,
    offline_export: str | None = None,
    from_export: Callable[..., Any] | None = None,
    source: str,
    policy: RecoveryPolicy | None = None,
) -> dict[str, Any]:
    """Run ``collect_live(**kwargs)`` under the recovery policy.

    Returns ``{status, mode, result|export_result, decisions, unresolved,
    receipt}``.  ``status`` is ``ok`` (live), ``degraded`` (offline fallback,
    receipt required) or ``unresolved`` (no observation produced).
    """
    policy = policy or RecoveryPolicy()
    kwargs = dict(kwargs or {})
    decisions: list[dict[str, Any]] = []
    history: list[str] = []
    attempt = 0
    last_exc: BaseException | None = None
    while True:
        try:
            result = collect_live(**kwargs)
        except Exception as exc:  # noqa: BLE001 -- taxonomy, not suppression
            last_exc = exc
            klass = cf.classify(exc)
            fp = _strategy_fingerprint(exc, attempt=attempt)
            decision = policy.next(
                _TO_POLICY[klass], attempt=attempt,
                strategy_fingerprint=fp, history=history)
            decisions.append(decision.to_dict())
            history.append(fp)
            if decision.action == "retry" and klass in _TRANSIENT:
                attempt += 1
                continue
            break
        else:
            return {"status": "ok", "mode": "live", "result": result,
                    "decisions": decisions, "unresolved": [],
                    "receipt": {"attempts": attempt + 1, "fallback": None}}
    # Terminal: retry exhausted, refused, replan or escalate.
    assert last_exc is not None
    entry = cf.unresolved(source, last_exc, source=source)
    if offline_export and from_export is not None:
        try:
            export_result = from_export(offline_export)
        except Exception as exc2:  # noqa: BLE001
            entry["fallback_error"] = type(exc2).__name__
            return {"status": "unresolved", "mode": "none", "result": None,
                    "decisions": decisions, "unresolved": [entry],
                    "receipt": {"attempts": attempt + 1,
                                "fallback": "attempted_failed"}}
        return {
            "status": "degraded", "mode": "export", "result": export_result,
            "decisions": decisions, "unresolved": [entry],
            "receipt": {
                "attempts": attempt + 1,
                "fallback": {
                    "from": "live", "to": "offline_export",
                    "path": str(offline_export),
                    "failure_class": entry["failure_class"],
                },
            },
        }
    return {"status": "unresolved", "mode": "none", "result": None,
            "decisions": decisions, "unresolved": [entry],
            "receipt": {"attempts": attempt + 1, "fallback": "unavailable"}}


__all__ = ["collect_with_recovery"]
