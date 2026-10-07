"""SparkForge Context Engineering Package."""
from __future__ import annotations

from sparkforge_azure.context.context_tree import ContextTreeEntry, build_context_tree
from sparkforge_azure.context.funnel import ContextChunk, ContextFunnel, MinimalContext
from sparkforge_azure.context.gateway import ContextGateway, GatewayError
from sparkforge_azure.context.gateway_models import GatewayProfile, GatewayRequest
from sparkforge_azure.context.host_usage import HostTokenState
from sparkforge_azure.context.knowledge_pack import KnowledgePack, KnowledgePackLoader
from sparkforge_azure.context.planner import ExecutionPlan, plan_execution
from sparkforge_azure.context.progressive import (
    KnowledgeLevelA,
    KnowledgeLevelB,
    KnowledgeLevelC,
    ProgressiveDisclosureManager,
)
from sparkforge_azure.context.quality import (
    ContextObservation,
    ContextQualityReport,
    CounterfactualContextBenchmark,
    MinimumSufficientContextBenchmark,
)

__all__ = [
    "ContextChunk",
    "ContextFunnel",
    "MinimalContext",
    "KnowledgePack",
    "KnowledgePackLoader",
    "KnowledgeLevelA",
    "KnowledgeLevelB",
    "KnowledgeLevelC",
    "ProgressiveDisclosureManager",
    "ContextGateway",
    "GatewayError",
    "GatewayProfile",
    "GatewayRequest",
    "HostTokenState",
    "ExecutionPlan",
    "plan_execution",
    "ContextTreeEntry",
    "build_context_tree",
    "ContextObservation",
    "ContextQualityReport",
    "CounterfactualContextBenchmark",
    "MinimumSufficientContextBenchmark",
]
