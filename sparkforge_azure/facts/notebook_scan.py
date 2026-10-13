"""Static scan of notebooks/code for Azure access patterns.

Recognizes ``abfss://`` paths, three-part Unity Catalog names, ``dbutils``
filesystem usage, table writes (``saveAsTable``/``table``/SQL) and Delta
operations (``MERGE``, ``OPTIMIZE``, ``VACUUM``, ``RESTORE``).  Everything is a
Fact anchored at file:line; the scanner never judges -- rules do.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sparkforge_azure.facts.scan import varrer_source_files
from sparkforge_azure.findings.models import Fact, sort_facts

ABFSS_RE = re.compile(r"abfss://[A-Za-z0-9_./@-]+")
UC_NAME_RE = re.compile(r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b")
DBUTILS_RE = re.compile(r"\bdbutils\.(fs|secrets|widgets|notebook)\b")
SAVE_AS_TABLE_RE = re.compile(r"\.saveAsTable\(\s*[\"']([^\"']+)[\"']")
TABLE_READ_RE = re.compile(r"\bspark\.table\(\s*[\"']([^\"']+)[\"']")
SQL_TABLE_RE = re.compile(
    r"\b(MERGE\s+INTO|INSERT\s+INTO|UPDATE|DELETE\s+FROM|SELECT\s+.*?\s+FROM|OPTIMIZE|"
    r"VACUUM|RESTORE)\s+([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*){0,2})",
    re.IGNORECASE,
)
DELTA_OPS = frozenset({"MERGE", "OPTIMIZE", "VACUUM", "RESTORE", "INSERT", "UPDATE",
                       "DELETE"})

_SQL_LINE = re.compile(r"(sql\s*\(|--\s|%sql|CREATE\s+TABLE|MERGE\s+INTO|"
                       r"SELECT\s+.*FROM|INSERT\s+INTO)", re.IGNORECASE)

# First segment of a 3-part match that is an API call, never a UC catalog name.
_NON_UC_PREFIX = frozenset({
    "spark", "dbutils", "delta", "self", "json", "sys", "os", "re", "np", "pd",
    "windows", "core", "dfs", "blob", "net", "com", "azuredatabricks",
})


def _is_uc_name(line: str, m: re.Match[str]) -> bool:
    if m.group(1).lower() in _NON_UC_PREFIX:
        return False
    before = line[m.start() - 1] if m.start() else ""
    after = line[m.end()] if m.end() < len(line) else ""
    return before not in ".@/" and after not in ".@"


def _subject(filename: str, line: int, symbol: str = "") -> dict[str, Any]:
    s: dict[str, Any] = {"file": filename, "line": line}
    if symbol:
        s["symbol"] = symbol
    return s


def scan_source(source: str, *, filename: str,
                provenance: dict[str, Any] | None = None) -> list[Fact]:
    """Scan one source text (a .py/.sql file or an .ipynb cell blob)."""
    prov = dict(provenance or {})
    prov.setdefault("source", f"notebook:{filename}")
    facts: list[Fact] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        for m in ABFSS_RE.finditer(line):
            facts.append(Fact(
                kind="notebook.abfss_path",
                subject=_subject(filename, lineno),
                attrs={"url": m.group(0).rstrip("\"'"), "line_text": line.strip()[:200]},
                provenance=dict(prov)))
        for m in DBUTILS_RE.finditer(line):
            facts.append(Fact(
                kind="notebook.dbutils",
                subject=_subject(filename, lineno),
                attrs={"api": f"dbutils.{m.group(1)}", "line_text": line.strip()[:200]},
                provenance=dict(prov)))
        for m in SAVE_AS_TABLE_RE.finditer(line):
            facts.append(Fact(
                kind="notebook.write_table",
                subject=_subject(filename, lineno, symbol=m.group(1)),
                attrs={"target": m.group(1), "api": "saveAsTable",
                       "line_text": line.strip()[:200]},
                provenance=dict(prov)))
        for m in TABLE_READ_RE.finditer(line):
            facts.append(Fact(
                kind="notebook.uc_table",
                subject=_subject(filename, lineno, symbol=m.group(1)),
                attrs={"table": m.group(1), "api": "spark.table",
                       "line_text": line.strip()[:200]},
                provenance=dict(prov)))
        for m in UC_NAME_RE.finditer(line):
            if not _is_uc_name(line, m):
                continue
            name = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
            facts.append(Fact(
                kind="notebook.uc_table",
                subject=_subject(filename, lineno, symbol=name),
                attrs={"table": name, "line_text": line.strip()[:200]},
                provenance=dict(prov)))
        if _SQL_LINE.search(line):
            for m in SQL_TABLE_RE.finditer(line):
                op = m.group(1).split()[0].upper()
                facts.append(Fact(
                    kind="notebook.delta_op" if op in DELTA_OPS else "notebook.sql_op",
                    subject=_subject(filename, lineno, symbol=m.group(2)),
                    attrs={"op": op, "table": m.group(2),
                           "line_text": line.strip()[:200]},
                    provenance=dict(prov)))
    facts.append(Fact(
        kind="notebook.analyzed",
        subject={"file": filename, "line": 0},
        measures={"lines": len(source.splitlines())},
        provenance=dict(prov)))
    return facts


def scan_paths(paths: list[Path], *, base: Path | None = None) -> list[Fact]:
    """Scan .py/.sql/.ipynb files.  .ipynb cells are concatenated per file."""
    facts: list[Fact] = []
    for path in sorted(paths):
        name = path.name if base is None else path.relative_to(base).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if path.suffix == ".ipynb":
            try:
                import json

                nb = json.loads(text)
                text = "\n".join(
                    "".join(cell.get("source", []))
                    for cell in nb.get("cells", [])
                    if cell.get("cell_type") in {"code", "markdown"}
                )
            except ValueError:
                continue
        facts.extend(scan_source(text, filename=name))
    return sort_facts(facts)


def scan_dir(directory: Path) -> list[Fact]:
    """Scan a directory through the shared traversal (denylist + confinement)."""
    paths = [p for p in varrer_source_files(directory, "*").arquivos
             if p.suffix.lower() in {".py", ".sql", ".ipynb"}]
    return scan_paths(paths, base=directory)


def skipped_facts(skipped: list[dict[str, str]], *,
                  provenance: dict[str, Any] | None = None) -> list[Fact]:
    """Facts for paths the traversal refused to read.

    A skipped notebook is missing evidence, not absence of evidence -- the fact
    keeps the reason (sensitive name, symlink, size cap) visible downstream.
    """
    prov = dict(provenance or {})
    prov.setdefault("source", "notebook:scan")
    return [
        Fact(kind="notebook.skipped",
             subject={"file": s["path"], "line": 0},
             attrs={"reason": s["reason"]},
             provenance=dict(prov))
        for s in skipped
    ]


__all__ = ["scan_dir", "scan_paths", "scan_source", "skipped_facts"]
