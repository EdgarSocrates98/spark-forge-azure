---
id: azure.fabric.data-factory
title: Fabric Data Factory - diferenças para ADF, gateways, Copy job e Dataflow Gen2
domain: fabric-data-factory
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/what-is-copy-job
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.adf.pipelines-ir-managed-vnet, azure.synapse.pipelines-and-linked-services, migration.synapse-to-fabric, azure.fabric.capacity-and-throttling]
---

# Fabric Data Factory ≠ Azure Data Factory

## Resumo

Fabric Data Factory é a "próxima geração" do ADF, mas **não é o mesmo produto**: SaaS na
capacidade F vs PaaS pay-as-you-go. Código/JSON de pipeline ADF não roda igual no Fabric.
Comparação oficial atualizada em 2026-10-05.

## Mapa de conceitos

| ADF | Fabric Data Factory |
|---|---|
| Dataset + linked service | **Connection** |
| Publish | não existe (Save/Run) |
| Debug mode | não existe |
| Execute Pipeline | **Invoke pipeline** |
| Triggers (schedule, tumbling, event) | schedule; eventos via **Activator**; tumbling ≈ schedule por intervalo |
| Mapping Data Flow | **Dataflow Gen2** com transforms de MDF (**PREVIEW**; ferramenta de upgrade para pipelines elegíveis ADF/Synapse) |
| Artefato CDC | **Copy job** |
| Synapse Link | **Mirroring** |
| Azure IR / SHIR / Azure-SSIS IR | **sem IR**; SHIR → **on-premises data gateway (OPDG)** ou **VNet data gateway**; Azure-SSIS = "a definir" |
| Managed VNet + managed private endpoints | "a definir" — usar VNet data gateway |

## Gateways vs SHIR

| | SHIR (ADF) | OPDG (Fabric) |
|---|---|---|
| Nós | até 8 | até 10 |
| SO | Windows; containers suportados | só Windows |
| Credenciais | Key Vault suportado | credential store central; **sem Key Vault** |

## Atividades

- ~90% das atividades ADF existem no Fabric.
- **Faltam**: SSIS, Synapse notebook/SJD, Validation.
- **Novas**: Outlook, Teams, Semantic model refresh, Fabric Notebook, Dataflow Gen2.

## Copy job

- Cópia full ou incremental (watermark, CDC); modos append/overwrite/merge/SCD2; múltiplos
  agendamentos; execução via gateway; Git/CI-CD; variable library.
- Core GA; **PREVIEW**: auto-partitioning, conectores de replicação CDC, SCD2 com CDC.

## Monitoramento

- Monitor hub do Fabric (jobs, alertas, capacidade, agentes) — **o Monitor hub está em
  preview** na página lida; investigação de pipeline falho com Operations agent também
  em preview.

## Armadilhas de migração ADF → Fabric

- Pipelines que dependem de managed VNet/managed private endpoints não têm equivalente
  direto.
- Credenciais em Key Vault via SHIR viram credenciais no gateway (mudança de modelo de
  segredo — revisar com segurança).
- Expressões e parâmetros globais: validar caso a caso (página de upgrade não relida).

## Não verificado

- Conteúdo do guia de upgrade/planejamento ADF → Fabric (URL conhecida, não lida).

## Fontes

- https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-factory/what-is-copy-job (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub (retrieved: 2026-10-06)
