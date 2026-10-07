"""Offline bundle (sections 82-84): portable, redacted evidence for offline exchange.

Content: facts, findings, rules (only those cited), knowledge slice (front matter of
the cited/selected entries), graph slice (bounded), receipts, redacted config,
runtime matrices, evidence refs.  Never included: secrets, tokens, credentials,
connection strings or raw cloud dumps -- every JSON document is redacted and then
must pass ``assert_clean`` before it is written; ``verify_bundle`` re-scans.

Layout: a directory with one JSON per part plus ``MANIFEST.json`` (sha256 per file).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure import __version__
from sparkforge_azure.collectors.redact import RedactionReport, assert_clean, redact

PARTS = ("facts", "findings", "rules", "knowledge", "graph", "receipts", "config",
         "runtime_matrix", "evidence_refs")
FORBIDDEN_NAMES = ("raw", ".raw.json")


class BundleError(ValueError):
    pass


def _dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def _load_json(path: Path) -> Any:
    if any(n in path.name for n in FORBIDDEN_NAMES):
        raise BundleError(f"raw cloud dumps are never bundled: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _cited_rules(findings: list[Mapping[str, Any]], catalog_dir: Path | None) -> list[dict]:
    ids = sorted({str(f.get("rule_id")) for f in findings if f.get("rule_id")})
    if not catalog_dir or not catalog_dir.is_dir():
        return [{"id": i, "definition": None} for i in ids]
    import yaml

    found: dict[str, Any] = {}
    for p in sorted(catalog_dir.glob("*.yaml")):
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        rules = doc.get("rules", []) if isinstance(doc, dict) else doc if isinstance(doc, list) \
            else []
        for r in rules or []:
            if isinstance(r, dict) and r.get("id") in ids:
                found[r["id"]] = r
    return [{"id": i, "definition": found.get(i)} for i in ids]


def _knowledge_slice(knowledge_root: Path | None, ids: Iterable[str]) -> list[dict]:
    wanted = set(ids)
    if not wanted or not knowledge_root or not knowledge_root.is_dir():
        return []
    from sparkforge_azure.knowledgebase.metadata import load_entries

    entries, _ = load_entries(knowledge_root)
    out = []
    for e in entries:
        if e.id in wanted:
            out.append({"id": e.id, "path": e.path, "domain": e.domain, "status": e.status,
                        "verified_at": str(e.verified_at), "authority": e.authority,
                        "sources": [s.url for s in e.sources]})
    return sorted(out, key=lambda x: x["id"])


def build_bundle(
    out_dir: str | Path,
    *,
    facts: str | Path | None = None,
    findings: str | Path | None = None,
    graph: str | Path | None = None,
    graph_seeds: Iterable[str] = (),
    graph_budget: int = 60,
    receipts: Iterable[str | Path] = (),
    config: str | Path | None = None,
    knowledge_root: str | Path | None = None,
    knowledge_ids: Iterable[str] = (),
    catalog_dir: str | Path | None = None,
    matrices_dir: str | Path | None = None,
) -> dict[str, Any]:
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise BundleError(f"output directory not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    report = RedactionReport()
    parts: dict[str, Any] = {}

    facts_list = _load_json(Path(facts)) if facts else []
    findings_list = _load_json(Path(findings)) if findings else []
    if isinstance(facts_list, Mapping):
        facts_list = facts_list.get("facts", [])
    if isinstance(findings_list, Mapping):
        findings_list = findings_list.get("findings", [])
    parts["facts"] = facts_list
    parts["findings"] = findings_list
    parts["rules"] = _cited_rules(findings_list, Path(catalog_dir) if catalog_dir else None)
    kids = set(knowledge_ids)
    for f in findings_list:
        for s in f.get("sources") or []:
            if isinstance(s, Mapping) and s.get("knowledge_id"):
                kids.add(str(s["knowledge_id"]))
    parts["knowledge"] = _knowledge_slice(Path(knowledge_root) if knowledge_root else None, kids)
    if graph:
        from sparkforge_azure.graph.query import slice_graph
        from sparkforge_azure.graph.store import load_graph

        g = load_graph(graph)
        seeds = list(graph_seeds)
        if seeds:
            sub, truncated = slice_graph(g, seeds, budget=graph_budget)
            parts["graph"] = {"seeds": seeds, "truncated": truncated, "graph": sub.to_dict()}
        else:
            # A whole workspace graph is not a minimal slice: require explicit seeds.
            parts["graph"] = {"omitted": "no graph seeds given"}
    else:
        parts["graph"] = None
    parts["receipts"] = [_load_json(Path(r)) for r in receipts]
    parts["config"] = _load_json(Path(config)) if config else None
    mats = []
    if matrices_dir and Path(matrices_dir).is_dir():
        import yaml

        for p in sorted(Path(matrices_dir).glob("*.yaml")):
            mats.append(yaml.safe_load(p.read_text(encoding="utf-8")))
    parts["runtime_matrix"] = mats
    parts["evidence_refs"] = sorted({str(e) for f in findings_list for e in f.get("evidence", [])})

    manifest: dict[str, Any] = {"schema_version": 1, "engine": "spark-forge-azure",
                                "version": __version__, "files": {}}
    for name in PARTS:
        clean = redact(parts[name], report=report, hash_principals=False)
        assert_clean(clean)
        text = _dump(clean)
        (out / f"{name}.json").write_text(text, encoding="utf-8", newline="\n")
        manifest["files"][f"{name}.json"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    manifest["redaction"] = report.to_dict()
    (out / "MANIFEST.json").write_text(_dump(manifest), encoding="utf-8", newline="\n")
    return {"status": "ok", "path": out.as_posix(), "files": sorted(manifest["files"]),
            "redactions": manifest["redaction"]}


def verify_bundle(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    problems: list[str] = []
    try:
        manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "fail", "problems": [f"manifest unreadable: {exc}"]}
    listed = set(manifest.get("files", {}))
    present = {p.name for p in root.iterdir() if p.is_file() and p.name != "MANIFEST.json"}
    problems += [f"unlisted file: {n}" for n in sorted(present - listed)]
    for name, digest in sorted(manifest.get("files", {}).items()):
        f = root / name
        if not f.is_file():
            problems.append(f"missing: {name}")
            continue
        text = f.read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
            problems.append(f"hash mismatch: {name}")
        try:
            assert_clean(json.loads(text))
        except ValueError as exc:
            problems.append(f"{name}: {exc}")
    return {"status": "ok" if not problems else "fail", "problems": problems}
