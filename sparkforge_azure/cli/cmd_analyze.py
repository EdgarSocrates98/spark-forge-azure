"""``analyze pyspark``, ``judge`` e ``knowledge select`` — portas para motores existentes.

Os três verbos só expõem o que o pacote já faz (extrator AST PySpark, motor de
regras, packs de knowledge). Os demais ``analyze <kind>`` das skills continuam
planejados: não há extrator para eles e a CLI não finge que há.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sparkforge_azure.cli.main import CliError
from sparkforge_azure.paths import state_dir


def _anchor(path: Path) -> Path | None:
    """Raiz para ancorar o path relativo dos facts: cwd, se o alvo estiver dentro."""
    cwd = Path.cwd().resolve()
    return cwd if path.resolve().is_relative_to(cwd) else None


def _analyze_pyspark(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.facts.pyspark_ast import extract_path, extract_tree

    target = Path(args.path)
    if not target.exists():
        raise CliError(f"path not found: {target}")
    root = _anchor(target)
    if target.is_dir():
        facts = extract_tree(target.resolve(), repo_root=root)
    else:
        facts = extract_path(target.resolve(), repo_root=root)
    rows = [f.to_dict() for f in facts]
    out_path = None
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({"facts": rows}, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return {"status": "ok", "count": len(rows), "facts": rows,
            "out": out_path.as_posix() if out_path else None}


def _load_facts(path: Path) -> list[Any]:
    from sparkforge_azure.findings.models import Fact

    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError(f"cannot read facts: {exc}") from exc
    rows = (raw.get("facts") or raw.get("fact_list")) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise CliError("facts file must be a list, {'facts': [...]} or "
                       "a collector envelope with 'fact_list'")
    facts = []
    for row in rows:
        if not isinstance(row, dict) or "kind" not in row or "subject" not in row:
            raise CliError("every fact needs 'kind' and 'subject'")
        facts.append(Fact(
            kind=row["kind"], subject=row["subject"],
            measures=row.get("measures") or {}, attrs=row.get("attrs") or {},
            provenance=row.get("provenance") or {},
        ))
    return facts


def _runtime(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key or not value:
            raise CliError(f"--runtime expects key=value, got {pair!r}")
        out[key] = value
    return out


def _judge(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.rules.engine import judge
    from sparkforge_azure.rules.loader import CatalogError, load_catalog

    facts = _load_facts(Path(args.facts))
    try:
        rules = load_catalog()
    except CatalogError as exc:
        raise CliError(str(exc)) from exc
    findings, skipped = judge(facts, rules, _runtime(args.runtime), return_skipped=True)
    return {
        "status": "findings" if findings else "ok",
        "findings": [f.to_dict() for f in findings],
        "skipped": skipped,
        "fact_count": len(facts),
    }


def _knowledge_roots() -> list[Path]:
    # `knowledge_dir()` resolve env override -> raiz do repo -> `_data/knowledge`
    # no wheel; antes era `repo_root() or cwd`, que num pip install olhava para
    # `<cwd>/knowledge` e respondia "pack not found" (mesma classe de bug do
    # `fleet_root()` — §8.3).
    from sparkforge_azure.knowledge_ref import knowledge_dir

    base = knowledge_dir()
    return [base / "azure", base]


def _knowledge_select(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.codeintel.query_expansion import expand_query
    from sparkforge_azure.knowledge_engine.packs import PackRegistry

    cache = state_dir() / "knowledge-cache"
    for root in _knowledge_roots():
        registry = PackRegistry(root, cache_dir=cache)
        if any(d.domain == args.domain for d in registry.descriptors()):
            index = registry.load(args.domain)
            break
    else:
        raise CliError(f"knowledge pack not found: {args.domain}")
    if args.query:
        terms = tuple(t.casefold() for t in expand_query(args.query).terms)
        claims = index.search(terms, limit=args.limit)
    else:
        claims = index.claims[: args.limit]
    return {"status": "ok", "domain": args.domain,
            "claims": [c.to_dict() for c in claims]}


def register(sub: argparse._SubParsersAction) -> None:
    a = sub.add_parser("analyze", help="extract facts offline (only kinds with an extractor)")
    s = a.add_subparsers(dest="analyze_kind", metavar="<kind>")
    p = s.add_parser("pyspark", help="PySpark AST facts from a .py file or directory")
    p.add_argument("--path", required=True, help="file or directory to analyse")
    p.add_argument("--out", help="write {'facts': [...]} to this JSON file")
    p.set_defaults(func=_analyze_pyspark)

    j = sub.add_parser("judge", help="apply the versioned rule catalogue to facts")
    j.add_argument("--facts", required=True, help="facts JSON (list or {'facts': [...]})")
    j.add_argument("--runtime", action="append", default=[], metavar="KEY=VERSION",
                   help="runtime component version, repeatable (e.g. spark=3.5.0)")
    j.set_defaults(func=_judge)

    k = sub.add_parser("knowledge", help="dated knowledge packs")
    ks = k.add_subparsers(dest="knowledge_cmd", metavar="<op>")
    q = ks.add_parser("select", help="bounded claims from one knowledge pack")
    q.add_argument("--domain", required=True, help="pack dir under knowledge/azure or knowledge")
    q.add_argument("--query", help="terms to rank claims (omit = first claims)")
    q.add_argument("--limit", type=int, default=8)
    q.set_defaults(func=_knowledge_select)
