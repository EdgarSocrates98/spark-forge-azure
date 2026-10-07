"""Azure workspace manifest (``sparkforge-azure.workspace.yaml``) and the static
workspace graph (sections 62 and 66).

The manifest DECLARES: repositories (path + role), relationships between them,
cloud resources with explicit ids (ARM resource id, Databricks workspace id/url,
Fabric workspace GUID), bindings from a repository resource (e.g. a terraform
address) to a declared cloud resource, domains and architecture boundaries.

Nothing is discovered: an undeclared repository is not scanned, an undeclared
resource is not invented.  ARM ids are shape-validated; repository paths may
not escape the manifest directory.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.graph.arm import (
    DATABRICKS_WORKSPACE_ID_RE,
    GUID_RE,
    is_arm_id,
    kind_for_arm_id,
    parse_arm_id,
)
from sparkforge_azure.graph.model import (
    NODE_KINDS,
    Edge,
    Graph,
    Node,
    Provenance,
    azure_node_id,
    node_id,
)
from sparkforge_azure.graph.semantic import build_code_graph
from sparkforge_azure.paths import resolve_within

MANIFEST_NAME = "sparkforge-azure.workspace.yaml"
ROLES = frozenset(
    {"terraform", "bicep", "databricks", "adf", "fabric", "synapse", "shared", "app", "docs"}
)
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
_RELATION = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class WorkspaceError(ValueError):
    """Invalid or unsafe workspace manifest."""


@dataclass(frozen=True)
class RepositoryDecl:
    name: str
    path: str
    role: str
    resolved: Path
    exists: bool


@dataclass(frozen=True)
class CloudResourceDecl:
    name: str
    kind: str
    arm_id: str | None = None
    databricks_workspace_id: str | None = None
    workspace_url: str | None = None
    fabric_workspace_id: str | None = None

    @property
    def node_id(self) -> str:
        if self.arm_id:
            return azure_node_id(self.arm_id)
        if self.databricks_workspace_id:
            return f"azure:databricks:{self.databricks_workspace_id}"
        if self.fabric_workspace_id:
            return f"azure:fabric:{self.fabric_workspace_id.lower()}"
        raise WorkspaceError(f"cloud resource without explicit id: {self.name}")


@dataclass(frozen=True)
class Binding:
    repository: str
    address: str
    target: str  # declared cloud resource name or ARM id


@dataclass(frozen=True)
class WorkspaceManifest:
    name: str
    root: Path
    repositories: tuple[RepositoryDecl, ...]
    relationships: tuple[tuple[str, str, str], ...] = ()
    cloud_resources: tuple[CloudResourceDecl, ...] = ()
    bindings: tuple[Binding, ...] = ()
    domains: tuple[Mapping[str, Any], ...] = ()
    boundaries: tuple[Mapping[str, Any], ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict)

    def repository(self, name: str) -> RepositoryDecl | None:
        return next((r for r in self.repositories if r.name == name), None)

    def resource(self, ref: str) -> CloudResourceDecl | None:
        for res in self.cloud_resources:
            if res.name == ref:
                return res
            if res.arm_id and is_arm_id(ref) and res.arm_id.lower() == ref.strip().lower():
                return res
        return None

    def subscriptions(self) -> tuple[str, ...]:
        subs = {
            parse_arm_id(r.arm_id).subscription_id.lower()
            for r in self.cloud_resources
            if r.arm_id
        }
        return tuple(sorted(subs))


def load_workspace_manifest(path: str | Path) -> WorkspaceManifest:
    manifest_path = Path(path).expanduser().resolve()
    if manifest_path.is_dir():
        manifest_path = manifest_path / MANIFEST_NAME
    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise WorkspaceError(f"manifest unreadable: {manifest_path.name}") from exc
    except yaml.YAMLError as exc:
        raise WorkspaceError(f"manifest is not valid YAML: {manifest_path.name}") from exc
    return parse_workspace_manifest(raw, manifest_path.parent)


def parse_workspace_manifest(raw: Any, root: str | Path) -> WorkspaceManifest:
    if not isinstance(raw, Mapping):
        raise WorkspaceError("manifest must be a mapping")
    if raw.get("schema_version", 1) != 1:
        raise WorkspaceError("schema_version must be 1")
    name = raw.get("workspace")
    if not isinstance(name, str) or not _NAME.match(name.strip()):
        raise WorkspaceError("workspace must be a simple non-empty name")
    base = Path(root).resolve()
    repos = _repositories(raw.get("repositories"), base)
    names = {r.name for r in repos}
    resources = _resources(raw.get("cloud_resources") or [])
    return WorkspaceManifest(
        name=name.strip(),
        root=base,
        repositories=repos,
        relationships=_relationships(raw.get("relationships") or [], names),
        cloud_resources=resources,
        bindings=_bindings(raw.get("bindings") or [], names),
        domains=_named_list(raw.get("domains") or [], "domains"),
        boundaries=_named_list(raw.get("boundaries") or [], "boundaries"),
        raw=dict(raw),
    )


def _safe_repo_path(value: Any, repo: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceError(f"repository path missing: {repo}")
    v = value.strip().replace("\\", "/")
    if v.startswith("/") or re.match(r"^[A-Za-z]:", v) or v.startswith("~"):
        raise WorkspaceError(f"repository path must be relative: {repo}")
    if any(part == ".." for part in v.split("/")):
        raise WorkspaceError(f"repository path traversal refused: {repo}")
    return v


def _repositories(raw: Any, base: Path) -> tuple[RepositoryDecl, ...]:
    if not isinstance(raw, list) or not raw:
        raise WorkspaceError("repositories must be a non-empty list")
    out: list[RepositoryDecl] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, Mapping):
            raise WorkspaceError("repository entry must be a mapping")
        rname = entry.get("name")
        if not isinstance(rname, str) or not _NAME.match(rname) or rname in seen:
            raise WorkspaceError(f"duplicate or invalid repository name: {rname!r}")
        rel = _safe_repo_path(entry.get("path"), rname)
        role = entry.get("role", "shared")
        if role not in ROLES:
            raise WorkspaceError(f"unknown repository role {role!r}: {rname}")
        candidate = base / rel
        if candidate.is_symlink():
            raise WorkspaceError(f"repository path symlink refused: {rname}")
        resolved = resolve_within(base, candidate)
        if resolved is None:
            raise WorkspaceError(f"repository escapes workspace root: {rname}")
        out.append(RepositoryDecl(rname, rel, role, resolved, resolved.is_dir()))
        seen.add(rname)
    return tuple(sorted(out, key=lambda r: r.name))


def _relationships(raw: Any, names: set[str]) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(raw, list):
        raise WorkspaceError("relationships must be a list")
    out: set[tuple[str, str, str]] = set()
    for entry in raw:
        if not isinstance(entry, Mapping):
            raise WorkspaceError("relationship must be a mapping")
        src, rel, dst = (entry.get(k) for k in ("source", "relation", "target"))
        if src not in names or dst not in names:
            raise WorkspaceError(f"relationship references undeclared repository: {src}->{dst}")
        if not isinstance(rel, str) or not _RELATION.match(rel):
            raise WorkspaceError(f"invalid relationship relation: {rel!r}")
        out.add((src, rel, dst))
    return tuple(sorted(out))


def _resources(raw: Any) -> tuple[CloudResourceDecl, ...]:
    if not isinstance(raw, list):
        raise WorkspaceError("cloud_resources must be a list")
    out: list[CloudResourceDecl] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, Mapping):
            raise WorkspaceError("cloud resource must be a mapping")
        rname = entry.get("name")
        if not isinstance(rname, str) or not _NAME.match(rname) or rname in seen:
            raise WorkspaceError(f"duplicate or invalid cloud resource name: {rname!r}")
        arm = entry.get("arm_id")
        dbx = entry.get("databricks_workspace_id")
        url = entry.get("workspace_url")
        fab = entry.get("fabric_workspace_id")
        if arm is not None and not is_arm_id(arm):
            raise WorkspaceError(f"invalid ARM resource id for {rname}")
        if dbx is not None and not DATABRICKS_WORKSPACE_ID_RE.match(str(dbx)):
            raise WorkspaceError(f"invalid databricks_workspace_id for {rname}")
        if url is not None and not re.match(r"^https://[A-Za-z0-9.-]+/?$", str(url)):
            raise WorkspaceError(f"workspace_url must be an https host URL: {rname}")
        if fab is not None and not GUID_RE.match(str(fab)):
            raise WorkspaceError(f"fabric_workspace_id must be a GUID: {rname}")
        if not (arm or dbx or fab):
            raise WorkspaceError(f"cloud resource needs an explicit id: {rname}")
        kind = entry.get("kind") or (kind_for_arm_id(arm) if arm else (
            "databricks_workspace" if dbx else "fabric_workspace"))
        if kind not in NODE_KINDS["azure"]:
            raise WorkspaceError(f"unknown azure kind {kind!r}: {rname}")
        out.append(
            CloudResourceDecl(
                rname, kind, arm.strip().rstrip("/") if arm else None,
                str(dbx) if dbx is not None else None,
                str(url).rstrip("/") if url else None,
                str(fab).lower() if fab else None,
            )
        )
        seen.add(rname)
    return tuple(sorted(out, key=lambda r: r.name))


def _bindings(raw: Any, names: set[str]) -> tuple[Binding, ...]:
    if not isinstance(raw, list):
        raise WorkspaceError("bindings must be a list")
    out: set[Binding] = set()
    for entry in raw:
        if not isinstance(entry, Mapping):
            raise WorkspaceError("binding must be a mapping")
        repo, address, target = (entry.get(k) for k in ("repository", "address", "target"))
        if repo not in names:
            raise WorkspaceError(f"binding references undeclared repository: {repo!r}")
        if not isinstance(address, str) or not address or ".." in address:
            raise WorkspaceError("binding address must be a non-empty string")
        if not isinstance(target, str) or not target:
            raise WorkspaceError("binding target must be a non-empty string")
        out.add(Binding(repo, address.strip(), target.strip()))
    return tuple(sorted(out, key=lambda b: (b.repository, b.address, b.target)))


def _named_list(raw: Any, label: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(raw, list):
        raise WorkspaceError(f"{label} must be a list")
    out = []
    for entry in raw:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("name"), str):
            raise WorkspaceError(f"{label} entries need a name")
        out.append(dict(entry))
    return tuple(sorted(out, key=lambda e: e["name"]))


# -- static graph -------------------------------------------------------------
def repo_node_id(name: str) -> str:
    return node_id("code", "repository", name)


def build_workspace_graph(
    manifest: WorkspaceManifest,
    *,
    use_codeintel: bool = True,
    code_graphs: Mapping[str, Graph] | None = None,
) -> Graph:
    """Static graph: repositories (+ their code graphs), declared resources,
    bindings, domains and boundaries.  ``code_graphs`` supplies already-built
    per-repository code graphs (incremental rebuild, see ``store``)."""

    prov = Provenance("static", f"manifest:{manifest.name}")
    graph = Graph()
    for repo in manifest.repositories:
        attrs = {"path": repo.path, "role": repo.role, "exists": repo.exists}
        graph.add_node(Node(repo_node_id(repo.name), "repository", "code", attrs, prov))
        if not repo.exists:
            graph.add_unresolved({"reason": "repository_missing", "repository": repo.name})
            continue
        if code_graphs is not None and repo.name in code_graphs:
            code = code_graphs[repo.name]
        else:
            code = build_code_graph(repo.resolved, repo=repo.name, use_codeintel=use_codeintel)
        for nid in sorted(code.nodes):
            graph.add_node(code.nodes[nid])
        for key in sorted(code.edges):
            graph.add_edge(code.edges[key])
        for item in code.unresolved:
            graph.add_unresolved({**item, "repository": repo.name})
        for nid, node in code.nodes.items():
            if node.kind in ("file", "test", "config"):
                graph.add_edge(Edge(repo_node_id(repo.name), "contains", nid, {}, prov))
    for src, rel, dst in manifest.relationships:
        graph.add_edge(Edge(repo_node_id(src), rel, repo_node_id(dst), {}, prov))
    for res in manifest.cloud_resources:
        attrs: dict[str, Any] = {"declared_name": res.name, "declared": True}
        for key in ("arm_id", "databricks_workspace_id", "workspace_url", "fabric_workspace_id"):
            value = getattr(res, key)
            if value:
                attrs[key] = value
        graph.add_node(Node(res.node_id, res.kind, "azure", attrs, prov))
    _apply_bindings(graph, manifest, prov)
    for dom in manifest.domains:
        did = node_id("knowledge", "domain", dom["name"])
        graph.add_node(Node(did, "domain", "knowledge", {"name": dom["name"]}, prov))
        for repo_name in dom.get("repositories") or []:
            if manifest.repository(repo_name) is None:
                graph.add_unresolved({"reason": "domain_unknown_repository", "domain": dom["name"],
                                      "repository": repo_name})
                continue
            graph.add_edge(Edge(repo_node_id(repo_name), "member_of", did, {}, prov))
        for res_name in dom.get("cloud_resources") or []:
            res = manifest.resource(res_name)
            if res is None:
                graph.add_unresolved({"reason": "domain_unknown_resource", "domain": dom["name"],
                                      "resource": res_name})
                continue
            graph.add_edge(Edge(res.node_id, "member_of", did, {}, prov))
    for bnd in manifest.boundaries:
        bid = node_id("knowledge", "boundary", bnd["name"])
        attrs = {k: v for k, v in bnd.items() if isinstance(v, (str, int, bool, list))}
        graph.add_node(Node(bid, "boundary", "knowledge", attrs, prov))
        for side in ("source", "target"):
            ref = bnd.get(side)
            if isinstance(ref, str) and manifest.repository(ref) is not None:
                graph.add_edge(Edge(bid, f"constrains_{side}", repo_node_id(ref), {}, prov))
    _check_boundaries(graph, manifest)
    graph.meta = {"workspace": manifest.name, "kind": "static"}
    return graph


def _apply_bindings(graph: Graph, manifest: WorkspaceManifest, prov: Provenance) -> None:
    for b in manifest.bindings:
        source = node_id("code", "symbol", f"{b.repository}/{b.address}")
        res = manifest.resource(b.target)
        if res is None and is_arm_id(b.target):
            target = azure_node_id(b.target)
            if target not in graph.nodes:
                graph.add_node(
                    Node(target, kind_for_arm_id(b.target), "azure",
                         {"arm_id": b.target, "declared": True, "via": "binding"}, prov)
                )
        elif res is None:
            graph.add_unresolved({"reason": "binding_target_undeclared",
                                  "repository": b.repository, "address": b.address,
                                  "target": b.target})
            continue
        else:
            target = res.node_id
        if source not in graph.nodes:
            graph.add_unresolved({"reason": "binding_source_not_found",
                                  "repository": b.repository, "address": b.address,
                                  "target": target})
            continue
        graph.add_edge(Edge(source, "binds_to", target, {"declared": True}, prov))


def _check_boundaries(graph: Graph, manifest: WorkspaceManifest) -> None:
    """A boundary with ``allowed: false`` between two repositories becomes an
    unresolved violation when a declared relationship crosses it."""

    for bnd in manifest.boundaries:
        if bnd.get("allowed", True):
            continue
        src, dst = bnd.get("source"), bnd.get("target")
        for s, rel, d in manifest.relationships:
            if s == src and d == dst:
                graph.add_unresolved({"reason": "boundary_violation", "boundary": bnd["name"],
                                      "relationship": f"{s}-{rel}->{d}"})


__all__ = [
    "MANIFEST_NAME",
    "ROLES",
    "Binding",
    "CloudResourceDecl",
    "RepositoryDecl",
    "WorkspaceError",
    "WorkspaceManifest",
    "build_workspace_graph",
    "load_workspace_manifest",
    "parse_workspace_manifest",
    "repo_node_id",
]
