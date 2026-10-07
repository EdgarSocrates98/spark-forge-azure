---
id: azure.network.private-link-dns
title: Rede para dados no Azure - VNet, NSG, Private Endpoint, Private DNS, managed VNet e egress
domain: azure-networking
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/managed-virtual-network-private-endpoint
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.adls.gen2, azure.unity-catalog.troubleshooting-external-locations, azure.adf.pipelines-ir-managed-vnet, azure.keyvault.secrets-and-rbac, governance.multi-layer-conflicts]
---

# Rede para dados no Azure

## Conceitos

- **VNet/subnet**: espaço de endereços privado; **NSG** filtra tráfego por subnet/NIC.
- **Service endpoint**: estende identidade da subnet ao serviço PaaS (tráfego sai pelo
  backbone, mas o serviço mantém IP público).
- **Private Endpoint (PE)**: NIC com IP privado na sua VNet mapeada para **um recurso
  específico** (não o serviço inteiro).
- **Managed VNet**: rede gerida pelo serviço (ADF, Synapse, Fabric) com **managed private
  endpoints** aprovados pelo dono do recurso.
- **Egress**: saída para internet; em managed VNet do ADF todas as portas de saída estão
  abertas.
- (NSG e service endpoints: conceitos gerais; páginas específicas não relidas.)

## DNS é metade do problema

- A conexão continua usando o FQDN público; o Azure publica CNAME para
  `privatelink.<serviço>`; a **zona Private DNS** linkada à VNet responde com o IP privado.
- Resolver o CNAME público **não** prova que há PE nem dá acesso: com acesso público
  desabilitado o serviço rejeita mesmo que o DNS resolva.
- Uma zona por tipo de serviço; **não** reutilizar a mesma zona para PEs de serviços
  diferentes (sobrescreve A-records).
- VNet com zona `privatelink.blob...` só resolve contas **sem** PE para IP público se
  houver fallback to internet ou registro manual — senão NXDOMAIN.
- Configuração automática de DNS só acontece com os nomes de zona recomendados.

## Zonas recomendadas (Azure comercial)

| Serviço (subresource) | Zona |
|---|---|
| Storage blob | `privatelink.blob.core.windows.net` |
| ADLS Gen2 (dfs) | `privatelink.dfs.core.windows.net` |
| Storage queue | `privatelink.queue.core.windows.net` |
| Key Vault (vault) | `privatelink.vaultcore.azure.net` |
| Azure Databricks (databricks_ui_api, browser_authentication) | `privatelink.azuredatabricks.net` |
| Event Hubs / Service Bus | `privatelink.servicebus.windows.net` |
| Data Factory (dataFactory / portal) | `privatelink.datafactory.azure.net` / `privatelink.adf.azure.com` |
| Synapse (Sql, SqlOnDemand / Dev / Web) | `privatelink.sql.azuresynapse.net` / `privatelink.dev.azuresynapse.net` / `privatelink.azuresynapse.net` |
| Purview (account / portal / platform) | `privatelink.purview.azure.com` / `privatelink.purviewstudio.azure.com` / `privatelink.purview-service.microsoft.com` |
| Microsoft Fabric (workspace) | `privatelink.fabric.microsoft.com` |
| Azure Monitor (AMPLS) | `privatelink.monitor.azure.com` + `oms`/`ods` opinsights + `agentsvc` + blob |

## Padrões de dados

- **Databricks UC → ADLS com firewall**: access connector em "Resource instances" +
  "Allow Azure trusted services" quando acesso público desabilitado.
- **ADF managed VNet**: PE nasce Pending → aprovação; sem custom DNS; recurso com PE de
  outra VNet perde acesso público a partir da managed VNet.
- **Fabric Data Factory**: sem managed VNet do ADF ("a definir"); usar **VNet data
  gateway**.
- **Diagnostic settings** para storage/Event Hubs com firewall: "Allow trusted Microsoft
  services".

## Diagnóstico (ordem)

1. O FQDN resolve para IP **privado** a partir do compute? (zona linkada à VNet certa)
2. PE está **Approved**?
3. Firewall do recurso permite (VNet/IP/resource instance/trusted services)?
4. NSG/UDR/firewall de saída permitem a porta (443; Event Hubs Kafka 9093)?
5. Só então: identidade/permissões.

## Fontes

- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/managed-virtual-network-private-endpoint (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory (retrieved: 2026-10-06)
