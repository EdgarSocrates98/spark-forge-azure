# Azure/Databricks/Fabric research — as of 2026-10-06
Format: fact — source — status. VERIFIED = read directly from cited page/API on 2026-10-06 (learn.microsoft.com, PyPI JSON, GitHub API, Terraform registry API).

## 1. Azure Databricks Runtime
- Supported DBR: 19 (Spark 4.2.0, rel Jun 15 2026, EOS "determined at LTS transition", not LTS); 18 LTS (Spark 4.1.0, rel Jun 10 2026, EOS Jun 10 2029); 17.3 LTS (Spark 4.0.0, rel Oct 22 2025, EOS Oct 22 2028); 16.4 LTS (Spark 3.5.2, rel May 9 2025, EOS May 9 2028); 15.4 LTS (Spark 3.5.0, rel Aug 19 2024, EOS Aug 19 2027); 14.3 LTS (Spark 3.5.0, rel Feb 1 2024, EOS Feb 1 2027) — https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/ — status: VERIFIED
- 4 latest LTS = 18 LTS, 17.3 LTS, 16.4 LTS, 15.4 LTS (14.3 LTS supported to Feb 2027) — same — VERIFIED
- DBR 18 LTS env: Ubuntu 24.04.4, Java Zulu21 (JDK 21), Scala 2.13.16, Python 3.12.3, R 4.5.1, Delta Lake 4.2.0 — https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/18 — VERIFIED
- DBR 17.3 LTS env: Ubuntu 24.04.3, Java Zulu17, Scala 2.13.16, Python 3.12.3, R 4.4.2, Delta 4.0.0 — .../runtime/17.3lts — VERIFIED
- DBR 16.4 LTS env: Ubuntu 24.04.2, Java Zulu17, Scala 2.12.15 OR 2.13.10 (two variants), Python 3.12.3, R 4.4.0, Delta 3.3.1 — .../runtime/16.4lts — VERIFIED
- DBR 15.4 LTS env: Ubuntu 22.04.4, Java Zulu 8, Scala 2.12.15, Python 3.11.11, R 4.3.2, Delta 3.2.0 — .../runtime/15.4lts — VERIFIED
- DBR 18: UC Python UDFs use Arrow by default; TIMESTAMP in UDFs no longer carries tzinfo (restore with replace(tzinfo=timezone.utc)) — runtime/18 — VERIFIED
- Spark 4.x on Databricks: 17.3 LTS (4.0.0), 18 LTS (4.1.0), 19 (4.2.0) — runtime index — VERIFIED
- MLflow per ML runtime: 19→3.12.0, 18→3.8.1, 17.3→3.0.1, 16.4→2.21.3, 15.4→2.13.1 — runtime index — VERIFIED
- Photon: native C++ vectorized engine; default on SQL warehouses/serverless; classic compute UI default on but via Clusters/Jobs API must set runtime_engine=PHOTON (Pipelines API photon=true); stateless streaming only; no acceleration for UDF/RDD/Dataset APIs; different DBU rate on Photon instances — https://learn.microsoft.com/en-us/azure/databricks/compute/photon — VERIFIED
- Serverless env versions (3-year support): v6 (Ubuntu 24.04.4, Python 3.12.3, Databricks Connect 19, Scala 2.13.18, JDK 17, rel Sep 3 2026, EOS Sep 3 2029); v5 (DB Connect 18, Scala 2.13.16, JDK 17, rel Feb 25 2026, EOS Feb 25 2029); v4 (DB Connect 17.3.2, rel Aug 13 2025, EOS Aug 13 2028); v3 (Python 3.12.3, DB Connect 16.4.2, rel Jun 13 2025, EOS Jun 13 2028); v2 (Python 3.11.10, DB Connect 15.4.5, rel Nov 21 2024, EOS Nov 21 2027); v1 (Python 3.10.12, DB Connect 14.3.7, rel Mar 12 2024, EOS Mar 12 2027) — https://learn.microsoft.com/en-us/azure/databricks/release-notes/serverless/environment-version/ — VERIFIED
- Env versions = stable Spark Connect client API; also usable on classic compute via "Environments" dependency mode — same — PREVIEW (Beta)
- DISCREPANCY: DBR 19 doc says Spark 4.2.0 rel Jun 15 2026; spark.apache.org news lists Spark 4.2.0 on Jul 14 2026 — UNVERIFIED which is correct

## 2. Microsoft Fabric Spark runtimes
- Runtime 2.0: GA; Spark 4.1 (4.1.1), Delta 4.2, Java 21, Scala 2.13.16, Python 3.13, R 4.5.2, Mariner/Azure Linux 3.0; EOS Aug 31 2028 — https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0 , .../runtime , .../lifecycle — VERIFIED
- Runtime 2.0 GA but not yet default; plan to become default for new workspaces/environments late Sep 2026 — runtime-2-0 — VERIFIED (plan); actual switch UNVERIFIED
- Runtime 1.3: stage EOSA; Spark 3.5 (3.5.5), Delta 3.2, Java 11, Scala 2.12.17, Python 3.11, R 4.4.1, Mariner 2.0; EOS Sep 30 2026; LTS Oct 1 2026 for 6 months (to Mar 2027); still the default for new workspaces — .../lifecycle , .../runtime-1-3 — VERIFIED
- Runtime 1.2/1.1 no longer listed — .../runtime — VERIFIED (absence)
- Native Execution Engine (Gluten+Velox) on 1.3 and 2.0; toggle spark.native.enabled; "up to 6x" TPC-DS SF1000 — .../runtime — VERIFIED (vendor claim)
- Delta 4.2-specific features experimental and Spark-only; avoid on tables shared across Fabric engines — runtime-2-0 — VERIFIED
- EventHubConnector deprecated on 1.3; use Kafka Spark connector — runtime-1-3 — VERIFIED
- Lifecycle: exp preview 2-3 mo, preview 3 mo, GA 24 mo, LTS ~12 mo, EOSA 6 mo before EOS — lifecycle — VERIFIED
- Runtime 2.0 custom live pools — runtime-2-0 — PREVIEW

## 3. Azure Synapse Spark
- Synapse Spark 3.5: rel Oct 13 2025, GA; LTS from Nov 1 2027 (12 mo); EOS announcement Oct 31 2027; EOS effective Oct 31 2028 — https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-version-support — VERIFIED
- Synapse Spark 3.4: rel Nov 21 2023; "deprecated and soon to be disabled"; EOS announced Apr 30 2025; EOS effective Mar 31 2026 (past) — same — VERIFIED
- Synapse Spark 3.3: rel Nov 17 2022; EOS effective Mar 31 2025 — same — VERIFIED
- No Spark 4.x runtime in Synapse; MS recommends Fabric Runtime 2.0 — same — VERIFIED
- Pool upgrade to 3.5 not via UX; use Update-AzSynapseSparkPool -SparkVersion 3.5 -ForceApplySetting — same — VERIFIED
- Migration pages (URLs from search results; contents not fetched): https://learn.microsoft.com/en-us/fabric/data-engineering/synapse-to-fabric-spark-migration-assistant (assistant in public preview: pools, notebooks, SJDs, lake DBs); .../migrate-synapse-spark-pools ; .../synapse-migration-spark-workloads ; .../migrate-synapse-data-pipelines ; https://learn.microsoft.com/en-us/azure/data-factory/how-to-upgrade-your-azure-synapse-analytics-pipelines-to-fabric-data-factory — PREVIEW (assistant) / URLs VERIFIED via search only
- Full Synapse discontinuation not announced (only targeted deprecations) — Q&A https://learn.microsoft.com/en-us/answers/questions/5828755/do-we-have-any-indication-that-azure-synapse-analy — UNVERIFIED (community, not official)

## 4. Unity Catalog
- Object model: metastore (one per region, many workspaces) > catalog > schema > {table (managed/external/foreign), view (+materialized, metric), volume (managed/external), function (UDF, stored procedure, registered model), model, service (model/model-provider/MCP/agent services), secret, feature}; directly under metastore: storage credential, external location, external metadata, service credential, connection, share, provider, recipient, clean room — https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects — VERIFIED (services = Beta; feature = Public Preview)
- UC auto-enabled for workspaces created after Nov 9 2023 — .../unity-catalog/ — VERIFIED
- Model privileges: CREATE MODEL, CREATE MODEL VERSION, APPLY TAG, EXECUTE; registered models implemented as functions — securable-objects — VERIFIED
- Access needs USE CATALOG + USE SCHEMA + object privilege; catalog/schema grants inherit to children, metastore grants do NOT; BROWSE at catalog only — securable-objects — VERIFIED
- Fine-grained DML privileges (INSERT/UPDATE/DELETE) — securable-objects — PREVIEW (Beta)
- Workspace-catalog binding: restrict catalog to workspaces (optionally read-only); supersedes privilege grants — securable-objects (link .../access-control/workspace-catalog-binding) — VERIFIED
- External location/storage credential binding: isolation-mode ISOLATED + `databricks workspace-bindings update-bindings external-location`; no read-only binding for external locations; checked when privilege exercised; existing external tables unaffected if later unbound — https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations — VERIFIED
- Table-level row filters/column masks: SQL UDF-based; DBR >=12.2 LTS; not on views; no Iceberg REST/Unity REST access; no time travel; no clones; dedicated compute needs DBR 15.4+ w/ serverless (FGAC), writes 16.3+ — https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/filters-and-masks/ — VERIFIED (GA, no preview label)
- ABAC: governed-tag policies at catalog/schema/table (metastore-level = Beta); row filter + column mask policies; GRANT policies; DENY policies Beta; ABAC time travel Beta; recommended over per-table filters — https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/ — VERIFIED (core policies appear GA; sub-features Beta)
- Access connector for Azure Databricks: Azure resource Microsoft.Databricks/accessConnectors; system-assigned and/or user-assigned managed identity; same region as storage; creator Contributor/Owner on RG; granter Owner/User Access Administrator on storage; role Storage Blob Data Contributor (or Storage Blob Delegator + container-level Contributor); file events add Storage Queue Data Contributor, Storage Account Contributor, EventGrid EventSubscription Contributor on RG — https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities , .../external-locations-adls — VERIFIED
- VNet-injected + storage firewall: add access connector under Networking "Resource instances"; if public access disabled need "Allow Azure trusted services" (--bypass AzureServices) — same pages — VERIFIED
- External location constraints: HNS ADLS Gen2 only; ASCII-only paths; containers with immutability/WORM policies unsupported; Premium storage accounts need "Provided" queue for file events; Azure Blob (non-HNS) unsupported for file events — same + manage-external-locations — VERIFIED
- COMMON ERROR: WRITE FILES without READ FILES on external location -> PERMISSION_DENIED; grant both — manage-external-locations — VERIFIED
- File events ON by default for new locations; if credential lacks roles -> validation warning, "Force create" or enable_file_events=false; limits: 7-day cache, 2000 files/s — manage-external-locations — VERIFIED
- Read-only flag may take up to 60 min to propagate — manage-external-locations — VERIFIED
- CREATE EXTERNAL LOCATION required on BOTH metastore and storage credential; CREATE MANAGED LOCATION / CREATE EXTERNAL TABLE / CREATE EXTERNAL VOLUME on location — external-locations-adls — VERIFIED
- Other error strings (AuthorizationPermissionMismatch, 403 firewall) — not found in fetched docs — UNVERIFIED (do not cite)

## 5. ADLS Gen2
- Evaluation: role assignment exists? yes -> ABAC conditions (none = grant; all match = grant; else fall to ACL); no role -> ACL; ACL permits -> grant else deny. ACLs cannot restrict access already granted by RBAC — https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model — VERIFIED
- Shared Key / account+service SAS bypass RBAC & ACL; user-delegation SAS can be ACL-checked (suoid) — same — VERIFIED
- Roles: Blob Data Owner (set owner, all ACLs), Contributor (ACL only on owned items), Reader — same — VERIFIED
- Limits: 4000 role assignments/subscription; 32 ACL entries per file/dir (effectively 28; access and default each 32); keep group memberships <200 — same — VERIFIED
- Traverse needs --X on all parents; list needs R-X — same — VERIFIED
- Small files: target 256 MB–100 GB; ops billed in 4 MB increments; per-file overhead; Avro for write-heavy/Event Hubs, Parquet/ORC read-heavy; put date last in path when ACLs by region/subject — https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices — VERIFIED
- ABFS driver config details (fs.azure.*) — UNVERIFIED; abfss://container@account.dfs.core.windows.net URI VERIFIED via UC pages

## 6. Azure Event Hubs
- Kafka endpoint NAMESPACE.servicebus.windows.net:9093; SASL_SSL mandatory; OAUTHBEARER (Entra ID/RBAC) or PLAIN with username="$ConnectionString"; Kafka >=1.0 — https://learn.microsoft.com/en-us/azure/event-hubs/azure-event-hubs-apache-kafka-overview — VERIFIED
- Kafka supported only in Standard/Premium/Dedicated (not Basic) — same — VERIFIED
- Kafka Streams, Kafka transactions: public preview Premium/Dedicated; compression gzip only on Premium/Dedicated — same — PREVIEW
- Generated SAS tokens unsupported on Kafka endpoint; OAUTHBEARER Java needs custom sasl.login.callback.handler.class — same — VERIFIED
- Spark Kafka source/sink config (tutorial): format("kafka"); subscribe; kafka.bootstrap.servers=...:9093; kafka.sasl.mechanism=PLAIN; kafka.security.protocol=SASL_SSL; kafka.sasl.jaas.config=EH_SASL; kafka.request.timeout.ms=60000; kafka.session.timeout.ms=30000; kafka.group.id; failOnDataLoss; if offset gap error set spark.streaming.kafka.allowNonConsecutiveOffsets=true; sink uses topic + checkpointLocation — https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-kafka-spark-tutorial — VERIFIED
- Databricks shaded JAAS class (kafkashaded.org.apache...) and Spark OAUTHBEARER-with-Entra config — UNVERIFIED
- Quotas (https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-quotas — VERIFIED):
  - Basic: 256 KB msg, 1 consumer group/hub, 1 day retention, 32 partitions, 10 hubs/ns, 40 TU max, no Capture, no Kafka
  - Standard: 1 MB, 20 CG/hub, 7 days, 32 partitions, 10 hubs/ns, 40 TU, Capture priced separately, 1000 Kafka CGs/ns, 5000 connections
  - Premium: 1 MB, 100 CG/hub, 90 days, 100 partitions/hub (200 per PU per namespace), 100 hubs/PU, 16 PU, 1 TB/PU, Capture included
  - Dedicated: 20 MB, 1000 CG/hub, 90 days, 1024 partitions/hub (2000/CU), 1000 hubs, 10 CU (more via support), Capture included
  - TU: ingress 1 MB/s or 1000 ev/s; egress 2 MB/s or 4096 ev/s; 5 non-epoch receivers per CG; 12 auth rules/namespace
- Capture: Standard/Premium/Dedicated only; Avro (Parquet only via Stream Analytics no-code editor); Blob or ADLS Gen2 (Gen1 retired); no premium storage; window = first of time/size; path {Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}; writes empty files when idle; bypasses egress quota; needs containers/write + blobs/write (Storage Blob Data Owner) — https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-capture-overview — VERIFIED

## 7. Fabric Real-Time Intelligence
- Components: Real-Time hub, Eventstreams, Eventhouse (KQL DB; KQL + T-SQL), Real-Time dashboards, Activator, Map, data agents, digital twin builder (preview) — https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview — VERIFIED
- Eventstreams: many sources (Event Hubs, IoT Hub, CDC DBs, Kafka, Confluent, MSK, Kinesis, Pub/Sub, MQTT); destinations Eventhouse, Lakehouse (Delta), custom endpoint, derived stream, Activator, Spark Notebook (preview); Kafka endpoint backed by auto-created Event Hubs namespace; limits 1 MB msg, 90 d retention, at-least-once; needs >= F4 — https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview — VERIFIED
- Eventstream preview features: schema-aware eventstream, SQL operator, DeltaFlow CDC, HTTP/MQTT/Oracle CDC/ADX/Mirrored-DB sources, workspace private link, capacity operation events — same — PREVIEW; Schema Registry event schema sets GA — VERIFIED
- Eventhouse: native anomaly detection, OneLake availability; explicit GA label not on page — treat as GA; label UNVERIFIED
- Activator: no-code rules engine; sources eventstreams/Fabric+Azure events/Power BI/RT dashboards; actions pipelines, notebooks, Spark jobs, dataflows, UDFs, copy jobs, Power Automate, Teams, email; business events publish, warehouse-SQL rules, ontology rules = preview — https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction — VERIFIED (core GA by absence of label)
- RTI throttling: skips 20 s delay stage; throttles (reject) only at 60 min future capacity — .../enterprise/throttling — VERIFIED

## 8. Microsoft Purview
- Unified Catalog: governance domains, data products, glossary terms, critical data elements, OKRs, data quality, health controls/actions, self-service access policies; regional rollout; requires enterprise upgrade of new Purview experience — https://learn.microsoft.com/en-us/purview/unified-catalog — VERIFIED
- Data Map = scanning/metadata layer; classic lineage concepts https://learn.microsoft.com/en-us/purview/data-gov-classic-lineage (entity + column-level lineage, execution status) — VERIFIED
- Databricks Unity Catalog connector: new source "Azure Databricks Unity Catalog" (incremental scan; SP, system-assigned MI, PAT; managed VNet IR; no scoped scan) vs old "Azure Databricks" (Hive+UC; scoped scan); metadata of metastore/catalog/schema/table/view/columns/tags; lineage only from notebook runs, needs system.access + SELECT on system.access.table_lineage/column_lineage; column lineage from clusters not SQL warehouses; external tables metadata only; ADF-triggered Databricks lineage not shown; no lineage in China region; scan advanced-mode scope = preview — https://learn.microsoft.com/en-us/purview/register-scan-azure-databricks-unity-catalog — VERIFIED
- Fabric: native governance = OneLake catalog (discovery, insights, domains, endorsement, lineage); Purview adds Information Protection, DLP, Audit, Insider Risk, Copilot/agent governance — https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric — VERIFIED
- Purview ADF/Synapse lineage connector pages — not fetched — UNVERIFIED
- Purview SDKs (PyPI): azure-purview-datamap 1.0.0b2 (Apr 2025, current Data Map); azure-purview-catalog 1.0.0b4 (2022); account/administration/scanning stale 2021 betas — VERIFIED

## 9. ADF vs Fabric Data Factory (https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory — VERIFIED, updated 2026-10-05)
- Fabric DF = next generation of ADF; PaaS vs SaaS; capacity (F SKU) vs pay-as-you-go
- Dataset+linked service -> connections; no publish (Save/Run); no debug mode; Execute Pipeline -> Invoke pipeline; triggers -> schedule/event (Activator), tumbling as interval schedule
- Mapping Data Flow -> Dataflow Gen2 with MDF transforms (PREVIEW; upgrade tool for eligible ADF/Synapse pipelines); CDC artifact -> Copy job; Synapse Link -> Mirroring
- ADF IR types: Azure (autoresolve/regional), Self-hosted, Azure-SSIS (Synapse pipelines: Azure + self-hosted only) — https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime — VERIFIED
- Fabric: no IR; SHIR -> on-premises data gateway (OPDG) / VNet data gateway; Azure-SSIS = "to be determined"; ADF Managed VNet + managed private endpoints = "to be determined" (use VNet data gateway) — compare page — VERIFIED
- SHIR up to 8 nodes, Key Vault, containers; OPDG up to 10 nodes, Windows only, central credential store, no Key Vault — compare page — VERIFIED
- ~90% of ADF activities in Fabric; missing: SSIS, Synapse notebook/SJD, Validation; new: Outlook, Teams, Semantic model refresh, Fabric Notebook, Dataflow Gen2 — compare page — VERIFIED
- Copy job (https://learn.microsoft.com/en-us/fabric/data-factory/what-is-copy-job): full/incremental (watermark, CDC), append/overwrite/merge/SCD2, multiple schedules, gateway hosting, Git/CICD, variable library; GA core; auto-partitioning, CDC replication connectors, SCD2 CDC = PREVIEW — VERIFIED
- Upgrade guide: https://learn.microsoft.com/en-us/fabric/data-factory/upgrade-planning-azure-data-factory (referenced by compare page) — URL VERIFIED via link, content not read

## 10. Fabric capacities (https://learn.microsoft.com/en-us/fabric/enterprise/licenses , .../throttling , .../metrics-app — VERIFIED)
- F SKUs/CUs: F2=2, F4=4, F8=8, F16=16, F32=32, F64=64 (=P1/A4, 8 vcores), Trial=64, F128, F256, F512, F1024, F2048, F4096, F8192 (CU = number)
- F64+ lets Free-license Viewer-role users consume Power BI; <F64 requires Pro/PPU for viewers; F billed per second (1-min min); optional yearly reservation; P SKUs being retired
- Timepoint 30 s (2,880 per 24 h); interactive smoothed >=5 min up to 64 min; background smoothed 24 h; bursting allows temporary overuse
- Throttle stages by future-capacity consumed: <=10 min overage protection; 10-60 min interactive delay (+20 s); 60 min-24 h interactive rejection; >24 h background rejection (all rejected). In-flight ops not throttled; error CapacityLimitExceeded
- Recovery: scale SKU up, pause/resume, capacity overage billing (3x rate); carryforward + burndown; Autoscale Billing for Spark disables bursting/smoothing for Spark
- Warehouse = background; eventstreams reduce CU allocation instead of rejection
- Capacity Metrics app: capacity admin installs; pages Health, Compute (14 d), Storage (30 d), Timepoint(+summary/item detail), Autoscale for Spark, Plan capacity; latency 10-15 min; no alerts (use capacity overview events/Activator)

## 11. Cost Management & Databricks billing
- Cost Details API generateCostDetailsReport api-version 2025-03-01: async POST->poll->blobLink CSV; EA/MCA scopes only; <=1 call/day (refresh every 4 h); chunk by day/week; use Exports if >2 GB/month — https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/manage-automation — VERIFIED
- Exports API for scheduled storage export — same — VERIFIED
- Query API QPU limits 12/10 s, 60/min, 600/h per tenant; headers x-ms-ratelimit-microsoft.costmanagement-qpu-{consumed,remaining,retry-after}; 429 — same — VERIFIED
- Budgets API Microsoft.CostManagement/budgets api-version 2025-03-01 (doc default moniker 2026-06-01); scopes subscription/EA billing account/MCA billing profile/CSP customer; up to 5 Actual + 5 Forecasted thresholds; evaluated daily; GET shows last evaluated spend (use Query API for live) — https://learn.microsoft.com/en-us/rest/api/cost-management/budgets/create-or-update?view=rest-cost-management-2025-03-01 — VERIFIED
- system.billing.usage: ~12 h availability; columns record_id, account_id, workspace_id, sku_name, cloud, usage_start_time, usage_end_time, usage_date, custom_tags, usage_unit, usage_quantity, usage_metadata, identity_metadata, record_type (ORIGINAL/RETRACTION/RESTATEMENT; SUM to net), ingestion_date, billing_origin_product, product_features (is_photon, is_serverless...), usage_type; usage_metadata.metastore_id always null on Azure — https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing — VERIFIED
- system.billing.list_prices schema/retention — not fetched — UNVERIFIED

## 12. Model Context Protocol
- Latest spec version string: 2026-07-28 (/specification/latest resolves to it; previous 2025-11-25) — https://modelcontextprotocol.io/specification/latest — VERIFIED
- 2026-07-28 changes: stateless (no initialize; per-request _meta protocolVersion/clientCapabilities); Mcp-Session-Id/sessions removed; server/discover required; subscriptions/listen; ping, logging/setLevel, roots list_changed removed; tasks -> extension io.modelcontextprotocol/tasks; Multi Round-Trip Requests (resultType input_required); required resultType on results; SSE resumability removed — https://modelcontextprotocol.io/specification/2026-07-28/changelog — VERIFIED
- Minor: extensions in capabilities; OTel trace context in _meta; deterministic tools/list order; Mcp-Method/Mcp-Name headers + x-mcp-header; ttlMs/cacheScope on list/read; resource-not-found -> -32602; iss RFC 9207; inputSchema/outputSchema any JSON Schema 2020-12; structuredContent any JSON; error codes -32020..-32099 reserved — changelog — VERIFIED
- Deprecated: Roots, Sampling, Logging; HTTP+SSE transport; DCR (RFC7591) in favor of Client ID Metadata Documents; 12-month deprecation window — changelog — VERIFIED
- ToolAnnotations: readOnlyHint, destructiveHint (meaningful only if readOnlyHint false), idempotentHint, openWorldHint — https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2026-07-28/schema.ts — VERIFIED; defaults UNVERIFIED for this version; annotations are untrusted unless server trusted — .../specification/2026-07-28/server/tools — VERIFIED
- outputSchema optional; server MUST return conforming structuredContent when declared, clients SHOULD validate; also mirror as TextContent; tools/list pagination via cursor/nextCursor; tool errors via isError:true; tool names 1-128 chars [A-Za-z0-9_.-] — tools page — VERIFIED
- Python SDK `mcp`: 2.3.0 (2026-10-02), Production/Stable, Python>=3.10, MAJOR VERSION 2 (v1->v2 migration guide at py.sdk.modelcontextprotocol.io) — https://pypi.org/project/mcp/ — VERIFIED; spec version targeted by 2.3.0 UNVERIFIED

## 13. PyPI latest (pypi.org JSON API, 2026-10-06 — VERIFIED)
- azure-identity 1.26.0 (2026-10-01); azure-mgmt-resourcegraph 8.0.1 (2025-11-24); azure-mgmt-costmanagement 5.0.0 (2026-07-08, py>=3.10); azure-monitor-query 2.0.0 (2025-07-30); azure-storage-file-datalake 12.26.0 (2026-09-30, py>=3.10); azure-eventhub 5.15.1 (2025-10-30); databricks-sdk 0.147.0 (2026-10-06, py>=3.10); azure-mgmt-datafactory 10.0.0 (2026-07-08, py>=3.10); azure-mgmt-databricks 3.0.0; azure-mgmt-eventhub 12.0.0; azure-mgmt-monitor 7.0.0; azure-monitor-opentelemetry 1.8.10
- azure-purview-datamap 1.0.0b2; azure-purview-catalog 1.0.0b4; azure-purview-account/administration/scanning 2021 betas
- opentelemetry-api 1.45.0; opentelemetry-sdk 1.45.0 (2026-09-25, py>=3.10)
- mcp 2.3.0; pyspark 4.2.0; delta-spark 4.4.1; pyiceberg 0.12.0; deltalake 1.6.6; pip-audit 2.10.1; uv 0.12.23; cyclonedx-bom 7.5.0; cyclonedx-python-lib 11.12.0

## 14. Terraform / Bicep
- azurerm latest 5.8.0 (2026-10-01) — major 5 — https://registry.terraform.io/v1/providers/hashicorp/azurerm — VERIFIED; 5.0 upgrade guide not read — UNVERIFIED
- databricks provider 1.136.0 (2026-10-05); azapi 2.13.0 (2026-09-28); Terraform CLI v1.16.5 (2026-10-02) — registry/GitHub API — VERIFIED
- azurerm_databricks_access_connector exists (name, resource_group_name, location, identity block) — https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/databricks_access_connector — VERIFIED (existence); exact identity type enum UNVERIFIED
- UC TF: databricks_storage_credential, databricks_external_location (UC docs link to registry) — VERIFIED (existence)
- Bicep latest v0.48.1 (2026-10-05) — https://github.com/Azure/bicep/releases — VERIFIED; notable features UNVERIFIED

## 15. Delta / Iceberg / Spark
- Delta Lake OSS latest v4.4.1 (2026-10-05); 4.4.0 (2026-08-20: Spark 4.2 support, UC Delta API for Kernel/Flink, identity columns DDL, generated cols with UC); 4.3.0 (2026-06-18: UC Delta REST API, replaceOn/replaceUsing, UniForm atomic+incremental Iceberg conversion, Spark 4.1); 4.2.0 (2026-04-16: UC managed tables, Kernel geospatial/Variant GA/collations); 3.3.3 (2026-08-12 maintenance, no delta-iceberg) — https://github.com/delta-io/delta/releases — VERIFIED
- Delta Spark 4.4.x built for Spark 4.2.0/4.1.0/4.0.1 (Scala 2.13) — release notes — VERIFIED
- Liquid clustering supported in Fabric RT 2.0 (Delta 4.2) — runtime-2-0 page — VERIFIED; deletion vectors in Delta 4.x — not re-read — UNVERIFIED by cited page
- Iceberg latest 1.12.0 (2026-09-30) — https://github.com/apache/iceberg/releases — VERIFIED
- Iceberg spec v1,v2,v3 complete/adopted; v3 adds nanosecond timestamps, unknown, variant, geometry, geography, default values, multi-arg transforms, row lineage, binary deletion vectors, encryption keys; 1.10.0 added v3 row lineage readers — https://iceberg.apache.org/spec/ (search summary) — VERIFIED (summary); v4 UNVERIFIED
- Apache Spark: 4.2.0 (Jul 14 2026 per news; see §1 discrepancy); 4.1.3 (Jul 15 2026; 4.1.0 Dec 16 2025); 4.0.4 (Jul 15 2026; 4.0.0 May 23 2025); 3.5.9 maintenance (Jul 16 2026); 3.4.x EOL (3.4.4 Oct 27 2024) — https://spark.apache.org/news/index.html — VERIFIED
- Mapping: Fabric RT2.0 = Spark 4.1; Databricks 18 LTS = Spark 4.1.0; Synapse max = 3.5

## 16. CycloneDX / supply chain
- CycloneDX current spec 1.7 (rel Oct 21 2025); ECMA-424 (Dec 10 2025, TC54); JSON/XML/Protobuf — https://cyclonedx.org/specification/overview/ — VERIFIED
- GitHub CycloneDX/specification latest tag 1.7.2 (2026-09-17); schema id http://cyclonedx.org/schema/bom-1.7.schema.json — VERIFIED
- pip-audit 2.10.1: --locked (pyproject.toml and pylock.*.toml only), -r requirements.txt (--no-deps pinned / --require-hashes), output json/cyclonedx-json/cyclonedx-xml/markdown — https://github.com/pypa/pip-audit README — VERIFIED
- uv.lock hash behavior / uv export with hashes — doc fetch unusable — UNVERIFIED
- cyclonedx-bom 7.5.0, cyclonedx-python-lib 11.12.0 — PyPI — VERIFIED; supported output spec versions UNVERIFIED

## UNVERIFIED summary
Photon DBU multiplier; list_prices schema; Databricks shaded Kafka JAAS; Spark OAUTHBEARER for Event Hubs; ABFS driver configs; azurerm 5.0 breaking changes; access connector HCL identity enum; uv hashes; mcp 2.3.0 target spec; Eventhouse GA label; Fabric RT2.0 default switch actual date; Spark 4.2.0 date discrepancy; Iceberg v4; MCP annotation defaults in 2026-07-28; Purview ADF/Synapse lineage pages.
