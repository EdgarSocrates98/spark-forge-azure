"""Peer-to-peer delegation for spark-forge-azure (lf-0029).

Optional, governed delegation to sibling forges — ``data-sentinel-forge``
(runtime diagnostics over exported Databricks/Delta/lakehouse artifacts)
and ``forge-doctor-data`` (static analysis) — with the same contract
shapes the-forge defines natively (``theforge/SpecialistCapability/v1``,
``theforge/SpecialistDelegation/v1``, ``theforge/EvidenceHandoff/v1``).
sparkforge_azure never imports a sibling forge; this package re-implements
the semantics locally over the real CLI surfaces (``data-sentinel …``,
``forge-doctor-data …``).

Azure boundary (AGENTS.md): no Azure-cloud verb is declared — sentinel's
cloud reads are AWS-only, and Azure identity (Entra ID, managed identity,
service principal) never leaves this forge's own collect boundary. Absent
specialist → explicit discovery state + the declared ``native-analysis``
fallback — never a simulated execution.
"""

from sparkforge_azure.delegation.contracts import (  # noqa: F401
    DELEGATION_FAILURES,
    DELEGATION_RISKS,
    DISCOVERY_STATES,
    EVIDENCE_HANDOFF_SCHEMA,
    SPECIALIST_CAPABILITY_SCHEMA,
    SPECIALIST_DELEGATION_SCHEMA,
    DeclaredCapability,
    DelegationChain,
    DelegationError,
    DelegationPlan,
    DelegationPolicy,
    DelegationRefusal,
    EvidenceHandoff,
    EvidenceRef,
    ExecResult,
    HandoffError,
    HandoffFinding,
    PeerDiscovery,
    PeerDiscoveryReport,
    SpecialistCapability,
    SpecialistDelegation,
    SpecialistIdentity,
    SpecialistRef,
)
from sparkforge_azure.delegation.discovery import (  # noqa: F401
    PeerSpec,
    discover_peer,
    discover_peers,
)
from sparkforge_azure.delegation.execute import run_governed  # noqa: F401
from sparkforge_azure.delegation.governance import (  # noqa: F401
    admit_hop,
    bound_handoff,
    capability_risks,
    gate_capability,
    idempotency_key,
    may_retry,
    new_correlation_id,
    redact_handoff,
    resolve_capability_argv,
    seal_handoff,
    start_chain,
    verify_integrity,
)
from sparkforge_azure.delegation.peers import (  # noqa: F401
    DOCTOR_DATA,
    PEERS,
    SENTINEL,
    consumer_delegation,
)
from sparkforge_azure.delegation.router import plan_delegation  # noqa: F401
from sparkforge_azure.delegation.run import (  # noqa: F401
    delegate,
    discover,
    handoffs,
    plan,
)
