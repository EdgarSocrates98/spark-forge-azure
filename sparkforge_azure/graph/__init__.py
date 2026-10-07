"""Graphfy: the semantic/workspace graph of the Forge (layer L3).

Infrastructure for retrieval, impact analysis, context expansion, workspace
understanding, knowledge linking and change analysis -- not visualization.
Layers: code | data | azure | knowledge | evidence.  Composition only by
explicit ids, declared bindings or verified references (never by name).
Stdlib + PyYAML only.  See docs/architecture/GRAPHFY.md.
"""

from __future__ import annotations

from sparkforge_azure.graph.adapters import (
    from_fragment,
    knowledge_graph,
    read_front_matter,
    to_fragment,
)
from sparkforge_azure.graph.arm import is_arm_id, kind_for_type, parse_arm_id
from sparkforge_azure.graph.federation import FederationResult, federate
from sparkforge_azure.graph.impact import impact
from sparkforge_azure.graph.live import live_graph_from_facts
from sparkforge_azure.graph.model import (
    LAYERS,
    NODE_KINDS,
    PROVENANCE_KINDS,
    Edge,
    Graph,
    GraphError,
    Node,
    Provenance,
    azure_node_id,
    node_id,
)
from sparkforge_azure.graph.query import find_nodes, neighbors, shortest_path, slice_graph
from sparkforge_azure.graph.semantic import build_code_graph
from sparkforge_azure.graph.store import build_incremental, load_graph, save_graph
from sparkforge_azure.graph.workspace import (
    MANIFEST_NAME,
    WorkspaceError,
    WorkspaceManifest,
    build_workspace_graph,
    load_workspace_manifest,
    parse_workspace_manifest,
)

__all__ = [
    "LAYERS",
    "MANIFEST_NAME",
    "NODE_KINDS",
    "PROVENANCE_KINDS",
    "Edge",
    "FederationResult",
    "Graph",
    "GraphError",
    "Node",
    "Provenance",
    "WorkspaceError",
    "WorkspaceManifest",
    "azure_node_id",
    "build_code_graph",
    "build_incremental",
    "build_workspace_graph",
    "federate",
    "find_nodes",
    "from_fragment",
    "impact",
    "is_arm_id",
    "kind_for_type",
    "knowledge_graph",
    "live_graph_from_facts",
    "load_graph",
    "load_workspace_manifest",
    "neighbors",
    "node_id",
    "parse_arm_id",
    "parse_workspace_manifest",
    "read_front_matter",
    "save_graph",
    "shortest_path",
    "slice_graph",
    "to_fragment",
]
