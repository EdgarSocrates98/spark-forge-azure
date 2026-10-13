# Indice da base de conhecimento Azure

Gerado por `python scripts/check_knowledge.py --write-index`. Nao edite a mao:
o check falha se esta tabela divergir do front matter dos documentos.

Contrato de metadados: `sparkforge_azure/knowledgebase/metadata.py`.
Matrizes com fonte por celula: `knowledge/matrices/*.yaml`.
Expansao deterministica de consulta: `knowledge/query_expansion.yaml`.

| id | path | domain | status |
|---|---|---|---|
| `agentic.evidence-first` | `agentic/evidence-first.md` | agentic | VERIFIED |
| `azure.adf.pipelines-ir-managed-vnet` | `azure/adf/pipelines-ir-managed-vnet.md` | azure-data-factory | VERIFIED |
| `azure.adls.gen2` | `azure/storage/adls-gen2.md` | azure-adls | VERIFIED |
| `azure.databricks.runtime-and-compute` | `azure/databricks/runtime-and-compute.md` | azure-databricks | VERIFIED |
| `azure.databricks.workflows` | `azure/databricks/workflows.md` | azure-databricks | VERIFIED |
| `azure.entra.managed-identity` | `azure/identity/entra-managed-identity.md` | azure-entra | VERIFIED |
| `azure.eventhubs.kafka-and-spark` | `azure/eventhubs/eventhubs-and-kafka.md` | azure-event-hubs | VERIFIED |
| `azure.fabric.capacity-and-throttling` | `azure/fabric/capacity-and-throttling.md` | azure-finops | VERIFIED |
| `azure.fabric.data-engineering-spark` | `azure/fabric/data-engineering-spark.md` | fabric-data-engineering | VERIFIED |
| `azure.fabric.data-factory` | `azure/fabric/data-factory.md` | fabric-data-factory | VERIFIED |
| `azure.fabric.onelake-security` | `azure/fabric/onelake-security.md` | fabric-onelake | VERIFIED |
| `azure.fabric.onelake-shortcuts` | `azure/fabric/onelake-shortcuts.md` | fabric-onelake | VERIFIED |
| `azure.fabric.realtime-intelligence` | `azure/fabric/realtime-intelligence.md` | fabric-realtime | VERIFIED |
| `azure.fabric.workspace-identity` | `azure/fabric/workspace-identity.md` | fabric-identity | VERIFIED |
| `azure.finops.cost-management-and-dbu` | `azure/finops/cost-management-and-dbu.md` | azure-finops | VERIFIED |
| `azure.iac.bicep` | `azure/iac/bicep.md` | azure-bicep | VERIFIED |
| `azure.iac.terraform-azurerm` | `azure/iac/terraform-azurerm.md` | azure-terraform | VERIFIED |
| `azure.keyvault.secrets-and-rbac` | `azure/identity/keyvault.md` | azure-keyvault | VERIFIED |
| `azure.network.private-link-dns` | `azure/network/private-link-dns.md` | azure-networking | VERIFIED |
| `azure.observability.monitor-log-analytics` | `azure/observability/monitor-log-analytics.md` | azure-observability | VERIFIED |
| `azure.purview.unified-catalog-and-lineage` | `azure/purview/unified-catalog-and-lineage.md` | azure-purview | VERIFIED |
| `azure.spark.execution-model` | `spark/execution-model.md` | azure-spark | VERIFIED |
| `azure.spark.performance-aqe-shuffle-skew` | `spark/performance-aqe-shuffle-skew.md` | spark-performance | VERIFIED |
| `azure.spark.streaming-state-checkpoint` | `spark/streaming-state-checkpoint.md` | spark-streaming | VERIFIED |
| `azure.synapse.pipelines-and-linked-services` | `azure/synapse/pipelines-and-linked-services.md` | azure-synapse | VERIFIED |
| `azure.synapse.spark-runtimes` | `azure/synapse/spark-runtimes.md` | azure-synapse | VERIFIED |
| `azure.unity-catalog.privileges-and-fgac` | `azure/unity-catalog/privileges-and-fgac.md` | unity-catalog | VERIFIED |
| `azure.unity-catalog.securable-model` | `azure/unity-catalog/securable-model.md` | unity-catalog | VERIFIED |
| `azure.unity-catalog.troubleshooting-external-locations` | `azure/unity-catalog/troubleshooting-external-locations.md` | unity-catalog | VERIFIED |
| `data-quality.contracts-and-expectations` | `data-quality/contracts-and-expectations.md` | data-quality | VERIFIED |
| `governance.multi-layer-conflicts` | `governance/multi-layer-conflicts.md` | governance | VERIFIED |
| `lakehouse.delta-lake` | `lakehouse/delta-lake.md` | delta-lake | VERIFIED |
| `lakehouse.iceberg` | `lakehouse/iceberg.md` | iceberg | VERIFIED |
| `lakehouse.open-table-formats` | `lakehouse/open-table-formats.md` | open-table-formats | VERIFIED |
| `migration.aws-to-azure-concepts` | `migration/aws-to-azure-concepts.md` | migration | VERIFIED |
| `migration.synapse-to-fabric` | `migration/synapse-to-fabric.md` | migration | VERIFIED |
| `spark.streaming.runtime-matrix` | `streaming/runtime-matrix.md` | spark-streaming | VERIFIED |
