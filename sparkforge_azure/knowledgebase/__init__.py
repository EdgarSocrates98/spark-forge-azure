"""Base de conhecimento Azure versionada: contrato, frescor, matrizes, expansao,
impacto e carga preguicosa. Stdlib + PyYAML apenas."""
from __future__ import annotations

from sparkforge_azure.knowledgebase.expansion import (
    Expansion,
    ExpansionError,
    ExpansionRule,
    expand,
    load_rules,
    parse_rules,
    validate_targets,
)
from sparkforge_azure.knowledgebase.freshness import (
    DEFAULT_MAX_AGE_DAYS,
    Freshness,
    freshness,
    freshness_report,
)
from sparkforge_azure.knowledgebase.impact import impact, knowledge_closure
from sparkforge_azure.knowledgebase.loader import KnowledgeBase, load_body, load_index, select
from sparkforge_azure.knowledgebase.matrices import (
    Matrix,
    MatrixError,
    load_matrices,
    load_matrix,
    parse_matrix,
    validate_matrix,
)
from sparkforge_azure.knowledgebase.metadata import (
    AUTHORITIES,
    DOMAINS,
    STATUSES,
    KnowledgeEntry,
    KnowledgeError,
    Source,
    load_entries,
    validate_front_matter,
    validate_graph,
)

__all__ = [
    "AUTHORITIES",
    "DEFAULT_MAX_AGE_DAYS",
    "DOMAINS",
    "STATUSES",
    "Expansion",
    "ExpansionError",
    "ExpansionRule",
    "Freshness",
    "KnowledgeBase",
    "KnowledgeEntry",
    "KnowledgeError",
    "Matrix",
    "MatrixError",
    "Source",
    "expand",
    "freshness",
    "freshness_report",
    "impact",
    "knowledge_closure",
    "load_body",
    "load_entries",
    "load_index",
    "load_matrices",
    "load_matrix",
    "load_rules",
    "parse_matrix",
    "parse_rules",
    "select",
    "validate_front_matter",
    "validate_graph",
    "validate_matrix",
    "validate_targets",
]
