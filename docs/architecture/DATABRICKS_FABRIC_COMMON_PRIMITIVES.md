# Databricks × Fabric — primitivos compartilhados (Cycle 3)

Dois verticais profundos, uma infraestrutura. Este documento registra o
que é **comum por decisão** (reuso medido) e o que é **diferente por
domínio** (separação medida) — a fronteira que o Cycle 3 explicitou.

## Compartilhado (nunca duplicado)

| Primitivo | Módulo | Usado por |
|---|---|---|
| Fact/Finding/Verdict | `facts`, `findings`, `azure.governance.model` | access + fabric |
| Rule engine + catálogo | `rules` (`SF-ACC`, `SF-PY`, `SF-FAB`) | ambos |
| Evidence paths | `graph` evidence builder | ambos |
| AgentOps spans/ledger | `agentic` (`fabric.*`/`diagnose.*`) | ambos |
| Trust/taint DATA_ONLY | `agentic.trust` | ambos |
| Receipt | `azure.receipt` | ambos |
| Knowledge scoping | `knowledgebase.vertical` + `packs.yaml` | ambos |
| Collector boundary (redact → assert_clean → facts) | `collectors.base` | ambos |
| Notebook AST scanner | `facts.notebook_scan`, `facts.pyspark_ast` | ambos |
| TokenSave benchmark/frontier | `evals.token_efficient` | ambos |
| Surface lock, claims, doctor | `scripts/`, `doctor.py` | ambos |
| `paths.state_dir()` | `paths` | ambos |

## Separado (domínio, não duplicação de infra)

| Eixo | Databricks/UC (Cycle 2) | Fabric (Cycle 3) |
|---|---|---|
| Plano | ARM (workspace é recurso ARM) | SaaS (workspace ≠ ARM — nunca fabricar ARM id) |
| Case loader | `azure/casefile.py` | `fabric/casefile.py` |
| Diagnosis chain | `azure/pipeline.py` | `fabric/diagnose.py` (chain própria) |
| Graph layer | `azure` (kinds ARM) | `fabric` (17 kinds SaaS) |
| Regras | `SF-ACC-*` | `SF-FAB-*` (catalogo separado) |
| Failure layers | `unity_catalog`, `azure_rbac`, `adls_acl`, … | `fabric_workspace`, `onelake_security`, `shortcut_auth`, `capacity`, … |
| CLI | `diagnose --bundle` | `diagnose fabric --bundle` |
| MCP | `sfa_diagnose_access` | `sfa_diagnose_fabric` |
| Identidade | Entra ID / managed identity → RBAC/ACL | workspace roles + item permissions + OneLake roles + delegated effective identity |

## Decisões registradas

- **Grafo**: novo layer `fabric` no registry (`graph/model.py`) — o modelo
  SaaS do Fabric não cabe no layer ARM sem equivalência falsa (invariante
  7 do AGENTS.md).
- **Regras**: `SF-FAB-*` em `rules/catalog/fabric.yaml`; `SF-PY-*` é
  compartilhado (notebook Fabric é PySpark — mesmo scanner, mesmo
  catálogo).
- **Fingerprint de ambiente**: `fabric/fingerprint.py` ancora memória a
  tenant/capacity/workspace — reuso cross-environment exige match
  explícito.
- **Waste**: `fabric/waste.py` detecta fetches repetidos / list-after-
  graph-hit sobre spans AgentOps — sempre `evidence: hypothesis`.
