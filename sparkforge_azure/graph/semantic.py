"""Static code graph builder (Graphfy code layer, section 62).

Sources: repository files, Python symbols, imports, tests and configs.  Python
symbols and call edges come from Code Intelligence (``codeintel.index``) when
it is available; otherwise an ``ast`` walk produces the same node kinds.
Imports, tests and configs always come from the local walk, which only records
references it can verify (a module that resolves to a file in the repository,
a config that names a repository path verbatim).  Nothing is executed.
"""

from __future__ import annotations

import ast
import re
import sqlite3
import tempfile
from collections.abc import Iterable
from pathlib import Path

from sparkforge_azure.graph.model import Edge, Graph, Node, Provenance, node_id
from sparkforge_azure.paths import scan_repository

CONFIG_SUFFIXES = frozenset({".yaml", ".yml", ".json", ".toml"})
IAC_SUFFIXES = {".tf": "terraform", ".bicep": "bicep"}
MAX_CONFIG_BYTES = 256 * 1024
_TF_RESOURCE = re.compile(r'^\s*resource\s+"([A-Za-z0-9_]+)"\s+"([A-Za-z0-9_-]+)"\s*\{', re.M)
_NOTEBOOK_MARKER = "# Databricks notebook source"


def _key(repo: str, rel: str) -> str:
    return f"{repo}/{rel}" if repo else rel


def is_test_path(rel: str) -> bool:
    parts = rel.split("/")
    name = parts[-1]
    return (
        "tests" in parts[:-1]
        or "test" in parts[:-1]
        or (name.startswith("test_") and name.endswith(".py"))
        or name.endswith("_test.py")
    )


def file_node_id(repo: str, rel: str) -> str:
    kind = "test" if is_test_path(rel) and rel.endswith(".py") else (
        "config" if Path(rel).suffix.lower() in CONFIG_SUFFIXES | set(IAC_SUFFIXES) else "file"
    )
    return node_id("code", kind, _key(repo, rel))


def build_code_graph(
    root: str | Path,
    *,
    repo: str = "",
    use_codeintel: bool = True,
    source: str | None = None,
) -> Graph:
    base = Path(root).resolve()
    prov = Provenance("static", source or f"repo:{repo or base.name}")
    graph = Graph()
    report = scan_repository(base)
    rel_files = [p.relative_to(base).as_posix() for p in report.files]
    py_files = [r for r in rel_files if r.endswith(".py")]
    module_index = _module_index(py_files)

    for rel in rel_files:
        _add_file_node(graph, base, repo, rel, prov)

    engine = "ast"
    if use_codeintel and py_files:
        try:
            _symbols_from_codeintel(graph, base, repo, prov, set(py_files))
            engine = "codeintel"
        except Exception as exc:  # any engine failure -> ast fallback
            graph.add_unresolved(
                {"reason": "codeintel_unavailable", "detail": type(exc).__name__}
            )
    for rel in py_files:
        _walk_python(graph, base, repo, rel, prov, module_index, symbols=(engine == "ast"))
    _config_references(graph, base, repo, rel_files, py_files, prov)
    prune_unverified_calls(graph)
    graph.meta = {"engine": engine, "repo": repo, "skipped": len(report.skipped)}
    return graph


# -- files ------------------------------------------------------------------
def _add_file_node(graph: Graph, base: Path, repo: str, rel: str, prov: Provenance) -> None:
    suffix = Path(rel).suffix.lower()
    attrs: dict[str, object] = {"path": rel, "repo": repo}
    nid = file_node_id(repo, rel)
    kind = nid.split(":", 2)[1]
    if suffix in IAC_SUFFIXES:
        attrs["iac"] = IAC_SUFFIXES[suffix]
    elif suffix in CONFIG_SUFFIXES:
        attrs["format"] = suffix.lstrip(".")
    elif suffix == ".py":
        attrs["language"] = "python"
    graph.add_node(Node(nid, kind, "code", attrs, prov))
    if suffix == ".tf":
        _terraform_resources(graph, base, repo, rel, nid, prov)
    if suffix == ".py" and _is_notebook(base / rel):
        nb = node_id("data", "notebook", _key(repo, rel))
        graph.add_node(Node(nb, "notebook", "data", {"path": rel, "repo": repo}, prov))
        graph.add_edge(Edge(nid, "defines", nb, {}, prov))


def _is_notebook(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.readline().strip() == _NOTEBOOK_MARKER
    except OSError:
        return False


def _terraform_resources(
    graph: Graph, base: Path, repo: str, rel: str, file_id: str, prov: Provenance
) -> None:
    text = _read_text(base / rel)
    if text is None:
        return
    for rtype, rname in _TF_RESOURCE.findall(text):
        address = f"{rtype}.{rname}"
        sid = node_id("code", "symbol", _key(repo, address))
        graph.add_node(
            Node(
                sid,
                "symbol",
                "code",
                {"address": address, "resource_type": rtype, "iac": "terraform",
                 "path": rel, "repo": repo},
                prov,
            )
        )
        graph.add_edge(Edge(file_id, "defines", sid, {}, prov))


def _read_text(path: Path, limit: int = MAX_CONFIG_BYTES) -> str | None:
    try:
        data = path.read_bytes()[:limit]
    except OSError:
        return None
    return data.decode("utf-8", errors="replace")


# -- python -----------------------------------------------------------------
def _module_index(py_files: Iterable[str]) -> dict[str, str]:
    index: dict[str, str] = {}
    for rel in py_files:
        parts = rel[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        index[".".join(parts)] = rel
        # src-layout: also index without a leading "src" segment
        if parts[0] == "src" and len(parts) > 1:
            index.setdefault(".".join(parts[1:]), rel)
    return index


def _resolve_module(module: str, index: dict[str, str]) -> str | None:
    probe = module
    while probe:
        if probe in index:
            return index[probe]
        if "." not in probe:
            return None
        probe = probe.rsplit(".", 1)[0]
    return None


def _symbol_id(repo: str, rel: str, kind: str, qualname: str) -> str:
    return node_id("code", kind, f"{_key(repo, rel)}::{qualname}")


def _walk_python(
    graph: Graph,
    base: Path,
    repo: str,
    rel: str,
    prov: Provenance,
    module_index: dict[str, str],
    *,
    symbols: bool,
) -> None:
    text = _read_text(base / rel, limit=2 * 1024 * 1024)
    if text is None:
        return
    try:
        tree = ast.parse(text)
    except SyntaxError:
        graph.add_unresolved({"reason": "unparseable_python", "path": _key(repo, rel)})
        return
    fid = file_node_id(repo, rel)
    current_pkg = rel[:-3].replace("/", ".")
    imported_names: dict[str, str] = {}  # local name -> target file rel
    for item in ast.walk(tree):
        modules: list[tuple[str, list[str]]] = []
        if isinstance(item, ast.Import):
            modules = [(alias.name, []) for alias in item.names]
        elif isinstance(item, ast.ImportFrom):
            mod = item.module or ""
            if item.level:
                pkg = current_pkg.split(".")
                if rel.endswith("__init__.py"):
                    pkg = pkg[:-1]
                anchor = pkg[: max(len(pkg) - item.level, 0)]
                mod = ".".join([*anchor, mod] if mod else anchor)
            modules = [(mod, [a.name for a in item.names])]
        for mod, names in modules:
            if not mod:
                continue
            imp = node_id("code", "import", mod)
            graph.add_node(Node(imp, "import", "code", {"module": mod}, prov))
            graph.add_edge(Edge(fid, "imports", imp, {}, prov))
            candidates = [f"{mod}.{n}" for n in names] + [mod]
            for cand in candidates:
                target = _resolve_module(cand, module_index)
                if target and target != rel:
                    tid = file_node_id(repo, target)
                    relation = "tests" if is_test_path(rel) else "imports"
                    graph.add_edge(Edge(fid, relation, tid, {"module": cand}, prov))
                    if relation == "tests":
                        graph.add_edge(Edge(fid, "imports", tid, {"module": cand}, prov))
                    for n in names:
                        imported_names.setdefault(n, target)
                    break
    if symbols:
        _ast_symbols(graph, tree, repo, rel, fid, prov, imported_names)


def _ast_symbols(
    graph: Graph,
    tree: ast.Module,
    repo: str,
    rel: str,
    fid: str,
    prov: Provenance,
    imported_names: dict[str, str],
) -> None:
    local: dict[str, str] = {}
    by_line: dict[int, str] = {}

    def visit(body: list[ast.stmt], prefix: str, parent: str) -> None:
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(stmt, ast.ClassDef) else "function"
                qual = f"{prefix}{stmt.name}"
                sid = _symbol_id(repo, rel, kind, qual)
                attrs = {"name": stmt.name, "qualified_name": qual, "path": rel, "repo": repo,
                         "start_line": stmt.lineno,
                         "end_line": getattr(stmt, "end_lineno", stmt.lineno)}
                if kind == "function" and prefix:
                    attrs["method"] = True
                graph.add_node(Node(sid, kind, "code", attrs, prov))
                graph.add_edge(Edge(parent, "defines", sid, {}, prov))
                if not prefix:
                    local[stmt.name] = sid
                if kind == "function":
                    by_line[stmt.lineno] = sid
                visit(stmt.body, f"{qual}.", sid)

    visit(tree.body, "", fid)
    # Calls: only to top-level names of this file or names imported from a
    # repository file that defines them (verified reference, never by guess).
    for stmt in ast.walk(tree):
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        caller = by_line.get(stmt.lineno)
        if caller is None:
            continue
        for call in ast.walk(stmt):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                name = call.func.id
                if name in local and local[name] != caller:
                    graph.add_edge(Edge(caller, "calls", local[name], {}, prov))
                elif name in imported_names:
                    target_rel = imported_names[name]
                    for kind in ("function", "class"):
                        tid = _symbol_id(repo, target_rel, kind, name)
                        graph.add_edge(
                            Edge(caller, "calls", tid, {"via_import": True}, prov)
                        )


def prune_unverified_calls(graph: Graph) -> None:
    """Drop ``calls`` edges whose target symbol does not exist (verified only)."""

    for key in [k for k in graph.edges if k[1] == "calls" and k[2] not in graph.nodes]:
        del graph.edges[key]


# -- codeintel ----------------------------------------------------------------
_CI_KINDS = {"class": "class", "function": "function", "method": "function"}


def _symbols_from_codeintel(
    graph: Graph, base: Path, repo: str, prov: Provenance, py_files: set[str]
) -> None:
    from sparkforge_azure.codeintel.index import indexar  # lazy: L2 engine

    with tempfile.TemporaryDirectory(prefix="sfa-graphfy-") as tmp:
        db = Path(tmp) / "graph.sqlite3"
        indexar(base, db)
        con = sqlite3.connect(db)
        try:
            rows = con.execute(
                "SELECT n.id, n.kind, n.name, n.qualified_name, n.start_line, n.end_line, f.path"
                " FROM nodes n JOIN files f ON f.id = n.file_id ORDER BY n.id"
            ).fetchall()
            mapping: dict[str, str] = {}
            for ci_id, kind, name, qual, start, end, path in rows:
                if path not in py_files:
                    continue
                gkind = _CI_KINDS.get(kind, "symbol")
                sid = _symbol_id(repo, path, gkind, qual)
                attrs = {"name": name, "qualified_name": qual, "path": path, "repo": repo,
                         "start_line": start, "end_line": end}
                if kind == "method":
                    attrs["method"] = True
                graph.add_node(Node(sid, gkind, "code", attrs, prov))
                parent = file_node_id(repo, path)
                if "." in qual:
                    owner = qual.rsplit(".", 1)[0]
                    for okind in ("class", "function"):
                        cand = _symbol_id(repo, path, okind, owner)
                        if cand in graph.nodes:
                            parent = cand
                            break
                graph.add_edge(Edge(parent, "defines", sid, {}, prov))
                mapping[ci_id] = sid
            for src, dst, kind in con.execute(
                "SELECT source_id, target_id, kind FROM edges ORDER BY source_id, target_id, kind"
            ).fetchall():
                if src in mapping and dst in mapping:
                    relation = re.sub(r"[^a-z0-9_]", "_", str(kind).lower()) or "references"
                    graph.add_edge(Edge(mapping[src], relation, mapping[dst], {}, prov))
        finally:
            con.close()


# -- configs ------------------------------------------------------------------
def _config_references(
    graph: Graph,
    base: Path,
    repo: str,
    rel_files: list[str],
    py_files: list[str],
    prov: Provenance,
) -> None:
    configs = [r for r in rel_files if Path(r).suffix.lower() in CONFIG_SUFFIXES]
    targets = [r for r in rel_files if r not in configs]
    for cfg in configs:
        text = _read_text(base / cfg)
        if not text:
            continue
        cid = file_node_id(repo, cfg)
        for target in targets:
            if target in text:  # verbatim repository path only
                graph.add_edge(
                    Edge(cid, "configures", file_node_id(repo, target), {"match": "path"}, prov)
                )


__all__ = ["build_code_graph", "file_node_id", "is_test_path", "prune_unverified_calls"]
