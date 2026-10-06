# AWS → Azure Portability Matrix

> Fase 0 (Discovery), §5 do prompt fundacional. Documento normativo: toda capability do
> Spark Forge AWS aparece aqui com uma classificação e uma justificativa. **Nenhuma
> omissão silenciosa** (§265).

- Referência auditada: `EdgarSocrates98/spark-forge-aws` @ `6b1b97a137d7397ff6c7a98f7fe7be100132983f` (`main`, v0.5.0).
- Evidência bruta (determinística, regenerável): [`evidence/aws_audit.json`](evidence/aws_audit.json),
  produzida por `python scripts/aws_portability_audit.py <aws-checkout> --out docs/architecture/evidence/aws_audit.json`.
- Totais medidos: **422 módulos, 145 139 linhas**, 133 módulos com marcadores AWS
  (`boto3`, `arn:aws`, Glue, Lake Formation, EMR, S3, Athena, CloudWatch, IAM, Kinesis/MSK).
- Versão máquina-legível (status de implementação + testes): [`/parity.yaml`](../../parity.yaml).
- Proveniência arquivo-a-arquivo do que foi copiado: [`evidence/provenance.json`](evidence/provenance.json).

## Classes (§5–§10)

| Classe | Critério de entrada | Obrigação ao portar |
|---|---|---|
| `COPY_SAFE` | 0 marcadores AWS **e** dependências internas fecham em módulos também COPY_SAFE | cópia com rename de pacote apenas (`sparkforge.` → `sparkforge_azure.`); testes portados **e** teste Azure-contexto |
| `ADAPT` | núcleo neutro, mas há campo/termo/caminho provider-specific ou aresta para módulo AWS | adaptação explícita documentada em `provenance.json` (`changes`) |
| `REIMPLEMENT_AZURE_NATIVE` | semântica AWS ≠ Azure (IAM, Lake Formation, Glue Catalog, S3, EMR) | implementação nova; **proibido** alias (§8, §269) |
| `NOT_APPLICABLE` | capability sem análogo útil no Azure | justificar; nenhuma abstração falsa (§9) |
| `DEFER` | sem caso real, dependência externa, preview, ou evidência insuficiente | justificar e apontar gatilho de reabertura |

Regra do copy test (§267): o script de cópia (`scripts/port_from_aws.py`) **recusa** copiar
arquivo com marcador AWS sem que a entrada correspondente declare `ADAPT` e liste as mudanças.

## 1. Sistemas internos obrigatórios (§263)

| Capability AWS | Onde vive no AWS | Classe | Azure — decisão |
|---|---|---|---|
| Agentic Runtime (trust, handoff, governor, budget, stop, recovery, checkpoint, debate, referee, arbitration, blackboard) | `sparkforge/agentic/*` (36 arq., 12k LOC, 29 marcadores concentrados em `executor/`, `memory`, `security`, `evidence`) | `COPY_SAFE` (núcleo) / `ADAPT` (`memory`, `security`, `evidence`, `executor/*`) | Núcleo copiado. `memory` ganha fingerprint Azure (tenant/subscription/workspace/DBR/Fabric runtime, §129). `executor/*` depende de `rules.loader`/`case.store` → portado em onda posterior. |
| Decision Plane (SHADOW/ASSISTED/ACTIVE) | `sparkforge/decision/*`, `economy/decision_*` | `COPY_SAFE` | 0 marcadores, 0 deps externas além de PyYAML. |
| Model Router + scorecards + champion/challenger | `economy/model_router.py`, `economy/router.py`, `agentic/shadow.py` | `COPY_SAFE` / `ADAPT` (`router.py`: 4 marcadores — Bedrock) | Provider list sem Bedrock-default; routing por capability, não por provedor de nuvem. |
| Context Gateway, RoleContextPlan, Context Quality | `sparkforge/context/*` | `COPY_SAFE` | Profiles `economy/balanced/deep` (§46). |
| Context Ledger | `observability/context_ledger.py` | `COPY_SAFE` | — |
| Token Ledger + Economy Reconciliation | `economy/ledger.py`, `economy/reconcile.py` | `COPY_SAFE` | Invariantes `OBSERVED≠ESTIMATED`, `UNKNOWN≠0`, `BYTES≠TOKENS` com teste próprio. |
| Waste Detector | `economy/waste_detector.py` | `COPY_SAFE` | — |
| AgentOps (inspect/compare/baseline/timeline/waste/coverage) | `observability/agentops.py` | `COPY_SAFE` | Separado de Azure Observability (§145). |
| OpenTelemetry | `observability/otlp.py`, `tracer.py` | `COPY_SAFE` | Export OTLP opcional; sem SDK obrigatório no core. |
| TokenSave | **não existe com esse nome no AWS**: funções espalhadas em `codeintel/{search,refs,context,budget}`, `context/progressive.py`, `economy/recall.py` | `ADAPT` → **capability explícita nova** `sparkforge_azure/tokensave/` | §40 exige capability nomeada; AWS tem as peças, não o subsistema. Retrieval ladder L0–L6 (§43) implementada como máquina de estados. |
| Code Intelligence | `sparkforge/codeintel/*` (18 arq., 8.7k LOC, 2 marcadores em `security.py`) | `ADAPT` | Deps em `facts.scan` (neutro, copiado) e `facts.pyspark_ast` (`GlueContext` → adaptado). Formatos Azure novos: Bicep, Terraform `azurerm`, ADF pipeline JSON, notebooks Databricks (`# COMMAND ----------`), Fabric notebook source (§51). |
| Semantic / Workspace Graph | `workspace/{semantic,graph,impact,federated,federation}.py` | `ADAPT` → **Graphfy** (`sparkforge_azure/graph/`) | Nome Graphfy (§55): semantic/workspace graph do Forge. Code/Data/Azure Resource/Knowledge/Evidence graphs (§57–§61). |
| Live Graph | `collect/live_graph.py` | `REIMPLEMENT_AZURE_NATIVE` | Fonte = Azure Resource Graph (§177), não AWS Config/API. Composição só por ID ARM explícito (§64). |
| Workspace Federation | `workspace/federated.py` | `ADAPT` | Static + live + artifact + knowledge (§67). |
| Workspace Manifest | `workspace/manifest.py` (2 marcadores) | `ADAPT` | `cloud_resources` declara IDs ARM / Databricks workspace URL / Fabric workspace ID. |
| Doctor | `sparkforge/doctor.py` (5 marcadores) | `ADAPT` | Áreas §80; inspeção somente, sem mutação de nuvem (§81). |
| Offline Bundle | `scripts/verify_offline_bundle.py` + journal | `ADAPT` | `sparkforge-azure offline-bundle` com redator obrigatório (§84). |
| Knowledge Compiler | `knowledge_engine/compiler.py`, `packs.py` | `COPY_SAFE` | Lazy (§71); expansão determinística de query (§72) com termos Azure. |
| Knowledge freshness / drift | `knowledge_freshness.py`, `knowledge_drift.py` | `ADAPT` | Estados §162; impacto em rules/skills/agents/evals/docs (§163). |
| Knowledge Impact Graph | parcial em `knowledge_drift.py` | `ADAPT` | Arestas knowledge→rule/skill/agent/eval no Graphfy. |
| Claims + Claim Lock | `docs/claims.lock.json`, `scripts/check_vnext_claims.py` | `ADAPT` | `claims.lock.json` com `claim_id`, `proof.cmd`, `expect`, `sha` (§85). |
| Proofs | `sparkforge/proof/*` | `COPY_SAFE` | dep `rules.loader` portada junto. |
| Receipts | `sparkforge/receipt/*` | `ADAPT` | `_hash` depende de `findings.models` (adaptado). |
| Surface Lock | `observability/surface.py`, `docs/surface.lock.json`, `scripts/check_surface_lock.py` | `ADAPT` | Cobre CLI commands, MCP tools, schemas, capabilities (§87) — AWS cobre bytes de tools/skills/knowledge; Azure adiciona hash por nome+schema e lista de comandos CLI. |
| Capability Manifest | `manifest.json` | `ADAPT` | Gerado, não escrito à mão; contém `provider=azure`, `domain=data` (§188). |
| Parity Matrix | `parity.yaml` (host-platform parity) | `ADAPT` | No AWS, `parity.yaml` é paridade entre **hosts** (Claude Code/Devin/Codex). No Azure, `parity.yaml` cobre AWS capability ↔ Azure status (§90) **e** mantém seção `hosts`. |
| Forge Lab + Digital Twin | `sparkforge/lab/*`, `lab/`, `labs/forge-lab` | `ADAPT` (núcleo) / `REIMPLEMENT_AZURE_NATIVE` (`lab/aws.py`, cenários) | Twin determinístico de tenant/subscription/RG/workspace/storage/identity/network/catalog/runtime (§169); 17 cenários (§170). |
| MCP | `adapters/mcp.py`, `mcp_compact.py`, `mcp_envelope.py` (30k LOC em `adapters/`, 914 marcadores) | `ADAPT` (plumbing) / `REIMPLEMENT_AZURE_NATIVE` (inventário de tools) | Plumbing genérico: registro com risco declarado, compact mode, paginação, envelope. Unknown risk → DENY (§154). |
| Forge Protocol | `sparkforge/protocols/forge.py`, `a2a_adapter.py` | `COPY_SAFE` | Contratos byte-compatíveis (`ForgeCapability`, `ForgeTask`, `ForgeEvidenceBundle`, `ForgeResult`, `ForgeHealth`, `ForgeHandoff`) — teste de compatibilidade de serialização. |
| SDD machinery | `sparkforge/sdd/*` | `ADAPT` | deps `case`, `change`, `facts.scan`, `receipt` — portadas. Fluxo DISCOVER→SHIP (§165). |
| Supply Chain | `scripts/gen_lock.py`, `gen_sbom.py`, `verify_wheel.py`, `locks/` | `ADAPT` | Lock com hashes via `uv`; SBOM CycloneDX; wheel reprodutível; clean-install em venv. |
| CI | `.github/workflows/{ci,release,refresh-knowledge}.yml` | `ADAPT` | Tiers fast/full/security/scheduled (§202). |
| Policy / autonomy | `sparkforge/policy/*`, `agents/autonomy.py` | `ADAPT` | Cloud mutation default deny (§208). |
| Registry (agents/models/tools) | `sparkforge/registry/*` | `ADAPT` | `models.py`: 2 marcadores (Bedrock). |
| Case store / resume / router | `sparkforge/case/*` | `ADAPT` | `resume` depende de `collect` (AWS) → aresta cortada. Cross-process resume (§134). |
| Journal | `sparkforge/journal/*` | `COPY_SAFE` | — |
| Evals harness | `sparkforge/evals/*` | `ADAPT` | Pirâmide Tier 0–4 (§171). |

## 2. Núcleo de análise (facts → rules → findings)

| Capability AWS | Classe | Azure — decisão |
|---|---|---|
| `findings/models.py` (`Fact`, `Finding`, `RuntimeContext` com `glue`, `emr`, `athena`) | `ADAPT` | `RuntimeContext` com `spark`, `databricks_runtime`, `fabric_runtime`, `synapse_runtime`, `delta`, `iceberg`. Nunca reaproveitar `glue` como "runtime genérico". |
| `rules/engine.py`, `rules/expr.py`, `rules/loader.py` | `COPY_SAFE` | Motor neutro. |
| `rules/version_scope.py` (5 marcadores) | `ADAPT` | Chaves de escopo Azure. |
| `rules/catalog/*.yaml` (50 arquivos, 221 regras) | `ADAPT` (Spark genérico, Parquet, Delta/Iceberg-neutro) / `NOT_APPLICABLE` (Glue, Athena, EMR, LF, S3) | Catálogo Azure novo, áreas `SFA-*`. Regras Spark genéricas re-derivadas com fonte Apache. |
| `packs/*` | `ADAPT` | — |
| `facts/scan.py` | `COPY_SAFE` | — |
| `facts/pyspark_ast.py` | `ADAPT` | remove `GlueContext`; adiciona `dbutils`, `spark.conf.set`, `abfss://`, `onelake` paths, Event Hubs Kafka options. |
| `facts/*` restantes (69 arq., 38.8k LOC, 850 marcadores) — extratores Glue job/EMR/Athena/CloudWatch/S3/LF/Kinesis/MSK/DMS | `REIMPLEMENT_AZURE_NATIVE` ou `NOT_APPLICABLE` | Extratores Azure: Databricks cluster/job JSON, UC grants, ADF pipeline, Fabric item definitions, Synapse, Event Hubs, ADLS ACL, Terraform `azurerm`, Bicep, Spark event log (neutro → `ADAPT`). |
| `diagnosis/`, `errors/` | `ADAPT` (motor) / `REIMPLEMENT_AZURE_NATIVE` (catálogo de erros) | Catálogo de erros Azure (`AuthorizationPermissionMismatch`, `PERMISSION_DENIED`, `This request is not authorized to perform this operation`, IR offline, capacity throttling…). |
| `reporting/` | `ADAPT` | — |
| `scan/` (16 marcadores) | `ADAPT` | — |
| `simulate/` (9 marcadores) | `DEFER` | Simulação de config depende de runtime matrix fonteada; reabrir em v0.3. |
| `change/` (proposal/sandbox/apply) | `ADAPT` | Apply local apenas; cloud write = deny. |

## 3. Domínios de plataforma

| AWS | Classe | Azure |
|---|---|---|
| Glue jobs / Glue versions / tuning (`tuning/`, facts Glue) | `NOT_APPLICABLE` | Sem análogo 1:1. Spark tuning genérico + Databricks/Fabric/Synapse específicos (§211). |
| EMR on EC2 / EMR on EKS | `NOT_APPLICABLE` | Compute = Databricks / Fabric Spark / Synapse Spark. |
| Glue Data Catalog (`catalog/`) | `REIMPLEMENT_AZURE_NATIVE` | Unity Catalog (§17) + Fabric/OneLake + Hive metastore legado. Nunca pressupor Glue (§23). |
| Lake Formation (`lakeformation/`, 2.5k LOC, 147 marcadores) | `REIMPLEMENT_AZURE_NATIVE` | Governança multicamada: Entra + Azure RBAC + ADLS ACL + UC + Purview + rede (§29–§30). **Não** é alias de UC. |
| AWS IAM | `REIMPLEMENT_AZURE_NATIVE` | Entra ID, Managed Identity (system/user-assigned), Service Principal, Workload Identity, RBAC (§31–§32). |
| S3 (`storage/`) | `REIMPLEMENT_AZURE_NATIVE` | ADLS Gen2 (HNS, ABFSS, ACL+RBAC, Private Endpoint), OneLake, Blob. |
| Athena | `NOT_APPLICABLE` | Mais próximo: Synapse Serverless SQL / Databricks SQL / Fabric SQL endpoint — **sem** equivalência de regra. |
| CloudWatch | `REIMPLEMENT_AZURE_NATIVE` | Azure Monitor / Log Analytics / Databricks system tables / Fabric monitoring. |
| Kinesis / MSK / Flink-on-AWS (`streaming/`) | `REIMPLEMENT_AZURE_NATIVE` | Event Hubs (+Kafka endpoint), Fabric RTI; Structured Streaming neutro `ADAPT`. |
| DMS / CDC (facts) | `ADAPT` (Debezium, Delta CDF neutros) / `REIMPLEMENT` (DMS → ADF CDC, Databricks CDC) | — |
| Glue DQDL (`dqdl/`) | `NOT_APPLICABLE` | Azure: DLT/Lakeflow expectations, contratos de dados neutros (§214–§215). |
| `dq_ai/` (12 marcadores) | `DEFER` | Reabrir com data contracts v0.2. |
| AWS FinOps (`finops/`, `capacity/`) | `REIMPLEMENT_AZURE_NATIVE` (Cost Management, Fabric capacity, Databricks DBU) / `ADAPT` (`capacity` matemático) | §35–§38. |
| Terraform AWS (`terraform/`) | `REIMPLEMENT_AZURE_NATIVE` | `azurerm` + `databricks` providers; Bicep. |
| Iceberg (`iceberg/`) | `ADAPT` | Sem Glue Catalog; catálogos UC/REST. |
| Migration Glue→Glue (`migration/`, 113 marcadores) | `NOT_APPLICABLE` (Glue upgrade) / `DEFER` (AWS→Azure, §219 "futuro, não MVP") | Synapse→Fabric knowledge entra em v0.2 (§220). |
| Control-M (`controlm/`) | `DEFER` | "quando relevante" (§13); sem caso Azure ainda. |
| Airflow (`orchestration/`) | `COPY_SAFE` | Neutro. |
| `analytics/`, `databases/`, `platform/`, `workflows/`, `workload/`, `reliability/`, `architecture/` | `ADAPT` | Revisados por arquivo na onda que os porta; nenhum entra no MVP sem teste Azure. |
| `integrate/` (hosts Claude Code/Devin/Codex/Copilot) | `ADAPT` | Skills/agents instaláveis por host. |
| `cli/` (AWS legado) e `adapters/cli.py` | `REIMPLEMENT_AZURE_NATIVE` | CLI nova `sparkforge-azure` (§0). |
| `cloud/`, `providers/` | `ADAPT` | `provider=azure`. |
| `tools/` (`sparkforge-tools`) | `DEFER` | Coberto pela CLI única + MCP; reabrir se host exigir. |
| `evals/` | `ADAPT` | — |

## 4. Ativos não-Python

| Ativo AWS | Classe | Azure |
|---|---|---|
| `skills/` (60 skills, contrato `sparkforge_contract: v1`) | `ADAPT` (formato) / `REIMPLEMENT_AZURE_NATIVE` (conteúdo) | 21 skills iniciais (§157), fonte única + mirrors gerados (§159). |
| `agents/` (personas + executores `sf-*`) | `ADAPT` | Taxonomia §94 + 20 specialists §95 com manifest §98. |
| `knowledge/` (73 docs) | `ADAPT` (agentic/engenharia neutros) / `REIMPLEMENT_AZURE_NATIVE` (plataforma) | Metadados obrigatórios `source/authority/verified_at/versions/status` (§277). |
| `lab/scenarios/golden.yaml` (Golden 20) | `REIMPLEMENT_AZURE_NATIVE` | 17 cenários Azure (§170). |
| `fixtures/` | `REIMPLEMENT_AZURE_NATIVE` | Fixtures sintéticas Azure; **nunca** dump real (§176). |
| `locks/`, `requirements.txt` | `ADAPT` | Lock com hashes. |
| `vendor/` (caveman) | `NOT_APPLICABLE` | Ferramenta de host do AWS; não é capability de produto. |
| `contracts/*.schema.json` | `ADAPT` | `platform-graph`, `lakehouse-catalog` → schemas Azure. |
| Docs `docs/vnext`, `docs/historico`, prompts `prompt_evo_*` | `NOT_APPLICABLE` | Histórico do AWS; não copiar (§266). |

## 5. Capabilities exclusivas Azure (`AZURE_ONLY`, §92)

OneLake shortcut analysis · Fabric capacity / throttling analysis · Fabric vs Synapse separation ·
Multi-layer governance conflict diagnosis (RBAC × ACL × UC × rede) · Private Endpoint DNS diagnosis ·
Databricks workspace binding analysis · ADF Integration Runtime diagnosis.

## 6. Como manter

1. Regerar evidência quando o AWS mudar de SHA de referência.
2. `tests/test_parity_matrix.py` falha se algum subsistema de `aws_audit.json` não tiver entrada em `parity.yaml`.
3. Mudança de classe exige justificativa em `parity.yaml` (`reason`).
