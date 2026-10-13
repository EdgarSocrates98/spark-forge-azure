"""Scoped knowledge compiler for the access vertical (prompt 151-152).

``knowledge/packs.yaml`` declares the minimum packs for the Databricks /
Unity Catalog / ADLS access vertical.  ``compile_access_knowledge`` maps a
``failure_layer`` to the packs that cover it and selects entries only from
those domains (plus ``crosscut_domains`` such as ``governance``).  A UC
failure therefore never loads fabric/synapse/adf material — the excluded
domains are returned so callers can prove the scope.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.knowledgebase.loader import KnowledgeBase

PACKS_FILE = "packs.yaml"


def load_packs(root: Path | None = None) -> dict[str, Any]:
    """Parse ``knowledge/packs.yaml``; missing file → empty manifest."""
    kb_root = root or KnowledgeBase().root
    path = Path(kb_root) / PACKS_FILE
    if not path.is_file():
        return {"schema_version": 0, "crosscut_domains": [], "packs": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    packs = data.get("packs") or {}
    return {
        "schema_version": data.get("schema_version", 0),
        "crosscut_domains": list(data.get("crosscut_domains") or []),
        "packs": {
            name: {
                "vertical": str(spec.get("vertical") or ""),
                "purpose": str(spec.get("purpose") or ""),
                "domains": list(spec.get("domains") or []),
                "failure_layers": list(spec.get("failure_layers") or []),
            }
            for name, spec in packs.items()
            if isinstance(spec, dict)
        },
    }


def vertical_domains(root: Path | None = None) -> set[str]:
    """Union of every vertical-pack domain plus the crosscut domains."""
    manifest = load_packs(root)
    domains = set(manifest["crosscut_domains"])
    for spec in manifest["packs"].values():
        domains.update(spec["domains"])
    return domains


def packs_for_layer(
    failure_layer: str | None,
    root: Path | None = None,
    *,
    vertical: str | None = None,
) -> list[str]:
    """Pack names covering ``failure_layer``; unresolved → every pack of the
    calling vertical (``vertical``) — never the other vertical's packs.

    ``vertical=None`` keeps the historical behavior (all packs)."""
    manifest = load_packs(root)
    if not failure_layer or failure_layer == "unresolved":
        return sorted(
            name for name, spec in manifest["packs"].items()
            if vertical is None or spec["vertical"] == vertical)
    matched = [
        name
        for name, spec in manifest["packs"].items()
        if failure_layer in spec["failure_layers"]
        and (vertical is None or spec["vertical"] == vertical)
    ]
    return sorted(matched)


def compile_access_knowledge(
    failure_layer: str | None,
    terms: str | list[str],
    *,
    root: Path | None = None,
    limit: int = 8,
    vertical: str | None = None,
) -> dict[str, Any]:
    """Select knowledge entries scoped to the packs covering ``failure_layer``.

    Returns the selected entry ids (metadata only — bodies stay on disk),
    the pack/domain scope used, and ``excluded_domains`` as proof that
    unrelated domains (fabric, synapse, adf, ...) were not loaded.
    ``vertical`` restricts the pack set — an unresolved Fabric case never
    pulls access packs and vice-versa (same layer name in both verticals
    resolves to the caller's vertical, e.g. ``delta_perf``).
    """
    kb = KnowledgeBase(root)
    manifest = load_packs(kb.root)
    pack_names = packs_for_layer(failure_layer, kb.root, vertical=vertical)
    scope = set(manifest["crosscut_domains"])
    for name in pack_names:
        scope.update(manifest["packs"][name]["domains"])
    entries = kb.select(terms, domains=scope, limit=limit) if scope else []
    all_domains = {entry.domain for entry in kb.load_index().values()}
    return {
        "failure_layer": failure_layer,
        "vertical": vertical,
        "packs": pack_names,
        "domains": sorted(scope),
        "entries": entries,
        "excluded_domains": sorted(all_domains - scope),
    }


__all__ = [
    "PACKS_FILE",
    "compile_access_knowledge",
    "load_packs",
    "packs_for_layer",
    "vertical_domains",
]
