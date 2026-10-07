"""Graphfy typed model: Node, Edge, Provenance and Graph.

Graphfy is the semantic/workspace graph of the Forge.  Every node lives in one
layer (code | data | azure | knowledge | evidence), has a deterministic id and
carries provenance (static | live | artifact | knowledge).  Serialization is
canonical (sorted keys, sorted nodes/edges) so the same input always produces
the same bytes and the same fingerprint.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1

LAYERS: tuple[str, ...] = ("code", "data", "azure", "knowledge", "evidence")

# Kinds per layer.  The first block of each set is the contract of section 55;
# the trailing names are documented extensions (see docs/architecture/GRAPHFY.md).
NODE_KINDS: dict[str, frozenset[str]] = {
    "code": frozenset(
        {"file", "symbol", "function", "class", "import", "test", "config", "repository"}
    ),
    "data": frozenset(
        {
            "dataset", "table", "column", "pipeline", "notebook", "job", "stream",
            "checkpoint", "cluster",
        }
    ),
    "azure": frozenset(
        {
            "tenant", "subscription", "resource_group", "workspace", "storage_account",
            "filesystem", "databricks_workspace", "unity_catalog", "adf", "fabric_workspace",
            "event_hub", "purview", "network", "identity",
            "fabric_capacity", "key_vault", "resource",
        }
    ),
    "knowledge": frozenset(
        {"knowledge", "rule", "skill", "agent", "eval", "finding", "domain", "boundary"}
    ),
    "evidence": frozenset({"fact", "finding", "evidence", "decision", "receipt", "trace"}),
}

PROVENANCE_KINDS: tuple[str, ...] = ("static", "live", "artifact", "knowledge")

_RELATION = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class GraphError(ValueError):
    """Invalid graph content (unknown layer/kind, malformed id or relation)."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def node_id(layer: str, kind: str, key: str) -> str:
    """Deterministic id ``layer:kind:key``.  ``key`` is used verbatim."""

    if layer not in NODE_KINDS:
        raise GraphError(f"unknown layer: {layer!r}")
    if not isinstance(key, str) or not key:
        raise GraphError("node key must be a non-empty string")
    return f"{layer}:{kind}:{key}"


def azure_node_id(arm_id: str) -> str:
    """Azure resources are keyed by ARM id only (case-insensitive by contract).

    The kind is deliberately NOT part of the id: the same ARM id observed
    statically (manifest) and live (Resource Graph) must be one node.
    """

    value = arm_id.strip().rstrip("/").lower()
    if not value.startswith("/subscriptions/"):
        raise GraphError(f"not an ARM resource id: {arm_id!r}")
    return f"azure:{value}"


@dataclass(frozen=True)
class Provenance:
    kind: str
    source: str
    observed_at: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in PROVENANCE_KINDS:
            raise GraphError(f"unknown provenance kind: {self.kind!r}")
        if not isinstance(self.source, str) or not self.source:
            raise GraphError("provenance source must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "source": self.source, "observed_at": self.observed_at}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Provenance:
        return cls(str(raw["kind"]), str(raw["source"]), raw.get("observed_at"))

    def label(self) -> str:
        return f"{self.kind}:{self.source}"


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    layer: str
    attrs: Mapping[str, Any] = field(default_factory=dict)
    provenance: Provenance = field(default_factory=lambda: Provenance("static", "unknown"))

    def __post_init__(self) -> None:
        if self.layer not in NODE_KINDS:
            raise GraphError(f"unknown layer: {self.layer!r}")
        if self.kind not in NODE_KINDS[self.layer]:
            raise GraphError(f"kind {self.kind!r} not allowed in layer {self.layer!r}")
        if not isinstance(self.id, str) or not self.id.startswith(f"{self.layer}:"):
            raise GraphError(f"node id must start with its layer: {self.id!r}")
        object.__setattr__(self, "attrs", dict(self.attrs))

    __hash__ = None  # type: ignore[assignment]  # attrs is a dict

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "layer": self.layer,
            "attrs": _jsonable(self.attrs),
            "provenance": self.provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Node:
        return cls(
            str(raw["id"]),
            str(raw["kind"]),
            str(raw["layer"]),
            dict(raw.get("attrs") or {}),
            Provenance.from_dict(raw.get("provenance") or {"kind": "static", "source": "unknown"}),
        )


@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str
    attrs: Mapping[str, Any] = field(default_factory=dict)
    provenance: Provenance = field(default_factory=lambda: Provenance("static", "unknown"))

    def __post_init__(self) -> None:
        if not _RELATION.match(self.relation or ""):
            raise GraphError(f"invalid relation: {self.relation!r}")
        if not self.source or not self.target:
            raise GraphError("edge endpoints must be non-empty")
        object.__setattr__(self, "attrs", dict(self.attrs))

    __hash__ = None  # type: ignore[assignment]

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.source, self.relation, self.target)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "relation": self.relation,
            "target": self.target,
            "attrs": _jsonable(self.attrs),
            "provenance": self.provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Edge:
        return cls(
            str(raw["source"]),
            str(raw["relation"]),
            str(raw["target"]),
            dict(raw.get("attrs") or {}),
            Provenance.from_dict(raw.get("provenance") or {"kind": "static", "source": "unknown"}),
        )


class Graph:
    """Mutable, deterministic multi-layer graph.

    Merge rule: nodes are unified ONLY by identical id.  A second observation
    of the same id adds missing attrs (first writer wins on conflict, the
    conflicting value is recorded) and records the extra provenance under
    ``attrs["observed_by"]``.  A kind/layer clash on the same id is never
    silently resolved: it lands in ``unresolved``.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str, str], Edge] = {}
        self.unresolved: list[dict[str, Any]] = []
        self.meta: dict[str, Any] = {}

    # -- mutation ---------------------------------------------------------
    def add_node(self, node: Node) -> Node:
        current = self.nodes.get(node.id)
        if current is None:
            self.nodes[node.id] = node
            return node
        if current.kind != node.kind or current.layer != node.layer:
            self.add_unresolved(
                {
                    "reason": "kind_conflict",
                    "id": node.id,
                    "kept": f"{current.layer}:{current.kind}",
                    "rejected": f"{node.layer}:{node.kind}",
                    "source": node.provenance.label(),
                }
            )
            return current
        attrs = dict(current.attrs)
        conflicts = dict(attrs.get("attr_conflicts") or {})
        for key, value in node.attrs.items():
            if key in ("observed_by", "attr_conflicts"):
                continue
            if key not in attrs:
                attrs[key] = value
            elif attrs[key] != value and value not in (None, "", {}, []):
                if attrs[key] in (None, "", {}, []):
                    attrs[key] = value
                else:
                    conflicts[key] = sorted({canonical_json(attrs[key]), canonical_json(value)})
        if conflicts:
            attrs["attr_conflicts"] = conflicts
        observed = set(attrs.get("observed_by") or [current.provenance.label()])
        observed.update(node.attrs.get("observed_by") or [])
        observed.add(node.provenance.label())
        if len(observed) > 1:
            attrs["observed_by"] = sorted(observed)
        merged = Node(current.id, current.kind, current.layer, attrs, current.provenance)
        self.nodes[node.id] = merged
        return merged

    def add_edge(self, edge: Edge) -> Edge:
        current = self.edges.get(edge.key)
        if current is None:
            self.edges[edge.key] = edge
            return edge
        attrs = {**edge.attrs, **current.attrs}
        merged = Edge(current.source, current.relation, current.target, attrs, current.provenance)
        self.edges[edge.key] = merged
        return merged

    def add_unresolved(self, item: Mapping[str, Any]) -> None:
        record = _jsonable(dict(item))
        if record not in self.unresolved:
            self.unresolved.append(record)

    def merge(self, other: Graph) -> Graph:
        """Return a NEW graph with ``self`` then ``other`` (deterministic)."""

        result = self.copy()
        for nid in sorted(other.nodes):
            result.add_node(other.nodes[nid])
        for key in sorted(other.edges):
            result.add_edge(other.edges[key])
        for item in other.unresolved:
            result.add_unresolved(item)
        return result

    def copy(self) -> Graph:
        g = Graph()
        g.nodes = dict(self.nodes)
        g.edges = dict(self.edges)
        g.unresolved = [dict(u) for u in self.unresolved]
        g.meta = dict(self.meta)
        return g

    # -- read -------------------------------------------------------------
    def node(self, nid: str) -> Node | None:
        return self.nodes.get(nid)

    def out_edges(self, nid: str, relation: str | None = None) -> list[Edge]:
        return [
            e for k, e in sorted(self.edges.items())
            if k[0] == nid and (relation is None or k[1] == relation)
        ]

    def in_edges(self, nid: str, relation: str | None = None) -> list[Edge]:
        return [
            e for k, e in sorted(self.edges.items())
            if k[2] == nid and (relation is None or k[1] == relation)
        ]

    def neighbors(
        self,
        nid: str,
        relation: str | Iterable[str] | None = None,
        direction: str = "out",
    ) -> tuple[str, ...]:
        if direction not in ("out", "in", "both"):
            raise GraphError(f"invalid direction: {direction!r}")
        relations = _relation_filter(relation)
        found: set[str] = set()
        for (src, rel, dst) in self.edges:
            if relations is not None and rel not in relations:
                continue
            if direction in ("out", "both") and src == nid:
                found.add(dst)
            if direction in ("in", "both") and dst == nid:
                found.add(src)
        return tuple(sorted(found))

    def subgraph(self, ids: Iterable[str]) -> Graph:
        keep = set(ids)
        g = Graph()
        for nid in sorted(keep):
            if nid in self.nodes:
                g.nodes[nid] = self.nodes[nid]
        for key, edge in sorted(self.edges.items()):
            if key[0] in g.nodes and key[2] in g.nodes:
                g.edges[key] = edge
        g.meta = dict(self.meta)
        return g

    def dangling_edges(self) -> list[Edge]:
        return [
            e for k, e in sorted(self.edges.items())
            if k[0] not in self.nodes or k[2] not in self.nodes
        ]

    # -- serialization ----------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        unresolved = sorted(self.unresolved, key=canonical_json)
        return {
            "schema_version": SCHEMA_VERSION,
            "meta": _jsonable(self.meta),
            "nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes)],
            "edges": [self.edges[k].to_dict() for k in sorted(self.edges)],
            "unresolved": unresolved,
            "stats": self.stats(),
        }

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=indent, ensure_ascii=True)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Graph:
        if raw.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
            raise GraphError("unsupported graph schema_version")
        g = cls()
        for item in raw.get("nodes") or []:
            g.add_node(Node.from_dict(item))
        for item in raw.get("edges") or []:
            g.add_edge(Edge.from_dict(item))
        for item in raw.get("unresolved") or []:
            g.add_unresolved(item)
        g.meta = dict(raw.get("meta") or {})
        return g

    @classmethod
    def from_json(cls, text: str) -> Graph:
        return cls.from_dict(json.loads(text))

    def fingerprint(self) -> str:
        payload = {
            "nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes)],
            "edges": [self.edges[k].to_dict() for k in sorted(self.edges)],
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def stats(self) -> dict[str, Any]:
        layers: dict[str, int] = {}
        for node in self.nodes.values():
            layers[node.layer] = layers.get(node.layer, 0) + 1
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "unresolved": len(self.unresolved),
            "layers": dict(sorted(layers.items())),
        }


def _relation_filter(relation: str | Iterable[str] | None) -> frozenset[str] | None:
    if relation is None:
        return None
    if isinstance(relation, str):
        return frozenset({relation})
    return frozenset(relation)


def _jsonable(value: Any) -> Any:
    """Normalize to plain JSON types (tuples -> lists, sets -> sorted lists)."""

    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_jsonable(v) for v in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


__all__ = [
    "LAYERS",
    "NODE_KINDS",
    "PROVENANCE_KINDS",
    "SCHEMA_VERSION",
    "Edge",
    "Graph",
    "GraphError",
    "Node",
    "Provenance",
    "azure_node_id",
    "canonical_json",
    "node_id",
]
