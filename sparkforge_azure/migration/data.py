"""Data / metadata -> OneLake / Lakehouse strategy (SDD DATA_ONELAKE).

Each data asset gets a strategy from the closed set
{retain, shortcut, copy, hybrid} with decision-dimension evidence
(prompt §110-115).  Shortcut-first *when eligible* — never mandatory;
zero-copy is never zero-cost/zero-risk.
"""
from __future__ import annotations

from typing import Any

from sparkforge_azure.migration.model import DATA_STRATEGIES


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def recommend_data_strategy(facts: list[Any]) -> list[dict[str, Any]]:
    """One recommendation per storage path / table, with evidence."""
    recs: list[dict[str, Any]] = []
    retirement_paths = {
        str(f.subject.get("path"))
        for f in _facts(facts, "mig.adls_path")
        if f.attrs.get("retirement")}
    retirement_accounts = {
        str(f.subject.get("storage_account_id"))
        for f in _facts(facts, "mig.storage_account")
        if f.attrs.get("retirement")}
    for f in _facts(facts, "mig.adls_path"):
        path = str(f.subject.get("path"))
        fmt = str(f.attrs.get("format", "")).lower()
        account = path.split("/", 1)[0]
        retired = path in retirement_paths or account in retirement_accounts
        dims = {"format": fmt or "unknown",
                "source_retirement": bool(retired),
                "hns": None,
                "size_gb": f.attrs.get("size_gb")}
        if fmt == "delta" and not retired:
            strategy = "shortcut"
            why = ("Delta no ADLS elegivel a OneLake shortcut "
                   "(zero-copy candidato; schema sync automatico). "
                   "Shortcut-first quando apropriado, nunca mandatorio.")
        elif retired:
            strategy = "copy"
            why = ("retirement da fonte declarado — copiar para OneLake "
                   "remove dependencia do storage legado")
        elif fmt in {"parquet", "csv", "json"}:
            strategy = "hybrid"
            why = ("formato nao-Delta: files podem virar shortcut de Files/ "
                   "ou copia para tabelas gerenciadas — revisar consumidores")
        else:
            strategy = "retain"
            why = "evidencia insuficiente para zero-copy; manter e revisar"
        recs.append({"asset": path, "strategy": strategy,
                     "target_type": ("fabric_shortcut" if strategy
                                     == "shortcut" else
                                     "fabric_lakehouse" if strategy
                                     in {"copy", "hybrid"} else None),
                     "dimensions": dims, "evidence": [f.id],
                     "explanation": why})
    for t in _facts(facts, "mig.table"):
        loc = str(t.attrs.get("location") or "")
        fmt = str(t.attrs.get("format", "")).lower()
        managed = str(t.attrs.get("kind", "")).lower() == "managed"
        if managed and fmt == "delta":
            strategy, target = "copy", "fabric_lakehouse"
            why = ("tabela managed HMS: metadata+data migram; Delta no "
                   "lakehouse preserva catalogo")
        elif fmt == "delta":
            strategy, target = "shortcut", "fabric_shortcut"
            why = ("external Delta table: shortcut no lakehouse sem copiar "
                   "dados (avaliar latencia/egress)")
        else:
            strategy, target = "hybrid", None
            why = "formato nao-Delta: avaliar conversao a Delta ou copy"
        recs.append({"asset": str(t.subject.get("table")),
                     "strategy": strategy, "target_type": target,
                     "dimensions": {"format": fmt, "managed": managed,
                                    "location": loc},
                     "evidence": [t.id], "explanation": why})
    return recs


def hms_assessment(facts: list[Any]) -> dict[str, Any]:
    """Lake database / HMS metadata: managed vs external split (§118-123)."""
    dbs = _facts(facts, "mig.lake_database")
    tables = _facts(facts, "mig.table")
    managed = [t for t in tables
               if str(t.attrs.get("kind", "")).lower() == "managed"]
    external = [t for t in tables
                if str(t.attrs.get("kind", "")).lower() == "external"]
    return {
        "lake_databases": len(dbs),
        "managed_tables": len(managed),
        "external_tables": len(external),
        "managed_evidence": [t.id for t in managed],
        "external_evidence": [t.id for t in external],
        "note": ("lake database -> lakehouse/schema mapping; external "
                 "tables precisam de decisao de location (prompt §121-123)"),
    }


__all__ = ["DATA_STRATEGIES", "hms_assessment", "recommend_data_strategy"]
