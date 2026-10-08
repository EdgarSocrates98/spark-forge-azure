"""Deterministic coordinator routing (sections 97 and 107).

The coordinator never fans out to every specialist. Given domain names or free-text terms it
returns the *minimal* ordered list of specialists, capped by ``max_agents``.

Matching is longest-phrase-first with masking: once a phrase is matched its span is consumed,
so ``"fabric data factory"`` routes to Fabric and never also to ADF via ``"data factory"``.
Ordering: more matched phrases first, then canonical specialist order. No model is used.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sparkforge_azure.agentmanifest.model import SPECIALIST_IDS
from sparkforge_azure.skills.registry import normalize

DEFAULT_MAX_AGENTS = 3
MAX_AGENTS_CEILING = 5


@dataclass(frozen=True)
class Route:
    specialist: str
    domain: str
    terms: tuple[str, ...]


#: Routing table: one row per specialist, in canonical order. Rendered into
#: ``agents/coordinator.md`` and checked for consistency by the tests.
ROUTING_TABLE: tuple[Route, ...] = (
    Route("fabric-specialist", "Microsoft Fabric (workspace, Spark, Data Factory do Fabric)",
          ("fabric", "fabric spark", "fabric notebook", "fabric lakehouse", "fabric warehouse",
           "fabric data factory", "dataflow gen2", "fabric capacity", "fabric pipeline")),
    Route("azure-databricks-specialist", "Azure Databricks (compute, jobs, DABs)",
          ("databricks", "azure databricks", "dbr", "cluster policy", "databricks job",
           "asset bundle", "photon", "lakeflow", "dlt", "serverless compute")),
    Route("unity-catalog-specialist", "Unity Catalog (grants, external locations)",
          ("unity catalog", "unity-catalog", "uc", "grant", "external location",
           "storage credential", "workspace binding", "metastore", "catalog binding",
           "permission denied")),
    Route("synapse-specialist", "Azure Synapse Analytics",
          ("synapse", "dedicated sql pool", "serverless sql pool", "synapse spark pool",
           "synapse pipeline", "synapse workspace")),
    Route("adf-specialist", "Azure Data Factory",
          ("adf", "azure data factory", "data factory", "integration runtime",
           "self hosted integration runtime", "linked service", "copy activity",
           "tumbling window")),
    Route("adls-specialist", "ADLS Gen2 / Storage",
          ("adls", "adls gen2", "data lake storage", "acl", "storage account",
           "hierarchical namespace", "abfss", "storage firewall")),
    Route("onelake-specialist", "OneLake (shortcuts, segurança OneLake)",
          ("onelake", "onelake shortcut", "shortcut", "onelake security", "onelake catalog")),
    Route("event-hubs-specialist", "Event Hubs (namespace, partições, Kafka endpoint)",
          ("event hubs", "event hub", "eventhub", "eventhubs", "kafka endpoint",
           "consumer group", "throughput unit", "processing unit", "partition count",
           "capture")),
    Route("streaming-specialist", "Spark Structured Streaming / Fabric RTI",
          ("structured streaming", "streaming", "watermark", "checkpoint", "foreachbatch",
           "availablenow", "readstream", "exactly once", "late data", "eventstream",
           "real time intelligence")),
    Route("purview-specialist", "Microsoft Purview (data map, lineage, classificação)",
          ("purview", "microsoft purview", "lineage", "data map", "scan", "classification",
           "sensitivity label", "glossary")),
    Route("entra-specialist", "Entra ID, Managed Identity, RBAC, Key Vault",
          ("entra", "entra id", "managed identity", "service principal", "rbac",
           "role assignment", "key vault", "workload identity", "secret scope")),
    Route("networking-specialist", "Rede (Private Link, DNS, VNet, NSG)",
          ("private endpoint", "private link", "vnet", "vnet injection", "dns",
           "private dns zone", "nsg", "secure cluster connectivity", "firewall", "egress")),
    Route("finops-specialist", "FinOps (Cost Management, DBU, capacidade)",
          ("cost", "custo", "finops", "billing", "dbu", "capacity units", "reservation",
           "budget", "chargeback", "cost management")),
    Route("spark-performance-specialist", "Performance Spark",
          ("skew", "oom", "out of memory", "shuffle", "spill", "small files", "aqe",
           "broadcast", "partition", "slow job", "job lento", "event log")),
    Route("delta-specialist", "Delta Lake",
          ("delta", "delta lake", "merge", "optimize", "vacuum", "z order", "liquid clustering",
           "deletion vectors", "delta log", "time travel", "change data feed")),
    Route("iceberg-specialist", "Apache Iceberg / UniForm",
          ("iceberg", "apache iceberg", "uniform", "snapshot expiration", "manifest list",
           "iceberg metadata")),
    Route("terraform-specialist", "Terraform (azurerm, databricks provider)",
          ("terraform", "azurerm", "tfstate", "terraform plan", "databricks provider", "hcl")),
    Route("bicep-specialist", "Bicep / ARM",
          ("bicep", "arm template", "what if", "bicepparam")),
    Route("migration-specialist", "Migração (Synapse/HDInsight/on-prem → Databricks/Fabric)",
          ("migration", "migracao", "migrar", "migrate", "lake formation", "glue", "emr",
           "hadoop", "hdinsight", "on prem", "legacy")),
    Route("observability-specialist", "Observabilidade (Azure Monitor, Log Analytics)",
          ("observability", "observabilidade", "azure monitor", "log analytics", "kql",
           "diagnostic settings", "alert", "system tables", "metrics", "telemetry")),
)


def _phrase_index() -> list[tuple[str, int]]:
    """All (normalized phrase, route index) pairs, longest phrase first; deterministic."""
    order = {r.specialist: i for i, r in enumerate(ROUTING_TABLE)}
    pairs: list[tuple[str, int]] = []
    for route in ROUTING_TABLE:
        for term in route.terms:
            pairs.append((normalize(term).strip(), order[route.specialist]))
        pairs.append((normalize(route.specialist.removesuffix("-specialist")).strip(),
                      order[route.specialist]))
    uniq = sorted(set(pairs), key=lambda p: (-len(p[0]), p[0], p[1]))
    return uniq


def match_terms(text: str) -> dict[str, tuple[str, ...]]:
    """The matched phrases per specialist after longest-first masking."""
    hay = normalize(text)
    scores: dict[str, set[str]] = {}
    for phrase, idx in _phrase_index():
        needle = f" {phrase} "
        if needle in hay:
            hay = hay.replace(needle, " | ")
            scores.setdefault(ROUTING_TABLE[idx].specialist, set()).add(phrase)
    return {k: tuple(sorted(v)) for k, v in scores.items()}


def match_scores(text: str) -> dict[str, int]:
    """Number of distinct phrases matched per specialist after longest-first masking."""
    return {k: len(v) for k, v in match_terms(text).items()}


def route(
    query: str | Iterable[str], *, max_agents: int = DEFAULT_MAX_AGENTS
) -> list[str]:
    """Return the minimal ordered list of specialists for ``query`` (capped)."""
    if max_agents < 1 or max_agents > MAX_AGENTS_CEILING:
        raise ValueError(f"max_agents must be within 1..{MAX_AGENTS_CEILING}")
    text = query if isinstance(query, str) else " ; ".join(sorted(query))
    scores = match_scores(text)
    canon = {s: i for i, s in enumerate(SPECIALIST_IDS)}
    ranked = sorted(scores, key=lambda s: (-scores[s], canon[s]))
    return ranked[:max_agents]


def explain_route(
    query: str | Iterable[str], *, max_agents: int = DEFAULT_MAX_AGENTS
) -> list[dict[str, object]]:
    """The route with a per-candidate explanation (spec: route explainability).

    Every specialist appears exactly once: ``selected`` when it made the cut,
    ``below_cap`` when it matched but ranked past ``max_agents``, ``no_match``
    when no phrase survived masking. Deterministic — same query, same report.
    """
    if max_agents < 1 or max_agents > MAX_AGENTS_CEILING:
        raise ValueError(f"max_agents must be within 1..{MAX_AGENTS_CEILING}")
    text = query if isinstance(query, str) else " ; ".join(sorted(query))
    terms = match_terms(text)
    scores = {k: len(v) for k, v in terms.items()}
    canon = {s: i for i, s in enumerate(SPECIALIST_IDS)}
    ranked = sorted(scores, key=lambda s: (-scores[s], canon[s]))
    selected = set(ranked[:max_agents])
    out: list[dict[str, object]] = []
    for specialist in SPECIALIST_IDS:
        matched = list(terms.get(specialist, ()))
        if specialist in selected:
            decision, reason = "selected", f"matched {len(matched)} phrase(s) within cap"
        elif matched:
            decision, reason = "below_cap", f"matched {len(matched)} phrase(s), ranked past cap"
        else:
            decision, reason = "no_match", "no phrase matched"
        out.append({
            "specialist": specialist,
            "matched_terms": matched,
            "score": len(matched),
            "decision": decision,
            "reason": reason,
        })
    out.sort(key=lambda r: (-int(r["score"]), canon[str(r["specialist"])]))
    return out


def render_routing_table() -> str:
    """Markdown routing table embedded in ``agents/coordinator.md``."""
    lines = ["| Domínio | Termos de roteamento | Specialist |", "|---|---|---|"]
    for r in ROUTING_TABLE:
        lines.append(f"| {r.domain} | {', '.join(r.terms[:5])} | `{r.specialist}` |")
    return "\n".join(lines)
