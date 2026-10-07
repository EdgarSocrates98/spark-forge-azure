"""Valida a base `knowledge/` inteira e imprime um resumo JSON.

Checa: contrato de front matter (ids, enums, datas, fontes, related), matrizes
com fonte por celula, `query_expansion.yaml` (alvos resolvem para id ou
dominio) e se `INDEX.md` lista exatamente as entradas. Frescor e reportado;
so vira violacao com `--strict-freshness`.

Uso:
    python scripts/check_knowledge.py [--root knowledge] [--today 2026-10-06]
                                      [--max-age-days 90] [--strict-freshness]
                                      [--write-index]

Sai com 1 em qualquer violacao; 2 se a raiz for invalida ou um subcaminho escapar dela.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparkforge_azure.knowledgebase.expansion import (  # noqa: E402
    ExpansionError,
    load_rules,
    validate_targets,
)
from sparkforge_azure.knowledgebase.freshness import freshness_report  # noqa: E402
from sparkforge_azure.knowledgebase.matrices import load_matrices  # noqa: E402
from sparkforge_azure.knowledgebase.metadata import KnowledgeEntry, load_entries  # noqa: E402
from sparkforge_azure.paths import resolve_within  # noqa: E402


class RootError(Exception):
    """Raiz invalida ou subcaminho que escapa dela (sai com 2)."""


def sub(root: Path, relative: str) -> Path:
    safe = resolve_within(root, relative)
    if safe is None:
        raise RootError(f"{relative} escapa da raiz {root}")
    return safe

INDEX_ROW = re.compile(
    r"^\|\s*`?([a-z0-9.\-]+)`?\s*\|\s*`?([^|`]+?)`?\s*\|"
    r"\s*([a-z\-]+)\s*\|\s*([A-Z]+)\s*\|"
)
MIN_LINES, MAX_LINES = 60, 200


def render_index(entries: list[KnowledgeEntry]) -> str:
    lines = [
        "# Indice da base de conhecimento Azure",
        "",
        "Gerado por `python scripts/check_knowledge.py --write-index`. Nao edite a mao:",
        "o check falha se esta tabela divergir do front matter dos documentos.",
        "",
        "Contrato de metadados: `sparkforge_azure/knowledgebase/metadata.py`.",
        "Matrizes com fonte por celula: `knowledge/matrices/*.yaml`.",
        "Expansao deterministica de consulta: `knowledge/query_expansion.yaml`.",
        "",
        "| id | path | domain | status |",
        "|---|---|---|---|",
    ]
    for entry in sorted(entries, key=lambda e: e.id):
        lines.append(f"| `{entry.id}` | `{entry.path}` | {entry.domain} | {entry.status} |")
    return "\n".join(lines) + "\n"


def check_index(root: Path, entries: list[KnowledgeEntry]) -> list[str]:
    index = sub(root, "INDEX.md")
    if not index.is_file():
        return ["INDEX.md ausente (rode com --write-index)"]
    listed: dict[str, tuple[str, str, str]] = {}
    for line in index.read_text(encoding="utf-8").splitlines():
        match = INDEX_ROW.match(line)
        if match and match.group(1) != "id":
            listed[match.group(1)] = (match.group(2), match.group(3), match.group(4))
    errors = []
    expected = {e.id: (e.path, e.domain, e.status) for e in entries}
    for entry_id, row in expected.items():
        if entry_id not in listed:
            errors.append(f"INDEX.md: falta {entry_id}")
        elif listed[entry_id] != row:
            errors.append(f"INDEX.md: linha de {entry_id} diverge {listed[entry_id]} != {row}")
    for entry_id in listed:
        if entry_id not in expected:
            errors.append(f"INDEX.md: lista id inexistente {entry_id}")
    return errors


def line_warnings(root: Path, entries: list[KnowledgeEntry]) -> list[str]:
    warnings = []
    for entry in entries:
        count = len(sub(root, entry.path).read_bytes().splitlines())
        if not MIN_LINES <= count <= MAX_LINES:
            warnings.append(f"{entry.path}: {count} linhas (alvo {MIN_LINES}-{MAX_LINES})")
    return warnings


def run(argv: list[str] | None = None) -> tuple[int, dict]:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT / "knowledge")
    parser.add_argument("--today", type=date.fromisoformat, default=None)
    parser.add_argument("--max-age-days", type=int, default=90)
    parser.add_argument("--strict-freshness", action="store_true")
    parser.add_argument("--write-index", action="store_true")
    args = parser.parse_args(argv)
    root: Path = args.root.expanduser().resolve()
    if not root.is_dir():
        raise RootError(f"--root nao e diretorio: {root}")
    today = args.today or date.today()

    entries, violations = load_entries(root)
    matrices, matrix_errors = load_matrices(sub(root, "matrices"))
    violations += matrix_errors

    expansion_terms = 0
    expansion_path = sub(root, "query_expansion.yaml")
    if expansion_path.is_file():
        try:
            rules = load_rules(expansion_path)
            expansion_terms = len(rules)
            violations += validate_targets(rules, (e.id for e in entries))
        except ExpansionError as exc:
            violations += exc.errors
    else:
        violations.append("query_expansion.yaml ausente")

    if args.write_index and entries:
        sub(root, "INDEX.md").write_text(render_index(entries), encoding="utf-8", newline="\n")
    violations += check_index(root, entries)

    report = freshness_report(entries, today, args.max_age_days)
    if args.strict_freshness:
        violations += [f"frescor: {i} nao esta VERIFIED" for i in report["not_fresh"]]

    summary = {
        "ok": not violations,
        "root": root.as_posix(),
        "entries": len(entries),
        "domains": sorted({e.domain for e in entries}),
        "preview_entries": sorted(e.id for e in entries if e.preview),
        "matrices": sorted(matrices),
        "expansion_terms": expansion_terms,
        "freshness": {"today": report["today"], "counts": report["counts"],
                      "not_fresh": report["not_fresh"]},
        "warnings": line_warnings(root, entries),
        "violations": violations,
    }
    return (0 if not violations else 1), summary


def main(argv: list[str] | None = None) -> int:
    try:
        code, summary = run(argv)
    except RootError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
