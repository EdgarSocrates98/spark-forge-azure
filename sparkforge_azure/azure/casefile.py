"""Case bundle loading for the access diagnostic pipeline.

A bundle is a directory::

    case.yaml          -- name, principal, operation, target, compute, expect?
    unity_catalog.{json,yaml}
    rbac.json          -- {"assignments": [...]}
    adls.json          -- {"account_id", "hns", "acl": {path: {...}}}
    network.json       -- storage firewall / private endpoint posture
    entra.json         -- {"principals": {id: {...}}}
    notebooks/         -- optional .py/.sql/.ipynb scanned by notebook_scan

Everything is data.  ``to_scenario`` produces the dict shape that
``governance.diagnose`` already validates.  Notebook discovery goes through
``facts.scan.varrer_source_files`` so a hostile bundle cannot escape the
directory with a symlink or smuggle in a credential-named file unnoticed --
skipped paths land on ``CaseBundle.skipped`` as evidence gaps.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.adapters.upstream import UPSTREAM_ARTIFACT, UpstreamError, read_upstream_facts
from sparkforge_azure.facts.scan import varrer_source_files

ARTIFACT_NAMES = ("unity_catalog", "rbac", "adls", "network", "entra", "compute")
_SUFFIXES = (".json", ".yaml", ".yml")
NOTEBOOK_SUFFIXES = frozenset({".py", ".sql", ".ipynb"})


class CaseError(ValueError):
    """Bundle inválido ou ilegível. Surfaces traduzem para exit 2 / erro MCP."""


@dataclass
class CaseBundle:
    """Loaded bundle: case dict, artifact payloads, and the file each came from."""

    root: Path
    case: dict[str, Any]
    artifacts: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    notebook_files: list[Path] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    upstream_facts: list[dict[str, Any]] = field(default_factory=list)

    def to_scenario(self) -> dict[str, Any]:
        """Build the Scenario.from_dict input from the bundle."""
        case = self.case
        scenario: dict[str, Any] = {
            "name": case.get("name", self.root.name),
            "principal": case["principal"],
            "operation": case["operation"],
            "target": case["target"],
        }
        compute = dict(case.get("compute") or {})
        compute.update(self.artifacts.get("compute") or {})
        if compute:
            scenario["compute"] = compute
        for name in ("unity_catalog", "rbac", "adls", "network", "entra"):
            if self.artifacts.get(name) is not None:
                scenario[name] = self.artifacts[name]
        return scenario


def _load_payload(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise CaseError(f"artifact unreadable: {path.name}") from exc
    try:
        if path.suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except ValueError as exc:
        raise CaseError(f"artifact is not valid {path.suffix}: {path.name}") from exc


def load_bundle(root: str | Path) -> CaseBundle:
    root = Path(root)
    if not root.is_dir():
        raise CaseError(f"bundle directory not found: {root}")
    case_file = next((root / f"case{s}" for s in _SUFFIXES if (root / f"case{s}").is_file()),
                     None)
    if case_file is None:
        raise CaseError(f"bundle missing case.yaml: {root}")
    case = _load_payload(case_file)
    if not isinstance(case, Mapping):
        raise CaseError("case.yaml must be a mapping")
    for key in ("principal", "operation", "target"):
        if key not in case:
            raise CaseError(f"case.yaml missing required key: {key}")
    bundle = CaseBundle(root=root, case=dict(case),
                        sources={"case": case_file.name})
    for name in ARTIFACT_NAMES:
        path = next((root / f"{name}{s}" for s in _SUFFIXES
                     if (root / f"{name}{s}").is_file()), None)
        if path is None:
            continue
        payload = _load_payload(path)
        if not isinstance(payload, Mapping):
            raise CaseError(f"{path.name} must be a mapping")
        bundle.artifacts[name] = dict(payload)
        bundle.sources[name] = path.name

    upstream_doc = root / UPSTREAM_ARTIFACT
    if upstream_doc.is_file():
        try:
            bundle.upstream_facts = read_upstream_facts(upstream_doc)
        except UpstreamError as exc:
            raise CaseError(str(exc)) from exc
        bundle.sources["upstream"] = upstream_doc.name
    nb_dir = root / "notebooks"
    if nb_dir.is_dir():
        varredura = varrer_source_files(nb_dir, "*")
        bundle.notebook_files = [p for p in varredura.arquivos
                                 if p.suffix.lower() in NOTEBOOK_SUFFIXES]
        bundle.skipped = [{"path": p.relativo, "reason": p.razao}
                          for p in varredura.pulos]
    return bundle


__all__ = ["ARTIFACT_NAMES", "CaseBundle", "CaseError", "load_bundle"]
