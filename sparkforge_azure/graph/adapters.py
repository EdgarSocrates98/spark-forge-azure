"""Adapters: Graphfy <-> ``workspace.federated.GraphFragment`` and the
knowledge-layer adapter (knowledge entries, skills, agents).

The knowledge adapter reads YAML front matter only:

* ``knowledge/**/*.md``: ``id``, ``domain``, ``related``;
* ``skills/*/SKILL.md``: ``name`` and ``metadata.knowledge_refs``;
* ``agents/*.md``: ``id``, ``skills``, ``knowledge_refs``.

References resolve by explicit knowledge id or explicit path prefix
(``knowledge/azure/storage/``).  Anything that does not resolve goes to
``unresolved``.  Absent directories are tolerated (empty layer).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.graph.model import LAYERS, Edge, Graph, Node, Provenance, node_id
from sparkforge_azure.workspace.federated import GraphFragment

# -- GraphFragment ------------------------------------------------------------


def to_fragment(graph: Graph, source_id: str, source_kind: str = "graphfy") -> GraphFragment:
    data = graph.to_dict()
    return GraphFragment(
        source=source_id,
        nodes=tuple(data["nodes"]),
        edges=tuple(data["edges"]),
        provenance=({"source_id": source_id, "source_kind": source_kind},),
        unresolved=tuple(data["unresolved"]),
        source_id=source_id,
        source_kind=source_kind,
    )


def from_fragment(fragment: GraphFragment, *, default_layer: str = "evidence") -> Graph:
    """Lift a fragment into Graphfy.  Records without a valid layer/kind are
    kept out of the graph and reported as unresolved (no guessing)."""

    from sparkforge_azure.graph.model import NODE_KINDS, GraphError

    graph = Graph()
    prov = Provenance("artifact", fragment.source_id or "fragment")
    for raw in fragment.nodes:
        rec = dict(raw)
        nid = str(rec.get("id", ""))
        layer = str(rec.get("layer") or (nid.split(":", 1)[0] if ":" in nid else default_layer))
        kind = str(rec.get("kind", ""))
        if layer not in LAYERS or kind not in NODE_KINDS[layer]:
            graph.add_unresolved({"reason": "fragment_node_unmapped", "id": nid, "kind": kind})
            continue
        if not nid.startswith(f"{layer}:"):
            nid = node_id(layer, kind, nid)
        attrs = rec.get("attrs") if isinstance(rec.get("attrs"), Mapping) else {
            k: v for k, v in rec.items() if k not in ("id", "kind", "layer", "provenance")
        }
        try:
            graph.add_node(Node(nid, kind, layer, attrs or {}, prov))
        except GraphError as exc:
            graph.add_unresolved({"reason": "fragment_node_invalid", "id": nid,
                                  "detail": str(exc)})
    for raw in fragment.edges:
        rec = dict(raw)
        try:
            graph.add_edge(Edge(str(rec.get("source", "")), str(rec.get("relation", "")),
                                str(rec.get("target", "")), {}, prov))
        except GraphError as exc:
            graph.add_unresolved({"reason": "fragment_edge_invalid", "detail": str(exc)})
    for item in fragment.unresolved:
        graph.add_unresolved(dict(item))
    return graph


# -- knowledge ----------------------------------------------------------------


def read_front_matter(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if isinstance(v, (str, int))]
    return []


def knowledge_graph(root: str | Path) -> Graph:
    base = Path(root).resolve()
    prov = Provenance("knowledge", "knowledge-base")
    graph = Graph()
    entries = _knowledge_entries(base)
    by_id: dict[str, str] = {}
    by_path: dict[str, str] = {}
    for entry in entries:
        kid = node_id("knowledge", "knowledge", entry["id"])
        attrs = {k: entry[k] for k in ("id", "domain", "path", "title", "validated") if k in entry}
        graph.add_node(Node(kid, "knowledge", "knowledge", attrs, prov))
        by_id[entry["id"]] = kid
        by_path[entry["path"]] = kid
    for entry in entries:
        src = by_id[entry["id"]]
        for rel in entry.get("related", []):
            if rel in by_id:
                graph.add_edge(Edge(src, "related", by_id[rel], {}, prov))
            else:
                graph.add_unresolved({"reason": "unknown_related", "source": entry["id"],
                                      "ref": rel})

    def resolve_refs(src: str, refs: list[str]) -> None:
        for ref in refs:
            targets: list[str] = []
            if ref in by_id:
                targets = [by_id[ref]]
            else:
                norm = ref.replace("\\", "/")
                prefix = norm if norm.endswith(("/", ".md")) else norm + "/"
                targets = sorted(
                    kid for p, kid in by_path.items()
                    if p == norm or p.startswith(prefix)
                )
            if not targets:
                graph.add_unresolved({"reason": "unknown_knowledge_ref", "source": src,
                                      "ref": ref})
            for t in targets:
                graph.add_edge(Edge(src, "refers_knowledge", t, {"ref": ref}, prov))

    skills_dir = base / "skills"
    skill_ids: dict[str, str] = {}
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            fm = read_front_matter(skill_md) or {}
            name = str(fm.get("name") or skill_md.parent.name)
            sid = node_id("knowledge", "skill", name)
            skill_ids[name] = sid
            graph.add_node(Node(sid, "skill", "knowledge",
                                {"id": name, "path": skill_md.relative_to(base).as_posix()},
                                prov))
            meta = fm.get("metadata") if isinstance(fm.get("metadata"), Mapping) else {}
            resolve_refs(sid, _as_list(meta.get("knowledge_refs")))
    agents_dir = base / "agents"
    if agents_dir.is_dir():
        for agent_md in sorted(agents_dir.glob("*.md")):
            fm = read_front_matter(agent_md)
            if fm is None:
                continue
            aid_name = str(fm.get("id") or agent_md.stem)
            aid = node_id("knowledge", "agent", aid_name)
            graph.add_node(Node(aid, "agent", "knowledge",
                                {"id": aid_name, "path": agent_md.relative_to(base).as_posix()},
                                prov))
            for skill in _as_list(fm.get("skills")):
                if skill in skill_ids:
                    graph.add_edge(Edge(aid, "uses_skill", skill_ids[skill], {}, prov))
                else:
                    graph.add_unresolved({"reason": "unknown_skill", "source": aid_name,
                                          "ref": skill})
            resolve_refs(aid, _as_list(fm.get("knowledge_refs")))
    graph.meta = {"kind": "knowledge", "entries": len(entries)}
    return graph


def _knowledge_entries(base: Path) -> list[dict[str, Any]]:
    kdir = base / "knowledge"
    if not kdir.is_dir():
        return []
    entries: dict[str, dict[str, Any]] = {}
    validated: list[Any] = []
    try:  # lazy: validated loader when the knowledgebase package is present
        from sparkforge_azure.knowledgebase import load_entries
    except ImportError:
        load_entries = None
    if load_entries is not None:
        try:
            validated, _errors = load_entries(kdir)
        except Exception:  # tolerate: fall back to raw front matter below
            validated = []
    for e in validated:
        path = f"knowledge/{e.path}"
        entries[path] = {"id": e.id, "domain": e.domain, "title": e.title,
                         "related": list(e.related), "path": path, "validated": True}
    for md in sorted(kdir.rglob("*.md")):
        if md.is_symlink():
            continue
        path = md.relative_to(base).as_posix()
        if path in entries:
            continue
        fm = read_front_matter(md)
        if not fm or not isinstance(fm.get("id"), str):
            continue
        entries[path] = {"id": fm["id"], "domain": str(fm.get("domain", "")),
                         "title": str(fm.get("title", "")),
                         "related": _as_list(fm.get("related")), "path": path,
                         "validated": False}
    seen: set[str] = set()
    out = []
    for path in sorted(entries):
        e = entries[path]
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        out.append(e)
    return out


__all__ = ["from_fragment", "knowledge_graph", "read_front_matter", "to_fragment"]
