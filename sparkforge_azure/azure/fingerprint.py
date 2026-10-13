"""Databricks/ADLS environment fingerprint.

Espelho de `fabric.fingerprint`: a fingerprint de ambiente e o eixo que
impede reuso de memoria/relatorio entre ambientes. Para Databricks os
eixos de identidade sao tenant / subscription / workspace / metastore /
storage account — vindos dos facts `environment.scope` mais o alvo e o
compute do caso. Eixo ausente fica ausente, nunca inventado.

Convergencia cross-vertical (prompt_evo_cycle6 §9, audit W0): fabric,
stream e migration ja emitem `environment_fingerprint` no resultado;
databricks era o unico vertical sem — a matriz registrou a divergencia.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def azure_fingerprint(case: Mapping[str, Any], facts: list[Any]) -> dict[str, Any]:
    """Fingerprint deterministico de ambiente para um caso Databricks."""
    axes: dict[str, str] = {}
    for f in facts:
        kind = getattr(f, "kind", None) or (
            f.get("kind") if isinstance(f, Mapping) else None
        )
        if kind != "environment.scope":
            continue
        attrs = getattr(f, "attrs", None) or (
            f.get("attrs") if isinstance(f, Mapping) else {}
        )
        key, val = str(attrs.get("key")), str(attrs.get("value"))
        # Primeiro escritor vence por eixo — conflito real e reportado por
        # SF-ACC-013, nunca resolvido aqui.
        if key and val:
            axes.setdefault(key, val)
    compute = case.get("compute") or {}
    target = case.get("target") or {}
    for key, value in (
        ("workspace_id", compute.get("workspace_id")),
        ("compute_type", compute.get("type")),
        ("metastore_id", target.get("metastore_id")),
        ("target_table", target.get("table")),
        ("storage_account", _storage_account(target.get("url"))),
    ):
        if value:
            axes.setdefault(key, str(value))
    return {
        "axes": axes,
        "axis_order": sorted(axes),
        "complete_axes": sorted(
            a for a in ("tenant_id", "workspace_id") if a in axes
        ),
    }


def _storage_account(url: Any) -> str:
    """`abfss://container@ACCOUNT.dfs.core.windows.net/...` -> `ACCOUNT`."""
    if not isinstance(url, str) or "@" not in url:
        return ""
    host = url.split("@", 1)[1].split("/", 1)[0]
    return host.split(".", 1)[0]


__all__ = ["azure_fingerprint"]
