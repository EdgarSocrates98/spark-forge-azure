"""Declared specialist peers of spark-forge-azure (lf-0029).

The two optional specialists this forge may delegate to, and the real CLI
verbs each delegation binds to — inventoried from the audit
(``forge-cli/docs/integration/audit-data.md`` §2.1/§3.1), never invented:

- **data-sentinel-forge** (``data-sentinel``) — runtime diagnostics over
  *exported artifacts*: ``analyze --file --platform databricks`` (driver/
  executor/cluster logs: OOM, skew, shuffle, spill, streaming stalls),
  ``spark explain``, ``spark optimize``, ``sql analyze``, and the
  ``lakehouse`` group (``metadata``/``operation``/``access``/``compat``)
  for Delta/Unity Catalog dumps. **Sentinel has no Azure-cloud verbs** —
  its cloud reads are AWS-only (``glue *``, ``emr *``), which this forge
  deliberately does not declare: every delegation here is LOCAL_READ over
  an artifact already on disk, never an Azure API call. Azure identity
  (Entra ID, managed identity, service principal) therefore never leaves
  this forge's own collect boundary.
- **forge-doctor-data** (``forge-doctor-data``) — static analysis:
  ``scan <path> --format agent`` covering PySpark/Delta review,
  antipatterns, config, dependency hygiene, security, environment
  diagnostics, structure and quality gates.

Everything declared is LOCAL_READ — no capability here mutates anything
and none reaches an Azure API (sentinel and doctor are read-only by
construction — ``read_only_default: true`` in both ``forge.agentic.json``
— and this forge declares no write-capable entrypoint). If a future
sentinel release adds Azure-cloud verbs, they enter as ``external_read``
+ ``network`` + ``external_cost`` here — never silently.
"""

from __future__ import annotations

from sparkforge_azure.delegation.contracts import (
    DeclaredCapability,
    DelegationPolicy,
    SpecialistDelegation,
    SpecialistRef,
)
from sparkforge_azure.delegation.discovery import PeerSpec

__all__ = [
    "SENTINEL",
    "DOCTOR_DATA",
    "PEERS",
    "PEER_BY_PROVIDER",
    "consumer_delegation",
    "CONSUMER_PROVIDER",
    "HANDOFFS_DIR_NAME",
]

CONSUMER_PROVIDER = "spark-forge-azure"
HANDOFFS_DIR_NAME = "delegation/handoffs"

# ---------------------------------------------------------------------------
# data-sentinel-forge — runtime diagnostics over exported artifacts
#
# Verb inventory pinned to data-sentinel-forge cli/__init__.py:
#   analyze --file/-f --platform/-p --json --no-persist    (log or --sql)
#   spark explain --file/-f --platform --json --no-persist
#   spark optimize --sql <file> --json --no-persist
#   sql analyze --file/-f --platform --dialect --json --no-persist
#   lakehouse metadata|operation|access --file/-f --platform --json --no-persist
#   lakehouse compat --runtime --operation --table-format --json
#   capabilities --descriptors
#
# `--platform databricks` is the Azure-relevant value of sentinel's own
# Platform enum — declared literally in each entrypoint, never forwarded
# from an untrusted input.
# ---------------------------------------------------------------------------

SENTINEL = PeerSpec(
    provider="data-sentinel-forge",
    cli="data-sentinel",
    dist_names=("data-sentinel", "data-sentinel-forge", "data_sentinel"),
    capabilities_probe=("capabilities", "--descriptors"),
    capabilities=(
        DeclaredCapability(
            id="sentinel.databricks-logs",
            description=(
                "Runtime log diagnostics over exported Databricks artifacts "
                "— driver/executor/cluster logs: OOM, data skew, shuffle, "
                "spill, executor loss, streaming microbatch stalls"
            ),
            intents=["runtime-diagnostics", "databricks-diagnostics",
                     "spark-logs", "oom", "data-skew", "shuffle", "spill",
                     "runtime-logs", "streaming", "event-hubs", "pipelines"],
            entrypoint=["{cli}", "analyze", "--file", "{target}",
                        "--platform", "databricks", "--json", "--no-persist"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
        DeclaredCapability(
            id="sentinel.spark-explain",
            description=(
                "Physical Spark plan analysis (Databricks EXPLAIN output)"
            ),
            intents=["runtime-diagnostics", "spark-explain", "physical-plan"],
            entrypoint=["{cli}", "spark", "explain", "--file", "{target}",
                        "--platform", "databricks", "--json", "--no-persist"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
        DeclaredCapability(
            id="sentinel.sql-optimize",
            description=(
                "Composite SQL analysis — static + joins/cardinality "
                "(heavy SQL on Databricks SQL / Synapse-shaped queries)"
            ),
            intents=["runtime-diagnostics", "sql-analysis", "heavy-sql"],
            entrypoint=["{cli}", "spark", "optimize", "--sql", "{target}",
                        "--dialect", "{dialect}", "--json", "--no-persist"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
        DeclaredCapability(
            id="sentinel.sql-analyze",
            description="Static analysis of heavy SQL (joins, antipatterns)",
            intents=["runtime-diagnostics", "sql-analysis", "heavy-sql"],
            entrypoint=["{cli}", "sql", "analyze", "--file", "{target}",
                        "--platform", "databricks", "--dialect", "{dialect}",
                        "--json", "--no-persist"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
        DeclaredCapability(
            id="sentinel.delta-metadata",
            description=(
                "Delta Lake / Iceberg metadata analysis (exported "
                "metadata.json — table layout, snapshots, runtime issues; "
                "Unity Catalog or ADLS-backed tables alike)"
            ),
            intents=["runtime-diagnostics", "delta-lake", "lakehouse",
                     "delta-metadata", "unity-catalog"],
            entrypoint=["{cli}", "lakehouse", "metadata", "--file", "{target}",
                        "--platform", "databricks", "--json", "--no-persist"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
        DeclaredCapability(
            id="sentinel.lakehouse-operation",
            description=(
                "Lakehouse operation analysis — MERGE/APPEND/DDL on Delta "
                "(SQL is analyzed, never executed)"
            ),
            intents=["runtime-diagnostics", "delta-lake", "lakehouse",
                     "merge-operations"],
            entrypoint=["{cli}", "lakehouse", "operation", "--file", "{target}",
                        "--platform", "databricks", "--json", "--no-persist"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
        DeclaredCapability(
            id="sentinel.lakehouse-access",
            description=(
                "Lakehouse access analysis — Unity Catalog grants / access "
                "policy dumps (read-only review of an exported artifact)"
            ),
            intents=["runtime-diagnostics", "lakehouse", "unity-catalog",
                     "access-control"],
            entrypoint=["{cli}", "lakehouse", "access", "--file", "{target}",
                        "--platform", "databricks", "--json", "--no-persist"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
        DeclaredCapability(
            id="sentinel.lakehouse-compat",
            description=(
                "Offline compatibility assessment — knowledge-base verdict "
                "for runtime/operation/table-format (e.g. a Databricks "
                "runtime + merge + delta)"
            ),
            intents=["runtime-diagnostics", "delta-lake", "lakehouse",
                     "compat-check"],
            entrypoint=["{cli}", "lakehouse", "compat",
                        "--runtime", "{runtime}",
                        "--operation", "{operation}",
                        "--table-format", "{table_format}", "--json"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=60,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
    ),
    expected_descriptor_ids=(),
)

# ---------------------------------------------------------------------------
# forge-doctor-data — static analysis
#
# Verb surface pinned to forge-doctor-data cli/scan.py + cli/common.py:
#   scan [PATH] --format text|json|html|sarif|agent --check CATEGORY
#       --quiet --fail-on error|warning --no-plugins --files --output
#   --version (callback), capabilities list|explain|graph
# The `agent` format emits scan-json@3.0: {tool, version, schema_version,
# project, summary, findings: [{id, sev, loc, fp}]}.
# ---------------------------------------------------------------------------

DOCTOR_DATA = PeerSpec(
    provider="forge-doctor-data",
    cli="forge-doctor-data",
    dist_names=("forge-doctor-data", "forge_doctor_data"),
    capabilities_probe=None,  # no descriptor verb; version probe is the handshake
    capabilities=(
        DeclaredCapability(
            id="doctor.scan-project",
            description=(
                "Static project scan — PySpark/Delta review, antipatterns, "
                "config, dependency hygiene, security, environment "
                "diagnostics, structure and quality gates "
                "(scan-json@3.0 agent output)"
            ),
            intents=["static-analysis", "pyspark-review", "antipatterns",
                     "config", "deps-hygiene", "security",
                     "env-diagnostics", "structure", "quality-gates"],
            entrypoint=["{cli}", "scan", "{target}", "--format", "agent",
                        "--check", "{check}"],
            execution_mode="local",
            risk="read_only",
            external_cost="none",
            timeout_s=300,
            discovery_mode="probe",
            verification_mode="handshake",
        ),
    ),
)

PEERS: tuple[PeerSpec, ...] = (SENTINEL, DOCTOR_DATA)
PEER_BY_PROVIDER: dict[str, PeerSpec] = {p.provider: p for p in PEERS}

# Intents the consumer declares it may need. They are the routing surface of
# ``router.plan_delegation`` — a task names them; the router matches tokens.
# Azure contexts only: Databricks, Delta, lakehouse, streaming/Event Hubs,
# pipelines — never AWS vocabulary (no glue/emr intents exist here).
_SENTINEL_INTENTS = [
    "runtime-diagnostics",
    "databricks-diagnostics",
    "spark-logs",
    "oom",
    "data-skew",
    "shuffle",
    "spill",
    "runtime-logs",
    "streaming",
    "event-hubs",
    "pipelines",
    "spark-explain",
    "physical-plan",
    "sql-analysis",
    "heavy-sql",
    "delta-lake",
    "lakehouse",
    "delta-metadata",
    "unity-catalog",
    "merge-operations",
    "access-control",
    "compat-check",
]

_DOCTOR_INTENTS = [
    "static-analysis",
    "pyspark-review",
    "antipatterns",
    "config",
    "deps-hygiene",
    "security",
    "env-diagnostics",
    "structure",
    "quality-gates",
]


def consumer_delegation() -> SpecialistDelegation:
    """The ``theforge/SpecialistDelegation/v1`` declaration of spark-forge-azure.

    Both specialists are ``optional`` — absent peers degrade to the named
    fallback (``native-analysis``: this forge's own extractors/judges),
    never to a simulated execution.
    """
    return SpecialistDelegation(
        consumer=CONSUMER_PROVIDER,
        specialists=[
            SpecialistRef(
                provider=SENTINEL.provider,
                optional=True,
                intents=list(_SENTINEL_INTENTS),
            ),
            SpecialistRef(
                provider=DOCTOR_DATA.provider,
                optional=True,
                intents=list(_DOCTOR_INTENTS),
            ),
        ],
        policy=DelegationPolicy(
            discovery="runtime",
            execution="governed",
            preserve_evidence=True,
            fallback="native-analysis",
        ),
    )
