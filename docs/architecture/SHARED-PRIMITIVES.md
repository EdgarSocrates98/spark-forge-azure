# Shared Primitives — Spark Forge AWS × Spark Forge Azure × API Forge (§193)

> Inventário comparativo. **Não extrair código** (§194) e **não criar Forge Kernel** (§192):
> este documento é a evidência que um kernel futuro (§293) precisaria.

Referências medidas em 2026-10-06:
- Spark Forge AWS @ `6b1b97a` (`sparkforge/`, Python ≥3.10, dataclasses).
- API Forge @ working tree local (`src/apiforge/`, Python 3.12, Pydantic v2, contratos versionados `apiforge/<name>/v1`).
- Spark Forge Azure (este repo, `sparkforge_azure/`).

## Forge Protocol — divergência real

| Conceito | Spark Forge AWS (`protocols/forge.py`) | API Forge (`contracts/forge_protocol.py`) | Spark Forge Azure |
|---|---|---|---|
| Capability | `ForgeCapability{name, version, domains, operations, trust_floor}` | `ForgeCapabilityDescriptor{capability_id, operation, state, risk, surfaces, evidence, limitations}` | AWS shape (COPY_SAFE) **+** `to_apiforge_descriptor()` |
| Task | `ForgeTask{task_type, objective, inputs, budget, requested_by, risk}` id=hash | `ForgeTaskRequest{task_id, capability_id, intent, inputs, budgets, risk, origin_engine…}` | AWS shape + adaptador |
| Evidence | `ForgeEvidenceBundle{facts, findings, evidence_refs, unresolved}` | `ForgeEvidenceBundle{task_id, artifacts[path,kind], produced_at, unresolved}` | AWS shape + adaptador |
| Result | `ForgeResult{task_id, status, summary, evidence, metrics, rollback}` | `ForgeTaskResult{task_id, status, payload, evidence, gaps, limitations, error_code}` | AWS shape + adaptador |
| Health | `ForgeHealth{status, version, capabilities[], checks}` | `ForgeHealth{engine, protocol_version, state, capabilities:int, tasks_by_state, unresolved}` | AWS shape + adaptador |
| Handoff | `ForgeHandoff{…, authority="DATA_ONLY"}` | `ForgeHandoff{…, delivery="prepared"}` | AWS shape, `authority` fixo `DATA_ONLY` |
| Discovery | — | registry de contracts | `forge describe` → `{engine, provider:"azure", domain:"data", protocol_version, capabilities}` (§188) |

**Conclusão:** os dois Forges existentes **não** são wire-compatíveis. O Azure não escolhe um
vencedor: mantém paridade com o irmão (AWS) e oferece tradução determinística e testada para o
schema API Forge (`sparkforge_azure/protocols/apiforge_compat.py`). Unificação fica para o The
Forger ou kernel futuro, com esta tabela como insumo.

## Primitivas agentic/economia

| Primitiva | AWS | API Forge | Azure | Semântica equivalente? |
|---|---|---|---|---|
| TrustEnvelope / taint / DATA_ONLY | `agentic/trust.py` | contratos de agentic state | copiado | AWS≡Azure; API Forge parcial |
| RoleContextPlan | `agentic/role_plans.py` | — | copiado | AWS≡Azure |
| StopPolicy (STOP_* / CONTINUE / REVIEW / DEBATE / HUMAN) | `agentic/stop.py` | — | copiado | AWS≡Azure |
| Recovery taxonomy | `agentic/recovery.py` | — | copiado + falhas Azure (`authentication_failure`, `authorization_failure`, `network_failure`) | superconjunto |
| Semantic Checkpoint | `agentic/checkpoint.py` | `runtime/semantic_checkpoint.py` | copiado | campos diferentes; mesma intenção |
| Token Ledger | `economy/ledger.py` | `economy/token_ledger.py` | copiado | ambos separam observed/estimated |
| Context Ledger | `observability/context_ledger.py` | — | copiado | AWS≡Azure |
| AgentOps waste | `economy/waste_detector.py`, `observability/agentops.py` | `evals/agentops.py` | copiado | categorias sobrepostas |
| Decision Memory | `agentic/memory.py` | `contracts/agentic_memory.py` | adaptado (fingerprint Azure) | intenção igual, schema diferente |
| Surface lock | `docs/surface.lock.json` (bytes por superfície) | — | adaptado (nome+schema hash por tool e comando) | Azure é superconjunto |
| Claims lock | `docs/claims.lock.json` | — | adaptado | AWS≡Azure (campos) |
| Supply chain audit | `scripts/gen_lock.py`, `gen_sbom.py` | `scripts/supply_chain_audit.py` | adaptado | — |

## Candidatos a kernel futuro (somente evidência, sem ação)

Repetidos e semanticamente equivalentes em ≥2 Forges: TrustEnvelope/DATA_ONLY, Token Ledger
(observed≠estimated), Semantic Checkpoint, AgentOps waste categories, claims lock.
Divergentes (não extrair): Forge Protocol wire shapes, Decision Memory schema.
