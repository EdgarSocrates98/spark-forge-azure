"""Persist/load Graphfy graphs under ``.sparkforge-azure/graph/``.

Layout::

    .sparkforge-azure/graph/
      graph.json          composed static workspace graph (+ fingerprint)
      index.json          {"repos": {name: content_fingerprint}, "graph_fingerprint": ...}
      repos/<name>.json   cached per-repository code graph

Incremental rebuild: a repository's code graph is rebuilt only when its
content fingerprint changed (``workspace.manifest.fingerprint``: hashes of
file names and contents, nothing executed).  Loading verifies the stored
fingerprint, so a hand-edited or truncated graph is refused, not trusted.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sparkforge_azure.graph.model import Graph, GraphError
from sparkforge_azure.graph.semantic import build_code_graph
from sparkforge_azure.graph.workspace import WorkspaceManifest, build_workspace_graph
from sparkforge_azure.workspace.manifest import fingerprint as repo_fingerprint

STATE_DIR = Path(".sparkforge-azure") / "graph"


def default_state_dir(root: str | Path) -> Path:
    return Path(root) / STATE_DIR


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save_graph(graph: Graph, path: str | Path) -> str:
    data = graph.to_dict()
    fp = graph.fingerprint()
    data["fingerprint"] = fp
    _atomic_write(Path(path), json.dumps(data, sort_keys=True, indent=1, ensure_ascii=True))
    return fp


def load_graph(path: str | Path, *, verify: bool = True) -> Graph:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GraphError(f"graph unreadable: {Path(path).name}") from exc
    if not isinstance(raw, dict):
        raise GraphError("graph file must contain an object")
    graph = Graph.from_dict(raw)
    stored = raw.get("fingerprint")
    if verify and stored is not None and stored != graph.fingerprint():
        raise GraphError("graph fingerprint mismatch (file modified or corrupted)")
    return graph


def _try_load(path: Path) -> Graph | None:
    if not path.is_file():
        return None
    try:
        return load_graph(path)
    except GraphError:  # corrupted cache: caller rebuilds
        return None


def build_incremental(
    manifest: WorkspaceManifest,
    *,
    state_dir: str | Path | None = None,
    use_codeintel: bool = True,
    persist: bool = True,
) -> tuple[Graph, dict[str, Any]]:
    state = Path(state_dir) if state_dir is not None else default_state_dir(manifest.root)
    index_path = state / "index.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(index, dict):
            index = {}
    except (OSError, ValueError):
        index = {}
    previous: dict[str, str] = dict(index.get("repos") or {})
    current: dict[str, str] = {}
    code_graphs: dict[str, Graph] = {}
    rebuilt: list[str] = []
    reused: list[str] = []
    for repo in manifest.repositories:
        if not repo.exists:
            continue
        fp = repo_fingerprint(repo.resolved)
        current[repo.name] = fp
        cache = state / "repos" / f"{repo.name}.json"
        cached = _try_load(cache) if previous.get(repo.name) == fp else None
        if cached is not None:
            code_graphs[repo.name] = cached
            reused.append(repo.name)
            continue
        code = build_code_graph(repo.resolved, repo=repo.name, use_codeintel=use_codeintel)
        code_graphs[repo.name] = code
        rebuilt.append(repo.name)
        if persist:
            save_graph(code, cache)
    graph = build_workspace_graph(manifest, use_codeintel=use_codeintel, code_graphs=code_graphs)
    report: dict[str, Any] = {
        "rebuilt": sorted(rebuilt),
        "reused": sorted(reused),
        "removed": sorted(set(previous) - set(current)),
        "graph_fingerprint": graph.fingerprint(),
    }
    if persist:
        for name in report["removed"]:
            stale = state / "repos" / f"{name}.json"
            if stale.is_file():
                stale.unlink()
        save_graph(graph, state / "graph.json")
        _atomic_write(
            index_path,
            json.dumps({"repos": dict(sorted(current.items())),
                        "graph_fingerprint": report["graph_fingerprint"]},
                       sort_keys=True, indent=1),
        )
        report["path"] = (state / "graph.json").as_posix()
    return graph, report


__all__ = ["STATE_DIR", "build_incremental", "default_state_dir", "load_graph", "save_graph"]
